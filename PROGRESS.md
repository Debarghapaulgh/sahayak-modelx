# PROGRESS — sahayak-modelx

Living status for serving + fine-tuning the open Indian 30B MoE base into West Bengal's Bengali-medium teaching
model. Plan: [`EXECUTION_PLAN.md`](EXECUTION_PLAN.md) · Data: [`DATA_ENGINE.md`](DATA_ENGINE.md) · Tracker: **[Issues](../../issues)**.

_Last updated: 2026-09-19._

## Where we are
| Area | Status | Notes |
|---|---|---|
| **License** | ✅ done | official base is **Apache-2.0** — commercial + govt + redistribution OK |
| **Base serves cleanly** | ✅ **done** | needs the **chat template**; one-command deploy in [`Serving/`](Serving) (PR #13). **Re-validated live 2026-09-19** with teaching prompts: coherent Bengali lesson plan / worked sum / story once `<think>` is stripped. Endpoint torn down after. |
| Reasoning trace | ⚠️ finding | `enable_thinking:false` is **not honoured** on LMI; the base spends the budget in an English `<think>` trace. SFT must teach direct answering; serving strips the trace. |
| Format discipline | ⚠️ finding | base stamps **ধাপ 1/2/3** on every task (quiz, concept) — blunt ধাপে ধাপে prompt. Fix in data: `DATA_ENGINE.md` Track 4. |
| Repo + CI + branching | ✅ done | `feature → develop → main`, CI + branch-policy enforced |
| Data (honest SFT set) | 🟡 ready | `Finetune/prepare_data.py` → 491/66, 0 template overlap |
| **Data engine (Debargha, PR #12)** | 🟡 **pending hardening** | 61 books OCR'd → **13,914 approved chunks**, `locale.json` (8 North Bengal districts, sourced), grounding-first pipeline, ~3,000 SFT. **Blockers:** hardcoded API keys (rotate), 125 MB JSONL in git (→ LFS/bucket), locale defaults CBSE/English, stale test, no CI run. See Track 0. |
| Localisation ontology | 🟡 to move in | `GovWB/localized-learning-db/` (affordance gate, disanalogy flags, teacher authenticity) → `DataEngine/localization/` (Track 3) |
| Data Engine plan | ✅ written | `DATA_ENGINE.md`, Tracks 0–7, epic + per-track issues |
| RAG on WBBSE | ⏭ next | index the 13,914 approved chunks with the curriculum manifest |
| Fine-tune v1 (rung 3) | ⏳ needs data ≥ 10k + GPU quota | wider LoRA + DPO — `EXECUTION_PLAN.md` Phase 4 |
| CPT (rung 4) → v2 | ⏭ planned | rights-cleared WB corpus; IndiaAI / partner compute — Phase 7 |
| Eval | ⏳ | `Evaluation/` + `Finetune/eval_compare.py` → WB-local scorecard (Track 5) |

## Resolved: the "degenerate output" saga
Both checkpoints looped on **raw completion** because the base **requires the chat template**. With messages the official
base is coherent in English and Bengali. Working config: [`Serving/README.md`](Serving/README.md). (Closed issue #4.)

## Open infra items (not blocking data work)
- **Scale-to-zero** not wired (plain ProductionVariant) → rebuild as inference components. Until then **teardown when idle**.
- **EC2 GPU quota = 0**, self-serve bump rejected → **AWS Support case**. Training fallbacks: SageMaker Training Jobs, Modal.
- **g5 capacity** flaky in Mumbai — retry; a 30B pull can take 35–40 min.

## How to check SageMaker (needs AWS access, region **ap-south-1**)
- `aws logs tail /aws/sagemaker/Endpoints/sahayak-30b --follow --region ap-south-1`
- Console: SageMaker → Endpoints; CloudWatch → Log groups; Billing → Budgets
- Rule: one writer on the endpoint at a time; **always teardown when idle**.

## Cost posture
GPU spend is from AWS **credits**, not cash — but an idle g5.12xlarge ≈ ₹16.7k/day, so every experiment tears down.
