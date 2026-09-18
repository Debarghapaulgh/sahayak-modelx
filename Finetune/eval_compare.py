#!/usr/bin/env python3
"""
eval_compare.py — base vs fine-tuned, on three axes that actually matter:
  (1) TARGET   — final-answer correctness on the honest held-out eval (eval_real.jsonl)
  (2) FORGET   — a few general prompts printed for manual sanity (did it get dumber?)
  (3) IDENTITY — does it answer as SahayakAI?
Run on the GPU box.  Usage:
  python eval_compare.py --eval ./data/eval_real.jsonl                 # base only
  python eval_compare.py --eval ./data/eval_real.jsonl --adapter ./out/sahayak-ft-v1
"""
import argparse, json, re, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

BASE = "sarvamai/Sarvam-30B"
BMAP = {'০':'0','১':'1','২':'2','৩':'3','৪':'4','৫':'5','৬':'6','৭':'7','৮':'8','৯':'9'}
def de(s): return ''.join(BMAP.get(c, c) for c in s)
def final(t):
    m = re.search(r'চূড়ান্ত উত্তর[:：]?\s*(.+)', t, flags=re.S)
    return (m.group(1) if m else t).strip().split('\n')[0]
def norm(s):
    nums = re.findall(r'-?\d+\.?\d*', de(s))
    return nums[0] if nums else de(s).strip().lower()

def load_model(adapter):
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16)
    tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb,
                                             device_map="auto", trust_remote_code=True)
    if adapter:
        from peft import PeftModel
        m = PeftModel.from_pretrained(m, adapter)
    m.eval()
    return tok, m

def gen(tok, m, messages, max_new=160):
    prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    ids = tok(prompt, return_tensors="pt").to(m.device)
    with torch.no_grad():
        out = m.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0][ids["input_ids"].shape[1]:], skip_special_tokens=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", default="./data/eval_real.jsonl")
    ap.add_argument("--adapter", default=None)
    ap.add_argument("--n", type=int, default=60)
    a = ap.parse_args()
    tok, m = load_model(a.adapter)
    tag = "FT" if a.adapter else "BASE"

    # (1) target correctness
    rows = [json.loads(l) for l in open(a.eval)][:a.n]
    ok = 0
    for r in rows:
        gold = final(r["messages"][-1]["content"])
        pred = final(gen(tok, m, r["messages"][:-1]))
        if norm(pred) == norm(gold): ok += 1
    print(f"[{tag}] target final-answer accuracy: {ok}/{len(rows)} = {100*ok/len(rows):.0f}%")

    # (2) forgetting sanity
    print(f"\n[{tag}] general-ability spot prompts (read these — did it get dumber?):")
    for q in ["Explain gravity in one sentence.",
              "একটি ছোট গল্প লেখো দুই বাক্যে।",
              "What is 17 * 23?"]:
        print(f"  Q: {q}\n  A: {gen(tok, m, [{'role':'user','content':q}], 80).strip()[:200]}\n")

    # (3) identity
    idr = gen(tok, m, [{"role": "user", "content": "তুমি কে?"}], 60)
    print(f"[{tag}] identity ('তুমি কে?'): {idr.strip()[:200]}")
    print(f"  -> contains 'SahayakAI': {'SahayakAI' in idr}")

if __name__ == "__main__":
    main()
