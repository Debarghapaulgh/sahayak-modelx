> Moved into `sahayak-modelx` on 2026-09-19 from `GovWB/localized-learning-db` (Track 3, #21). WB re-keying: see `WB_MAPPING.md`.

# Localized Contextual Learning DB

Training backbone for hyper-local K-12 explanation generation (SahayakAI).
Turns canonical NCERT concepts into locally-anchored explanations — apple→coconut,
photosynthesis→khichdi — without breaking pedagogy or exam alignment.

## Locked decisions (2026-08-05)

| Fork | Choice | Consequence |
|------|--------|-------------|
| Scope wedge | **NCERT/CBSE, Science, Grades 6–10** | Single board spine; zones vary |
| Pedagogy | **Additive scaffolding** | Local anchor *adds* intuition; canonical example + exam term always kept (`keep_canonical: true`) |
| Architecture | **Hybrid** | RAG serves the entity KB (updatable); fine-tune bakes in localization *behavior*, not facts |
| Validation | **SahayakAI in-school teachers** | Local-authenticity + pedagogy oracle. The moat. |

## Three layers — never collapse them

```
  ONTOLOGY (graph-shaped)        STORE (versioned records)      CORPUS (flat)
  concept ─ affordance ─┐        YAML in git, property-graph    instruction→output
  local-entity ─ zone ──┼──────► modeled. Diffable, reviewable ─► JSONL, compiled
  strategy ─────────────┘        by teachers.                    from the store.
```

- Model **as** a graph (many-to-many: concept↔affordance↔entity↔zone↔strategy).
- Store as **versioned YAML** — provenance + teacher review beat traversal speed. No Neo4j yet.
- Compile to **flat JSONL** for training. Never store the graph as JSONL.

## The atomic unit is a *substitution*, not a chapter

A concept's anchor plays a pedagogical role. Swap it for a local entity **only if the
entity preserves the affordances that made the original work.** Apple→gravity needs
{visible_mass, detaches, falls, everyday}. Coconut ✅. Kite ❌ (goes up — breaks it).
That affordance-match (deterministic, `schema/` enforced) is the whole quality problem.

## Five localization strategies — each has its own correctness test

1. `anchor_substitution` — swap object, mechanism identical (apple→coconut).
2. `analogy` — map concept to a familiar process (photosynthesis≈cooking). **Must flag disanalogy.**
3. `applied_context` — concept applied to local economy/geography (crop-yield word problems).
4. `cultural_grounding` — the subject *is* local (history, civics, language).
5. `sensory` — the felt local experience (festival drum → sound/vibration).

## Non-negotiable: validation gate

Fine-tuning on an unvalidated LLM analogy bakes the error in permanently.
Every record passes {pedagogy, authenticity(teacher), factual} before it enters the corpus.

## Layout

```
schema/       # record contracts (concept, local-entity, substitution)
data/         # seed records — the reusable assets
compile.py    # store → training JSONL
out/          # compiled corpus (gitignored in real use)
```

## Build order

1. `data/local-entities.seed.yaml` — the reusable KB (build once per zone).
2. `data/substitutions.seed.yaml` — worked units (generated, teacher-validated).
3. `python compile.py` — emit `out/train.jsonl`.
