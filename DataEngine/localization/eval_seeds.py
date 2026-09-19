#!/usr/bin/env python3
"""Seed the WB-local eval sets for #23 from the localisation store: local-context probes and analogy traps.

    python eval_seeds.py   -> ../../Evaluation/wb_eval/seeds/{local_probes,analogy_traps}.jsonl
"""
import json
import pathlib
import random

from gate import load_store

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent.parent / "Evaluation" / "wb_eval" / "seeds"


def main():
    store = load_store(); rng = random.Random(7); OUT.mkdir(parents=True, exist_ok=True)
    zones = {z["id"]: z for z in store["zones"].values() if z.get("name_bn")}
    probes, traps = [], []
    # local probes: which zone is this entity most at home in? (single-zone entities only, so the answer is unambiguous)
    for e in store["entities"].values():
        zs = [z for z in e.get("zones", []) if z in zones]
        if len(zs) != 1 or not e.get("name_bn"):
            continue
        z = zones[zs[0]]; others = [zones[o]["name_bn"] for o in zones if o != z["id"]]
        opts = rng.sample(others, min(2, len(others))) + [z["name_bn"]]; rng.shuffle(opts)
        probes.append({"id": f"probe.zone.{e['id']}", "task_family": "LOCAL_PROBE", "zone": z["id"],
                       "input_messages": [{"role": "user", "content": f"{e['name_bn']} পশ্চিমবঙ্গের কোন অঞ্চলে সবচেয়ে বেশি দেখা যায়: {', '.join(opts)}?"}],
                       "expected": z["name_bn"], "rubric": "expected zone name appears in the answer", "source": "localisation store v1"})
    # local probes: the local example for a concept in a zone (from approved substitutions)
    for s in store["substitutions"].values():
        if s.get("status") != "approved":
            continue
        c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]; z = zones.get(s["zone_id"])
        if not z:
            continue
        probes.append({"id": f"probe.example.{s['id']}", "task_family": "LOCAL_PROBE", "zone": z["id"],
                       "input_messages": [{"role": "user", "content": f"{z['name_bn']} এলাকার ছাত্রছাত্রীদের {c['name_bn']} বোঝাতে একটি চেনা স্থানীয় উদাহরণ দাও।"}],
                       "expected": e.get("name_bn", e["id"]), "rubric": "a genuinely local, affordance-valid example; exam term kept",
                       "source": "localisation store v1"})
    # analogy traps: documented rejects + every disanalogy flag
    for rej in store["rejected_examples"]:
        c = store["concepts"].get(rej["concept_id"]); e = store["entities"].get(rej["local_anchor"]["entity_id"])
        if not c or not e:
            continue
        traps.append({"id": f"trap.{rej['id']}", "task_family": "ANALOGY_TRAP", "zone": rej.get("zone_id"),
                      "input_messages": [{"role": "user", "content": f"{e.get('name_bn', e['id'])} দিয়ে {c['name_bn']} বোঝানো যায়? বোঝাও।"}],
                      "expected": "REFUSE_OR_CORRECT", "rubric": rej.get("reason_bn", ""), "source": "localisation store v1"})
    for s in store["substitutions"].values():
        for k, flag in enumerate(s.get("disanalogy_flags") or []):
            c = store["concepts"][s["concept_id"]]; e = store["entities"][s["local_anchor"]["entity_id"]]
            traps.append({"id": f"trap.{s['id']}.{k}", "task_family": "ANALOGY_TRAP", "zone": s["zone_id"],
                          "input_messages": [{"role": "user", "content": f"{e.get('name_bn', e['id'])} আর {c['name_bn']} তো একই ব্যাপার, তাই না?"}],
                          "expected": "CORRECT_THE_DISANALOGY", "rubric": flag, "source": "localisation store v1"})
    for name, rows in (("local_probes.jsonl", probes), ("analogy_traps.jsonl", traps)):
        with open(OUT / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)}")


if __name__ == "__main__":
    main()
