# Re-keying the localisation ontology to West Bengal (Track 3, #21)

The seed ontology (`schema/`, `data/`) was built on an NCERT Science G6–10 spine. Everything about it
transfers; only the *keys* change.

## 1. Concept spine → the WB curriculum manifest
- `concept.lo_code` stays the canonical, board-agnostic node.
- `concept.board_aliases` (already in the schema) gains an entry per WB textbook chapter, keyed to
  `synthetictutor/knowledge/curriculum_manifest.py` (`board`, `grade`, `subject`, `textbook`, `chapter`, `topic`).
  Example: `c_photo` → `{board: WBBSE, grade: 7, textbook: "পরিবেশ ও বিজ্ঞান", chapter: …, manifest_id: …}`.
- A concept with no WB alias is **out of scope** for WB generation (skipped, not guessed).

## 2. Zones (the salience unit; districts are metadata)
Aligned with #16: `north_bengal` (exists as `north_bengal_tea_belt`), `gangetic_plain`, `rarh_plateau`,
`sundarbans_delta`, `kolkata_metro`, optional `medinipur_coastal`. Non-WB seed zones (Kerala, Tamil Nadu,
Punjab, Deccan, Rajasthan) stay in the KB for reuse but are excluded from WB compiles via `--zones`.

## 3. Pipeline insertion (after `LocaleRetriever`, before generation)
`LocalizationStrategySelector` → picks a strategy per (concept, zone) from the substitution store.
`AffordanceGate` → deterministic: the local entity's affordances must satisfy the canonical anchor's
required affordances; `analogy` requires non-empty `disanalogy_flags`; `keep_canonical` is always true.
A record enters training only with `status: approved` (teacher sign-off, #17).

## 4. Compile
`python compile.py --zones north_bengal_tea_belt,sundarbans_delta` → `out/train.jsonl` (messages format
with the RAG context block). `out/` is git-ignored; rebuild from the store.

## Next
- [ ] add `manifest_id` to `board_aliases` in `schema/schemas.yaml` and re-key the 8 seed concepts
- [ ] `--zones` filter in `compile.py`
- [ ] `AffordanceGate` + `LocalizationStrategySelector` modules under `synthetictutor/knowledge/`
- [ ] jsonschema for the three record types in CI (#24)
