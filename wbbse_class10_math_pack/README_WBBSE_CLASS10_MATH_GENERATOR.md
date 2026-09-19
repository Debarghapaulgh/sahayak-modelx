# WBBSE Class 10 Mathematics (Ganit Prakash Class X) SFT Dataset Generator Pack

This package contains the complete, grounded, multi-threaded synthetic dataset generation and verification suite for **WBBSE Class 10 Mathematics (`Ganit Prakash Class X` / গণিত প্রকাশ - দশম শ্রেণি)**.

---

## 📌 Target Curriculum & Syllabus Verification (2025–2026)

- **Board**: West Bengal Board of Secondary Education (WBBSE - মাধ্যমিক)
- **Grade/Class**: Class 10 (দশম শ্রেণি)
- **Subject**: Mathematics (গণিত)
- **Textbook**: *Ganit Prakash Class X (গণিত প্রকাশ - দশম শ্রেণি)* (Official WBBSE Madhyamik Textbook)
- **Syllabus Year**: 2025–2026 (Verified 100% Full Syllabus - 26 Core Chapters)
- **Grounded Chunks**: 808 clean, deduplicated textbook passages in `wbbse_class10_math_grounding_chunks.json`.

---

## 📁 Pack Contents

```
wbbse_class10_math_pack/
├── README_WBBSE_CLASS10_MATH_GENERATOR.md   # Setup & execution instructions
├── wbbse_class10_math_config.yaml           # WBBSE Class 10 Math topic & preamble config
├── wbbse_class10_math_grounding_chunks.json # 808 clean grounded textbook chunks
├── generate_wbbse_class10_math_sft.py       # High-throughput parallel LLM generator
└── clean_and_verify_wbbse_math.py           # Deduplication, digit normalization & verifier
```

---

## 🚀 How to Run

### Step 1: Install Prerequisites
Ensure Python 3.9+ is installed. No complex third-party dependencies are required (built using standard Python libraries: `json`, `urllib`, `concurrent.futures`, `argparse`).

### Step 2: Set API Key (Required)
The generator reads keys only from the environment or `--key`. There is no built-in key pool, and keys must never be committed to this repository:

```bash
# Option A: Pass via environment variable
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Option B: Pass via command-line argument
python generate_wbbse_class10_math_sft.py --key "sk-or-v1-your-key-here"
```

### Step 3: Run the Generator
To generate 1,000 clean SFT records (or adjust `--target` to 2,000):

```bash
python generate_wbbse_class10_math_sft.py --target 1000 --workers 8
```

- `--target`: Number of records to generate (e.g. 1000 or 2000).
- `--workers`: Number of parallel worker threads (default: 8).

### Step 4: Run Post-Processing & Verification
Once generation finishes, run the verifier script to deduplicate records, enforce 100% Bengali digits (`০-৯`), and generate the final cleaned dataset:

```bash
python clean_and_verify_wbbse_math.py
```

---

## 📊 Output Files

Upon execution, the pipeline creates:

1. `candidates_wbbse_class10_math.jsonl`: Raw candidate generation objects with metadata context (grade, subject, book, district, prompt, response).
2. `wbbse-class10-math-sft-chat.jsonl`: Raw multi-turn SFT chat conversation format.
3. `wbbse-class10-math-sft-chat-clean.jsonl`: Final verified, deduplicated SFT Chat dataset ready for model training/fine-tuning.

---

## 💡 System Prompt & Formatting Rules

The generator uses an authentic WBBSE Madhyamik teacher/tutor persona preamble:
- **Tone**: Respectful to teachers ('আপনি' / 'করুন') and encouraging to students ('তুমি' / 'এসো সমাধান করি').
- **Numerals**: 100% West Bengal Bengali digits (`০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯`).
- **Terminology**: Official WBBSE Bengali mathematical terms (একচলবিশিষ্ট দ্বিঘাত সমীকরণ, সরল সুদ, বৃত্তের স্পর্শক, পরিমিতি, ত্রিকোণমিতি, রাশিবিজ্ঞান).
