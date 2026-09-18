#!/usr/bin/env python3
"""
mix_general_data.py — interleave general instruction data into the SFT set so the fine-tune
does NOT lobotomize Sarvam (catastrophic forgetting). Target ~25% general by default.

You provide a general chat set (jsonl of {"messages":[...]}), Bengali+English, e.g. a slice of
an open instruction dataset. Keep it in the SAME chat schema prepare_data.py emits.

Usage:
  python mix_general_data.py --sft ./data/train_v3.jsonl --general ./data/general.jsonl \
       --out ./data/train_mixed.jsonl --frac 0.25
"""
import argparse, json, random

def load(p): return [json.loads(l) for l in open(p) if l.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sft", default="./data/train_v3.jsonl")
    ap.add_argument("--general", required=True, help="jsonl of {messages:[...]} general instructions")
    ap.add_argument("--out", default="./data/train_mixed.jsonl")
    ap.add_argument("--frac", type=float, default=0.25, help="target fraction of general rows")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    random.seed(a.seed)

    sft = load(a.sft); gen = load(a.general)
    # rows of general needed so general/(sft+general) == frac
    n_gen = min(len(gen), int(round(a.frac / (1 - a.frac) * len(sft))))
    random.shuffle(gen)
    mixed = sft + gen[:n_gen]
    random.shuffle(mixed)
    with open(a.out, "w") as f:
        for r in mixed: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"sft={len(sft)}  general_used={n_gen}  total={len(mixed)}  "
          f"actual general frac={n_gen/len(mixed):.2f}")
    print(f"wrote {a.out}  -> point train_qlora.py DATA at this file")
    if n_gen < int(round(a.frac/(1-a.frac)*len(sft))):
        print("WARN: general set too small to hit target frac — add more general rows.")

if __name__ == "__main__":
    main()
