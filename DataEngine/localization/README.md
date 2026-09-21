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


## West Bengal store and compiler (2026-09-19)

The seed above stays as the reusable pattern; the live store is the `*_wb*.yaml` set in `data/`, merged by id in
`gate.py` (`STORE_FILES`, later files override earlier ones):

| File | What | Count |
|------|------|-------|
| `zones_wb.yaml` | 6 zones, `district_zone_map` for all 23 districts, names, festivals, units, languages | 6 / 23 |
| `entities_wb.yaml` + `entities_wb_batch2.yaml` | WB entities with affordance contracts, `NOT_<affordance>` guards, `authenticity` (teacher_informal, attested) | 71 |
| `concepts_wb.yaml` | concepts re-keyed to WBBPE/WBBSE (`exam_term_bn` always kept, `board_aliases` unverified until linked to the manifest) | 33 |
| `substitutions_wb.yaml` + `substitutions_wb_batch2.yaml` | Bengali substitutions, gate-validated, `status: approved` | 85 |
| `misconceptions_wb.yaml` | per-concept wrong/why/right triples (corrections, teacher notes, true/false quiz items) | 66 |

`python gate.py` must print `PASS` (exits 1 on any approved violation). `python compile_wb_sft.py` writes
`../out/sft_wb_v1_{train,eval}.jsonl` + `MANIFEST.json` (tracked) + `sample_50.jsonl` (tracked). Current build (seed 42):
**11,580 records, 10,637 train / 943 eval**, 76 template variants. Held-out split is
family-balanced: the last variant of every template family with two or more variants is eval-only (capped at 40
records each), so every task family has an eval slice and no template appears on both sides. Task families: CONCEPT_EXPLANATION 164, GUIDED_PROBLEM_SOLVING 7,151, LESSON_PLAN 761, LOCAL_CONTEXT_QA 182, MISCONCEPTION_CORRECTION 72, QUIZ_GENERATION 1,180, STORY 1,180, TEACHER_PEDAGOGY 146, WORKSHEET_PRACTICE 800.
Zones: gangetic_plain 2,991, kolkata_metro 795, medinipur_coastal 1,292, north_bengal_tea_belt 1,183, rarh_plateau 1,304, sundarbans_delta 1,248. Worked sums are computed, so every number in a solution is correct by construction; numbered steps
appear only in `GUIDED_PROBLEM_SOLVING`; digits are Bengali-digit checked (share 1.0).

To scale further: add substitutions and misconceptions (each yields explanations, teacher notes, quiz items, lesson
plans), add generator variants (a new `.vN` template), then raise the generator counts in `main()` and
`CAP_PER_TEMPLATE`. `make_review_sheet.py` prints Bengali A4 sheets for teachers when a batch needs a fresh look.
