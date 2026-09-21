#!/usr/bin/env python3
"""
launch_sagemaker_training.py — run train_qlora.py as a SageMaker Training Job (boto3 only, no SageMaker SDK).

  ./smoke_local.sh                                                       # FREE rehearsal on CPU first (required)
  python launch_sagemaker_training.py --dry-run                          # print the job spec; creates nothing
  python launch_sagemaker_training.py --limit 200 --max-steps 20 --wait  # smoke test on one ml.g5.12xlarge (~30-45 min)
  python launch_sagemaker_training.py --epochs 2 --save-steps 50 --wait  # full run, checkpoints synced to S3 every 50 steps
  python launch_sagemaker_training.py --resume-from JOB --epochs 2 --save-steps 50 --wait   # continue a capped/failed run
  python launch_sagemaker_training.py --status JOB | --logs JOB | --stop JOB

What it does: verifies the training file against DataEngine/out/MANIFEST.json (licence own + sha256), uploads the data
by content hash and this folder (sourcedir.tar.gz) to S3, then create_training_job with the HuggingFace PyTorch training
DLC in script mode (requirements.txt is installed at start). CheckpointConfig keeps /opt/ml/checkpoints in S3 while the
job runs, so a run that hits MaxRuntime or fails can be resumed instead of repeated. Region, account, role and bucket come
from flags/env; no secrets in code. Job names carry the owner (SM_OWNER or $USER); --stop refuses other people's jobs.

Quota (ap-south-1, read 2026-09-19): ml.g5.12xlarge training job usage = 1 -> one job at a time on the account;
post on #28 before launching. spot training = 0 -> on-demand (the --spot flag is ready for when that quota exists).
"""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time

import boto3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REGION = os.environ.get("AWS_REGION", "ap-south-1")
ROLE_NAME = os.environ.get("SM_ROLE", "sahayak-sagemaker-exec")
BUCKET = os.environ.get("SM_BUCKET", "sagemaker-sahayak-aps1")   # same region as the job; AmazonSageMakerFullAccess covers *sagemaker* buckets
OWNER = os.environ.get("SM_OWNER", os.environ.get("USER", "team")).lower().replace("_", "-")[:12]
IMAGE = os.environ.get("SM_TRAIN_IMAGE", "763104351884.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-training:"
                                          "2.5.1-transformers4.49.0-gpu-py311-cu124-ubuntu22.04")   # verified present in ap-south-1
SOURCE_FILES = ["train_qlora.py", "requirements.txt", "inspect_modules.py"]
DATA_TRAIN = os.path.join(ROOT, "DataEngine", "out", "sft_wb_v1_train.jsonl")
DATA_EVAL = os.path.join(ROOT, "DataEngine", "out", "sft_wb_v1_eval.jsonl")
MANIFEST = os.path.join(ROOT, "DataEngine", "out", "MANIFEST.json")


def sha(path, n=None):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:n] if n else h.hexdigest()


def check_provenance(train, allow):
    """Refuse data that is not the compiled, licence-clean set unless the caller says so explicitly."""
    if not os.path.exists(MANIFEST):
        msg = f"no {MANIFEST}: run DataEngine/localization/compile_wb_sft.py"
    else:
        m = json.load(open(MANIFEST))
        want = (m.get("sha256") or {}).get(os.path.basename(train))
        if m.get("licence") != "own":
            msg = f"MANIFEST licence is {m.get('licence')!r}, not 'own'"
        elif not want:
            msg = f"{os.path.basename(train)} is not in MANIFEST.json (only compiled files are)"
        elif want != sha(train):
            msg = f"{os.path.basename(train)} does not match MANIFEST sha256 (recompile, or you edited it)"
        else:
            print(f"provenance OK: {os.path.basename(train)} licence=own sha256={want[:12]} ({m.get('train')} rows)")
            return
    if allow:
        print("WARNING provenance not verified:", msg)
    else:
        sys.exit(f"refusing to train: {msg}. Pass --allow-unverified-data only for throwaway experiments.")


def upload_data(s3, bucket, train, ev):
    """s3://bucket/data/<sha>/train/… and /eval/… — same content, same key, so reruns cost nothing."""
    keys = {}
    for chan, path in (("train", train), ("eval", ev)):
        if not path or not os.path.exists(path):
            continue
        key = f"data/{sha(path, 12)}/{chan}/{os.path.basename(path)}"
        try:
            s3.head_object(Bucket=bucket, Key=key)
        except s3.exceptions.ClientError:
            s3.upload_file(path, bucket, key)
        keys[chan] = f"s3://{bucket}/{os.path.dirname(key)}/"
    return keys


def upload_source(s3, bucket, job):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for f in SOURCE_FILES:
            p = os.path.join(HERE, f)
            if os.path.exists(p):
                tar.add(p, arcname=f)
    buf.seek(0)
    key = f"source/{job}/sourcedir.tar.gz"
    s3.upload_fileobj(buf, bucket, key)
    return f"s3://{bucket}/{key}"


def build_spec(a, role_arn, data, source, job):
    hp = {"sagemaker_program": "train_qlora.py", "sagemaker_submit_directory": source, "sagemaker_region": REGION,
          "sagemaker_container_log_level": 20, "sagemaker_job_name": job,
          "epochs": a.epochs, "max-steps": a.max_steps, "limit": a.limit, "lr": a.lr, "maxlen": a.maxlen,
          "bs": a.bs, "ga": a.ga, "lora-r": a.r, "lora-alpha": a.alpha, "target-modules": a.target_modules, "eval-steps": a.eval_steps,
          "quant": a.quant, "attn": a.attn, "save-steps": a.save_steps, "resume": 1 if a.resume_from else 0}
    assert all(len(k) > 1 for k in hp), "1-char hyperparameter names arrive as -k and break argparse (seen 2026-09-19)"
    channels = [{"ChannelName": c, "InputMode": "File",
                 "DataSource": {"S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": uri, "S3DataDistributionType": "FullyReplicated"}}}
                for c, uri in data.items()]
    ckpt_job = a.resume_from or job
    spec = {"TrainingJobName": job, "RoleArn": role_arn,
            "AlgorithmSpecification": {"TrainingImage": IMAGE.format(region=REGION), "TrainingInputMode": "File",
                                       "EnableSageMakerMetricsTimeSeries": True,
                                       "MetricDefinitions": [{"Name": "train:loss", "Regex": "'loss': ([0-9.]+)"},
                                                             {"Name": "eval:loss", "Regex": "'eval_loss': ([0-9.]+)"}]},
            "HyperParameters": {k: json.dumps(v) for k, v in hp.items()},     # script mode json-decodes each value
            "InputDataConfig": channels,
            "OutputDataConfig": {"S3OutputPath": f"s3://{a.bucket}/runs/"},
            "CheckpointConfig": {"S3Uri": f"s3://{a.bucket}/checkpoints/{ckpt_job}/", "LocalPath": "/opt/ml/checkpoints"},
            "ResourceConfig": {"InstanceType": a.instance, "InstanceCount": 1, "VolumeSizeInGB": a.volume_gb,
                               **({"KeepAlivePeriodInSeconds": a.keep_alive * 60} if a.keep_alive else {})},
            "StoppingCondition": {"MaxRuntimeInSeconds": a.max_runtime_min * 60},
            "Environment": {"HF_HOME": "/tmp/hf", "HF_HUB_ENABLE_HF_TRANSFER": "1", "TOKENIZERS_PARALLELISM": "false",
                            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
            "Tags": [{"Key": "project", "Value": "sahayak-modelx"}, {"Key": "owner", "Value": OWNER}]}
    if a.spot:
        spec["EnableManagedSpotTraining"] = True
        spec["StoppingCondition"]["MaxWaitTimeInSeconds"] = a.max_runtime_min * 60 * 2
    return spec


def wait(sm, job, hourly_usd):
    last = None
    while True:
        d = sm.describe_training_job(TrainingJobName=job)
        cur = (d["TrainingJobStatus"], d.get("SecondaryStatus"))
        if cur != last:
            print(time.strftime("%H:%M:%S"), *cur, flush=True); last = cur
        if d["TrainingJobStatus"] in ("Completed", "Failed", "Stopped"):
            secs = d.get("BillableTimeInSeconds", 0)
            print(f"{d['TrainingJobStatus']}: billable {secs / 60:.0f} min ≈ ${secs / 3600 * hourly_usd:.2f} (estimate at ${hourly_usd}/h)")
            if d["TrainingJobStatus"] == "Failed":
                print("reason:", d.get("FailureReason"))
            else:
                print("artifact:", d.get("ModelArtifacts", {}).get("S3ModelArtifacts"))
            return d["TrainingJobStatus"]
        time.sleep(60)


def logs(job, lines):
    cw = boto3.client("logs", region_name=REGION)
    streams = cw.describe_log_streams(logGroupName="/aws/sagemaker/TrainingJobs", logStreamNamePrefix=job).get("logStreams", [])
    if not streams:
        print("no log streams yet"); return
    ev = cw.get_log_events(logGroupName="/aws/sagemaker/TrainingJobs", logStreamName=streams[0]["logStreamName"], limit=lines, startFromHead=False)
    for e in ev["events"]:
        print(e["message"].rstrip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--print-args", action="store_true", help="print the exact argv the SageMaker toolkit will pass to train_qlora.py (used by smoke_local.sh)")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--status"); ap.add_argument("--logs"); ap.add_argument("--stop")
    ap.add_argument("--force", action="store_true", help="with --stop: stop a job that is not yours (say why on #28)")
    ap.add_argument("--lines", type=int, default=60)
    ap.add_argument("--instance", default="ml.g5.12xlarge")
    ap.add_argument("--volume-gb", type=int, default=200)          # ~60 GB of bf16 shards + cache + checkpoints
    ap.add_argument("--max-runtime-min", type=int, default=0, help="0 = 150 for a smoke test, 1440 otherwise")
    ap.add_argument("--spot", action="store_true", help="managed spot (needs spot training quota > 0)")
    ap.add_argument("--keep-alive", type=int, default=0, help="minutes to keep the instance warm after the job (warm pool; quota 1) so the next job skips the capacity queue")
    ap.add_argument("--bucket", default=BUCKET)
    ap.add_argument("--train", default=DATA_TRAIN); ap.add_argument("--eval", default=DATA_EVAL)
    ap.add_argument("--allow-unverified-data", action="store_true")
    ap.add_argument("--skip-local-smoke", action="store_true", help="do not require a passing ./smoke_local.sh stamp")
    ap.add_argument("--resume-from", default=None, help="job name whose S3 checkpoints to continue from")
    ap.add_argument("--epochs", type=float, default=2.0); ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--save-steps", type=int, default=-1, help="-1 = 50 for a full run, 0 for a smoke test")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--maxlen", type=int, default=1024)
    # bs 8 x ga 1 measured 3.2x faster than bs 1 x ga 8 on g5.12xlarge (2026-09-20): the 4-bit dequant is paid per forward
    ap.add_argument("--bs", type=int, default=8); ap.add_argument("--ga", type=int, default=1)
    ap.add_argument("--r", type=int, default=16); ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--target-modules", default="query_key_value,dense"); ap.add_argument("--eval-steps", type=int, default=0)
    ap.add_argument("--quant", default="4bit", choices=["4bit", "none"]); ap.add_argument("--attn", default="sdpa")
    ap.add_argument("--hourly-usd", type=float, default=8.1, help="only for the cost estimate printed at the end")
    a = ap.parse_args()
    sm = boto3.client("sagemaker", region_name=REGION)
    if a.status:
        d = sm.describe_training_job(TrainingJobName=a.status)
        print(json.dumps({k: str(d.get(k)) for k in ("TrainingJobStatus", "SecondaryStatus", "FailureReason", "BillableTimeInSeconds", "ModelArtifacts", "CheckpointConfig")}, indent=1)); return
    if a.logs:
        logs(a.logs, a.lines); return
    if a.stop:
        if not a.stop.startswith(f"sahayak-qlora-{OWNER}-") and not a.force:
            sys.exit(f"{a.stop} is not one of your jobs (owner prefix sahayak-qlora-{OWNER}-); use --force only after posting on #28")
        sm.stop_training_job(TrainingJobName=a.stop); print("stop requested:", a.stop); return

    smoke = a.max_steps > 0 or a.limit > 0
    a.max_runtime_min = a.max_runtime_min or (150 if smoke else 1440)
    if a.save_steps < 0:
        a.save_steps = 0 if smoke else 50
    if a.print_args:
        # the sagemaker-training toolkit turns each user hyperparameter into --key value (or -k value for 1-char keys)
        hp = build_spec(a, "arn:aws:iam::0:role/x", {}, "s3://x/y", "x")["HyperParameters"]
        argv = []
        for k, v in sorted(hp.items()):
            if not k.startswith("sagemaker_"):
                v = json.loads(v); argv += [("--" if len(k) > 1 else "-") + k, str(v)]
        print(" ".join(argv)); return
    if not os.path.exists(a.train):
        sys.exit(f"missing {a.train}: run DataEngine/localization/compile_wb_sft.py first")
    check_provenance(a.train, a.allow_unverified_data)
    stamp = os.path.join(HERE, ".smoke_local.ok")
    if not a.skip_local_smoke and not (os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 7 * 86400):
        sys.exit("no recent ./smoke_local.sh pass (Finetune/.smoke_local.ok older than 7 days or missing): run it first, or --skip-local-smoke")
    acct = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
    role_arn = f"arn:aws:iam::{acct}:role/{ROLE_NAME}"
    job = f"sahayak-qlora-{OWNER}-{'smoke' if smoke else 'v1'}-{time.strftime('%Y%m%d-%H%M%S')}"
    if a.dry_run:
        data = {"train": f"s3://{a.bucket}/data/<sha>/train/", **({"eval": f"s3://{a.bucket}/data/<sha>/eval/"} if os.path.exists(a.eval) else {})}
        spec = build_spec(a, role_arn, data, f"s3://{a.bucket}/source/{job}/sourcedir.tar.gz", job)
        print(json.dumps(spec, indent=1)); print("\nDRY RUN: nothing created."); return
    # the quota is per instance type: only a running job on the SAME type blocks us
    busy = [j["TrainingJobName"] for j in sm.list_training_jobs(StatusEquals="InProgress", MaxResults=10).get("TrainingJobSummaries", [])
            if sm.describe_training_job(TrainingJobName=j["TrainingJobName"])["ResourceConfig"]["InstanceType"] == a.instance]
    if busy:
        sys.exit(f"a training job is already InProgress on {a.instance} (quota 1): " + ", ".join(busy))
    s3 = boto3.client("s3", region_name=REGION)
    data = upload_data(s3, a.bucket, a.train, a.eval)
    source = upload_source(s3, a.bucket, job)
    spec = build_spec(a, role_arn, data, source, job)
    sm.create_training_job(**spec)
    print("created:", job); print("console:", f"https://{REGION}.console.aws.amazon.com/sagemaker/home?region={REGION}#/jobs/{job}")
    print("checkpoints:", spec["CheckpointConfig"]["S3Uri"])
    if a.wait:
        status = wait(sm, job, a.hourly_usd)
        sys.exit(0 if status == "Completed" else 1)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(str(e))
