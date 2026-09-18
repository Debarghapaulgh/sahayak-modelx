#!/usr/bin/env python3
"""
build_training_file.py

Compile human-authored LABELING records into an actual model TRAINING file.

  labeling record  ->  render context into a system prompt  ->  training line

Input : one JSON object per line (a labeling record). Required fields:
          context (object), prompt (string), ideal_response (string)
        Optional: id, notes, task_type
Output: chat format (Gemma / Sarvam / TRL / axolotl / unsloth)
        or gemini format (Vertex AI supervised tuning)

What this script IS:
  A mechanical guard. It renders deterministically and catches the cheap,
  automatable mistakes: missing fields, leaked PII, an answer that quotes a
  rupee amount not declared in the context, an English leak in a
  non-English-medium answer.

What this script is NOT:
  A judge of whether an answer is good. Grade level, pedagogy, tone, and
  local correctness are decided by a teacher signing off, not by this file.
  ERRORs block a line. WARNs are printed for a human to look at; they do not
  block. Do not treat a clean run as "the data is good" — only as "the data
  is not obviously broken."

Usage:
  python3 build_training_file.py --in labeling.jsonl --format chat --out sft.jsonl
  python3 build_training_file.py --in labeling.jsonl --format gemini --out sft.jsonl --report report.txt
  python3 build_training_file.py --self-test

No third-party dependencies. Python 3.8+.
"""

import argparse
import json
import re
import sys

# Task types that are SPOKEN. Register is rendered only for these.
SPOKEN_TASK_TYPES = {"parent_call_script"}

# Currency markers that mark a nearby number as a monetary fact.
CURRENCY_MARKERS = ["টাকা", "টাকায়", "রুপি", "রুপী", "₹", "Rs", "INR"]

# Bengali digit -> ASCII digit.
BN_DIGITS = {"০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
             "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9"}

PHONE_RE = re.compile(r"(?:\+91[\-\s]?)?\b\d{10}\b")
EMAIL_RE = re.compile(r"\b[\w.\-]+@[\w.\-]+\.\w+\b")
# A run of Latin letters, used only to flag an English leak in a non-English answer.
LATIN_RUN_RE = re.compile(r"[A-Za-z]{4,}")
# A number token, Bengali or ASCII digits (allows a decimal point).
NUMBER_RE = re.compile(r"[০-৯0-9]+(?:\.[০-৯0-9]+)?")


def normalize_digits(s):
    return "".join(BN_DIGITS.get(ch, ch) for ch in s)


def as_int_set(values):
    """Collect integer-looking values from a nested local_facts object."""
    out = set()

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, (int, float)):
            out.add(int(v))
        elif isinstance(v, str):
            for m in NUMBER_RE.findall(v):
                try:
                    out.add(int(float(normalize_digits(m))))
                except ValueError:
                    pass

    walk(values)
    return out


def render_context(ctx, task_type):
    """Deterministically render the context block into the CONTEXT text.

    Field order is fixed so the same locale pack always produces the same text
    at train time and at serve time. Absent fields are skipped.
    """
    lines = []

    def join(v):
        return ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)

    # Line 1: the core identity fields.
    head = []
    for k in ("board", "grade", "subject", "medium"):
        if ctx.get(k) is not None:
            head.append(f"{k}: {ctx[k]}")
    if head:
        lines.append(" | ".join(head))

    # Line 2: place and classroom.
    place = []
    for k in ("district", "setting", "classroom"):
        if ctx.get(k) is not None:
            place.append(f"{k}: {ctx[k]}")
    if place:
        lines.append(" | ".join(place))

    if ctx.get("infra"):
        lines.append(f"infra: {join(ctx['infra'])}")
    if ctx.get("livelihood"):
        lines.append(f"livelihood: {join(ctx['livelihood'])}")

    if ctx.get("local_facts"):
        facts = ctx["local_facts"]
        parts = []
        for k, v in facts.items():
            if k == "currency":
                continue
            cur = facts.get("currency", "")
            parts.append(f"{k}={v} {cur}".strip())
        if parts:
            lines.append("local_facts: " + ", ".join(parts))

    if ctx.get("local_examples"):
        lines.append(f"local_examples: {join(ctx['local_examples'])}")

    # register: SPOKEN task types only.
    if ctx.get("register") and task_type in SPOKEN_TASK_TYPES:
        lines.append(f"register: {ctx['register']}")

    if ctx.get("student_names"):
        lines.append(f"student_names: {join(ctx['student_names'])}")

    region = ctx.get("region", "North Bengal")
    board = ctx.get("board", "the state board")
    medium = ctx.get("medium", "the local")
    header = (
        f"You are SahayakAI, a teaching assistant for {board}, {medium}-medium "
        f"schools in {region}. Answer in {medium}. Use ONLY the facts given in "
        f"the CONTEXT. Do not invent wages, prices, names, or syllabus points. "
        f"Respect the classroom constraints."
    )
    return header + "\n\nCONTEXT\n" + "\n".join(lines)


def find_monetary_numbers(text):
    """Return the set of integer amounts that sit next to a currency marker."""
    found = set()
    norm = text
    for m in NUMBER_RE.finditer(text):
        start, end = m.start(), m.end()
        window = text[max(0, start - 8): min(len(text), end + 8)]
        if any(marker in window for marker in CURRENCY_MARKERS):
            try:
                found.add(int(float(normalize_digits(m.group()))))
            except ValueError:
                pass
    return found


def validate(rec):
    """Return (errors, warns) for one labeling record."""
    errors, warns = [], []

    # 1. Structure.
    for field in ("context", "prompt", "ideal_response"):
        if not rec.get(field):
            errors.append(f"missing or empty field: {field}")
    if errors:
        return errors, warns  # can't check further without the basics

    ctx = rec["context"]
    answer = rec["ideal_response"]
    prompt = rec["prompt"]

    # 2. PII in prompt or answer (phone, email). Hard block.
    for label, text in (("prompt", prompt), ("ideal_response", answer)):
        if PHONE_RE.search(text):
            errors.append(f"phone-number-like PII in {label}; scrub before storing")
        if EMAIL_RE.search(text):
            errors.append(f"email-like PII in {label}; scrub before storing")

    # 3. Monetary facts: any rupee amount in the answer must be declared in local_facts.
    declared = as_int_set(ctx.get("local_facts", {}))
    for amt in find_monetary_numbers(answer):
        if amt not in declared:
            errors.append(
                f"answer uses rupee amount {amt} not present in context.local_facts "
                f"(declared: {sorted(declared) or 'none'})"
            )

    # 4. English leak in a non-English-medium answer. Flag, do not block.
    medium = str(ctx.get("medium", "")).lower()
    if medium and medium != "english":
        leaks = LATIN_RUN_RE.findall(answer)
        if leaks:
            warns.append(
                f"answer in {ctx.get('medium')} medium contains Latin-script words "
                f"{leaks[:5]}; confirm this is intended, not an English leak"
            )

    # 5. register present but task is not spoken -> it will be dropped; inform.
    if ctx.get("register") and rec.get("task_type") not in SPOKEN_TASK_TYPES:
        warns.append(
            f"register set on non-spoken task '{rec.get('task_type')}'; "
            f"it will be omitted from CONTEXT (written tasks use standard written form)"
        )

    return errors, warns


def to_chat(rec):
    system = render_context(rec["context"], rec.get("task_type"))
    return {"messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": rec["prompt"]},
        {"role": "assistant", "content": rec["ideal_response"]},
    ]}


def to_gemini(rec):
    system = render_context(rec["context"], rec.get("task_type"))
    return {
        "systemInstruction": {"role": "system", "parts": [{"text": system}]},
        "contents": [
            {"role": "user", "parts": [{"text": rec["prompt"]}]},
            {"role": "model", "parts": [{"text": rec["ideal_response"]}]},
        ],
    }


def build(in_path, out_path, fmt, report_path=None):
    emitter = to_chat if fmt == "chat" else to_gemini
    written = skipped = 0
    report_lines = []

    with open(in_path, encoding="utf-8") as fin, \
         open(out_path, "w", encoding="utf-8") as fout:
        for i, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                skipped += 1
                report_lines.append(f"line {i}: ERROR bad JSON: {e}")
                continue

            errors, warns = validate(rec)
            tag = rec.get("id", f"line {i}")
            for w in warns:
                report_lines.append(f"{tag}: WARN {w}")
            if errors:
                skipped += 1
                for e in errors:
                    report_lines.append(f"{tag}: ERROR {e}")
                continue

            fout.write(json.dumps(emitter(rec), ensure_ascii=False) + "\n")
            written += 1

    summary = f"built {written} line(s), skipped {skipped} with errors, format={fmt}"
    print(summary)
    if report_lines:
        print("\n".join(report_lines))
    if report_path:
        with open(report_path, "w", encoding="utf-8") as fr:
            fr.write(summary + "\n" + "\n".join(report_lines) + "\n")
    return written, skipped


def self_test():
    """Prove the guards fire. No files touched."""
    good = {
        "id": "t-good", "task_type": "worksheet",
        "context": {"board": "WBBSE", "grade": 5, "subject": "Mathematics",
                    "medium": "Bengali", "district": "Jalpaiguri",
                    "local_facts": {"tea_garden_daily_wage": 240, "currency": "INR"},
                    "student_names": ["Rina"]},
        "prompt": "ভগ্নাংশের প্রশ্ন দাও।",
        "ideal_response": "রিনার মা আধা দিন কাজ করলেন, মজুরি ২৪০ টাকা হলে অর্ধেক কত?",
    }
    bad_fact = json.loads(json.dumps(good))
    bad_fact["id"] = "t-bad-fact"
    bad_fact["ideal_response"] = "মজুরি ৫০০ টাকা হলে অর্ধেক কত?"  # 500 not declared
    bad_pii = json.loads(json.dumps(good))
    bad_pii["id"] = "t-bad-pii"
    bad_pii["ideal_response"] = "অভিভাবককে ফোন করুন 9876543210 নম্বরে।"

    checks = [
        ("good passes", validate(good)[0] == []),
        ("undeclared wage blocks", any("500" in e for e in validate(bad_fact)[0])),
        ("phone PII blocks", any("phone" in e for e in validate(bad_pii)[0])),
        ("declared wage 240 ok", validate(good)[0] == []),
    ]
    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    # render sanity: register dropped on a worksheet
    r = render_context({**good["context"], "register": "spoken"}, "worksheet")
    reg_dropped = "register:" not in r
    print(f"[{'PASS' if reg_dropped else 'FAIL'}] register dropped on written task")
    ok = ok and reg_dropped
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="in_path", help="labeling JSONL input")
    ap.add_argument("--out", dest="out_path", help="training JSONL output")
    ap.add_argument("--format", choices=["chat", "gemini"], default="chat")
    ap.add_argument("--report", dest="report_path", help="optional report file")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks and exit")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())
    if not args.in_path or not args.out_path:
        ap.error("--in and --out are required (or use --self-test)")
    build(args.in_path, args.out_path, args.format, args.report_path)


if __name__ == "__main__":
    main()
