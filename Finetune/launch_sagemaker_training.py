#!/usr/bin/env python3
"""
launch_sagemaker_training.py — run train_qlora.py as a SageMaker Training Job (boto3 only, no SageMaker SDK).

  python launch_sagemaker_training.py --dry-run                        # print the job spec; creates nothing
  python launch_sagemaker_training.py --limit 200 --max-steps 20 --wait # smoke test on one ml.g5.12xlarge (~30-45 min)
  python launch_sagemaker_training.py --epochs 2 --wait                 # full run on the compiled 10k set
  python launch_sagemaker_training.py --status JOB | --logs JOB | --stop JOB

What it does: uploads DataEngine/out/sft_wb_v1_{train,eval}.jsonl and this folder (sourcedir.tar.gz) to S3, then
create_training_job with the HuggingFace PyTorch training DLC in script mode (requirements.txt is installed at start).
Region, account, role and bucket come from flags/env; no secrets in code. The job stops itself when done, so unlike an
endpoint it cannot run up an idle bill — but a stuck job still bills until MaxRuntimeInSeconds.

Quota (ap-south-1, read 2026-09-19): ml.g5.12xlarge training job usage = 1 → one job at a time; spot training = 0 → on-demand.
"""
import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import time

import boto3

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
REGION = os.environ.get("AWS_REGION", "ap-south-1")
ROLE_NAME = os.environ.get("SM_ROLE", "sahayak-sagemaker-exec")
BUCKET = os.environ.get("SM_BUCKET", "sagemaker-sahayak-aps1")   # same region as the job; AmazonSageMakerFullAccess covers *sagemaker* buckets
IMAGE = os.environ.get("SM_TRAIN_IMAGE", "763104351884.dkr.ecr.{region}.amazonaws.com/huggingface-pytorch-training:"
                                          "2.5.1-transformers4.49.0-gpu-py311-cu124-ubuntu22.04")   # verified present in ap-south-1
SOURCE_FILES = ["train_qlora.py", "requirements.txt", "inspect_modules.py"]
DATA_TRAIN = os.path.join(ROOT, "DataEngine", "out", "sft_wb_v1_train.jsonl")
DATA_EVAL = os.path.join(ROOT, "DataEngine", "out", "sft_wb_v1_eval.jsonl")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def upload_data(s3, bucket, train, ev):
    """s3://bucket/data/<sha>/train/… and /eval/… — same content, same key, so reruns cost nothing."""
    keys = {}
    for chan, path in (("train", train), ("eval", ev)):
        if not path or not os.path.exists(path):
            continue
        key = f"data/{sha(path)}/{chan}/{os.path.basename(path)}"
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
          "bs": a.bs, "ga": a.ga, "r": a.r, "alpha": a.alpha, "target-modules": a.target_modules, "eval-steps": a.eval_steps}
    channels = [{"ChannelName": c, "InputMode": "File",
                 "DataSource": {"S3DataSource": {"S3DataType": "S3Prefix", "S3Uri": uri, "S3DataDistributionType": "FullyReplicated"}}}
                for c, uri in data.items()]
    return {"TrainingJobName": job, "RoleArn": role_arn,
            "AlgorithmSpecification": {"TrainingImage": IMAGE.format(region=REGION), "TrainingInputMode": "File",
                                       "EnableSageMakerMetricsTimeSeries": True,
                                       "MetricDefinitions": [{"Name": "train:loss", "Regex": "'loss': ([0-9.]+)"},
                                                             {"Name": "eval:loss", "Regex": "'eval_loss': ([0-9.]+)"}]},
            "HyperParameters": {k: json.dumps(v) for k, v in hp.items()},     # script mode json-decodes each value
            "InputDataConfig": channels,
            "OutputDataConfig": {"S3OutputPath": f"s3://{a.bucket}/runs/"},
            "ResourceConfig": {"InstanceType": a.instance, "InstanceCount": 1, "VolumeSizeInGB": a.volume_gb},
            "StoppingCondition": {"MaxRuntimeInSeconds": a.max_runtime_min * 60},
            "Environment": {"HF_HOME": "/tmp/hf", "HF_HUB_ENABLE_HF_TRANSFER": "1", "TOKENIZERS_PARALLELISM": "false",
                            "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
            "Tags": [{"Key": "project", "Value": "sahayak-modelx"}, {"Key": "owner", "Value": os.environ.get("USER", "team")}]}


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
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--status"); ap.add_argument("--logs"); ap.add_argument("--stop")
    ap.add_argument("--lines", type=int, default=60)
    ap.add_argument("--instance", default="ml.g5.12xlarge")
    ap.add_argument("--volume-gb", type=int, default=200)          # ~60 GB of bf16 shards + cache
    ap.add_argument("--max-runtime-min", type=int, default=0, help="0 = 150 for a smoke test, 1440 otherwise")
    ap.add_argument("--bucket", default=BUCKET)
    ap.add_argument("--train", default=DATA_TRAIN); ap.add_argument("--eval", default=DATA_EVAL)
    ap.add_argument("--epochs", type=float, default=2.0); ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--maxlen", type=int, default=1024); ap.add_argument("--bs", type=int, default=1); ap.add_argument("--ga", type=int, default=8)
    ap.add_argument("--r", type=int, default=16); ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--target-modules", default="q_proj,k_proj,v_proj,o_proj"); ap.add_argument("--eval-steps", type=int, default=0)
    ap.add_argument("--hourly-usd", type=float, default=8.1, help="only for the cost estimate printed at the end")
    a = ap.parse_args()
    sm = boto3.client("sagemaker", region_name=REGION)
    if a.status:
        d = sm.describe_training_job(TrainingJobName=a.status)
        print(json.dumps({k: str(d.get(k)) for k in ("TrainingJobStatus", "SecondaryStatus", "FailureReason", "BillableTimeInSeconds", "ModelArtifacts")}, indent=1)); return
    if a.logs:
        logs(a.logs, a.lines); return
    if a.stop:
        sm.stop_training_job(TrainingJobName=a.stop); print("stop requested:", a.stop); return

    smoke = a.max_steps > 0 or a.limit > 0
    a.max_runtime_min = a.max_runtime_min or (150 if smoke else 1440)
    acct = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
    role_arn = f"arn:aws:iam::{acct}:role/{ROLE_NAME}"
    job = f"sahayak-qlora-{'smoke' if smoke else 'v1'}-{time.strftime('%Y%m%d-%H%M%S')}"
    if not os.path.exists(a.train):
        sys.exit(f"missing {a.train}: run DataEngine/localization/compile_wb_sft.py first")
    if a.dry_run:
        data = {"train": f"s3://{a.bucket}/data/<sha>/train/", **({"eval": f"s3://{a.bucket}/data/<sha>/eval/"} if os.path.exists(a.eval) else {})}
        spec = build_spec(a, role_arn, data, f"s3://{a.bucket}/source/{job}/sourcedir.tar.gz", job)
        print(json.dumps(spec, indent=1)); print("\nDRY RUN: nothing created."); return
    s3 = boto3.client("s3", region_name=REGION)
    data = upload_data(s3, a.bucket, a.train, a.eval)
    source = upload_source(s3, a.bucket, job)
    spec = build_spec(a, role_arn, data, source, job)
    sm.create_training_job(**spec)
    print("created:", job); print("console:", f"https://{REGION}.console.aws.amazon.com/sagemaker/home?region={REGION}#/jobs/{job}")
    if a.wait:
        status = wait(sm, job, a.hourly_usd)
        sys.exit(0 if status == "Completed" else 1)


if __name__ == "__main__":
    main()
