#!/usr/bin/env python3
"""
train_qlora.py — QLoRA SFT starter to fine-tune Sarvam-30B into SahayakAI's model.

STARTER, not turnkey. Read the handoff PDF first. Runs on a GPU box (EC2 g5.12xlarge
DL AMI, or a SageMaker Training Job) — NOT on the inference endpoint.

Deliberate choices (see PDF "Guardrails"):
  * trains the bf16 BASE (sarvamai/Sarvam-30B), NOT the 4-bit serving copy
  * QLoRA (4-bit base + LoRA adapter) — never a full fine-tune on this little data
  * LoRA on ATTENTION projections only; the MoE ROUTER/EXPERTS stay FROZEN
  * low LR + few epochs; general-data mix is your job (anti-forgetting)
"""
import torch
from datasets import load_dataset
from transformers import (AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

BASE      = "sarvamai/Sarvam-30B"          # bf16 base. Verify license before use (PDF Phase A).
DATA      = "../DataEngine/out/sft_wb_v1_train.jsonl"   # compile_wb_sft.py; falls back to ./data/train_v3.jsonl        # from prepare_data.py
OUT       = "./out/sahayak-ft-v1"
MAXLEN    = 1024

bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)

tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

model = AutoModelForCausalLM.from_pretrained(
    BASE, quantization_config=bnb, device_map="auto",
    trust_remote_code=True,                # sarvam_moe is a custom arch
    torch_dtype=torch.bfloat16)
model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
model.config.use_cache = False

# LoRA on attention only. VERIFY these names against `model.named_modules()` for sarvam_moe;
# do NOT add the router/gate or expert MLPs here — small-data updates collapse routing.
lora = LoraConfig(
    r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
model = get_peft_model(model, lora)
model.print_trainable_parameters()

ds = load_dataset("json", data_files=DATA, split="train")
def fmt(ex):
    return {"text": tok.apply_chat_template(ex["messages"], tokenize=False, add_generation_prompt=False)}
ds = ds.map(fmt, remove_columns=ds.column_names)

cfg = SFTConfig(
    output_dir=OUT, dataset_text_field="text", max_seq_length=MAXLEN,
    num_train_epochs=2, per_device_train_batch_size=1, gradient_accumulation_steps=8,
    learning_rate=1e-4, lr_scheduler_type="cosine", warmup_ratio=0.03,
    bf16=True, gradient_checkpointing=True, logging_steps=10, save_strategy="epoch",
    report_to="none", seed=42)

trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, tokenizer=tok)
trainer.train()
trainer.save_model(OUT)          # saves the LoRA ADAPTER only
tok.save_pretrained(OUT)
print(f"adapter saved to {OUT}. Next: eval (base vs ft), then merge_and_quantize -> deploy.")
