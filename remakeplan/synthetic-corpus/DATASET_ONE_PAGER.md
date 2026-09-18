# SahayakAI Local Teacher Dataset — One-Page Guide

**Goal.** Make the model produce a *different, correct* answer when local context changes. Same request, tea-garden North Bengal vs urban Chennai, different answer. This is our moat.

**Scope now.** One locale, deep: **North Bengal, Bengali-medium, WBBSE.** Prove lift here before any other language or region.

---

### The one rule that governs everything

Fine-tuning teaches **behavior** (use the local context you are given; correct tone, format, refusal). It does **not** store facts. Every local fact — wage, prices, names, syllabus point, festival — arrives *inside* the context block; the training answer only *uses* it. If an answer invents a fact that was not in the context block, it is wrong.

---

### Step 0 — baseline first (do this before mass labeling)

Inject the context block into base Gemini via prompt and score it on a fixed 200-task local benchmark authored by real teachers. Fine-tune only the gaps that survive. If prompting already passes, we do not fine-tune, we ship prompt + retrieval. No labeling budget is spent until this gate is passed.

---

### Context tag block (every example carries this)

```json
{ "board":"WBBSE", "grade":5, "subject":"Mathematics", "medium":"Bengali",
  "district":"Jalpaiguri", "region":"North Bengal", "setting":"rural",
  "infra":["no_projector","shared_textbook"], "classroom":"multi_grade",
  "livelihood":["tea_garden"], "local_facts":{"daily_wage":240,"currency":"INR"},
  "local_examples":["tea leaves","plucking basket"],
  "student_names":["Rina","Bishal","Sujan"],
  "register":"north_bengal_bengali_spoken",   // SPOKEN tasks only (parent calls). Omit for worksheets.
  "season":"plucking season" }
```

Facts the answer may use go in `local_facts` / `local_examples`. The model must not add facts of its own.

---

### What counts as gold

An answer a **real North Bengal teacher would use as-is, without rewriting.** Interns draft and QA. A practicing local teacher signs off. No teacher sign-off = not gold. No exceptions.

### Non-negotiable rules

1. Author in the medium. Never English-then-translate.
2. Every fact used must come from the context block. No invented wages, names, syllabus points.
3. `register` tag applies to spoken tasks (parent calls) only. Worksheets and notes use standard written Bengali.
4. Respect infra tags. No projector step for a `no_projector` class.
5. Teacher dignity in tone. No condescension, no marketing register.
6. Strip all real PII (student names, phone numbers) before anything is stored. Use supplied example names only.
7. Never store un-reviewed AI text as gold. A model draft is a scaffold a teacher must rewrite.

### Task types (North Bengal track)

worksheet · lesson_plan · concept_explanation · grading_feedback · parent_call_script · differentiated_material · report_card_remark

### Delivery

- One JSONL per (subject × task_type). Filename `northbengal-{subject}-{tasktype}.jsonl`.
- Hold out 10% as eval before training. No locale+task leak between train and eval.
- Depth over volume: diverse across grade × subject × task within this one locale. 2k-4k teacher-signed pairs here beats 50k generic.

**Open decision (owner: founder).** Target model = Gemini supervised tuning vs Sarvam/Gemma LoRA. Indic register points at Sarvam. Settle before scaling labeling; it changes format and whether preference data (DPO) is possible.

Detailed schema + worked examples: `LOCALE_CONTEXT_LABELING_GUIDE.md`.
