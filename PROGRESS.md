# PROGRESS — sahayak-modelx

Living status for serving + fine-tuning **`sarvamai/Sarvam-30B`** (Apache-2.0 MoE) into a
Bengali-medium teaching model. Updated as work lands. Tracker: **[Issues](../../issues)**.

_Last updated: 2026-09-18._

## Where we are
| Phase | Status | Notes |
|---|---|---|
| **License** | ✅ done | official base is **Apache-2.0** — commercial + govt + redistribution OK |
| **Base serves cleanly** | 🔴 **blocked** | model emits **degenerate text** under vLLM/LMI. NOT the checkpoint (official + 3rd-party both fail). Cause hunt below. |
| Data (honest SFT set) | 🟡 ready | `Finetune/prepare_data.py` → 491 train / 66 eval, **0 template overlap**. Needs general-mix. |
| Fine-tune (QLoRA) | ⏸ waiting on base | `Finetune/train_qlora.py` — needs a cleanly-serving base first |
| Eval | ⏸ | `Finetune/eval_compare.py` |
| Deploy fine-tuned | ⏸ | `Finetune/merge_and_quantize.py` |

## The active blocker — degenerate output
Both the official bf16 base and the third-party 4-bit re-quant produce loops
(`"is is is…"`, blank lines, `</arg_value>`) when served on SageMaker LMI (vLLM).
**Leading causes (being tested):**
1. **Prompt format** — Sarvam mandates the **chat template**; raw completion is unsupported.
   Retesting now with the messages API (chat template applied server-side).
2. **vLLM build** — Sarvam recommends a specific vLLM (fork / hot-patch) for full support;
   the exact vLLM-listed repo is `sarvamai/sarvam2-30b-a3b`.

**Next if chat-format still fails:** try `sarvam2-30b-a3b` and/or Sarvam's vLLM build;
or serve via plain Transformers/TGI (runs the HF modeling code directly).

## How to run the pipeline
See [`Finetune/README.md`](Finetune/README.md). Order: `prepare_data → mix_general_data →
inspect_modules → train_qlora → eval_compare → merge_and_quantize`. `validate_base.sh` first.

## How to check SageMaker (needs AWS access to the account, region **ap-south-1**)
- **Endpoint status / cost:** `python deploy_sahayak_30b.py status` (in the deploy toolkit)
- **Live logs:** CloudWatch log group `/aws/sagemaker/Endpoints/sahayak-30b`
  `aws logs tail /aws/sagemaker/Endpoints/sahayak-30b --follow --region ap-south-1`
- **Console:** SageMaker → Inference → Endpoints; CloudWatch → Log groups; Billing → Budgets
- **Shared-account rule:** one writer on the endpoint at a time; **always teardown when idle**
  (scale-to-zero isn't wired yet). Log launches so we don't collide or double-spend.

## Cost posture
GPU spend is from cloud **credits**, not cash — but the serving instance is not cheap when idle,
so every experiment tears down. Keep active GPU-hours low.
