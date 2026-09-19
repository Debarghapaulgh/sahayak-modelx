# SAHAYAKAI SFT PART 1: STRUCTURED-JSON SPECIFICATION
# NATIVE STRUCTURED JSON TARGET ARCHITECTURE

This specification governs the production of the 1,500-record Structured-JSON SFT training corpus (`datasets/textbook_sft_part1/`).

---

## 1. OBJECTIVE & MATRIX ALLOCATION

The assistant's target response is native structured JSON, decoupled from internal provenance metadata.

### Cross-Matrix Allocation (1,500 Records):
| Stage | Grades | Q/A | Lesson Plans | Quizzes | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Primary** | Classes I–V | 240 | 105 | 105 | **450** |
| **Upper Primary** | Classes VI–VIII | 240 | 105 | 105 | **450** |
| **Secondary** | Classes IX–X | 200 | 85 | 90 | **375** |
| **Higher Secondary** | Classes XI–XII | 120 | 55 | 50 | **225** |
| **Total** | | **800** | **350** | **350** | **1,500** |

---

## 2. DUAL-LAYER SEPARATION

1. **Internal Dataset Layer**:
   - `id`, `task_type`, `requester_role`, `instructional_target`
   - `curriculum`: `board`, `stage`, `class`, `subject`, `textbook`, `chapter`, `topic`, `learning_outcomes`, `academic_session`, `syllabus_version`, `assessment_period`, `semester`
   - `source`: `source_mode`, `textbook_source_chunks`, `visual_dependency`
   - `local_context`: `mode`, `region`, `district`, `verified_local_facts`
   - `validation`: `schema`, `curriculum_alignment`, `topic_alignment`, `source_groundedness`, `local_groundedness`, `factual_correctness`, `instruction_following`, `grade_appropriateness`

2. **Model-Visible Layer**:
   ```json
   {
     "messages": [
       { "role": "user", "content": "<natural prompt without metadata>" },
       { "role": "assistant", "content": { ...structured JSON object... } }
     ]
   }
   ```

---

## 3. TASK-SPECIFIC STRUCTURED JSON SCHEMAS

### A. Question / Answer (`type: "qa"`)
```json
{
  "type": "qa",
  "answer": "বিশুদ্ধ আবৃত্ত দশমিককে সামান্য ভগ্নাংশে রূপান্তর করার নিয়ম...",
  "examples": [
    {
      "example": "০.৫৭৫৭৫৭... (০.৫̇৭̇)",
      "explanation": "লবে ৫৭ এবং হরে দুটি ৯ অর্থাৎ ৯৯ বসে লঘিষ্ঠ রূপ ১৯/৩৩।"
    }
  ],
  "practice": [
    {
      "question": "০.৩̇-কে সামান্য ভগ্নাংশে রূপান্তর করো।",
      "answer": "১/৩"
    }
  ]
}
```

### B. Lesson Plan (`type: "lesson_plan"`)
```json
{
  "type": "lesson_plan",
  "title": "দ্বি-স্তম্ভ লেখ পাঠপরিকল্পনা",
  "learning_objectives": [
    "দ্বি-স্তম্ভ লেখের উপযোগিতা ব্যাখ্যা করতে পারবে",
    "গ্রাফ কাগজে সঠিক স্কেল নির্বাচন করে তথ্য উপস্থাপন করতে পারবে"
  ],
  "duration_minutes": 40,
  "prerequisites": ["একক স্তম্ভলেখের মৌলিক ধারণা"],
  "materials": ["গ্রাফ পেপার", "স্কেল", "পেন্সিল", "রঙিন চক"],
  "introduction": "দৈনন্দিন জীবনে দুটি দলের তথ্যের তুলনার প্রয়োজনীয়তা আলোচনা (৫ মিনিট)।",
  "teaching_sequence": [
    {
      "step": 1,
      "teacher_activity": "বোর্ডে এক্স ও ওয়াই অক্ষ টেনে স্কেল নির্বাচন প্রদর্শন।",
      "student_activity": "গ্রাফ কাগজে অক্ষ চিহ্নিতকরণ ও স্কেল গণনা।",
      "duration_minutes": 15
    },
    {
      "step": 2,
      "teacher_activity": "জোড়া স্তম্ভের সমান প্রস্থ ও ব্যবধান বজায় রাখার নিয়ম নির্দেশ।",
      "student_activity": "প্রদত্ত তথ্যের দ্বি-স্তম্ভ লেখ অঙ্কন অনুশীলন।",
      "duration_minutes": 12
    }
  ],
  "practice_activity": "জোড়ায় জোড়ায় পছন্দের ফলের তালিকার দ্বি-স্তম্ভ লেখ তৈরি।",
  "assessment": {
    "questions": [
      "দ্বি-স্তম্ভ লেখের দুটি স্তম্ভের মধ্যবর্তী দূরত্ব কেমন হবে?",
      "উল্লম্ব অক্ষে ১ একক সমান কী ধরা হয়েছে?"
    ]
  },
  "recap": "স্কেল ও স্তম্ভের দূরত্বের প্রধান নিয়মাবলি পুনরাবৃত্তি (৫ মিনিট)।",
  "homework": "কষে দেখি ১৬-এর ৩ নম্বর সমস্যা সমাধান করা।"
}
```

### C. Quiz Generation (`type: "quiz"`)
```json
{
  "type": "quiz",
  "title": "অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ কুইজ",
  "instructions": "সমস্ত প্রশ্নের উত্তর দাও। প্রতিটি প্রশ্নের মান ডানপাশে দেওয়া আছে।",
  "total_marks": 15,
  "questions": [
    {
      "id": 1,
      "question_type": "SHORT_ANSWER",
      "question": "দ্বি-স্তম্ভ লেখ কাকে বলে? এর প্রধান উপযোগিতা কী?",
      "marks": 3
    },
    {
      "id": 2,
      "question_type": "SHORT_ANSWER",
      "question": "দ্বি-স্তম্ভ লেখ অঙ্কনের সময় অক্ষ ও স্কেল নির্বাচনের দুটি নিয়ম লেখো।",
      "marks": 3
    },
    {
      "id": 3,
      "question_type": "STRUCTURED",
      "question": "প্রদত্ত নম্বরের সারণি পর্যবেক্ষণ করে তুলনামূলক প্রশ্নের উত্তর দাও।",
      "marks": 6
    },
    {
      "id": 4,
      "question_type": "APPLICATION",
      "question": "দ্বি-স্তম্ভ লেখের খসড়া চিত্র অঙ্কন করো।",
      "marks": 3
    }
  ],
  "answer_key": [
    {
      "question_id": 1,
      "answer": "দুটি সম্পর্কিত তথ্যকে পাশাপাশি দুটি স্তম্ভের মাধ্যমে প্রকাশ করার লেখচিত্র। তুলনামূলক বিশ্লেষণের জন্য উপযোগী।"
    },
    {
      "question_id": 2,
      "answer": "x-অক্ষে গুণবাচক ও y-অক্ষে পরিমাণবাচক তথ্য স্থাপন এবং তথ্যের বিস্তারের ভিত্তিতে উপযুক্ত একক স্কেল ধরা।"
    },
    {
      "question_id": 3,
      "answer": "(ক) বিভাগ ক বেশি পেয়েছে (১); (খ) বিভাগ খ বিজ্ঞানে এগিয়ে (১); (গ) মোট ১৫০ (২); (ঘ) উল্লম্ব অক্ষে প্রাপ্ত নম্বর (২)।"
    },
    {
      "question_id": 4,
      "answer": "সঠিক অক্ষ নির্দেশ, উপযুক্ত স্কেল ও স্তম্ভদ্বয়ের স্পষ্ট পার্থক্য সূচক চিহ্নের ব্যবহার।"
    }
  ]
}
```

---

## 4. DETERMINISTIC VALIDATION RULES

1. `JSON Parse`: `messages[1].content` must be valid JSON object or dict.
2. `Type Verification`: `type` must be in `["qa", "lesson_plan", "quiz"]`.
3. `Quiz Marks Sum`: `sum(q.marks for q in questions) == total_marks`.
4. `Quiz Answer Key Completeness`: Every `question.id` must have a corresponding `answer_key.question_id`.
5. `Unique Question IDs`: Question IDs within a quiz must be unique.
6. `Lesson Plan Structure`: `learning_objectives`, `teaching_sequence`, `duration_minutes` must be non-empty and coherent.
7. `QA Content`: `answer` must be non-empty, and `examples`/`practice` properly structured when present.
8. `Topic Scope & Hard Negatives`: Reject off-topic answers (e.g. Percentage vs Squares/Cubes).