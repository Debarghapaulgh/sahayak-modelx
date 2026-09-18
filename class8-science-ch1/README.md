# Synthetic Student-Answer Corpus — Class 8 Science, Ch 1

**Purpose:** finetuning / eval data for SahayakAI. Same chapter, same 5 questions,
answered by 5 *deliberately different students*, each rendered in all **11 production
languages**. Teaches the model to recognise ability level, common misconceptions, and
answer-style variation — and (paired with `QUESTIONS.md` rubric) to grade and remediate.

## The 5 student personas

| # | Student | Type | Ability | Signature |
|---|---------|------|---------|-----------|
| 1 | Aarav Menon | The Topper | High | Precise, structured, exact terms, over-delivers |
| 2 | Lakshmi Barman | First-Gen Struggler | Low–Mod | Short, misspelled, merges terms, strong farm intuition |
| 3 | Rehan Qureshi | Curious Lateral Thinker | Average | Verbose, example-driven, "why?", some tangents |
| 4 | Meera Iyer | Rote Memoriser (anxious) | Mod–High | Verbatim textbook; breaks on application/HOTS |
| 5 | Karthik Reddy | Distracted Bright Kid | High/low-effort | One-liners, careless, occasional flash of insight |

Full cards in each `persona-*/PERSONA.md`.

## Languages (canon from `src/types/index.ts`)
English, Hindi, Kannada, Tamil, Telugu, Marathi, Bengali, Gujarati, Punjabi, Malayalam, Odia.

## Layout
```
class8-science-ch1/
  QUESTIONS.md            5 questions + ideal answer key (rubric)
  persona-1-aarav-topper/
    PERSONA.md            the student card
    answers.md            human-readable: 5 Q × 11 languages
    answers.jsonl         machine-ready: {persona, ability, q_id, language, answer}
  persona-2-lakshmi-firstgen/  ...
  ... (5 folders)
```

## Design rule (critical for label quality)
The **error character is preserved across languages** — a struggler's Malayalam answer
reads like a weak 13-yr-old wrote it (simple, colloquial, term-confusion), a topper's
Tamil is precise and rich. Translations reproduce *language-native equivalent* mistakes,
they do NOT literal-translate English typos, and they NEVER upgrade a weak answer into
correct textbook language.

## Known limitation
Low-resource-language authenticity (esp. Odia, Malayalam register + deliberate error
modelling) needs a native / Sarvam review pass before this is used as ground-truth
finetuning data. Treat as high-quality draft, not verified gold.
