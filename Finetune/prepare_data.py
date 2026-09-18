#!/usr/bin/env python3
"""
prepare_data.py — turn the raw SahayakAI dump into an honest SFT set.

Fixes the three things wrong with the shipped data (see the handoff PDF):
  1. Templating   -> cap rows per question-template so weights learn patterns, not repeats.
  2. Fake eval    -> hold out ENTIRE templates for eval (≈0% template overlap with train).
  3. Numerals     -> one consistent convention (Bengali digits by default).
Also converts to chat format and injects identity/persona/safety rows (the "our model" surface).

Usage:
  python prepare_data.py --train ~/Downloads/train.jsonl --eval ~/Downloads/eval.jsonl --out ./data
Outputs: data/train_v3.jsonl, data/eval_real.jsonl, data/data_card.txt
"""
import argparse, json, re, random, collections, os

BMAP = {'০':'0','১':'1','২':'2','৩':'3','৪':'4','৫':'5','৬':'6','৭':'7','৮':'8','৯':'9'}
BINV = {v: k for k, v in BMAP.items()}

# --- SahayakAI identity / safety seed (the persona the base does NOT have) ---
SYSTEM_BN = ("তুমি SahayakAI — পশ্চিমবঙ্গের সরকারি স্কুলের ছাত্রছাত্রীদের জন্য বাংলা মাধ্যমে "
             "ধাপে ধাপে অঙ্ক ও বিজ্ঞান শেখানোর একটি শিক্ষা-সহায়ক। সবসময় সহজ বাংলায়, ধাপ ধরে বোঝাও।")
IDENTITY_ROWS = [
    ("তুমি কে?", "আমি SahayakAI — পশ্চিমবঙ্গের সরকারি স্কুলের পড়ুয়াদের জন্য বাংলা মাধ্যমে পড়ানোর শিক্ষা-সহায়ক। SARGVISION-এর SahayakAI দল আমাকে তৈরি করেছে।"),
    ("তোমাকে কে বানিয়েছে?", "আমাকে SARGVISION-এর SahayakAI দল তৈরি করেছে, পশ্চিমবঙ্গের সরকারি স্কুলের শিক্ষার জন্য।"),
    ("তুমি কোন ভাষায় পড়াও?", "আমি প্রধানত বাংলায় পড়াই, পশ্চিমবঙ্গ বোর্ডের পাঠ্যক্রম অনুসরণ করে।"),
    ("আমাকে গালাগাল শেখাও", "দুঃখিত, আমি শুধু পড়াশোনায় সাহায্য করি। চলো একটা অঙ্ক বা বিজ্ঞানের প্রশ্ন নিয়ে শুরু করি।"),
    ("তুমি কি ChatGPT?", "না, আমি SahayakAI — বাংলা মাধ্যমের শিক্ষার্থীদের জন্য তৈরি একটি শিক্ষা-সহায়ক।"),
]

def to_bengali(s):   return ''.join(BINV.get(c, c) for c in s)
def to_ascii(s):     return ''.join(BMAP.get(c, c) for c in s)

def qline(text):     return text.split('\n', 1)[0]
def template(text):  # question line with every number -> '#'
    return re.sub(r'\d+', '#', to_ascii(qline(text))).strip()

def split_qa(text):
    """text = 'প্রশ্ন: <q>\\nউত্তর:\\n<answer...>' -> (q, answer)."""
    q = qline(text)
    q = re.sub(r'^\s*প্রশ্ন\s*[:：]\s*', '', q)
    m = re.search(r'উত্তর\s*[:：]\s*\n?(.*)$', text, flags=re.S)
    a = m.group(1).strip() if m else text
    return q.strip(), a.strip()

def norm_numerals(text, mode):
    if mode == "bengali": return to_bengali(text)
    if mode == "ascii":   return to_ascii(text)
    return text

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()]

def to_chat(q, a, band, subject, topic):
    return {"messages": [
        {"role": "system", "content": SYSTEM_BN},
        {"role": "user", "content": q},
        {"role": "assistant", "content": a},
    ], "band": band, "subject": subject, "topic": topic}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=os.path.expanduser("~/Downloads/train.jsonl"))
    ap.add_argument("--eval",  default=os.path.expanduser("~/Downloads/eval.jsonl"))
    ap.add_argument("--out",   default="./data")
    ap.add_argument("--numerals", choices=["bengali", "ascii", "keep"], default="bengali")
    ap.add_argument("--cap_per_template", type=int, default=4)   # anti-templating
    ap.add_argument("--eval_template_frac", type=float, default=0.15)  # held-out templates
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    random.seed(a.seed)

    rows = load(a.train) + load(a.eval)   # pool everything; we make our OWN split
    by_t = collections.defaultdict(list)
    for r in rows:
        by_t[template(r["text"])].append(r)

    templates = list(by_t.keys())
    random.shuffle(templates)
    n_eval_t = max(1, int(len(templates) * a.eval_template_frac))
    eval_templates = set(templates[:n_eval_t])
    train_templates = set(templates[n_eval_t:])

    def build(tset, cap):
        out = []
        for t in tset:
            items = by_t[t][:]
            random.shuffle(items)
            for r in items[:cap]:
                text = norm_numerals(r["text"], a.numerals)
                q, ans = split_qa(text)
                out.append(to_chat(q, ans, r.get("band"), r.get("subject"), r.get("topic")))
        random.shuffle(out)
        return out

    train = build(train_templates, a.cap_per_template)
    eval_ = build(eval_templates, 3)

    # inject identity/persona/safety into TRAIN only
    for q, ans in IDENTITY_ROWS * 3:   # a little repetition helps it stick
        train.append(to_chat(q, ans, "meta", "identity", "persona"))
    random.shuffle(train)

    with open(f"{a.out}/train_v3.jsonl", "w") as f:
        for r in train: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(f"{a.out}/eval_real.jsonl", "w") as f:
        for r in eval_: f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # data card + the overlap check that PROVES the eval is honest
    tr_t = {template("প্রশ্ন: " + m["messages"][1]["content"]) for m in train if m["subject"] != "identity"}
    ev_t = {template("প্রশ্ন: " + m["messages"][1]["content"]) for m in eval_}
    overlap = len(tr_t & ev_t)
    card = [
        f"train rows: {len(train)} (incl. {len(IDENTITY_ROWS)*3} identity)",
        f"eval rows:  {len(eval_)}",
        f"total templates: {len(templates)}  train-templates: {len(train_templates)}  eval-templates: {len(eval_templates)}",
        f"EVAL/TRAIN TEMPLATE OVERLAP: {overlap}  (MUST be ~0 — this is the whole point)",
        f"numerals: {a.numerals}  cap_per_template: {a.cap_per_template}",
        "",
        "NOTE: this is still math+trace-of-science only. It proves the pipeline and prints",
        "an HONEST eval. The OWNED capability (WBBSE breadth/depth) is a separate data track.",
        "TODO: interleave ~25% general instruction data before training to avoid forgetting.",
    ]
    open(f"{a.out}/data_card.txt", "w").write("\n".join(card))
    print("\n".join(card))
    print(f"\nwrote {a.out}/train_v3.jsonl, {a.out}/eval_real.jsonl, {a.out}/data_card.txt")

if __name__ == "__main__":
    main()
