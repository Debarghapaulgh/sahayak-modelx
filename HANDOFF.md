# HANDOFF — sahayak-modelx · written 2026-09-20 23:41 IST

Read this first in a new session, then `PROGRESS.md`, `EXECUTION_PLAN.md` ("GPU runs — process of record"), `DATA_ENGINE.md`, and issue #28. Memory files for this project live on the Mac at `~/.claude/projects/-Users-sargupta-GovWB/memory/` (loaded automatically only when the working directory is `/Users/sargupta/GovWB`).

## Goal and where we are
West Bengal's own Bengali-medium teaching model: open Apache-2.0 Sarvam-30B MoE base → LoRA/QLoRA on our licence-clean, teacher-attested WB dataset (v1) → later CPT (v2) → from-scratch north star (Siliguri centre). **Meeting with the Hon'ble IT Minister, Govt of West Bengal: Tue 23 Sep.** Demo must be ready Mon 22 Sep: adapter → eval scorecard → served in Mumbai next to the base.

Done: data engine (11,580 records, 10,637 train / 943 eval, `DataEngine/out/MANIFEST.json`, rebuild = `compile_wb_sft.py` seed 42); training path proven end to end on SageMaker; micro-batch sweep (bs1×ga8 51 s/step → **bs8×ga1 16.1 s/step**, 3.2×, eval loss unchanged); launcher hardened (owner-prefixed jobs, provenance gate, checkpoints/resume, per-instance-type guard, `--keep-alive`, `--spot`); free CPU rehearsal `Finetune/smoke_local.sh` (required before launch).

## Live state at 2026-09-20 23:41 IST
- **Sachitt's full run `sahayak-30b-full-2`** (ap-south-1, ml.g5.12xlarge): InProgress/Training. Repo script + our data, but **bs 1 × ga 8** (47 s/step → ~35 h ≈ ₹25k, ends Tue ~08:00), base = `abhinand/sarvam-30b-bf16` (a bf16 cast of the official FP32; tensor set identical), cap 120 h, checkpoints every 50 steps in `s3://sagemaker-sahayak-aps1/checkpoints/sahayak-30b-full-2/` (latest: checkpoint-150). Started 21:21 IST Sun. **Recommendation on the table: stop it and relaunch at bs 8 × ga 1 on the official base (~12 h, ~₹8.5k) — Abhishek's call, it is Sachitt's job.**
- Nothing of ours running; no endpoints in any region.

## Decisions waiting on Abhishek
1. Stop/relaunch `full-2` (above).
2. File quota requests: us-west-2 + ap-southeast-1 `ml.g5.12xlarge`/`ml.g6e.12xlarge` training → 1; Mumbai training 1→2, spot 0→2, `g6e.12xlarge` endpoint → 2. (`aws service-quotas request-service-quota-increase`; account change → needs his word.)
3. Send the AWS email (draft in the 20 Sep conversation; recreate from #28 + this file if lost): capacity assurance in ap-south-1 for 21–23 Sep + the quotas above + a named contact.
4. Who builds the bf16 FSDP variant (Sachitt's #28 step 4; can wait until after the 23rd).

## This week's sequence (re-planned around the 23rd)
Mon: adapter done (if relaunched tonight) → **eval runner** (base vs adapter on `Evaluation/wb_eval/seeds/` 76 probes + 11 traps + `FORMAT_SPEC.md` validators; run as a SageMaker job) → merge (`Finetune/merge_and_quantize.py`) → deploy on the **second Mumbai endpoint slot** next to the base (`Serving/deploy_endpoint.py`) → capture real outputs. Tue: review outputs, demo script, fallback = base + RAG. After the 23rd: FSDP variant, small-model recipe loop, DPO, CPT planning.

## Sachitt (Sachitt-AV-08; AWS identities `sagemaker-user`, `sahayak-deploy`)
Reads #28 (adopted everything on it) but has never replied; launches unposted jobs; his launcher once had a stop-all step that killed our jobs. Day 1: 23 jobs, 21 failed, ≈ ₹2,950; day 2: the full run above. His lane (no shared-slot risk): (a) our own bf16 conversion of the official FP32 into `s3://sagemaker-sahayak-aps1/models/`; (b) **scale-to-zero on the endpoint** (inference components) — needed for demo week; (c) FSDP variant after the 23rd. Rule to enforce: no job > 1 h without a `--dry-run` paste on #28; `SM_OWNER=sachitt`.

## Environment and facts you need
- Repo: `~/SahayakAIV2/sahayakai/sahayak-modelx`, branch flow `feature → develop → main` (never PR to main). CI: ruff E9/F63/F7/F82, nbformat, gitleaks.
- Python: `~/.pyenv/shims/python3` (yaml, pytest); launcher runs with `../deploy-aws-sahayak-30b/.venvb/bin/python` (boto3). AWS profile `sargvision` (**authenticates as root** — replace with an IAM user). Account 690839588406.
- Regions: **ap-south-1 = serving** (data residency; g5/g6e capacity unreliable: 80 min–3.5 h waits on Sun 20 Sep). **us-east-1 = experiments** (g5.12xlarge training quota 1, granted in 2 min; bucket `sagemaker-sahayak-30b-demo`). No other region has GPU quota. Mumbai bucket `sagemaker-sahayak-aps1`; `sahayak-models-aps1` is read-only for the exec role `sahayak-sagemaker-exec`.
- Quotas (ap-south-1): g5.12xlarge training 1 / endpoint 2 / warm pool 1; g6e.12xlarge training 1 + spot 1; many other g5/g6/g6e/g4dn types at 1; spot g5 0; EC2 G 0.
- Model facts: official `sarvamai/Sarvam-30B` is FP32 (128.6 GB, 26 shards), chat template in a separate `chat_template.jinja`, LoRA targets `query_key_value`,`dense` (router `gate` never); needs transformers ≥ 4.51 (pinned 4.51.3, trl 0.17.0, peft 0.15.2); reasoning model (`<think>`), `enable_thinking:false` not honoured on LMI.
- Serving: LMI `djl-inference:0.36.0-lmi28.0.0-cu130`, chat template mandatory; idle endpoint ≈ ₹16,700/day — teardown discipline; scale-to-zero needs inference components.
- Spend ledger in `PROGRESS.md`. Credits: ~$5k AWS Activate.

## Commands
```bash
cd ~/SahayakAIV2/sahayakai/sahayak-modelx/Finetune && ./smoke_local.sh                      # free rehearsal (required)
AWS_PROFILE=sargvision ../../deploy-aws-sahayak-30b/.venvb/bin/python launch_sagemaker_training.py --dry-run
AWS_PROFILE=sargvision AWS_REGION=us-east-1 SM_BUCKET=sagemaker-sahayak-30b-demo SM_OWNER=<you> \
  ../../deploy-aws-sahayak-30b/.venvb/bin/python launch_sagemaker_training.py --epochs 2 --save-steps 50 --keep-alive 20 --wait   # full run, bs8×ga1 default
python launch_sagemaker_training.py --status JOB | --logs JOB | --stop JOB      # --stop refuses other owners' jobs without --force
python DataEngine/localization/compile_wb_sft.py                                 # rebuild data (seed 42; sha256 must match MANIFEST)
```

## Standing rules
No keys in code (14 leaked keys in `develop` history still need rotation by Abhishek). Data: only `licence: own` (`Final/` from PR #12 is quarantined). No student PII. Never claim India residency for stored data (some is in us-east-1/Singapore). Teacher approval is informal (`teacher_informal` + attested_by + date). Never stop someone else's job silently. Commit trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`; PR footer `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

Tracking: #3 (model epic), #19 (data epic), #28 (Sachitt), #23 (Varun eval), #16 (Debargha locale). PRs #27–#41 on develop.
