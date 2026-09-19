# SAHAYAKAI SFT QUIZ GENERATION PIPELINE SPECIFICATION
# TOPIC-LOCKED + BLUEPRINT-GROUNDED + DETERMINISTIC VALIDATION ARCHITECTURE

This specification governs the generation and validation of all `QUIZ_GENERATION` training samples in the SahayakAI SFT dataset.

---

## 1. CORE PURPOSE & DIAGNOSTIC LESSONS

The comparative evaluation between the live product and SFT baselines demonstrated:
1. **The Primary Failure Mode in Untrained / Live Systems is Topic Misalignment**: Generating fluent, high-quality Bengali questions on the wrong topic (e.g., asked for *Percentages*, gave *Squares/Cubes*; asked for *Double-Bar Graphs*, gave *Large Numbers*; asked for *Recurring Decimals*, gave *Patterns/Sequences*).
2. **SFT Dataset Mandate**: The SFT dataset must exemplify **strict topic fidelity, deterministic mark structure, pedagogical diversity, and proper answer key separation**.

---

## 2. PRIORITY HIERARCHY

All SFT generation algorithms and validation gates MUST enforce quality in this strict order:
```text
Priority 1 -> Exact Topic & Curriculum Lock (Hard Gate: PASS/FAIL)
Priority 2 -> Topic-Constrained Textbook Retrieval (Hierarchy: Board -> Class -> Subject -> Chapter/Topic)
Priority 3 -> Deterministic Quiz Blueprint & Mark Allocation (Sum(marks) == Requested Marks)
Priority 4 -> Question-Level Topic & Relevance Validation (Every question must directly test target topic)
Priority 5 -> Answer Correctness & Independent Mathematical/Factual Verification
Priority 6 -> Audience & Response Mode Decoupling (Student Quiz vs Teacher with Answer Key)
Priority 7 -> Question Diversity (Cognitive levels: Recall, Calculation, Application, Analysis)
Priority 8 -> Monolingual Bengali Grammar, Terminology & Script Integrity
```

---

## 3. MASTER GENERATION PIPELINE

```text
USER REQUEST
      |
INTENT / TASK DETECTION (QUIZ_GENERATION)
      |
AUDIENCE RESOLUTION (Student vs Teacher with Answer Key)
      |
CURRICULUM HIERARCHY RESOLUTION (Board, Class, Subject, Chapter, Topic)
      |
TOPIC SCOPE LOCK & VALIDATION (VERIFIED / AMBIGUOUS / NOT_FOUND)
      |
TOPIC-CONSTRAINED TEXTBOOK RETRIEVAL
      |
QUIZ BLUEPRINT GENERATION (Total Marks, Question Slots, Cognitive Mix)
      |
SLOT-BY-SLOT QUESTION GENERATION
      |
QUESTION-LEVEL TOPIC VALIDATOR
      |
ANSWER KEY & MARKING SCHEME GENERATION (Separated from Quiz Body)
      |
DETERMINISTIC QUIZ-LEVEL VALIDATION (Marks, Count, Duplicate Check, Hard Negatives)
      |
FINAL SFT GROUNDED SAMPLE
```

---

## 4. TOPIC RESOLUTION & SCOPE LOCK

Before retrieval or generation, the user topic must be normalized and verified:
- Board: WBBSE / WBBPE / WBCHSE
- Class / Grade
- Subject
- Canonical Chapter & Topic Name
- Status: `VERIFIED` / `AMBIGUOUS` / `NOT_FOUND`

*Rule*: If status is not `VERIFIED`, generation is aborted / routed to review.

---

## 5. TOPIC-CONSTRAINED RETRIEVAL

Retrieval MUST NEVER use global semantic similarity alone. Retrieval MUST be hierarchical:
1. Exact Board, Class, Subject match
2. Exact Chapter/Topic boundary
3. Intra-chapter chunk ranking

---

## 6. QUIZ BLUEPRINT SPECIFICATION

Before generating questions, the pipeline constructs a structured blueprint with question slots, marks each, cognitive skills, and target concepts.

---

## 7. QUESTION-LEVEL TOPIC VALIDATOR & HARD NEGATIVES

Each generated question must pass independent topic verification:
- **Directly Relevant**: Question explicitly evaluates target topic operations or concepts.
- **Weakly Related**: General arithmetic prerequisite without topic context -> REJECT.
- **Unrelated / Off-Topic (Hard Negative)**: Immediately REJECT and regenerate.

### Hard Negative Rejection Benchmarks:
1. Target: `??????? ??: ?????? ????? ??????` (Recurring Decimals) -> REJECT `????????? ? ????` (Patterns/Sequences).
2. Target: `??????? ??: ????-?????? ???` (Double Bar Graphs) -> REJECT `???? ?????? ? ???????? ???` (Large Numbers).
3. Target: `??????? ??: ?????` (Percentage) -> REJECT `??????????? ? ???` (Squares and Cubes).

---

## 8. RESPONSE FORMATTING: STUDENT VS TEACHER MODE

### Mode A: `STUDENT_QUIZ`
Clean questions only without answers embedded.

### Mode B: `TEACHER_WITH_ANSWER_KEY`
Structured into two distinct blocks separated by a markdown divider (`---`):
1. **???? ??????????**
2. **????? ?????????? ? ????? ?????? (Answer Key & Marking Scheme)**

---

## 9. VALIDATION GATE ORDER & DETERMINISTIC RULES

1. `Schema & JSON Structure Validation`
2. `Class, Subject, Topic Hierarchy Match`
3. `Topic Scope Lock == PASS`
4. `Sum(Question Marks) == Blueprint Total Marks`
5. `Question-Level Relevance >= 0.90`
6. `No Duplicate or Near-Duplicate Questions`
7. `Mathematical & Factual Correctness == 100%`
8. `Audience Mode Compliance (Answer Separation Check)`
9. `Monolingual Bengali Grammar & Terminology Check`
