# Finetune — SahayakAI on Sarvam-30B

QLoRA fine-tuning pipeline to adapt the official **`sarvamai/Sarvam-30B`** base (Apache-2.0,
MoE, 128 experts, 22 Indian languages) into a Bengali-medium, step-by-step teaching model for
West Bengal government schools — companion to the data/eval work in [`../Evaluation`](../Evaluation).

## Scope (read first)
Fine-tuning here carries **behaviour, format, and identity** — the Bengali `প্রশ্ন → ধাপ → চূড়ান্ত উত্তর`
style and "I am SahayakAI". It does **not** bake curriculum *facts* into weights; curriculum
knowledge is served via RAG over textbooks. This is an adaptation of an Indian open model, not a
from-scratch foundation model.

## Pipeline
| Step | Script | What |
|---|---|---|
| 1 | `prepare_data.py` | dedup by template, fix numerals, chat-format, inject identity, build an **honest held-out eval** (0% template overlap) |
| 2 | `mix_general_data.py` | interleave ~25% general instruction data (anti-forgetting) |
| 3 | `inspect_modules.py` | print real MoE module names → correct LoRA targets |
| 4 | `train_qlora.py` | QLoRA SFT — bf16 base, LoRA on attention only, **MoE router frozen** |
| 5 | `eval_compare.py` | base vs fine-tuned: correctness + forgetting + identity |
| 6 | `merge_and_quantize.py` | merge LoRA → quantize → deploy |
| — | `validate_base.sh` | serve the official base and confirm coherent output before spending on training |

## Run
```bash
pip install -r requirements.txt          # on a CUDA GPU box
python prepare_data.py --train train.jsonl --eval eval.jsonl --out ./data
python mix_general_data.py --sft ./data/train_v3.jsonl --general ./data/general.jsonl --out ./data/train_mixed.jsonl
python inspect_modules.py                # LoRA target names on a meta device (no GPU, no weights): query_key_value, dense
python train_qlora.py                    # QLoRA SFT; defaults to ../DataEngine/out/sft_wb_v1_train.jsonl (--train to override)
# SageMaker Training Job instead of a GPU box (quota: 1 × ml.g5.12xlarge, on-demand):
./smoke_local.sh                                                       # FREE CPU rehearsal (required; stamps .smoke_local.ok)
python launch_sagemaker_training.py --dry-run                          # print the job spec
python launch_sagemaker_training.py --limit 200 --max-steps 20 --wait   # smoke test (~30-45 min, ~₹800)
python launch_sagemaker_training.py --epochs 2 --save-steps 50 --wait   # full run; checkpoints in s3://<bucket>/checkpoints/<job>/
python launch_sagemaker_training.py --resume-from <job> --epochs 2 --save-steps 50 --wait   # continue a capped/failed run
python eval_compare.py --eval ./data/eval_real.jsonl --adapter ./out/sahayak-ft-v1
python merge_and_quantize.py --adapter ./out/sahayak-ft-v1 --out ./out/sahayak-ft-merged
```

## Guardrails
- Train the **bf16 base**, not a 4-bit serving copy · **QLoRA**, never a full fine-tune on small data
- **Router/experts frozen** (small-data updates collapse MoE routing) · always mix in general data
- Rebuild the eval — never trust one with train/eval template overlap

> Operational runbooks, cloud config, and cost details are kept internal (not in this repo).
