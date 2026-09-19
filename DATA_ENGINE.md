# Data Engine — sahayak-modelx

**The data engine is the moat.** It turns West Bengal textbooks + local context + teacher judgement into
training and evaluation data that (a) makes SahayakAI-30 local-context-aware at the *weight* level
(rungs 3–4 in `EXECUTION_PLAN.md`) and (b) nobody can reproduce without our corpus.

_Owners: **[C]** Abhishek+Claude · **[D]** Debargha (@Debarghapaulgh — add as collaborator) ·
**[V]** varunesh-v (eval) · **[S]** Sachitt (GPU jobs, not data) · **[T]** teachers. Flow: `feature → develop → main`._

---

## 1. What already exists — do not rebuild

### A. Grounding corpus + generation pipeline — Debargha, PR #12 (`feature/synthetic-tutor`)
- **Textbooks:** 61 WBBPE / WBBSE / WBCHSE books OCR'd (Tesseract) → 19,566 raw chunks →
  **13,914 approved** (4,029 text-only + 9,885 with visual context), 5,652 quarantined.
  Manifest `datasets/final_grounding_corpus/wbbse_grounding_v1_manifest.json` (v1.0.0, SHA-256 per file, 2026-09-14).
  Frozen `wbbse_sft_source_pool.jsonl`: 1,649 verified chunks, Classes 6–10.
- **Coverage** (`corpus_distribution_audit.json`): WBBPE 5,284 · WBBSE 7,816 · WBCHSE 814. Grades 1–12
  (thin: Class 12 = 101, Class 1 = 334, Class 9 = 1,075). Subjects: Bengali 4,534 · Maths 3,970 · English 1,679 ·
  Science 755 · EVS 690 · HPE 670 · History 476 · Geography 205. 12,235 Bengali-medium.
- **Curriculum resolver** `synthetictutor/knowledge/curriculum_manifest.py`: WBBPE (I–V) → WBBSE (VI–X) → WBCHSE (XI–XII),
  real textbook names (সহজ পাঠ, আমাদের পরিবেশ, গণিতপ্রভা, গণিত প্রকাশ), learning outcomes, 2026 summative periods.
- **Locale layer** `locale.json` + `knowledge/locale_retriever.py`: **North Bengal, 8 districts** (Darjeeling, Kalimpong,
  Jalpaiguri, Alipurduar, Cooch Behar, Malda, Uttar Dinajpur, Dakshin Dinajpur), 100+ fields each with a **source**
  (MGNREGA wage, urea price, paddy yield, tea economy, literacy, rainfall, soil pH…), district synonyms, local units
  (বিঘা / কাঠা / সের / মণ), and a "no forced localisation" rule.
- **Pipeline** `pipeline/grounding_first_pipeline.py` (request-first): intent (teacher 85% / student 15%; task families
  CONCEPT_EXPLANATION, GUIDED_PROBLEM_SOLVING, MISCONCEPTION_CORRECTION, WORKSHEET_PRACTICE, QUIZ_GENERATION, LESSON_PLAN,
  TEACHER_PEDAGOGY) → curriculum target → BM25 textbook retrieval → locale retrieval → compatibility gate (0–5 fidelity)
  → grounded generation → 8-stage validation → export (ShareGPT / ChatML / HF). Specs in `docs/*.md`.
  Persona library, student/teacher simulators, judges (factual, pedagogical, leakage).
- **SFT sets** `Final/`: final_merged 3,000 · gold_standard 2,000 (API-generated) · expansion 500 · chatml 155 ·
  curated part-1 164 / 100 / 57 / 45. System prompt: SahayakAI · WBBPE/WBBSE/WBCHSE · Bengali-medium ·
  teacher **আপনি** / student **তুমি** · 100% Bengali digits · official WBBSE terminology · labelled steps
  (দেওয়া আছে / ধরি / সূত্রানুসারে / অতএব নির্ণেয় উত্তর).
- **Class-10 maths pack** `wbbse_class10_math_pack/`: Ganit Prakash X, 26 chapters (2025–26 verified), 808 chunks,
  parallel generator + verifier (dedupe, Bengali digits).

### B. Localisation ontology — `GovWB/localized-learning-db/` (2026-08-05; **to be moved into this repo**)
- Atomic unit = a **substitution**, not a chapter. Graph: concept (learning-outcome-anchored `lo_code`, `board_aliases`)
  ↔ affordances ↔ local_entity (kind, zones, affordances, teacher authenticity) ↔ **zone** (agro-cultural-ecological,
  not district) ↔ strategy.
- **Five strategies**, each with its own correctness test: `anchor_substitution` · `analogy` (**mandatory
  `disanalogy_flags`**) · `applied_context` · `cultural_grounding` · `sensory`.
- **Deterministic affordance match:** a local entity may replace a canonical anchor only if it satisfies the anchor's
  required affordances (coconut ✓ for gravity; kite ✗). Documented trap: a *matka* cools by **evaporation, not
  conduction** → `NOT_conduction_cooling` blocks the match. Fine-tuning on a wrong analogy bakes the error in permanently.
- **Additive scaffolding:** canonical example + exam term always kept (`keep_canonical: true`).
- **Validation gate** `{pedagogy, authenticity(teacher), factual}`; status `draft → teacher_review → approved`.
  Nothing enters the corpus un-approved.
- Seed: 7 zones (2 in WB: `north_bengal_tea_belt`, `sundarbans_delta`), 9 entities, 8 substitutions (Science G6–10),
  `compile.py` → messages JSONL with a RAG context block.

### C. The honest SFT scaffold — `Finetune/` (this repo)
- `prepare_data.py`: 491 train / 66 eval, **0 template overlap**, template cap 4, Bengali numerals.
- `mix_general_data.py` (anti-forgetting mix), `eval_compare.py` (base vs fine-tuned).

## 2. How they fit
**A** = what is true, where (curriculum + district facts + generation machinery). **B** = how to localise without
breaking pedagogy (affordance contracts, disanalogy flags, teacher authenticity). **C** = evaluation honesty.
A's locale retriever fetches district *facts*; it has no analogy-validity logic. B is inserted as a stage between
locale retrieval and generation; C's held-out discipline applies to everything; the two validation gates merge into one
whose **only path to `approved` is a teacher**.

```
intent → curriculum target → textbook retrieval → locale retrieval
      → [NEW] localisation strategy + affordance gate            (B)
      → compatibility gate → generation → 8-stage validation      (A)
      → [NEW] teacher review: authenticity + pedagogy → approved   (B)
      → compile → train / held-out, 0 template overlap            (C)
```

---

## 3. Tracks

### Track 0 — Harden and merge PR #12 (prerequisite) · [D] owner, [C] reviewer
PR #12 is **not mergeable as-is**. Required before merge:
1. **Secrets.** Remove hardcoded API keys from `wbbse_class10_math_pack/generate_wbbse_class10_math_sft.py`; read from
   env only. **Rotate any key that was ever committed** — the repo is public. Add a secret scan (gitleaks) to CI.
2. **Data out of git.** ~125 MB of JSONL (`datasets/final_grounding_corpus/*`, `Final/*`) → Git LFS or the
   `sahayak-models-aps1` bucket, with the manifest's SHA-256s as the contract. Manifests + audits stay in git.
3. **Locale defaults.** `locale.json` `region_summary.default_board: CBSE` / `default_medium: English` → `WBBSE` / `Bengali`.
4. **Stale test.** `tests/unit/test_ncert_localized_qa.py` imports `synthetic-corpus/scripts/…` (not in the PR) → fix or drop.
5. **Layout.** Root-level scripts (`generate_*.py`, `*_tesseract.py`, `parallel_ocr.py`, `wbbse_*_extract.py`,
   `train_sarg_llm.ipynb`, `adapter_config.json`) → `synthetictutor/scripts/`, `notebooks/`; fix the
   `Final/… (1).jsonl` filename.
6. **CI green** on the PR (ruff E9/F63/F7/F82, nbformat, shellcheck). The fork PR has no checks yet.
7. **Provenance on every record:** `{generator_model, provider, licence, chunk_ids, locale_keys, validator_version,
   teacher_id?}`. Records generated through OpenAI / Gemini APIs are **quarantined** until the licence decision (Track 3).
- **DoD:** merged to `develop` with CI green, no secrets in history (squash-merge; fork branch force-pushed clean),
  data via LFS/bucket. @Debarghapaulgh added as collaborator so issues can be assigned.

### Track 1 — Corpus coverage → whole-state spine · [D][C]
- Fill thin cells: Class 12 (101), Class 1 (334), Class 9 (1,075); Science (755), Geography (205), History (476).
- Coverage matrix board × grade × subject × chapter, ≥ 15 text-only chunks per chapter; `coverage_status` per cell in
  manifest v1.1; `corpus_distribution_audit.json` regenerated in CI.
- **DoD:** no (grade × subject) cell below threshold for WBBSE VI–X; every chapter of Ganit Prakash X, Ganit Prabha VI–VIII
  and the VI–VIII science texts covered.

### Track 2 — Locale: North Bengal → all of West Bengal · [D][T]
- Extend to **zones** (B's unit): `north_bengal_tea_belt` (exists), `sundarbans_delta`, `gangetic_plain`
  (Nadia / Murshidabad / Bardhaman rice belt), `rarh_plateau` (Purulia / Bankura / Jhargram), `kolkata_metro`.
- Per zone: sourced quantitative facts (same `{value, source}` shape as today), local entities with affordances (B schema),
  festivals, crops, units, livelihoods, rivers, weather. District → zone mapping table. Retriever gains zone-level retrieval;
  "no forced localisation" preserved.
- **DoD:** ≥ 5 zones, ≥ 40 local entities with teacher-validated authenticity, every quantitative fact sourced.

### Track 3 — Localisation ontology into the pipeline · [C][D]
- Move `localized-learning-db/` → `DataEngine/localization/` (schema, seeds, compile).
- Swap the NCERT `lo_code` spine → WB learning outcomes via `board_aliases`; map to `curriculum_manifest` entries.
- New stages after `LocaleRetriever`: `LocalizationStrategySelector` + `AffordanceGate` — choose strategy per
  (concept, zone), enforce affordance match, require `disanalogy_flags` for analogy, always `keep_canonical`.
- Merge validation: 8-stage deterministic + `{pedagogy, authenticity, factual}` + status lifecycle. Teacher sign-off can be a
  sheet export/import at first.
- **Licence policy for generated text:** prefer generation from our own served model (`Serving/`) or permissively-licensed
  open models; API-generated (OpenAI / Gemini) records stay out of training until legal clears them. Provenance mandatory.
- **DoD:** records carry strategy + `affordance_match` + flags; 0 records reach `approved` without a teacher; the
  matka-style trap test passes.

### Track 4 — Format-discipline data (the ধাপ finding) · [C][T]
- Live probe 2026-09-19: the base over-applies numbered **ধাপ 1 / 2 / 3** to *every* task because the system prompt says
  ধাপে ধাপে. Fix it in **data**, not the prompt — format by task: worked maths → labelled steps; quiz → প্রশ্ন / উত্তর,
  one line each, **no ধাপ**; concept → prose or plain bullets; story → prose; lesson plan → WB template.
  Register: teacher আপনি / student তুমি. Bengali digits throughout.
- Loosen the training system prompt to match ("step-by-step only where it aids understanding").
- **DoD:** ≥ 20% of SFT is non-maths tasks with no step numbering; eval has a format-compliance check per task family.

### Track 5 — Evaluation: WB-local and honest · [V][T]
- Extend `Evaluation/` (Bengal Validator, LLM Judge, Metrics, `audit_diversity`) + `Finetune/eval_compare.py`:
  held-out with 0 template overlap plus real student/teacher questions · **local-context probes** (place / festival /
  unit / crop facts per zone; an analogy-trap set that must *not* teach matka = conduction) · per-chapter WBBSE questions
  with citations · format compliance per task family · register check · **forgetting**: general Bengali + English
  benchmarks, threshold −5%.
- **DoD:** one `make eval` producing a scorecard; gates wired into `Finetune/`.

### Track 6 — Teacher review loop · [T][C]
- Reviewers per (grade × subject); review quota; sheet-based sign-off → `approved`; authenticity notes feed the entity KB.
- **DoD:** every zone's entities and a sample per (grade × subject) signed by a teacher; reviewer recorded in provenance.

### Track 7 — Storage, versioning, CI · [C]
- LFS / bucket for JSONL; manifests in git; `datasets/VERSIONS.md`; `make corpus` rebuilds manifest + audit;
  CI: secret scan, jsonschema validation for B, manifest SHA check, coverage-audit diff.
- **DoD:** reproducible corpus build from the manifest; CI blocks secrets and schema breaks.

---

## 4. Volume targets (honest)
| Milestone | Approved SFT records | Grounding chunks | Local entities | WB zones |
|---|---|---|---|---|
| now | 491 (`Finetune/`) + ~3,000 (PR #12, pending provenance audit) | 13,914 | 9 (seed) | 2 |
| v1 (6 wks) | 10,000 (+ DPO pairs 1,000) | 16,000 (thin cells filled) | 40 | 5 |
| v2 (3–4 mo) | 30,000 (+ DPO pairs 5,000) | 20,000 | 100 | 5 |
| CPT corpus (rung 4) | — | **0.5–2 B tokens**: approved chunks + public-domain Bengali literature + bn-Wikipedia + gazettes + **licensed** textbooks | — | — |

## 5. Order of work — data engine first
1. **Track 0** (PR #12 hardening) — this week. **Track 7** alongside it.
2. **Tracks 4 + 5** start immediately (no dependency on the merge).
3. **Tracks 1, 2, 3** after the merge.
4. **Track 6** runs continuously from week 2.

## 6. Rights and governance
- WBBSE / WBBPE / WBCHSE textbooks are copyrighted. Internal grounding and research use is not redistribution, but
  **training (CPT) on them needs the state's permission** — that ask belongs in the CoE / state proposal. Until then, SFT
  records reference chunks by id (provenance) and CPT uses only rights-cleared text.
- API-generated text: provider terms may restrict training competing models → quarantine + legal decision.
- **No student PII** in any dataset (DPDP §9). Teacher names in provenance only with consent.
- Non-partisan content. Every locale fact carries a source.

## 7. Tracking
Epic issue: **#** · per-track issues linked from it · `PROGRESS.md` = living status.
