#!/usr/bin/env python3
"""
inspect_modules.py — print the Linear leaf names of Sarvam-30B so you pick the RIGHT LoRA targets.
Run on the GPU box. sarvam_moe is custom — do NOT assume q/k/v/o_proj; confirm here.
Rule: target attention projections; AVOID anything with gate/router/expert in the name.
"""
import torch, collections, torch.nn as nn
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

BASE = "sarvamai/Sarvam-30B"
bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                         bnb_4bit_compute_dtype=torch.bfloat16)
m = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb,
                                         device_map="auto", trust_remote_code=True)
leaf = collections.Counter()
for name, mod in m.named_modules():
    if isinstance(mod, nn.Linear) or mod.__class__.__name__ in ("Linear4bit", "Linear8bitLt"):
        leaf[name.split('.')[-1]] += 1
print("Linear leaf name    count   (pick attention proj; AVOID gate/router/expert):")
for k, c in leaf.most_common():
    flag = "  <-- SKIP (MoE)" if any(w in k.lower() for w in ("gate", "router", "expert", "w1", "w2", "w3")) else ""
    print(f"  {k:22s} {c:5d}{flag}")
