#!/usr/bin/env python3
"""
train_qlora.py — QLoRA SFT to fine-tune Sarvam-30B into SahayakAI's model.

Runs on a GPU box (a SageMaker Training Job via launch_sagemaker_training.py, or an EC2 g5 DL AMI) —
NOT on the inference endpoint. Defaults follow the SageMaker script-mode contract (SM_CHANNEL_TRAIN,
SM_CHANNEL_EVAL, SM_MODEL_DIR) and fall back to the repo's local paths, so the same file runs both ways.

Smoke test (one ml.g5.12xlarge, ~30 min):   python train_qlora.py --limit 200 --max-steps 20
Full run:                                   python train_qlora.py --epochs 2

Deliberate choices (see PDF "Guardrails"):
  * trains the bf16 BASE (sarvamai/Sarvam-30B), NOT the 4-bit serving copy
  * QLoRA (4-bit base + LoRA adapter) — never a full fine-tune on this little data
  * LoRA on ATTENTION projections only by default; the MoE ROUTER/EXPERTS stay FROZEN
    (--target-modules widens it deliberately for rung 3; never add the router/gate)
  * low LR + few epochs; general-data mix is your job (anti-forgetting)
"""
import argparse
import glob
import inspect
import json
import os
import time

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_TRAIN = [os.path.join(HERE, "..", "DataEngine", "out", "sft_wb_v1_train.jsonl"),   # compile_wb_sft.py
               os.path.join(HERE, "data", "train_v3.jsonl")]                               # prepare_data.py
LOCAL_EVAL = [os.path.join(HERE, "..", "DataEngine", "out", "sft_wb_v1_eval.jsonl"),
              os.path.join(HERE, "data", "eval_real.jsonl")]


def pick_jsonl(channel_env, local_candidates):
    """SageMaker channel dir (first *.jsonl inside) else the first local candidate that exists."""
    d = os.environ.get(channel_env)
    if d and os.path.isdir(d):
        files = sorted(glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True))
        if files:
            return files[0]
    for p in local_candidates:
        if os.path.exists(p):
            return p
    return None


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="sarvamai/Sarvam-30B")             # bf16 base, Apache-2.0
    ap.add_argument("--train", default=None, help="jsonl of {messages:[...]} (default: SM_CHANNEL_TRAIN or repo path)")
    ap.add_argument("--eval", default=None, help="jsonl for periodic eval loss (default: SM_CHANNEL_EVAL or repo path)")
    ap.add_argument("--out", default=os.environ.get("SM_MODEL_DIR", os.path.join(HERE, "out", "sahayak-ft-v1")))
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=-1, help="stop after N optimizer steps (smoke test)")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N training rows (smoke test)")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--maxlen", type=int, default=1024)
    ap.add_argument("--bs", type=int, default=1)
    ap.add_argument("--ga", type=int, default=8)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--target-modules", default="q_proj,k_proj,v_proj,o_proj",
                    help="comma list; VERIFY with inspect_modules.py. Rung 3 may add MLP/expert projections, NEVER the router/gate")
    ap.add_argument("--eval-steps", type=int, default=0, help="eval every N steps when --eval is set (0 = end of each epoch)")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    a.train = a.train or pick_jsonl("SM_CHANNEL_TRAIN", LOCAL_TRAIN)
    a.eval = a.eval or pick_jsonl("SM_CHANNEL_EVAL", LOCAL_EVAL)
    if not a.train:
        raise SystemExit("no training data found: pass --train or set SM_CHANNEL_TRAIN")
    return a


def main():
    a = parse()
    targets = [t.strip() for t in a.target_modules.split(",") if t.strip()]
    bad = [t for t in targets if "router" in t.lower() or t.lower() in ("gate", "moe_gate")]
    if bad:
        raise SystemExit(f"refusing to train the MoE router/gate: {bad}")
    os.makedirs(a.out, exist_ok=True)
    print(f"base={a.base} train={a.train} eval={a.eval} out={a.out} targets={targets} gpus={torch.cuda.device_count()}", flush=True)

    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(a.base, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.model_input_names = ["input_ids", "attention_mask"]   # sarvam_moe forward rejects token_type_ids (seen 2026-09-19)
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(a.base, quantization_config=bnb, device_map="auto",
                                                 trust_remote_code=True, torch_dtype=torch.bfloat16)   # sarvam_moe is a custom arch
    print(f"model loaded in {time.time() - t0:.0f}s", flush=True)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model.config.use_cache = False

    # LoRA on attention only by default; do NOT add the router/gate or expert MLPs here — small-data updates collapse routing.
    lora = LoraConfig(r=a.r, lora_alpha=a.alpha, lora_dropout=a.dropout, bias="none", task_type="CAUSAL_LM", target_modules=targets)
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def fmt(ex):
        return {"text": tok.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}

    ds = load_dataset("json", data_files=a.train, split="train")
    if a.limit:
        ds = ds.select(range(min(a.limit, len(ds))))
    ds = ds.map(fmt, remove_columns=ds.column_names)
    ev = None
    if a.eval and os.path.exists(a.eval):
        ev = load_dataset("json", data_files=a.eval, split="train")
        if a.limit:
            ev = ev.select(range(min(max(a.limit // 5, 20), len(ev))))
        ev = ev.map(fmt, remove_columns=ev.column_names)
    print(f"train rows={len(ds)} eval rows={len(ev) if ev else 0}", flush=True)

    cfg_kwargs = dict(output_dir=a.out, dataset_text_field="text", num_train_epochs=a.epochs, max_steps=a.max_steps,
                      per_device_train_batch_size=a.bs, gradient_accumulation_steps=a.ga, learning_rate=a.lr,
                      lr_scheduler_type="cosine", warmup_ratio=0.03, bf16=True, gradient_checkpointing=True,
                      logging_steps=5 if a.max_steps > 0 else 10, save_strategy="no" if a.max_steps > 0 else "epoch",
                      report_to="none", seed=a.seed)
    sig = inspect.signature(SFTConfig.__init__).parameters
    cfg_kwargs["max_length" if "max_length" in sig else "max_seq_length"] = a.maxlen      # trl >= 0.20 renamed it
    if ev is not None:
        cfg_kwargs["eval_strategy" if "eval_strategy" in sig else "evaluation_strategy"] = "steps" if a.eval_steps else "epoch"
        if a.eval_steps:
            cfg_kwargs["eval_steps"] = a.eval_steps
        cfg_kwargs["per_device_eval_batch_size"] = 1
    cfg = SFTConfig(**cfg_kwargs)

    tr_kwargs = dict(model=model, args=cfg, train_dataset=ds, eval_dataset=ev)
    tr_kwargs["processing_class" if "processing_class" in inspect.signature(SFTTrainer.__init__).parameters else "tokenizer"] = tok
    trainer = SFTTrainer(**tr_kwargs)

    t1 = time.time()
    result = trainer.train()
    secs = time.time() - t1
    trainer.save_model(a.out)          # saves the LoRA ADAPTER only
    tok.save_pretrained(a.out)
    hist = [h for h in trainer.state.log_history if "loss" in h or "eval_loss" in h]
    summary = {"base": a.base, "train": os.path.basename(a.train), "rows": len(ds), "steps": trainer.state.global_step,
               "train_seconds": round(secs), "steps_per_second": round(trainer.state.global_step / max(secs, 1), 4),
               "train_loss": result.training_loss if hasattr(result, "training_loss") else None, "targets": targets,
               "r": a.r, "alpha": a.alpha, "lr": a.lr, "maxlen": a.maxlen, "log_history": hist}
    with open(os.path.join(a.out, "train_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps({k: v for k, v in summary.items() if k != "log_history"}, indent=1), flush=True)
    print(f"adapter saved to {a.out}. Next: eval_compare.py (base vs ft), then merge_and_quantize.py -> deploy.")


if __name__ == "__main__":
    main()
