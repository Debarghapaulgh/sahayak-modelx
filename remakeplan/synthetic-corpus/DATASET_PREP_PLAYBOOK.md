# Dataset Preparation Playbook

How to actually build the North Bengal teacher-model dataset, step by step. For Debargha, Siva, Varun. Read `DATASET_ONE_PAGER.md` for the strategy first. This document is the how.

Locale for now: North Bengal, Bengali-medium, WBBSE. One locale, deep.

---

## Folder layout

```
synthetic-corpus/
  locale-packs/
    north-bengal.json           # the local facts, names, calendar (input side)
  prompts/
    real-teacher-prompts.jsonl  # requests teachers actually make (demand side)
  benchmark/
    northbengal-benchmark.jsonl # 200 frozen eval tasks, teacher-authored. NEVER trained on
  gold/
    northbengal-math-worksheet.jsonl
    northbengal-science-lessonplan.jsonl
    ...                         # one file per (subject x task_type)
  scripts/
    generate_candidate.py       # context pack -> model draft
    validate.py                 # schema + no-invented-fact check
    scrub_pii.py                # strip names/phones before storing
    split.py                    # 90/10 train/eval, no leak
    score.py                    # run answers against benchmark + rubric
```

---

## Phase A — Locale pack (owner: Debargha)

The context block on every example is filled from one small, teacher-verified file. Build it once, reuse everywhere. This is where local facts live, so they never get invented inside answers.

`locale-packs/north-bengal.json`:

```json
{
  "region": "North Bengal",
  "board": "WBBSE",
  "medium": "Bengali",
  "districts": ["Jalpaiguri", "Darjeeling", "Alipurduar", "Cooch Behar"],
  "settings": ["rural", "semi-urban"],
  "livelihoods": ["tea_garden", "small_farming", "daily_wage", "small_shop"],
  "local_facts": {
    "tea_garden_daily_wage": 250,
    "currency": "INR",
    "common_prices": { "notebook": 30, "pen": 10, "kg_rice": 40 }
  },
  "local_examples": ["tea leaves", "plucking basket", "paddy field", "toy train", "river Teesta"],
  "student_names": ["Rina", "Bishal", "Sujan", "Anjali", "Nabin", "Puja", "Karan", "Mitali"],
  "season_calendar": {
    "plucking season": "Mar-Nov",
    "festivals": ["Durga Puja", "Kali Puja", "Poush Mela"]
  },
  "infra_defaults": ["no_projector", "shared_textbook", "load_shedding"],
  "syllabus": {
    "note": "chapter lists per grade x subject, from WBBSE textbooks",
    "math_grade5": ["numbers", "fractions", "measurement", "geometry", "data"]
  }
}
```

How to fill it: sit with a North Bengal teacher, confirm each number and list. Wages and prices must be real and current. Pull chapter lists straight from the WBBSE textbooks. Do not guess.

---

## Phase B — Real teacher prompts (owner: Varun, sourced by Debargha)

We need the requests teachers actually make, in their words, not requests we imagine. Target 200-400.

Sources, cheapest first:
- Pilot teachers: a 5-minute Google Form, "what did you last ask an assistant to make." Repeat weekly.
- Shadow 2-3 teachers for a day, write down every ask.
- Existing WhatsApp or app requests, scrubbed of PII.

Store as `prompts/real-teacher-prompts.jsonl`, one per line:

```json
{ "prompt": "ক্লাস ৫ এর ভগ্নাংশের ওয়ার্কশিট, ৫টা প্রশ্ন", "task_type": "worksheet", "grade": 5, "subject": "Mathematics" }
```

This distribution tells us what to cover and in what proportion. Do not over-index on worksheets if teachers actually ask more for parent-call scripts.

---

## Phase C — Benchmark first (owner: Siva, authored by teachers)

Before any training, freeze a 200-task evaluation set. This is what decides go or no-go, and what we measure every training run against.

- Sample 200 prompts from Phase B across grade x subject x task_type.
- For each, a real teacher writes the ideal answer (or, faster, teachers score model answers 1-5 later; authoring is stronger).
- Freeze it. It is never in any training file. `split.py` enforces no leak.

Rubric Siva writes, each item pass/fail or 1-5:
1. Correct grade level.
2. In Bengali, correct medium.
3. Uses only facts from the context block, invents none.
4. Respects infra tags (no projector step for no_projector).
5. Correct format for the task type.
6. Teacher would use as-is (the overall gold test).

---

## Phase D — Baseline experiment (owner: Varun)

The most important result this month. Prove whether we even need fine-tuning.

Prompt template, context injected:

```
System: You are a teaching assistant for WBBSE, Bengali-medium, North Bengal.
Use ONLY the facts in the context block. Do not invent wages, names, or syllabus points.
Respect the classroom constraints. Answer in Bengali.

Context: { ...the context block for this task... }

Examples:
[2-3 worked pairs from LOCALE_CONTEXT_LABELING_GUIDE.md]

Task: <the teacher prompt>
```

Run this on base Gemini across the 200 benchmark tasks. Score with `score.py` against the rubric.

- If it passes (say 80 percent teacher-usable): stop. Ship prompt plus retrieval. No fine-tuning. Document the result.
- If it fails on specific axes (register wrong, drifts to generic examples, format breaks): those failures define exactly what fine-tuning must fix. Proceed to Phase E, focused only on the gaps.

---

## Phase E — Gold data, only if Phase D fails (owner: Varun tooling, Debargha QA, teachers sign)

Do not hand-write thousands of examples. Generate, then have a teacher fix. The fix is the gold.

Loop per example:
1. `generate_candidate.py` takes a context block (from the locale pack) plus a prompt (from Phase B) and produces a draft from the strong model.
2. A North Bengal teacher edits the draft until they would use it as-is.
3. Store the teacher-approved version as `ideal_response`. That is one SFT record.
4. Keep the original draft too. The pair (original = rejected, edited = chosen) is a DPO record if we go that route.

SFT record:

```json
{ "id": "northbengal-math-0001", "context": { ... }, "task_type": "worksheet",
  "prompt": "...", "ideal_response": "<teacher-approved>", "notes": "..." }
```

DPO record (only if model choice supports it):

```json
{ "context": { ... }, "prompt": "...",
  "chosen": "<teacher-edited>", "rejected": "<original draft>" }
```

Why this way: the teacher edit is the highest-signal data we can get, and it is far faster than authoring from blank. The edit literally shows the model what to change.

Quantity target for this locale: 2k-4k teacher-signed SFT records, spread across grade x subject x task_type. Depth beats volume. Cover the common cells well before touching rare ones.

---

## Phase F — Validate, scrub, split, train (owner: Varun pipeline, Siva training)

Every file passes the pipeline before it counts:

1. `validate.py`: rejects any record missing required context fields, or whose answer uses a number or name not present in its context block. This is the anti-fact-baking check. Automate it, do not eyeball.
2. `scrub_pii.py`: removes any real student name or phone number. Only supplied example names allowed.
3. `split.py`: 90/10 train/eval. Hard fail if any benchmark task or its locale+task twin appears in train.
4. Train (Siva), once Debargha settles the model:
   - Gemini supervised tuning: upload SFT JSONL in the required format, tune, evaluate on the frozen benchmark.
   - Or Gemma / Sarvam LoRA: standard PEFT LoRA run, low rank to start, evaluate on the same benchmark.
5. Score the tuned model on the benchmark with `score.py`. Compare against the Phase D baseline. If it does not beat baseline, the data or the recipe is wrong, not the benchmark. Iterate.

---

## Weekly cadence

- Every week: teachers add prompts (Phase B) and sign off a batch of gold (Phase E).
- Every week: one training run against the frozen benchmark, one number to report: teacher-usable percent, tuned vs baseline.
- Stop expanding to new locales until North Bengal clears the bar.

---

## The three mistakes that kill this dataset

1. Facts invented inside answers instead of coming from the context block. `validate.py` must catch it.
2. Fluent Bengali that a real teacher would still rewrite. Sign-off gate catches it.
3. Spreading thin across many locales and subjects before proving one. Depth first.
