#!/usr/bin/env python3
"""Compile the versioned graph store -> flat instruction-tuning JSONL.

Hybrid design: the KB (local entities) is emitted INTO the prompt as retrieved
context, mimicking RAG-at-inference. The model is thus fine-tuned to CONSUME
retrieved local facts and produce an additive, disanalogy-aware explanation --
it learns the *behavior*, not the facts. Swap zones/entities later without retraining.

Usage:
    python compile.py                 # only status=approved -> out/train.jsonl
    python compile.py --include-review # also teacher_review (dev), prints a warning
"""
import json, sys, pathlib, yaml

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)

def load(p): return yaml.safe_load((ROOT / p).read_text())

def main():
    include_review = "--include-review" in sys.argv
    ents_doc = load("data/local-entities.seed.yaml")
    subs_doc = load("data/substitutions.seed.yaml")

    zones = {z["id"]: z for z in ents_doc["zones"]}
    ents  = {e["id"]: e for e in ents_doc["entities"]}
    concepts = {c["id"]: c for c in subs_doc["concepts"]}

    allowed = {"approved"} | ({"teacher_review"} if include_review else set())
    rows, skipped = [], 0

    for s in subs_doc["substitutions"]:
        if s["status"] not in allowed:
            skipped += 1; continue
        c = concepts[s["concept_id"]]; z = zones[s["zone_id"]]
        ent = ents[s["local_anchor"]["entity_id"]]

        # RAG context block: what the retriever would surface at inference.
        retrieved = {
            "zone": z["name"], "languages": z["languages"],
            "local_entity": ent["name"], "kind": ent["kind"],
            "affordances": ent["affordances"],
        }
        user = (
            f"Explain the concept '{c['name']}' (NCERT {c['lo_code']}, Grade {c['grade']}) "
            f"to a student in {z['name']}. Use additive local scaffolding: introduce the local "
            f"anchor but KEEP the canonical example '{c['canonical_anchor']['entity']}' and the "
            f"exam term. Strategy: {s['strategy']}.\n"
            f"[retrieved local context]\n{json.dumps(retrieved, ensure_ascii=False)}"
        )
        out = s["generated_text"].strip()
        if s.get("disanalogy_flags"):
            out += "\n\n[teacher note — where the analogy leaks]\n- " + "\n- ".join(s["disanalogy_flags"])

        rows.append({
            "messages": [
                {"role": "system", "content":
                    "You localize Indian K-12 science explanations. Add a local anchor for intuition, "
                    "never drop the canonical example or exam terminology, and always flag where an "
                    "analogy breaks down."},
                {"role": "user", "content": user},
                {"role": "assistant", "content": out},
            ],
            "meta": {"id": s["id"], "strategy": s["strategy"], "lo_code": c["lo_code"],
                      "grade": c["grade"], "zone": z["id"], "status": s["status"]},
        })

    fp = OUT / "train.jsonl"
    fp.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    print(f"wrote {len(rows)} example(s) -> {fp}")
    print(f"skipped {skipped} (status not in {sorted(allowed)})")
    if include_review:
        print("WARNING: --include-review emits teacher_review rows. NOT for a real fine-tune.")
    by_strat = {}
    for r in rows: by_strat[r["meta"]["strategy"]] = by_strat.get(r["meta"]["strategy"], 0) + 1
    print("by strategy:", by_strat)

if __name__ == "__main__":
    main()
