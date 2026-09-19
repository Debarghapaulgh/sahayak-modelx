# FINAL GENERATION & GROUNDING SPECIFICATION
# REQUEST-FIRST + CURRICULUM-GROUNDED + LOCALE-GROUNDED

This specification defines the master architectural standards for all future SahayakAI dataset generation, fine-tuning, and model evaluation.

---

## 1. Core Architecture Flow
```
                                 [ USER REQUEST ]
                                        │
                                        ▼
                             [ INTENT / TASK DETECTION ]
                                        │
                                        ▼
                        [ CURRICULUM TARGET RESOLUTION ]
           (Board Authority → Class → Subject → Textbook → Chapter → Topic)
                                        │
                                        ▼
                            [ TEXTBOOK RETRIEVAL ]
                     (BM25 Lexical + Multi-Chunk Synthesis)
                                        │
                                        ▼
                      [ LOCALE / LOCAL-CONTEXT RETRIEVAL ]
                        (locale.json Verified Facts Only)
                                        │
                                        ▼
                        [ GROUNDING COMPATIBILITY GATE ]
                 (Curriculum Fidelity 0-5 + Authority Alignment)
                                        │
                                        ▼
                                  [ GENERATION ]
                   (Hidden Internal Grounding + Dual-Layer Register)
                                        │
                                        ▼
                      [ 8-STAGE DETERMINISTIC VALIDATION ]
                  (Schema, Task Fidelity, Numerals, Factuality)
                                        │
                                        ▼
                   [ DIMENSION-WISE PEDAGOGICAL AUDIT ]
                                        │
                                        ▼
                                 [ FINAL RESPONSE ]
```

---

## 2. The 25 Master Architectural Principles

### 1. Request-First Paradigm
The user's educational request is the primary starting condition. The system must never select a random textbook chunk and force a synthetic user question around it.

### 2. Authority Resolution Hierarchy
* **WBBPE:** Primary & Pre-Primary to Class 5 (পশ্চিমবঙ্গ প্রাথমিক শিক্ষা পর্ষদ)
* **WBBSE:** Classes 6 to 10 (পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ)
* **WBCHSE:** Classes 11 to 12 (পশ্চিমবঙ্গ উচ্চমাধ্যমিক শিক্ষা সংসদ)
* Zero cross-authority relabeling.

### 3. Textbook Retrieval Precision
Retrieves the minimal coherent set of verified textbook chunks from `wbbse_sft_source_pool.jsonl`. Supports contiguous multi-chunk aggregation for 40-minute lesson plans and multi-step concept explanations.

### 4. Locale File as a First-Class Retrieval Source (`locale.json`)
The locale file provides verified regional facts, district statistics, weather norms, agricultural parameters, local units (বিঘা, কাঠা, ছটাক), and socio-cultural markers.

### 5. Grounding Priority Hierarchy
$$\mathbf{Curriculum / Textbook} > \mathbf{Verified Local Context (locale.json)} > \mathbf{General Knowledge}$$

### 6. Relevant Localization (Anti-Forced Localization)
Never insert tea gardens or rural imagery into generic math or science questions just to sound regional. If local context is not requested or pedagogically necessary, use **zero** local context.

### 7. Absolute Prohibition on Invented Local Facts
Never fabricate local population numbers, crop yields, wages, or prices. If a regional statistic is needed but absent from `locale.json`, present it strictly as a clearly labelled hypothetical (*"ধরা যাক, একটি কাল্পনিক চা-বাগানে..."*).

### 8. Locale Relevance Test
Before applying local facts, verify:
1. Is local context requested or directly beneficial?
2. Is the claim verified in `locale.json`?
3. Does it preserve the grade-level academic concept?

### 9. Teacher-First Product Model (Dual-Role Decoupling)
$$\begin{aligned}
\text{Requester Role: } & \mathbf{TEACHER \text{ (~85\%)}} \quad \text{vs} \quad \mathbf{STUDENT \text{ (~15\%)}} \\
\text{Instructional Target: } & \mathbf{STUDENT \text{ (~75\%)}} \quad \text{vs} \quad \mathbf{TEACHER \text{ (~20\%)}} \quad \text{vs} \quad \mathbf{BOTH \text{ (~5\%)}}
\end{aligned}$$

### 10. Dual-Layer Response Register
* When a Teacher requests student-facing materials: Address the teacher respectfully with **'আপনি'** while embedding student-friendly **'তুমি/তোমরা'** delivery scripts for classroom use.
* Teacher $\rightarrow$ Teacher tasks use formal pedagogical register.
* Student $\rightarrow$ Student tasks use friendly tutoring register.

### 11. Conversational Format & Hidden Internal Grounding
* User messages must contain natural requests with **zero** `পাঠ্যাংশ:` or raw OCR dumps.
* Textbook and locale contexts are injected internally during generation and tracked in external provenance logs.

### 12. Exception: User-Provided Source Tasks
When the user explicitly provides a passage (*"এই অনুচ্ছেদটি পড়ে..."*), it is preserved in the user message under task type `USER_PROVIDED_SOURCE`.

### 13. Grounding Compatibility Gate
Rejects mismatches across User Request $\leftrightarrow$ Curriculum $\leftrightarrow$ Textbook $\leftrightarrow$ Locale. Never force an answer from a mismatched chunk.

### 14. Curriculum Fidelity Score (0 to 5)
* **0:** Completely unrelated
* **1:** Same subject, wrong topic
* **2:** Related topic with substantial unsupported content
* **3:** Correct topic, reasonable alignment
* **4:** Strong chapter/topic alignment
* **5:** Directly grounded in textbook content and learning objectives
*(Scores 0 or 1 trigger automatic rejection).*

### 15. Answer-to-Prompt Contract Checklist
* [x] Correct Board Authority
* [x] Correct Class, Subject, Textbook & Chapter
* [x] Exact Task Fidelity (Lesson Plan / Problem Solving / Concept)
* [x] Bangla numerals (০, ১, ২...) in Bengali prose
* [x] Verified Locale Facts (when applicable)
* [x] Zero invented textbook or local claims

### 16. 8-Stage Validation Order
$$\text{Schema} \longrightarrow \text{Curriculum Consistency} \longrightarrow \text{Retrieval Relevance} \longrightarrow \text{Locale Relevance} \longrightarrow \text{Groundedness} \longrightarrow \text{Task Execution} \longrightarrow \text{Pedagogical Quality} \longrightarrow \text{LLM Judge}$$

### 17. Dimension-Wise Scoring Matrix
Every record is audited across 8 quantitative dimensions:
```json
{
  "topic_alignment": 0-5,
  "curriculum_alignment": 0-5,
  "local_context_groundedness": 0-5,
  "factual_correctness": 0-5,
  "instruction_following": 0-5,
  "pedagogical_quality": 0-5,
  "hallucination_risk": 0-5,
  "overall": 0-5
}
```

### 18. Hard Negatives Diagnostic Suite
Maintain test cases with deliberately mismatched topics, incorrect boards, and unverified local claims to continuously benchmark the compatibility gate.

### 19. Mathematics & Science Rigor
Computational correctness, step-by-step arithmetic, scientific notation ($H_2O, CO_2$), and unit preservation are strictly enforced.

### 20. Historical & Interpretive Fidelity
Historical claims must adhere to textbook framing without introducing unsupported interpretations.

### 21. Curriculum & Locale Harmonization
When localized pedagogy is used, the local setting illustrates the academic concept without modifying or distorting the underlying syllabus.

### 22. Full Provenance Tracking
Internal metadata tracks:
```json
{
  "curriculum": {
    "board": "...", "grade": "...", "subject": "...", "textbook": "...", "chapter": "...", "topic": "..."
  },
  "curriculum_fidelity_score": 5,
  "textbook_source_chunks": ["..."],
  "locale_source_chunks": ["..."],
  "requester_role": "TEACHER",
  "instructional_target": "STUDENT",
  "task_type": "CONCEPT_EXPLANATION"
}
```

### 23. Top 5 Engineering Priorities
1. Request-First Topic Retrieval
2. Strict Curriculum Compatibility Gate
3. Verified Locale-File Retrieval (`locale.json`)
4. Hard Rejection of Unsupported Local/Textbook Claims
5. Dimension-Wise Multi-Stage Validation

---
*Codified and Enforced for all future SahayakAI pipelines.*
