#!/usr/bin/env python3
"""Affordance gate + strategy selector for the localisation store (Track 3, #21).

A local entity may replace a concept's canonical anchor only if it satisfies the anchor's required
affordances. Analogies must carry disanalogy flags. NOT_<affordance> on an entity blocks any concept
that requires <affordance> (the matka != conduction, kite != gravity guardrails). The canonical exam
term is always kept.

    python gate.py            # report every substitution; exit 1 if an approved unit fails the gate
"""
import math
import pathlib
import sys

import yaml

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data"
STRATEGIES = {"anchor_substitution", "analogy", "applied_context", "cultural_grounding", "sensory"}
STORE_FILES = {
    "zones": ["zones_wb.yaml", "local-entities.seed.yaml"],
    "entities": ["local-entities.seed.yaml", "entities_wb.yaml"],
    "concepts": ["substitutions.seed.yaml", "concepts_wb.yaml"],
    "substitutions": ["substitutions.seed.yaml", "substitutions_wb.yaml"],
}


def _load(name):
    p = DATA / name
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


def load_store():
    """Merge the seed store and the West Bengal store by id (later files win)."""
    store = {"zones": {}, "entities": {}, "concepts": {}, "substitutions": {}, "rejected_examples": [],
             "district_zone_map": {}}
    for key, files in STORE_FILES.items():
        for f in files:
            doc = _load(f) or {}
            for rec in doc.get(key, []) or []:
                store[key][rec["id"]] = rec
    for f in STORE_FILES["substitutions"]:
        store["rejected_examples"] += (_load(f) or {}).get("rejected_examples", []) or []
    store["district_zone_map"] = (_load("zones_wb.yaml") or {}).get("district_zone_map", {})
    return store


def affordance_match(concept, entity):
    """(satisfied, required, missing, blocked): entity affordances vs the anchor's contract."""
    required = list(concept.get("canonical_anchor", {}).get("affordances", []))
    have = entity.get("affordances", {}) or {}
    missing = [a for a in required if not have.get(a)]
    blocked = [a for a in required if have.get("NOT_" + a)]
    return len(required) - len(missing), len(required), missing, blocked


def check(sub, store):
    """Gate one substitution. Returns dict(ok, match, reasons)."""
    reasons = []
    concept = store["concepts"].get(sub.get("concept_id"))
    entity = store["entities"].get((sub.get("local_anchor") or {}).get("entity_id"))
    zone = sub.get("zone_id")
    if not concept:
        reasons.append("unknown concept")
    if not entity:
        reasons.append("unknown entity")
    if zone not in store["zones"]:
        reasons.append(f"unknown zone {zone}")
    if sub.get("strategy") not in STRATEGIES:
        reasons.append(f"unknown strategy {sub.get('strategy')}")
    if not sub.get("keep_canonical", False):
        reasons.append("keep_canonical must be true (additive scaffolding)")
    if concept and concept.get("localizable") is False:
        reasons.append("concept marked non-localizable")
    if entity and zone and zone not in (entity.get("zones") or []):
        reasons.append(f"entity {entity['id']} not native to zone {zone}")
    if sub.get("strategy") == "analogy" and not sub.get("disanalogy_flags"):
        reasons.append("analogy without disanalogy_flags")
    if sub.get("status") == "approved":
        v = sub.get("validation") or {}
        if v.get("authenticity") in (None, "pending_teacher") or v.get("pedagogy") != "pass" or v.get("factual") != "pass":
            reasons.append("approved without a full validation record")
    match = "n/a"
    if concept and entity:
        n, m, missing, blocked = affordance_match(concept, entity)
        match = f"{n}/{m}"
        if blocked:
            reasons.append("blocked by NOT_ affordance: " + ", ".join(blocked))
        strat = sub.get("strategy")
        if strat == "anchor_substitution" and missing:
            reasons.append("anchor_substitution needs every required affordance; missing " + ", ".join(missing))
        elif strat == "analogy" and n < math.ceil(m / 2):
            reasons.append(f"analogy needs at least half the affordances ({n}/{m})")
        elif strat in ("applied_context", "cultural_grounding", "sensory") and m and n < 1:
            reasons.append("no shared affordance with the canonical anchor")
    return {"ok": not reasons, "match": match, "reasons": reasons}


def select_strategy(concept, entity):
    """Pick the strongest admissible strategy for (concept, entity); None if nothing is admissible."""
    n, m, missing, blocked = affordance_match(concept, entity)
    if blocked:
        return None
    if m and not missing:
        return "anchor_substitution"
    if m and n >= math.ceil(m / 2):
        return "analogy"
    if n >= 1:
        return "applied_context"
    return None


def main():
    store = load_store()
    bad = 0
    print(f"store: {len(store['zones'])} zones, {len(store['entities'])} entities, "
          f"{len(store['concepts'])} concepts, {len(store['substitutions'])} substitutions, "
          f"{len(store['rejected_examples'])} documented rejects\n")
    for sid, sub in store["substitutions"].items():
        r = check(sub, store)
        flag = "OK " if r["ok"] else "REJ"
        print(f"{flag} {r['match']:>5}  {sid:<28} {sub.get('strategy', ''):<20} {sub.get('status', '')}")
        for reason in r["reasons"]:
            print(f"        - {reason}")
        if not r["ok"] and sub.get("status") == "approved":
            bad += 1
    for rej in store["rejected_examples"]:
        c, e = store["concepts"].get(rej.get("concept_id")), store["entities"].get(rej["local_anchor"]["entity_id"])
        if not (c and e):
            print(f"TRAP {rej['id']:<30} skipped (concept/entity not in store)"); continue
        strat = select_strategy(c, e)
        print(f"TRAP {rej['id']:<30} gate would allow: {strat}  (must be None)")
        if strat is not None:
            bad += 1
    print(f"\n{'PASS' if not bad else 'FAIL'}: {bad} violation(s)")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
