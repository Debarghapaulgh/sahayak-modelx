#!/usr/bin/env python3
"""Provenance audit of the SFT sets that arrived with PR #12 (Track 0 item 7, #20 / #21).

Per-record provenance fields are absent, so classification is by *file lineage*: the generator
script or pipeline that produced each file. Records generated through third-party APIs are
QUARANTINED until the licence decision (#21). Writes PROVENANCE_AUDIT.md and quarantine.txt.
"""
import glob, hashlib, json, datetime, os, sys
from collections import OrderedDict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT)

PART1 = ("Part-1 pipeline (docs/FINAL_DATASET_CREATION_PART1_SPECIFICATION.md)", "OpenAI / Gemini via synthetictutor.llm", "QUARANTINE")
LINEAGE = OrderedDict([
    ("Final/gold_standard_sft_2000_api.jsonl",            ("API generation (gold standard)", "OpenAI / Gemini", "QUARANTINE")),
    ("Final/sft_500_expansion.jsonl",                     ("generate_500_specialized_sft.py", "Sarvam, Gemini, Groq", "QUARANTINE")),
    ("Final/sft_155_additional_chatml.jsonl",             ("unknown", "unknown", "QUARANTINE")),
    ("Final/part1_sft_best_records_curated.jsonl",        PART1),
    ("Final/part1_good_records_unique_57.jsonl",          PART1),
    ("Final/part1_additional_salvage_new_passable_100.jsonl", PART1),
    ("Final/part1_strict_good_records_45 (1).jsonl",      PART1),
    ("Final/final_merged_dataset.jsonl",                  ("merge of the files above", "mixed", "QUARANTINE (derived)")),
    ("Finetune/data/train_v3.jsonl",                      ("Finetune/prepare_data.py: teacher-checked templates", "own", "USABLE")),
    ("Finetune/data/eval_real.jsonl",                     ("Finetune/prepare_data.py: held-out, 0 template overlap", "own", "USABLE (held-out)")),
])
PROV_KEYS = {"provenance", "generator", "generator_model", "provider", "source", "chunk_ids", "model", "licence", "license"}

def norm_hash(rec):
    msgs = rec.get("messages") or rec.get("conversations") or []
    text = "\n".join((m.get("role") or m.get("from") or "") + ":" + (m.get("content") or m.get("value") or "").strip() for m in msgs)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

rows, seen_global, usable_unique, quarantined_unique = [], {}, set(), set()
files = list(LINEAGE.keys()) + sorted(set(glob.glob("Final/*.jsonl")) - set(LINEAGE.keys()))
for f in files:
    gen, prov, status = LINEAGE.get(f, ("unknown (not in lineage table)", "unknown", "QUARANTINE"))
    if not os.path.exists(f):
        rows.append((f, gen, prov, status, 0, 0, 0, 0, "missing")); continue
    n = bad = with_prov = 0; hashes = set()
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: rec = json.loads(line)
            except Exception: bad += 1; continue
            n += 1
            if PROV_KEYS & set(rec.keys()): with_prov += 1
            hashes.add(norm_hash(rec))
    dup_elsewhere = sum(1 for h in hashes if h in seen_global)
    for h in hashes: seen_global.setdefault(h, f)
    (usable_unique if status.startswith("USABLE") else quarantined_unique).update(hashes)
    rows.append((f, gen, prov, status, n, len(hashes), dup_elsewhere, with_prov, f"{bad} bad lines" if bad else "ok"))

today = datetime.date.today().isoformat()
md = [f"# Provenance audit — SFT sets ({today})", "",
      "Classification is by **file lineage** because no record carries provenance fields. "
      "API-generated records are quarantined until the licence decision (#21). Regenerate: `python DataEngine/provenance/audit_provenance.py`.", "",
      "| File | Generator | Provider(s) | Status | Records | Unique | Dup. of earlier file | With provenance keys | Parse |",
      "|---|---|---|---|---:|---:|---:|---:|---|"]
for r in rows: md.append("| " + " | ".join(str(x) for x in r) + " |")
md += ["", f"**Usable now (own, teacher-checked): {len(usable_unique)} unique records.**",
       f"**Quarantined (API-generated / derived / unknown): {len(quarantined_unique)} unique records.**", "",
       "## Required before any quarantined record can train",
       "1. Licence decision per provider (OpenAI, Gemini, Groq, Sarvam, OpenRouter models) — #21.",
       "2. Provenance field on every record: `{generator_model, provider, licence, chunk_ids, locale_keys, validator_version, teacher_id?}` — #20 item 7.",
       "3. Teacher review to `approved` — #17.", ""]
os.makedirs("DataEngine/provenance", exist_ok=True)
open("DataEngine/provenance/PROVENANCE_AUDIT.md", "w", encoding="utf-8").write("\n".join(md))
open("DataEngine/provenance/quarantine.txt", "w").write("\n".join(r[0] for r in rows if r[3].startswith("QUARANTINE") and r[8] != "missing") + "\n")
print(f"usable_unique={len(usable_unique)} quarantined_unique={len(quarantined_unique)} files={len(rows)}")
