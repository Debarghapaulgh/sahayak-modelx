"""
Part 1 1,500-Record Manifest Builder.
Constructs the full curriculum coverage matrix and sampling plan for the 1,500-record dataset.
"""

import os
import json
import random
from typing import Dict, Any, List

def build_part1_manifest():
    output_dir = "datasets/textbook_sft_part1"
    os.makedirs(output_dir, exist_ok=True)
    
    # Curriculum Catalog of verified topics across grades and subjects
    CURRICULUM_CATALOG = [
        # --- WBBPE Primary (Classes 1-5) ---
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 1, "subject": "General", "textbook": "সহজ পাঠ (প্রথম ভাগ)", "chapter": "প্রথম পাঠ", "topic": "বর্ণ ও শব্দ চেনা", "weight": 40},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 2, "subject": "Health and Physical Education", "textbook": "স্বাস্থ্য ও শারীরশিক্ষা", "chapter": "দেশাত্মবোধ", "topic": "কুচকাওয়াজ ও শারীরিক সমন্বয়", "weight": 40},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 3, "subject": "Mathematics", "textbook": "আমার গণিত", "chapter": "অধ্যায় ৪", "topic": "টাকা পয়সার হিসাব ও লেনদেন", "weight": 50},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 4, "subject": "Health and Physical Education", "textbook": "স্বাস্থ্য ও শারীরশিক্ষা", "chapter": "স্বাস্থ্যবিধান", "topic": "নির্মল বিদ্যালয় অভিযান", "weight": 50},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 4, "subject": "Environmental Studies", "textbook": "আমাদের পরিবেশ", "chapter": "পরিবেশ ও আকাশ", "topic": "মেঘ ও বৃষ্টিপাত", "weight": 50},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 5, "subject": "Environmental Studies", "textbook": "আমাদের পরিবেশ", "chapter": "পরিবেশ ও বনভূমি", "topic": "উদ্ভিদ ও বন্যপ্রাণী সংরক্ষণ", "weight": 60},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 5, "subject": "English", "textbook": "Butterflies", "chapter": "Lesson 3", "topic": "A Great Social Reformer (Begum Rokeya)", "weight": 50},
        {"board": "WBBPE", "stage": "PRIMARY", "grade": 5, "subject": "Mathematics", "textbook": "আমার গণিত", "chapter": "অধ্যায় ৭", "topic": "ভগ্নাংশের ধারণা ও তুলনা", "weight": 60},

        # --- WBBSE Upper Primary (Classes 6-8) ---
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 6, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১০", "topic": "আবৃত্ত দশমিক সংখ্যা", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 6, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "অধ্যায় ৩", "topic": "মৌলিক ও যৌগিক পদার্থ", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 7, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১৬", "topic": "দ্বি-স্তম্ভ লেখ", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 7, "subject": "Bengali", "textbook": "সাহিত্যমেলা", "chapter": "কবিতা", "topic": "বঙ্গভূমি প্রতি (মাইকেল মধুসূদন দত্ত)", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 7, "subject": "History", "textbook": "অতীত ও ঐতিহ্য", "chapter": "অধ্যায় ৪", "topic": "দিল্লি সুলতানি শাসন", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 8, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১১", "topic": "শতকরা", "weight": 60},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 8, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১২", "topic": "মিশ্রণ ও অনুপাত", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 8, "subject": "Bengali", "textbook": "ভাষা পাঠ", "chapter": "প্রথম অধ্যায়", "topic": "দল ও ধ্বনি পরিবর্তন (স্বরলোপ)", "weight": 50},
        {"board": "WBBSE", "stage": "UPPER_PRIMARY", "grade": 8, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "অধ্যায় ২", "topic": "অণুজীবের জগৎ", "weight": 40},

        # --- WBBSE Secondary (Classes 9-10) ---
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 9, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "অধ্যায় ২", "topic": "বল ও গতি (নিউটনের সূত্র)", "weight": 60},
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 9, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "অধ্যায় ৮", "topic": "উৎপাদকে বিশ্লেষণ", "weight": 60},
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 9, "subject": "English", "textbook": "Bliss", "chapter": "Lesson 2", "topic": "Autumn (John Clare)", "weight": 50},
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 10, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "অধ্যায় ১", "topic": "একচলবিশিষ্ট দ্বিঘাত সমীকরণ", "weight": 70},
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 10, "subject": "Life Science", "textbook": "জীবন বিজ্ঞান ও পরিবেশ", "chapter": "অধ্যায় ১", "topic": "জীবজগতে নিয়ন্ত্রণ ও সমন্বয় (হরমোন)", "weight": 70},
        {"board": "WBBSE", "stage": "SECONDARY", "grade": 10, "subject": "History", "textbook": "ইতিহাস ও পরিবেশ", "chapter": "অধ্যায় ৩", "topic": "প্রতিরোধ ও বিদ্রোহ (সাঁওতাল বিদ্রোহ)", "weight": 65},

        # --- WBCHSE Higher Secondary (Classes 11-12) ---
        {"board": "WBCHSE", "stage": "HIGHER_SECONDARY", "grade": 11, "subject": "General", "textbook": "ইতিহাস ও সমাজতত্ত্ব", "chapter": "প্রথম অধ্যায়", "topic": "নৃতাত্ত্বিক পর্যায় নিরূপণের উপায়", "weight": 55},
        {"board": "WBCHSE", "stage": "HIGHER_SECONDARY", "grade": 11, "subject": "English", "textbook": "Mindscapes", "chapter": "Short Stories", "topic": "The Eyes Have It (Ruskin Bond)", "weight": 60},
        {"board": "WBCHSE", "stage": "HIGHER_SECONDARY", "grade": 12, "subject": "Bengali", "textbook": "সাহিত্য চর্চা", "chapter": "গল্প", "topic": "কে বাঁচায় কে বাঁচে (মানিক বন্দ্যোপাধ্যায়)", "weight": 55},
        {"board": "WBCHSE", "stage": "HIGHER_SECONDARY", "grade": 12, "subject": "English", "textbook": "Mindscapes", "chapter": "Prose", "topic": "Strong Roots (APJ Abdul Kalam)", "weight": 55}
    ]

    QA_SUBTYPES = ["EXPLAIN", "DEFINE", "SOLVE", "STEP_BY_STEP", "GUIDED_SOLVE", "CORRECT_ERROR", "MISCONCEPTION", "COMPARE", "CLASSIFY", "CAUSE_EFFECT", "TEXT_SPECIFIC"]
    
    manifest_items = []
    
    # Generate 1,500 planned slots
    # 800 QA, 350 Lesson Plan, 350 Quiz
    
    task_pool = (["QA"] * 800) + (["LESSON_PLAN"] * 350) + (["QUIZ"] * 350)
    random.seed(42)
    random.shuffle(task_pool)
    
    for i, task_type in enumerate(task_pool, 1):
        topic_entry = random.choices(CURRICULUM_CATALOG, weights=[t["weight"] for t in CURRICULUM_CATALOG], k=1)[0]
        
        # Dual-role assignment
        requester_role = "TEACHER" if random.random() < 0.85 else "STUDENT"
        instructional_target = "STUDENT" if requester_role == "STUDENT" else ("STUDENT" if random.random() < 0.80 else "TEACHER")
        
        # QA Subtype or metadata
        qa_meta = None
        lp_meta = None
        qz_meta = None
        
        if task_type == "QA":
            subtype = random.choice(QA_SUBTYPES)
            qa_meta = {
                "subtype": subtype,
                "difficulty": "MODERATE",
                "cognitive_level": "APPLY" if "SOLVE" in subtype else "UNDERSTAND",
                "step_by_step": subtype in ["SOLVE", "STEP_BY_STEP"]
            }
        elif task_type == "LESSON_PLAN":
            grade = topic_entry["grade"]
            tier = "I_II" if grade <= 2 else ("III_V" if grade <= 5 else ("VI_VIII" if grade <= 8 else ("IX_X" if grade <= 10 else "XI_XII")))
            lp_meta = {
                "lesson_duration_minutes": 40,
                "pedagogical_model": "ACTIVITY_BASED" if grade <= 5 else "STANDARD_DIRECT",
                "grade_tier": tier,
                "teaching_aids": ["পাঠ্যবই", "ব্ল্যাকবোর্ড", "চক", "চার্ট"]
            }
        elif task_type == "QUIZ":
            grade = topic_entry["grade"]
            total_marks = 10 if grade <= 5 else (15 if grade <= 8 else 20)
            qz_meta = {
                "quiz_scope": "SINGLE_TOPIC",
                "question_count": 4 if total_marks <= 15 else 5,
                "total_marks": total_marks,
                "difficulty": "MODERATE",
                "answer_mode": "QUIZ_WITH_SEPARATE_ANSWER_KEY" if requester_role == "TEACHER" else "QUIZ_ONLY"
            }
            
        manifest_items.append({
            "slot_id": f"part1_slot_{i:04d}",
            "task_type": task_type,
            "requester_role": requester_role,
            "instructional_target": instructional_target,
            "curriculum": {
                "board": topic_entry["board"],
                "stage": topic_entry["stage"],
                "grade": topic_entry["grade"],
                "subject": topic_entry["subject"],
                "textbook": topic_entry["textbook"],
                "chapter": topic_entry["chapter"],
                "topic": topic_entry["topic"]
            },
            "source_mode": "TEXTBOOK_GROUNDED",
            "qa_metadata": qa_meta,
            "lesson_plan_metadata": lp_meta,
            "quiz_metadata": qz_meta
        })

    manifest_path = os.path.join(output_dir, "part1_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_items, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {len(manifest_items)} target slots in {manifest_path}")
    
    # Print summary statistics
    task_counts = {}
    board_counts = {}
    for item in manifest_items:
        t = item["task_type"]
        b = item["curriculum"]["board"]
        task_counts[t] = task_counts.get(t, 0) + 1
        board_counts[b] = board_counts.get(b, 0) + 1
        
    print("Task breakdown:", task_counts)
    print("Board breakdown:", board_counts)

if __name__ == "__main__":
    build_part1_manifest()