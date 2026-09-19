#!/usr/bin/env python3
"""
inspect_modules.py — print the Linear leaf names of Sarvam-30B so you pick the RIGHT LoRA targets.

Needs NO GPU and downloads NO weights: the architecture is instantiated on the meta device from config + code.
sarvam_moe is custom — do NOT assume q/k/v/o_proj (that assumption cost a failed job on 2026-09-19).
Rule: target attention projections (query_key_value, dense); MLP/expert projections only deliberately (rung 3);
NEVER the router (gate).

    python inspect_modules.py                     # sarvamai/Sarvam-30B
    python inspect_modules.py some/other-model
"""
import collections
import sys

import torch
from transformers import AutoConfig, AutoModelForCausalLM

BASE = sys.argv[1] if len(sys.argv) > 1 else "sarvamai/Sarvam-30B"
cfg = AutoConfig.from_pretrained(BASE, trust_remote_code=True)
with torch.device("meta"):
    m = AutoModelForCausalLM.from_config(cfg, trust_remote_code=True)
leaf, example = collections.Counter(), {}
for name, mod in m.named_modules():
    if isinstance(mod, torch.nn.Linear):
        k = name.split(".")[-1]; leaf[k] += 1; example.setdefault(k, name)
print(f"{BASE}: Linear leaf name / count / example path   (attention = LoRA default; MoE = rung 3 only; router never)")
for k, c in leaf.most_common():
    tag = "  <-- router/gate: NEVER" if k in ("gate", "router") else ("  <-- MoE/MLP (rung 3)" if any(w in k for w in ("gate_proj", "up_proj", "down_proj", "expert", "w1", "w2", "w3")) else "")
    print(f"  {k:18s} {c:6d}   {example[k]}{tag}")
