# FUTURE BATCH GENERATION SPECIFICATION: GROUNDING-FIRST SFT PIPELINE

## 1. Core Mandate & Status
* **Existing Dataset Status:** The existing 600-record corpus (Batch 1 & Batch 2) is officially **frozen** as a pilot benchmark.
* **Generation Freeze:** **Zero new SFT batches** will be generated until this request-first retrieval architecture and compatibility gate system are fully implemented and verified.

---

## 2. Fundamental Architectural Shift

### ❌ Previous Architecture (Source-First Generation — DEPRECATED):
```
Textbook Chunk → Generate Arbitrary User Question → Hope Question Matches Source
```
*(Flaw: Risk of topic mismatch, forced relevance, and unnatural synthetic queries).*

### ✅ New Architecture (Request-First Retrieval — MANDATORY):
```
USER INTENT / EDUCATIONAL TASK
        ↓
SUBJECT / GRADE / TOPIC / TASK DETECTION
        ↓
TEXTBOOK RETRIEVAL (Targeted Knowledge Lookup)
        ↓
GROUNDING COMPATIBILITY GATE (Strict Alignment Check)
        ↓
GENERATION (Textbook-Grounded Tutoring)
        ↓
SOURCE / FACTUAL / TASK VALIDATION (Multi-Tier Validation)
        ↓
ACCEPT OR REJECT (Track Retrieval Failures)
```

---

## 3. The 20 Grounding-First Architecture Rules

### 1. User Request is the Primary Condition
The natural user prompt is authoritative. It dictates the subject, grade level, topic, educational intent, and persona (student vs. teacher). Retrieval must be guided strictly by what the user is asking.

### 2. Grounding Compatibility Gate
After retrieving textbook chunks, verify strict semantic, curriculum, and topical alignment:
* If User asks: *"ক্রিয়ার কাল"* but Retriever finds *"কর্মধারয় সমাস"* $\rightarrow$ **REJECT RETRIEVAL**.
* Never force-fit an answer from a mismatched source. Re-retrieve or route to general-knowledge fallback.

### 3. Never Force the Source to Fit the User
* Do **NOT** rewrite user queries to match an irrelevant chunk.
* Do **NOT** answer topic Y when the user asked about topic X.
* Do **NOT** assume proximity in the same textbook implies relevance.

### 4. Source Context is Strictly Internal
* The textbook OCR text must **NEVER** be dumped into the simulated user's prompt.
* Prompt format: `SYSTEM PROMPT` + `NATURAL USER REQUEST` + `ASSISTANT RESPONSE`.
* Grounding metadata (chunk IDs, page numbers, book IDs) are tracked externally in provenance logs.

### 5. Exception: User-Provided Source Tasks
When the educational task explicitly requires user-provided context (e.g., *"এই অনুচ্ছেদটি পড়ে মূল বক্তব্য বুঝিয়ে দাও: [passage]"*), the passage belongs in the user message under task type `USER_PROVIDED_SOURCE`.

### 6. Source Selection Validation Gate
Before generation, automatically reject chunks containing:
* Administrative debris (publisher details, ISBN, committee lists, copyright notices).
* OCR fragments or unreadable page headers.
* Curriculum or authority mismatches.
* Insufficient content to answer the requested prompt.

### 7. Multi-Chunk Retrieval
Support aggregating 1 to $N$ adjacent/relevant chunks when required for:
* Lesson plans (40-minute pedagogy).
* Comprehensive chapter summaries.
* Multi-step concept comparisons.
*(Keep retrieval minimal and focused; avoid dumping whole books).*

### 8. Lesson-Plan Retrieval Rigor
For lesson plans, retrieve sufficient coherent curriculum material to construct realistic objectives, teaching steps, pedagogical activities, and blackboard work.

### 9. Quiz Retrieval Rigor
Generate quiz questions strictly from retrieved topic content. Never mix historical board exam papers into textbook-only chapter quizzes.

### 10. Misconception-Correction Retrieval
When a student brings a misconception, retrieve the specific scientific/grammatical fact to ground the correction accurately.

### 11. General-Knowledge Fallback (`source_mode = NOT_PROVIDED`)
If a legitimate academic question has no matching textbook chunk in the corpus:
* Fall back to general knowledge if permitted.
* **NEVER** fabricate textbook quotes or say *"প্রদত্ত পাঠ্য অনুযায়ী..."*.

### 12. Visual Dependency Detection
If an answer requires a diagram, chart, graph, map, or illustration:
* Retrieve the image and incorporate its verified OCR/description, OR
* Route to a non-visual task.
* Never generate questions relying on missing visual assets.

### 13. Hard Self-Containedness
Zero tolerance for references to missing context (e.g., *"উপরের ছবিতে যেমন দেখলে"*, *"পূর্ববর্তী পৃষ্ঠার ছকটি"*).

### 14. Multi-Domain Factual Validation
* **Mathematics:** Exact computational and formula verification.
* **Science:** Physical laws, chemical equations, units, notation integrity ($H_2O$, $CO_2$).
* **History/Geography:** Source-grounded historical dates, facts, and geographical features.
* **Language/Grammar:** Accurate rules, terminology, and complete prose.

### 15. Task-Fidelity Validation
Ensure exact alignment between task request and generated output (e.g., request for quiz $\rightarrow$ quiz output; request for lesson plan $\rightarrow$ lesson plan output).

### 16. Metadata Subordination
Curriculum metadata guides retrieval but cannot override the user's explicit question.

### 17. Retrieval Failure Tracking
Track `retrieval_failures` as a primary quality metric in audit reports alongside generation failures.

### 18. Zero-Tolerance Failure Conditions
Automatic rejection for:
1. User query / Source mismatch ($X \leftrightarrow Y$).
2. Administrative/OCR debris in source.
3. Assistant answering mismatched topic.
4. Factual / Mathematical / Scientific error.
5. Incomplete prompt leading to assistant guessing.
6. Hallucinated textbook attribution.
7. Unresolved visual dependencies.

### 19. Corpus-Level Operating Principle
```
Textbook Corpus (Knowledge Base)
       +
User Request (Educational Intent)
       ↓
Retriever (Relevant Knowledge Discovery)
       ↓
LLM (Pedagogical Response Generation)
       ↓
Validator (Source Fidelity & Correctness)
```

### 20. Strict Execution Policy
All future SFT generation scripts must implement this architecture from day one.

---

## 4. Audience & Dual-Role Model (Teacher-Centric Paradigm)

SahayakAI is primarily a **teacher/educator-facing assistant**. The dataset decouples the person asking the question from the intended recipient of the educational content.

### A. Independent Metadata Dimensions
1. 
equester_role:
   * **TEACHER (~85%):** Default persona. Teachers requesting lesson plans, teaching strategies, worksheets, quizzes, or classroom explanations to deliver to students.
   * **STUDENT (~15%):** Direct student requests for homework help, concept clarification, or problem solving.
2. instructional_target:
   * **STUDENT (~75%):** Educational content crafted for student comprehension.
   * **TEACHER (~20%):** Pedagogical design, lesson plans, assessment rubrics, TLM strategies.
   * **BOTH (~5%):** Shared activities, classroom discussions.

### B. Dual-Layer Response Register
* When 
equester_role = TEACHER and instructional_target = STUDENT:
  * Address the teacher respectfully using **'আপনি'** (e.g., *'আপনি ক্লাসে শিক্ষার্থীদের এভাবে বিষয়টি বুঝিয়ে বলতে পারেন...'*)
  * Provide the embedded classroom delivery script using student-friendly language and **'তুমি/তোমরা'**.
* When 
equester_role = TEACHER and instructional_target = TEACHER:
  * Use purely professional pedagogical register (**'আপনি'**).
* When 
equester_role = STUDENT and instructional_target = STUDENT:
  * Direct friendly tutoring register (**'তুমি/তোমরা'**).
