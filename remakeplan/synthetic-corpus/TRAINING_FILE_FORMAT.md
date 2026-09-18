# What the Actual Training Dataset Looks Like

The labeling record (with `context`, `notes`, `id`) is NOT what the model trains on. It is the human-authored source. A build step compiles it into the real training file. This document shows the exact bytes that go into training, and the transform.

Sample files you can open:
- `samples/northbengal-sft-chat.jsonl` — chat format for Gemma / Sarvam LoRA (TRL, axolotl, unsloth)
- `samples/northbengal-sft-gemini.jsonl` — Vertex AI Gemini supervised tuning format
- `samples/northbengal-dpo.jsonl` — preference pairs, if we do DPO

---

## The transform: labeling record → training example

The `context` block does not stay a JSON field. It is **rendered into the system prompt as text**, because at inference the app injects that same rendered context from the locale pack. Train and serve must see identical structure. `notes` and `id` are labeling metadata and are dropped.

Labeling record (what a human fills in):

```json
{
  "id": "northbengal-math-0001",
  "context": { "board":"WBBSE","grade":5,"subject":"Mathematics","medium":"Bengali",
    "district":"Jalpaiguri","setting":"rural","classroom":"multi_grade",
    "infra":["no_projector","shared_textbook"],"livelihood":["tea_garden"],
    "local_facts":{"tea_garden_daily_wage":240,"currency":"INR"},
    "local_examples":["tea leaves","plucking basket"],
    "student_names":["Rina","Bishal","Sujan","Anjali"] },
  "task_type": "worksheet",
  "prompt": "ক্লাস ৫ এর জন্য ভগ্নাংশের একটা ওয়ার্কশিট বানিয়ে দাও, ৫টা প্রশ্ন।",
  "ideal_response": "ভগ্নাংশ - অনুশীলন (শ্রেণি ৫) ...",
  "notes": "Rs 240 from local_facts, not invented. No register tag (written task)."
}
```

Training example (what the model sees), chat format:

```json
{"messages":[
  {"role":"system","content":"You are SahayakAI ... Use ONLY the facts given in the CONTEXT ...\n\nCONTEXT\nboard: WBBSE | grade: 5 | subject: Mathematics | medium: Bengali\ndistrict: Jalpaiguri | setting: rural | classroom: multi_grade\ninfra: no_projector, shared_textbook\nlivelihood: tea_garden\nlocal_facts: tea_garden_daily_wage=240 INR\nlocal_examples: tea leaves, plucking basket\nstudent_names: Rina, Bishal, Sujan, Anjali"},
  {"role":"user","content":"ক্লাস ৫ এর জন্য ভগ্নাংশের একটা ওয়ার্কশিট বানিয়ে দাও, ৫টা প্রশ্ন।"},
  {"role":"assistant","content":"ভগ্নাংশ - অনুশীলন (শ্রেণি ৫) ..."}
]}
```

Three turns: **system** carries the rendered context and the rules, **user** is the teacher's real prompt, **assistant** is the teacher-approved gold answer. That is the whole record.

---

## Format 1 — Chat (Gemma / Sarvam / any open-weights LoRA)

One JSON object per line. `messages` array, roles `system` / `user` / `assistant`. This is the format TRL, axolotl, and unsloth expect.

See `samples/northbengal-sft-chat.jsonl` for three real, fully rendered examples (fractions worksheet, parent-call script, EVS Q&A).

## Format 2 — Gemini supervised tuning (Vertex AI)

Same content, different envelope. `systemInstruction` plus a `contents` array with roles `user` / `model` (note: `model`, not `assistant`), each turn a `parts:[{text}]`.

See `samples/northbengal-sft-gemini.jsonl`.

## Format 3 — DPO preference pairs (only if the model choice supports it)

`prompt`, `chosen`, `rejected`. `chosen` is the teacher-edited answer, `rejected` is the original model draft (typically the generic-examples version). This teaches preference directly.

See `samples/northbengal-dpo.jsonl`. Notice the rejected answer uses apples and pizza; the chosen uses tea leaves and the real Rs 240 wage. That contrast is the training signal.

---

## Why render context into the prompt instead of keeping it as a field

Because the app must build the identical structure at inference time. When a real teacher in Jalpaiguri asks for a worksheet, the app looks up the North Bengal locale pack, renders the same CONTEXT block into the system prompt, and sends the teacher's request. The model was trained on exactly that shape, so it behaves. If we trained on raw JSON fields the model never sees in production, train and serve would diverge and the localness would not transfer.

This is also why facts live in the context block, not the weights: change the wage in the locale pack next season, and every future answer updates, no retrain.

---

## Field-by-field rendering rules (for the build script)

The build step (`scripts/build_training_file.py`, to be written) applies these:

| Labeling field | Where it goes in the training example |
|---|---|
| `context.*` | Rendered as the CONTEXT text block inside the system message |
| `context.register` | Included in CONTEXT only for spoken task types; omitted otherwise |
| `prompt` | user message content, verbatim |
| `ideal_response` | assistant / model message content, verbatim |
| `id`, `notes`, `task_type` | dropped (metadata only; `task_type` may be kept in a sidecar for split balancing) |

Rules the build step enforces before writing a line:
1. Every number and name in `ideal_response` must appear in the rendered CONTEXT. Fail otherwise (anti-fact-baking).
2. No real PII. Only `student_names` from the pack.
3. Deterministic rendering, so the same locale pack always produces the same CONTEXT text at train and at serve.

---

## Volume and shape target (North Bengal)

- 2k-4k SFT lines, spread across grade x subject x task_type.
- Same three-turn shape every line. Only CONTEXT, prompt, and answer vary.
- 90/10 train/eval split, benchmark held out entirely.
- If DPO: a few hundred to low thousands of preference pairs, harvested as the by-product of the teacher-edit loop (original draft = rejected, edited = chosen).
