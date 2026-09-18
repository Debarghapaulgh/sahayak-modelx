# Teacher Model — Project Plan and Task Breakdown

Owner: Abhishek Gupta · Team: Debargha Paul, Sivadeth PS (Siva), Varunesh V (Varun) · Locale: North Bengal, Bengali-medium, WBBSE

Companion docs: `DATASET_ONE_PAGER.md` (strategy at a glance), `LOCALE_CONTEXT_LABELING_GUIDE.md` (schema and worked examples), `DATASET_PREP_PLAYBOOK.md` (step-by-step how to build the dataset).

---

## 1. Goal

Make SahayakAI's teacher model **hyper-local and context-aware**: the same request produces a different, correct answer when the local context changes. A Class 5 fractions worksheet for a rural North Bengal tea-garden classroom in Bengali should read completely differently from one for urban Chennai, even for the identical prompt.

This is the moat. It can only come from real local classroom truth, which no competitor can scrape.

We prove it on **one locale first** (North Bengal, Bengali-medium, WBBSE) and expand only after it measurably beats the baseline.

---

## 2. The governing principle

Fine-tuning teaches **behavior**, not facts.

- Teach: use the local context you are given, correct register and tone, correct format, correct refusal.
- Do not bake into weights: wage, prices, names, syllabus points, festivals. These arrive inside the context block; the answer only uses what it was given.

Local facts live in a retrieval or context layer, not the model.

---

## 3. Baseline-first gate (non-negotiable)

No labeling budget is spent until this test runs.

1. Inject the local context block into base Gemini via prompt, with a couple of in-context examples.
2. Score it on a fixed 200-task local benchmark authored by real teachers.
3. If base Gemini already produces teacher-usable answers, we **do not fine-tune**. We ship prompt plus retrieval.
4. Only the gaps that survive this test justify fine-tuning.

This protects a three-engineer team from babysitting a labeling operation that may not be needed.

---

## 4. Dataset design

### Context tag block

Every example is one JSON object. Facts the answer may use live in `local_facts` and `local_examples`.

```json
{
  "id": "northbengal-math-0001",
  "context": {
    "board": "WBBSE", "grade": 5, "subject": "Mathematics", "medium": "Bengali",
    "district": "Jalpaiguri", "region": "North Bengal", "setting": "rural",
    "infra": ["no_projector", "shared_textbook"], "classroom": "multi_grade",
    "livelihood": ["tea_garden"],
    "local_facts": { "daily_wage": 240, "currency": "INR" },
    "local_examples": ["tea leaves", "plucking basket"],
    "student_names": ["Rina", "Bishal", "Sujan"],
    "register": "north_bengal_bengali_spoken",   // SPOKEN tasks only; omit for worksheets
    "season": "plucking season"
  },
  "task_type": "worksheet",
  "prompt": "<teacher's real request, in Bengali>",
  "ideal_response": "<gold answer a local teacher uses as-is>",
  "notes": "<why correct here; what a generic answer got wrong>"
}
```

### What counts as gold

An answer a **practicing North Bengal teacher would use as-is, without rewriting.** Engineers do not author gold. Teachers sign off. No sign-off means not gold.

### Non-negotiable data rules

1. Author in Bengali. Never English-then-translate.
2. Every fact used must come from the context block. No invented wages, names, syllabus points.
3. `register` applies to spoken tasks only (parent calls). Worksheets and notes use standard written Bengali.
4. Respect infra tags. No projector step for a `no_projector` class.
5. Teacher dignity in tone. No condescension, no marketing register.
6. Strip all real PII before storing. Use only supplied example names.
7. Never store un-reviewed AI text as gold.

### Task types (North Bengal track)

worksheet · lesson_plan · concept_explanation · grading_feedback · parent_call_script · differentiated_material · report_card_remark

### Delivery

- One JSONL per (subject × task_type). Filename `northbengal-{subject}-{tasktype}.jsonl`.
- Hold out 10% as eval before training. No locale+task leak across train and eval.
- Depth over volume. 2k-4k teacher-signed pairs in this one locale beats 50k generic.

---

## 5. Ownership

| Work | Owner | Support |
|---|---|---|
| Track lead and coordination | Siva | — |
| Model decision (Gemini tune vs Sarvam / Gemma LoRA) | Siva recommends, Debargha inputs on Indic/register → Abhishek decides | Varun |
| Recruit and pay 2-3 North Bengal teacher sign-off panel | Abhishek | Debargha liaises |
| Baseline experiment (prompt-inject on Gemini, score) | Varun | Siva harness |
| 200-task local benchmark authoring | Teachers | Debargha routes, Siva assembles |
| Eval scoring harness and rubric | Siva | — |
| Fine-tuning runs (SFT / LoRA) | Siva | Debargha |
| Data pipeline: validator, PII scrub, dedup, split | Varun | — |
| Bengali language QA and gold sign-off routing | Debargha | Teachers sign |
| Final go/no-go on fine-tuning | Abhishek | reads benchmark |

---

## 6. Task breakdown, this week

Full how-to for each step is in `DATASET_PREP_PLAYBOOK.md`. Summary of ownership this week below.

### Siva — track lead, training and evaluation
1. Own the plan and the weekly number: teacher-usable percent, tuned vs baseline. Coordinate Debargha and Varun.
2. Build the eval scoring harness against a 20-task placeholder set, ready for the real benchmark (Playbook Phase C, D).
3. Draft the eval rubric in concrete checkable terms: correct grade level, in-medium, uses only given facts, respects infra.
4. Own the training path (SFT, and LoRA if open-weights) and the model recommendation writeup, with Debargha's input on Indic register (Playbook Phase F).

### Debargha — Bengali QA, locale pack, teacher liaison
1. Build the North Bengal locale pack (Playbook Phase A): districts, names, livelihoods, wages, prices, season calendar, WBBSE chapter lists. This is the input side of every example.
2. Input to Siva's model recommendation on Indic register: where base Gemini's Bengali falls short and whether Sarvam or Gemma would do better.
3. Define and run the gold sign-off loop: how a draft reaches a teacher and returns marked.

### Varun — baseline experiment and data pipeline
1. Stand up context-block injection on base Gemini, run against Siva's 20-task placeholder set, report scores (Playbook Phase D). This is the most important result this month.
2. Ship the JSONL validator (rejects missing context fields or facts not in the context block) and the PII scrub step, as scripts anyone can run (Playbook Phase F).
3. Wire the candidate-generation script (context pack in, draft out) so teachers get drafts to edit (Playbook Phase E).

---

## 7. Sequencing and dependencies

1. **Abhishek** settles the model target and recruits the teacher panel. Nothing scales until this.
2. **Siva** builds the eval harness; **teachers** author the benchmark; **Varun** runs the baseline.
3. If baseline passes → stop, ship prompt plus retrieval, no labeling.
4. If baseline fails → **teachers** author gold, **Debargha** QA and routes sign-off, **Varun** packages, **Siva** trains and evaluates.

Two blockers only the founder can clear: the model decision and the teacher panel. Everything else waits on those.

---

## 8. Open decisions

- Target model: Gemini supervised tuning vs Sarvam / Gemma LoRA. Siva recommends this week, with Debargha's input on Indic register.
- Whether preference data (DPO) is collected, which depends on the model choice.
- Teacher panel: who, how many, how paid.
