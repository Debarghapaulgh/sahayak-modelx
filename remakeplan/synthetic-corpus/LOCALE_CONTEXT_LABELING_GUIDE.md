# Locale-Context Labeling Guide (full reference)

Companion to `DATASET_ONE_PAGER.md`. Read the one-pager first for the strategy and the non-negotiable rules. This document is the detailed schema, field reference, and worked examples labelers use day to day.

Scope now: one locale, deep. **North Bengal, Bengali-medium, WBBSE.** Prove lift here before any expansion.

---

## 1. The governing rule

Fine-tuning teaches **behavior**, not facts.

- Behavior we teach: use the local context you are given, correct register and tone, correct format, correct refusal.
- Facts we do **not** bake into weights: wage, prices, names, syllabus points, festivals. These arrive inside the context block, in `local_facts` and `local_examples`. The answer only uses what it was given.

If an answer introduces a fact that was not in the context block, the example is wrong. This is the single most common labeling mistake. Audit for it every time.

---

## 2. Context tag block

Every example is one JSON object. The `context` block is the locale conditioning. Facts the answer is allowed to use live in `local_facts` and `local_examples`.

```json
{
  "id": "northbengal-math-0001",
  "context": {
    "board": "WBBSE",
    "grade": 5,
    "subject": "Mathematics",
    "medium": "Bengali",
    "state": "West Bengal",
    "district": "Jalpaiguri",
    "region": "North Bengal",
    "setting": "rural",
    "infra": ["no_projector", "shared_textbook", "load_shedding"],
    "classroom": "multi_grade",
    "livelihood": ["tea_garden"],
    "local_facts": { "daily_wage": 240, "currency": "INR" },
    "local_examples": ["tea leaves", "plucking basket", "daily wage"],
    "student_names": ["Rina", "Bishal", "Sujan", "Anjali"],
    "season": "post-monsoon plucking season"
  },
  "task_type": "worksheet",
  "prompt": "<teacher's real request, in the medium they type>",
  "ideal_response": "<gold answer a local teacher would use as-is>",
  "notes": "<why this is correct here; what a generic answer got wrong>"
}
```

### Field reference

| Field | Notes |
|---|---|
| `board` | WBBSE for this track. Drives syllabus, chapter order, exam pattern |
| `grade` | 1-12 |
| `subject` | Mathematics, Science, Bengali, EVS, English, etc. |
| `medium` | Language of instruction. Not the same as prompt language |
| `state`, `district`, `region` | Geography. Region = our operating belt label |
| `setting` | rural / semi-urban / urban |
| `infra` | Real constraints: no_projector, load_shedding, shared_textbook, large_class |
| `classroom` | single_grade / multi_grade |
| `livelihood` | Local economy. Feeds word problems and analogies |
| `local_facts` | Numbers the answer may use (wage, price). The answer must not invent others |
| `local_examples` | Concrete local nouns to use instead of generic ones |
| `student_names` | Region-appropriate names for use inside examples |
| `register` | SPOKEN tasks only (parent calls). Omit for worksheets and written notes |
| `season` | Ground examples in the local calendar |

---

## 3. What counts as gold

An answer a **practicing North Bengal teacher would use as-is, without rewriting.**

- Interns draft and QA. A local teacher signs off. No sign-off means not gold.
- Being a fluent Bengali writer is not the same as knowing a tea-garden classroom. Drafts are drafts until a teacher confirms them.

---

## 4. Non-negotiable rules

1. Author in the medium. Never English-then-translate.
2. Every fact used must come from the context block. No invented wages, names, or syllabus points.
3. `register` applies to spoken tasks only. Worksheets and notes use standard written Bengali.
4. Respect infra tags. No projector step for a `no_projector` class.
5. Teacher dignity in tone. No condescension, no marketing register.
6. Strip all real PII before storing. Use only the supplied example names.
7. Never store un-reviewed AI text as gold. A model draft is a scaffold a teacher rewrites.

---

## 5. Task types (North Bengal track)

worksheet · lesson_plan · concept_explanation · grading_feedback · parent_call_script · differentiated_material · report_card_remark

Cover these across grades and subjects within the one locale. Depth over breadth.

---

## 6. Worked examples

Study the `notes` field. It names what a generic answer would get wrong. Note how every fact used appears first in `context.local_facts` or `context.local_examples`.

### 6.1 Worksheet — fractions, tea-garden (written, no register tag)

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
    "student_names": ["Rina", "Bishal", "Sujan", "Anjali"], "season": "plucking season"
  },
  "task_type": "worksheet",
  "prompt": "ক্লাস ৫ এর জন্য ভগ্নাংশের একটা ওয়ার্কশিট বানিয়ে দাও, ৫টা প্রশ্ন।",
  "ideal_response": "ভগ্নাংশ - অনুশীলন (শ্রেণি ৫)\n\n১. রিনার মা এক দিনে ৮ কেজি চা পাতা তোলেন। তার মধ্যে ১/৪ ভাগ কচি পাতা। কচি পাতা কত কেজি?\n\n২. একটা ঝুড়িতে ১২টা পাতার আঁটি আছে। বিশাল তার ১/৩ ভাগ আলাদা করল। সে কতগুলো আঁটি আলাদা করল?\n\n৩. সুজন ৩/৪ ঘণ্টা আর অঞ্জলি ১/২ ঘণ্টা পাতা তুলল। কে বেশি সময় কাজ করল?\n\n৪. এক দিনের মজুরি ২৪০ টাকা। রিনার মা আধা দিন (১/২) কাজ করলেন। তিনি কত টাকা পেলেন?\n\n৫. একটা আঁটির ২/৫ ভাগ শুকনো পাতা। বাকি কত ভাগ কাঁচা পাতা?",
  "notes": "No register tag: worksheets are standard written Bengali. The Rs 240 wage in Q4 comes from context.local_facts, not invented. Generic answer would use apples/pizza/malls and a made-up number. Multi-grade + no_projector means plain paper text, no on-screen step."
}
```

### 6.2 Parent-call script — attendance (spoken, register tag applies)

```json
{
  "id": "northbengal-parentcall-0002",
  "context": {
    "board": "WBBSE", "grade": 3, "subject": "General", "medium": "Bengali",
    "district": "Darjeeling", "region": "North Bengal", "setting": "rural",
    "livelihood": ["tea_garden"], "register": "north_bengal_bengali_spoken",
    "student_names": ["Sujan"]
  },
  "task_type": "parent_call_script",
  "prompt": "সুজন তিন দিন স্কুলে আসেনি। ওর বাবাকে ফোন করার জন্য একটা ছোট স্ক্রিপ্ট দাও।",
  "ideal_response": "নমস্কার, আমি সুজনের ক্লাস টিচার বলছি। ভালো আছেন তো?\n\nসুজন গত তিন দিন স্কুলে আসেনি, তাই একটু খোঁজ নিতে ফোন করলাম। ও কি অসুস্থ, নাকি অন্য কোনো অসুবিধা হয়েছে?\n\n(শুনুন)\n\nবুঝলাম। ও পড়াশোনায় ভালো, কয়েকটা দিন বাদ পড়লে পিছিয়ে যাবে। কাল থেকে যদি পাঠাতে পারেন খুব ভালো হয়। কোনো দরকার হলে আমাকে জানাবেন। ধন্যবাদ।",
  "notes": "Spoken task, so register tag applies. Warm, respectful, no blame. Assumes a garden-worker parent with a tight schedule. Short, leaves a listening pause. No lecture."
}
```

### 6.3 Conditioning check — same prompt, different locale (reference only, not this track)

```json
{
  "id": "chennai-math-0003",
  "context": {
    "board": "TN State", "grade": 5, "subject": "Mathematics", "medium": "Tamil",
    "district": "Chennai", "region": "Tamil Nadu", "setting": "urban",
    "livelihood": ["salaried", "small_shop"],
    "local_facts": { "bus_fare": 10, "currency": "INR" },
    "local_examples": ["bus fare", "idli", "shop change"],
    "student_names": ["Karthik", "Divya", "Priya"]
  },
  "task_type": "worksheet",
  "prompt": "5-ஆம் வகுப்புக்கு பின்னங்கள் பற்றி ஒரு worksheet தயார் செய்யுங்கள், 5 கேள்விகள்.",
  "ideal_response": "<Tamil worksheet using bus fare, idli counts, shop change; Karthik/Divya names>",
  "notes": "Same structure as 6.1. Everything local changes: language, examples, names, urban context. Shown only to illustrate that context drives the answer. Do not label Tamil now; North Bengal first."
}
```

---

## 7. Delivery

- One JSONL per (subject × task_type). Filename `northbengal-{subject}-{tasktype}.jsonl`.
- Hold out 10% as an eval set before any training. No locale+task combination may appear in both train and eval.
- Depth over volume. Diverse across grade × subject × task within this one locale. 2k-4k teacher-signed pairs here beats 50k generic.
- Validator must reject any example missing required context fields or using a fact absent from the context block.

**Open decision (owner: founder).** Target model = Gemini supervised tuning vs Sarvam/Gemma LoRA. Settle before scaling labeling; it changes format and whether preference (DPO) data is collected.
