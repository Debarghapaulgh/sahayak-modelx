# Output format by task (Track 4, #22)

**Finding (live probe, 2026-09-19):** the base stamps numbered **ধাপ ১ / ধাপ ২ / ধাপ ৩** on every answer,
including quizzes and concept explanations, because the system prompt says "ধাপে ধাপে". The fix is in
the **data**: each task family has its own target format, and the corpus must show the model when
*not* to enumerate. The eval (#23) scores compliance per family.

## Register and digits (all families)
- Target is a **teacher** (lesson plan, pedagogy, worksheet for the teacher): **আপনি** register (করুন, প্রদান করছি).
- Target is a **student**: **তুমি** register (লেখো, এসো সমাধান করি, মনে রাখবে).
- **Digits:** Bengali ০–৯ throughout (WBBSE convention). Units, currency: টাকা, কিমি, বিঘা where local.
- Terminology: official WBBSE Bengali terms (একচলবিশিষ্ট দ্বিঘাত সমীকরণ, সরল সুদ, ত্রিকোণমিতি, রাশিবিজ্ঞান …).
- Never expose reasoning traces. Answer directly.

## Families and target shapes
| Family | Shape | Step numbering |
|---|---|---|
| GUIDED_PROBLEM_SOLVING (worked maths / numericals) | labelled steps: **দেওয়া আছে → ধরি → সূত্রানুসারে → সমাধান → অতএব নির্ণেয় উত্তর**; final line boxed/bold | **yes**, labelled |
| CONCEPT_EXPLANATION | 2–5 short paragraphs or plain bullets; one local example (from the ontology) with the canonical term kept | no |
| MISCONCEPTION_CORRECTION | "ভুল ধারণা → কেন ভুল → সঠিক ধারণা → একটি পরীক্ষা/উদাহরণ" as short headed lines | no |
| QUIZ_GENERATION | numbered items, each **প্রশ্ন:** one line, **উত্তর:** one line; marks in brackets if asked; answer key separable | **no** |
| WORKSHEET_PRACTICE | numbered questions only; difficulty ramp; answer key at the end under **উত্তরমালা** | no |
| LESSON_PLAN | WB template: বিষয় · শ্রেণি · অধ্যায় · শিখন লক্ষ্য · উপকরণ · সূচনা (মিঃ) · মূল পাঠ (মিঃ) · হাতে-কলমে (মিঃ) · মূল্যায়ন (মিঃ) · বাড়ির কাজ | no |
| TEACHER_PEDAGOGY | prose to the teacher (আপনি), 3–6 sentences, one concrete classroom move | no |
| STORY (FLN, Classes I–III) | 5–8 short sentences, one character, one countable object, the sum stated once, one question at the end | no |

## Examples (target shape, not full length)
- **Quiz:** `১। প্রশ্ন: গাছ কোন প্রক্রিয়ায় খাদ্য তৈরি করে?  উত্তর: সালোকসংশ্লেষ।`
- **Worked sum:** `দেওয়া আছে: ৪০০-এর ১৫%। সূত্রানুসারে: ৪০০ × ১৫ ÷ ১০০ = ৬০। অতএব নির্ণেয় উত্তর: ৬০।`
- **Concept:** `সালোকসংশ্লেষ হলো … (দুই অনুচ্ছেদ)। মালদার আমগাছের পাতায় …` (canonical term kept)
- **Story:** `মিতুর ৩টি আম ছিল। রাজু আরও ২টি দিল। ৩ + ২ = ৫। এখন মিতুর ৫টি আম। মিতু ১টি খেলে কটা থাকবে?`

## Training system prompt (loosened)
"তুমি SahayakAI, পশ্চিমবঙ্গের সরকারি স্কুলের ছাত্রছাত্রী ও শিক্ষকদের জন্য বাংলা মাধ্যমের শিক্ষা-সহায়ক।
গণনার প্রশ্নে ধাপে ধাপে দেখাও; অন্য সব ক্ষেত্রে সরাসরি, সংক্ষিপ্ত ও কাজের উপযোগী উত্তর দাও। সাধারণ তথ্যপ্রশ্নে
ধাপ নম্বর দিও না। শিক্ষককে 'আপনি', ছাত্রছাত্রীকে 'তুমি'। সব সংখ্যা বাংলা অঙ্কে।"

## Validators (deterministic; used by generation and by #23)
- `no_steps_outside_maths`: reject `ধাপ\s*[০-৯0-9]` in every family except GUIDED_PROBLEM_SOLVING.
- `quiz_shape`: QUIZ requires ≥ 1 `প্রশ্ন:` and an equal count of `উত্তর:`.
- `bengali_digits`: ≥ 95% of digit characters in ০–৯.
- `register`: teacher-target → no `তুমি/তোমরা` imperative forms; student-target → no `আপনি`.
- `no_think`: reject `<think>` anywhere.

## Corpus mix target (v1)
≥ 20% of records from non-maths families with zero step numbering; every family ≥ 5% of the set.
