# FINAL DATASET CREATION — PART 1 SPECIFICATION
# TEXTBOOK-GROUNDED Q/A, LESSON PLANS AND QUIZ GENERATION

This specification governs the production of the foundational SahayakAI SFT training corpus (`datasets/textbook_sft_part1/`).

---

## 1. CORE PURPOSE & OBJECTIVE

Part 1 establishes the production-grade textbook-grounded instructional corpus for SahayakAI across three core task families:
1. **QUESTION / ANSWER (QA)**: Concept explanations, definitions, step-by-step problem solving, error correction, guided solving, comparative analysis.
2. **LESSON PLAN (LP)**: Grade-adapted pedagogical teaching sequences (I-II, III-V, VI-VIII, IX-X, XI-XII) grounded in specific textbook topics.
3. **QUIZ GENERATION (QZ)**: Blueprint-driven, topic-locked assessments with deterministic marks and decoupled answer keys for teacher/student modes.

The architecture strictly follows:
```text
USER REQUEST
    ↓
CURRICULUM TARGET RESOLUTION (Board → Stage → Class → Subject → Textbook → Chapter → Topic → Outcome)
    ↓
TEXTBOOK EVIDENCE RETRIEVAL (16,255 Approved Semantic Chunks; Visual Dependency Gate)
    ↓
OPTIONAL VERIFIED LOCALE RETRIEVAL (locale.json Evidence Layer)
    ↓
TASK-SPECIFIC GENERATION (QA / Lesson Plan / Quiz)
    ↓
DETERMINISTIC & MULTI-STAGE VALIDATION (10 Stages: Schema, Curriculum, Topic, Grounding, Local, Facts, Duplicate)
    ↓
GOLD SFT EXAMPLE
```

---

## 2. SOURCE HIERARCHY & VISUAL DEPENDENCY

1. **Approved Textbook Chunks**: Primary academic source of truth (16,255 approved chunks: 4,604 `ELIGIBLE_TEXT_ONLY`, 11,651 `ELIGIBLE_WITH_VISUAL_CONTEXT`).
2. **Visual Dependency Classification**:
   - `NONE`: Self-contained textual information.
   - `SUPPORTIVE`: Visual provides context, text remains sufficient.
   - `REQUIRED`: Fundamentally depends on diagram/map/graph/table. Never generate text-only SFT if visual is omitted.
3. **No General Knowledge Gap Filling**: If evidence is missing in the chunk, regenerate from another chunk or reject.

---

## 3. OFFICIAL CURRICULUM ARCHITECTURE & VERSIONING

### Primary Stage: WBBPE (Classes I–V)
- **Classes I–II**: Ability-based (Communication, Language Development, Basic Numeracy, Observation, Coordination). Avoid reduced secondary structures.
- **Classes III–V**: Explicit subject structure (Bengali, English, Mathematics, Environmental Studies, Health & Physical Education).

### Secondary Stage: WBBSE (Classes VI–X)
- **Classes VI–VIII**: 2026 Summative evaluation periods (1st, 2nd, 3rd Summative), structured concepts, guided solving.
- **Classes IX–X**: Summative periods + Internal Formative Evaluation (IFE), examination preparation, analytical reasoning, and misconception checking.

### Higher Secondary Stage: WBCHSE (Classes XI–XII)
- **Semester System**:
  - Class XI: Semester I & Semester II (Introduced 2024–25).
  - Class XII: Semester III & Semester IV (Introduced 2025–26).
- Semester-aware topic resolution and Council question pattern compliance.

---

## 4. DUAL-ROLE INTENT MODEL & NATURAL PROMPTS

- **Requester Role**: `TEACHER` (~85%) vs `STUDENT` (~15%).
- **Instructional Target**: `STUDENT` (~75%), `TEACHER` (~20%), `BOTH` (~5%).
- **Natural Prompts**: Zero exposure of internal metadata, chunk IDs, or artificial `পাঠ্যাংশ:` dumps.

---

## 5. TASK FAMILY SPECIFICATIONS

### Task Family A: Question / Answer (15 Subtypes)
`EXPLAIN`, `DEFINE`, `SOLVE`, `GUIDED_SOLVE`, `HINT`, `CORRECT_ERROR`, `MISCONCEPTION`, `COMPARE`, `CLASSIFY`, `SUMMARIZE`, `APPLY`, `CAUSE_EFFECT`, `TEXT_SPECIFIC`, `EXAMPLE_REQUEST`, `STEP_BY_STEP`.

### Task Family B: Lesson Plans (Grade Adapted)
Structure: Topic, Learning Outcomes, Prerequisites, Teaching Aids, Introduction, Teaching Sequence, Learner Activity, Guided Practice, Formative Assessment, Remediation, Homework. 5E format used when pedagogically natural.

### Task Family C: Quiz Generation (Blueprint-First)
- Topic Scope Lock: Hard rejection of off-topic questions (e.g. Percentage vs Squares/Cubes).
- Deterministic Marks: `sum(question_marks) == requested_marks`.
- Format: `STUDENT_QUIZ` (questions only) vs `TEACHER_WITH_ANSWER_KEY` (questions + `---` + `উত্তর নির্দেশিকা`).

---

## 6. LOCALE GROUNDING RULES

- Modes: `NONE`, `GENERIC_WB`, `REGION_LEVEL`, `DISTRICT_LEVEL`, `SCHOOL_SETTING`.
- Factual claims (wages, crops, tea yields, rainfall, population, prices) MUST be grounded in `locale.json`.
- Hypothetical local examples allowed only when explicitly hypothetical (e.g. "একটি কাল্পনিক চা-বাগানে...").

---

## 7. 10-STAGE VALIDATION PIPELINE

```text
Stage 1  → Schema & Format Validation
Stage 2  → Curriculum Consistency (Board, Class, Subject, Chapter, Topic)
Stage 3  → Topic Alignment & Scope Lock (Hard Negatives Check)
Stage 4  → Textbook Groundedness (Source chunk bounds)
Stage 5  → Task Completion & Behavioral Contract
Stage 6  → Local Context & Factual Verification
Stage 7  → Factual & Mathematical Step Verification
Stage 8  → Grade & Cognitive Level Appropriateness
Stage 9  → Exact & Semantic Deduplication
Stage 10 → Final Dimension-Wise LLM Quality Judge
```

---

## 8. DIRECTORY STRUCTURE & ARTIFACTS

```text
datasets/textbook_sft_part1/
├── qa_final.jsonl
├── lesson_plan_final.jsonl
├── quiz_final.jsonl
├── part1_review.jsonl
├── part1_excluded.jsonl
├── part1_hard_negatives.jsonl
├── curriculum_manifest.json
├── locale_manifest.json
├── part1_manifest.json
└── part1_audit.json
```