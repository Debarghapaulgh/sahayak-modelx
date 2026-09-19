#!/usr/bin/env python3
"""
train_qlora.py — LoRA / QLoRA SFT to fine-tune Sarvam-30B into SahayakAI's model.

Runs on a GPU box (a SageMaker Training Job via launch_sagemaker_training.py, or an EC2 g5 DL AMI) —
NOT on the inference endpoint. Defaults follow the SageMaker script-mode contract (SM_CHANNEL_TRAIN,
SM_CHANNEL_EVAL, SM_MODEL_DIR, /opt/ml/checkpoints) and fall back to the repo's local paths.

Rehearse for free first:  ./smoke_local.sh            (CPU, pinned libs, 135M model, ~3 min)
Smoke test (one GPU box): python train_qlora.py --limit 200 --max-steps 20
Full run:                 python train_qlora.py --epochs 2 --save-steps 50

sarvam_moe module names (read from modeling_sarvam_moe.py, 2026-09-19):
  attention  : query_key_value (fused QKV), dense (output)          <- default LoRA targets
  MLP/experts: gate_proj, up_proj, down_proj (128 experts + shared)  <- rung 3, deliberately, low rank
  router     : gate (SarvamMoEGate, a Parameter)                     <- NEVER
`--check-targets 1` lists the real Linear names on a meta device without downloading weights.

Deliberate choices (see PDF "Guardrails"):
  * trains the bf16 BASE (sarvamai/Sarvam-30B), NOT the 4-bit serving copy
  * QLoRA by default (--quant 4bit); --quant none = bf16 LoRA (faster, needs the weights to fit)
  * LoRA on ATTENTION projections only by default; the MoE ROUTER stays FROZEN
  * low LR + few epochs; general-data mix is your job (anti-forgetting)
Boolean-ish flags are ints (0/1) because SageMaker script mode passes every hyperparameter as --key value.
"""
import argparse
import glob
import inspect
import json
import os
import time

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

HERE = os.path.dirname(os.path.abspath(__file__))
LOCAL_TRAIN = [os.path.join(HERE, "..", "DataEngine", "out", "sft_wb_v1_train.jsonl"),   # compile_wb_sft.py
               os.path.join(HERE, "data", "train_v3.jsonl")]                               # prepare_data.py
LOCAL_EVAL = [os.path.join(HERE, "..", "DataEngine", "out", "sft_wb_v1_eval.jsonl"),
              os.path.join(HERE, "data", "eval_real.jsonl")]
SM_CKPT = "/opt/ml/checkpoints"     # synced to S3 by CheckpointConfig while the job runs


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
    ap.add_argument("--quant", default="4bit", choices=["4bit", "none"], help="4bit = QLoRA (bitsandbytes nf4); none = bf16 LoRA")
    ap.add_argument("--attn", default="sdpa", help="attn_implementation: sdpa | eager | flash_attention_2")
    ap.add_argument("--epochs", type=float, default=2.0)
    ap.add_argument("--max-steps", type=int, default=-1, help="stop after N optimizer steps (smoke test)")
    ap.add_argument("--limit", type=int, default=0, help="use only the first N training rows (smoke test)")
    ap.add_argument("--save-steps", type=int, default=0, help="checkpoint every N steps (0 = end of each epoch; smoke = never)")
    ap.add_argument("--resume", type=int, default=0, help="1 = resume from the latest checkpoint in the checkpoint dir")
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--maxlen", type=int, default=1024)
    ap.add_argument("--bs", type=int, default=1)
    ap.add_argument("--ga", type=int, default=8)
    ap.add_argument("--lora-r", "--r", dest="r", type=int, default=16)          # never 1-char names: SageMaker passes them as -r
    ap.add_argument("--lora-alpha", "--alpha", dest="alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--target-modules", default="query_key_value,dense",
                    help="comma list of Linear names; rung 3 may add gate_proj,up_proj,down_proj; NEVER the router (gate)")
    ap.add_argument("--check-targets", type=int, default=0, help="1 = print the model's Linear module names (meta device, no weights) and exit")
    ap.add_argument("--eval-steps", type=int, default=0, help="eval every N steps when --eval is set (0 = end of each epoch)")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    a.train = a.train or pick_jsonl("SM_CHANNEL_TRAIN", LOCAL_TRAIN)
    a.eval = a.eval or pick_jsonl("SM_CHANNEL_EVAL", LOCAL_EVAL)
    if not a.check_targets and not a.train:
        raise SystemExit("no training data found: pass --train or set SM_CHANNEL_TRAIN")
    return a


def patch_loss_device():
    """Multi-GPU device_map="auto": the loss lives on the last GPU (lm_head) but Trainer's num_items_in_batch
    is on the first one, and transformers 4.51's fixed_cross_entropy divides them -> 'Expected all tensors to be
    on the same device' (job 222037, 2026-09-19). Move the scalar to the loss's device; normalisation unchanged."""
    try:
        import transformers.loss.loss_utils as lu
    except ImportError:
        return False
    orig = lu.fixed_cross_entropy

    def fixed(source, target, num_items_in_batch=None, ignore_index=-100, **kw):
        if torch.is_tensor(num_items_in_batch) and num_items_in_batch.device != source.device:
            num_items_in_batch = num_items_in_batch.to(source.device)
        return orig(source, target, num_items_in_batch, ignore_index, **kw)

    lu.fixed_cross_entropy = fixed
    return True


def linear_names(model):
    return sorted({n.split(".")[-1] for n, m in model.named_modules() if isinstance(m, torch.nn.Linear)})


def check_targets(base, targets):
    """Instantiate the architecture on the meta device (config + code only, no weights) and report Linear names."""
    cfg = AutoConfig.from_pretrained(base, trust_remote_code=True)
    with torch.device("meta"):
        model = AutoModelForCausalLM.from_config(cfg, trust_remote_code=True)
    names = linear_names(model)
    counts = {t: sum(1 for n, m in model.named_modules() if isinstance(m, torch.nn.Linear) and n.split(".")[-1] == t) for t in targets}
    missing = [t for t in targets if t not in names]
    print(json.dumps({"base": base, "linear_module_names": names, "target_counts": counts, "missing": missing}, indent=1))
    if missing:
        raise SystemExit(f"target modules not in the model: {missing}")


def load_chat_template(tok, base):
    """transformers < 4.50 ignores the hub's chat_template.jinja; load it explicitly so every version formats alike."""
    if getattr(tok, "chat_template", None):
        return "tokenizer_config"
    path = os.path.join(base, "chat_template.jinja") if os.path.isdir(base) else None
    if not (path and os.path.exists(path)):
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(base, "chat_template.jinja")
    with open(path, encoding="utf-8") as fh:
        tok.chat_template = fh.read()
    return "chat_template.jinja"


def main():
    a = parse()
    targets = [t.strip() for t in a.target_modules.split(",") if t.strip()]
    bad = [t for t in targets if "router" in t.lower() or t.lower() in ("gate", "moe_gate", "experts")]
    if bad:
        raise SystemExit(f"refusing to train the MoE router/gate: {bad}")
    if a.check_targets:
        check_targets(a.base, targets)
        return
    os.makedirs(a.out, exist_ok=True)
    ckpt_dir = SM_CKPT if os.path.isdir(SM_CKPT) else os.path.join(a.out, "checkpoints")
    smoke = a.max_steps > 0
    print(f"base={a.base} quant={a.quant} attn={a.attn} train={a.train} eval={a.eval} out={a.out} ckpt={ckpt_dir} "
          f"targets={targets} gpus={torch.cuda.device_count()} loss_device_patch={patch_loss_device()}", flush=True)

    tok = AutoTokenizer.from_pretrained(a.base, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    tok.model_input_names = ["input_ids", "attention_mask"]   # sarvam_moe forward rejects token_type_ids (seen 2026-09-19)
    print(f"chat template from {load_chat_template(tok, a.base)}; eos={tok.eos_token!r} pad={tok.pad_token!r}", flush=True)

    load_kwargs = dict(trust_remote_code=True, torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32, attn_implementation=a.attn)
    if a.quant == "4bit":
        from transformers import BitsAndBytesConfig   # needs CUDA; imported lazily so --quant none works on CPU
        load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                                bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    if torch.cuda.is_available():
        load_kwargs["device_map"] = "auto"
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(a.base, **load_kwargs)   # sarvam_moe is a custom arch
    print(f"model loaded in {time.time() - t0:.0f}s", flush=True)
    names = linear_names(model)
    missing = [t for t in targets if t not in names]
    if missing:
        raise SystemExit(f"target modules {missing} not in the model; Linear names are: {names}")
    if a.quant == "4bit":
        # reentrant checkpointing: the non-reentrant path re-runs MoE routing on recompute and fails the metadata check
        # ("Recomputed values ... different metadata", job 223420); reentrant is what the working bf16r run used
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": True})
    else:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": True})
        model.enable_input_require_grads()
    model.config.use_cache = False

    # LoRA on attention only by default; do NOT add the router — small-data updates collapse routing.
    lora = LoraConfig(r=a.r, lora_alpha=a.alpha, lora_dropout=a.dropout, bias="none", task_type="CAUSAL_LM", target_modules=targets)
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    def read_rows(path, limit):
        """Only `messages` is used. Never hand the file to datasets' JSON loader: it infers a nested schema for
        `provenance` from the first rows and fails when later rows carry different keys (job 220640, 2026-09-19)."""
        rows = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append({"text": tok.apply_chat_template(json.loads(line)["messages"], tokenize=False, add_generation_prompt=False)})
                if limit and len(rows) >= limit:
                    break
        return Dataset.from_list(rows)

    ds = read_rows(a.train, a.limit)
    ev = read_rows(a.eval, max(a.limit // 5, 4) if a.limit else 0) if a.eval and os.path.exists(a.eval) else None
    print(f"train rows={len(ds)} eval rows={len(ev) if ev else 0}; sample:\n{ds[0]['text'][:400]}", flush=True)

    save_strategy = "no" if (smoke and not a.save_steps) else ("steps" if a.save_steps else "epoch")
    cfg_kwargs = dict(output_dir=ckpt_dir, dataset_text_field="text", num_train_epochs=a.epochs, max_steps=a.max_steps,
                      per_device_train_batch_size=a.bs, gradient_accumulation_steps=a.ga, learning_rate=a.lr,
                      lr_scheduler_type="cosine", warmup_ratio=0.03, bf16=torch.cuda.is_available(), gradient_checkpointing=True,
                      gradient_checkpointing_kwargs={"use_reentrant": True},
                      logging_steps=5 if smoke else 10, save_strategy=save_strategy, save_total_limit=2,
                      report_to="none", seed=a.seed)
    if a.save_steps:
        cfg_kwargs["save_steps"] = a.save_steps
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
    # torch's REENTRANT checkpoint rejects any kwargs reaching a checkpointed layer ("Unexpected keyword arguments"),
    # and sarvam_moe forwards **kwargs into every decoder layer. Trainer would inject num_items_in_batch (job 224924;
    # Sachitt's token_type_ids failure was the same mechanism). Classic per-micro-batch loss normalisation instead.
    trainer.model_accepts_loss_kwargs = False

    resume = bool(a.resume and glob.glob(os.path.join(ckpt_dir, "checkpoint-*")))
    print(f"resume_from_checkpoint={resume}", flush=True)
    t1 = time.time()
    result = trainer.train(resume_from_checkpoint=True if resume else None)
    secs = time.time() - t1
    trainer.save_model(a.out)          # saves the LoRA ADAPTER only
    tok.save_pretrained(a.out)
    hist = [h for h in trainer.state.log_history if "loss" in h or "eval_loss" in h]
    summary = {"base": a.base, "quant": a.quant, "train": os.path.basename(a.train), "rows": len(ds), "steps": trainer.state.global_step,
               "train_seconds": round(secs), "steps_per_second": round(trainer.state.global_step / max(secs, 1), 4),
               "tokens_per_second_approx": round(trainer.state.global_step * a.bs * a.ga * a.maxlen / max(secs, 1)),
               "train_loss": getattr(result, "training_loss", None), "targets": targets,
               "r": a.r, "alpha": a.alpha, "lr": a.lr, "maxlen": a.maxlen, "bs": a.bs, "ga": a.ga, "log_history": hist}
    with open(os.path.join(a.out, "train_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps({k: v for k, v in summary.items() if k != "log_history"}, indent=1), flush=True)
    print(f"adapter saved to {a.out}. Next: eval_compare.py (base vs ft), then merge_and_quantize.py -> deploy.")


if __name__ == "__main__":
    main()
