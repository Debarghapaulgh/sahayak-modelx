# PROGRESS — sahayak-modelx

Living status for serving + fine-tuning **`sarvamai/Sarvam-30B`** (Apache-2.0 MoE) into a
Bengali-medium teaching model. Plan: [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) · Tracker: **[Issues](../../issues)**.

_Last updated: 2026-09-18._

## Where we are
| Phase | Status | Notes |
|---|---|---|
| **License** | ✅ done | official base is **Apache-2.0** — commercial + govt + redistribution OK |
| **Base serves cleanly** | ✅ **done** | fixed — it needs the **chat template** (raw completion looped). Coherent EN+BN. See [`Serving/`](Serving). |
| Repo + CI + branching | ✅ done | `feature → develop → main`, CI + branch-policy enforced |
| Data (honest SFT set) | 🟡 ready | `Finetune/prepare_data.py` → 491/66, 0 template overlap. Needs general-mix + diversity build. |
| Diverse dataset v1 | ⏭ next | coverage matrix + grounded generation (see EXECUTION_PLAN Phase 2) |
| RAG on WBBSE | ⏭ next | curriculum *facts* via retrieval (parallel track) |
| Fine-tune (QLoRA) | ⏳ ready, needs GPU quota | `Finetune/train_qlora.py` on the bf16 base |
| Eval | ⏳ | `Finetune/eval_compare.py` |

## Resolved: the "degenerate output" saga
Both checkpoints looped on **raw completion** — because Sarvam-30B **requires the chat template**.
With `/v1/chat/completions` (messages) the official base is coherent: *"…is Paris"*, *"New Delhi"*,
and a Bengali step-by-step for 15% of 400. It's a **reasoning model** (`<think>`). Working serve
config: [`Serving/README.md`](Serving/README.md). (Closed issue #4.)

## Open infra items (not blocking progress)
- **Scale-to-zero** — not wired (plain ProductionVariant); rebuild as inference components. Until
  then **teardown when idle**.
- **EC2 GPU quota = 0** and the self-serve bump was rejected → needs an **AWS Support case**.
- **g5 capacity** flaky in Mumbai — deploys sometimes fail `InsufficientInstanceCapacity`; retry.

## How to check SageMaker (needs AWS access, region **ap-south-1**)
- `aws logs tail /aws/sagemaker/Endpoints/sahayak-30b --follow --region ap-south-1`
- Console: SageMaker → Endpoints; CloudWatch → Log groups; Billing → Budgets
- Rule: one writer on the endpoint at a time; **always teardown when idle**.

## Cost posture
GPU spend is from AWS **credits**, not cash — but an idle g5.12xlarge ≈ ₹16.7k/day, so every
experiment tears down. Keep active GPU-hours low.
