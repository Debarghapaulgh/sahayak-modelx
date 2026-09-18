import json
import os
import random
import sys

# Configure UTF-8 stdout for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_PACK_PATH = os.path.join(BASE_DIR, "locale-packs", "north-bengal.json")
PROMPTS_FILE = os.path.join(BASE_DIR, "prompts", "real-teacher-prompts.jsonl")

TASK_TYPES = [
    "worksheet",
    "lesson_plan",
    "concept_explanation",
    "parent_call_script",
    "grading_feedback",
    "report_card_remark",
    "differentiated_material"
]

def load_syllabus_pool():
    if not os.path.exists(LOCALE_PACK_PATH):
        print(f"Error: Locale pack not found at {LOCALE_PACK_PATH}")
        sys.exit(1)
        
    with open(LOCALE_PACK_PATH, "r", encoding="utf-8") as f:
        pack = json.load(f)
        
    syllabus = pack.get("syllabus", {})
    pool = []
    
    for key, chapters in syllabus.items():
        if key == "note":
            continue
        try:
            parts = key.split("_grade")
            if len(parts) == 2:
                subject_raw = parts[0]
                grade = int(parts[1])
                
                subject_map = {
                    "math": "Mathematics",
                    "science": "Science",
                    "evs": "EVS",
                    "history": "History",
                    "geography": "Geography",
                    "bengali": "Bengali",
                    "english": "English"
                }
                subject = subject_map.get(subject_raw, subject_raw.capitalize())
                
                for chapter in chapters:
                    pool.append({
                        "grade": grade,
                        "subject": subject,
                        "chapter": chapter
                    })
        except Exception:
            continue
            
    return pool

def load_student_names():
    # Load all student names from locale pack to populate prompts
    if os.path.exists(LOCALE_PACK_PATH):
        try:
            with open(LOCALE_PACK_PATH, "r", encoding="utf-8") as f:
                pack = json.load(f)
            names = []
            for pool in pack.get("student_names", {}).values():
                names.extend(pool)
            if names:
                return names
        except Exception:
            pass
    return ["রিনা", "বিশাল", "সুজন", "কমলা", "সোমরা", "ললিত"]

def generate_natural_prompt(grade, subject, chapter, task_type, student_name):
    # Perfect, native-speaker Bengali/Benglish prompt templates
    templates = {
        "worksheet": [
            f"ক্লাস {grade} এর {subject} বিষয়ের '{chapter}' চ্যাপ্টারের ওপর ৫টি ছোট প্রশ্ন তৈরি করে দাও।",
            f"শ্রেণি {grade} এর {subject} বিষয়ের '{chapter}' থেকে ৫টি ছোট প্রশ্ন তৈরি করো।"
        ],
        "lesson_plan": [
            f"শ্রেণি {grade} এর {subject} ক্লাসে '{chapter}' পড়ানোর জন্য একটি সম্পূর্ণ পাঠ পরিকল্পনা (উদ্দেশ্য, উপকরণ, কার্যকলাপ ও মূল্যায়ন সহ) তৈরি করো।",
            f"'{chapter}' বিষয়টি পড়ানোর জন্য শ্রেণি {grade} এর একটি পাঠ পরিকল্পনা বানিয়ে দাও যাতে শিখন উদ্দেশ্য, টিচিং এইডস ও অ্যাক্টিভিটি থাকে।",
            f"Design a structured lesson plan for Class {grade} {subject} on '{chapter}' covering learning objectives, materials needed, classroom activities, and assessment.",
            f"Create a practical Class {grade} {subject} lesson plan for '{chapter}' with objectives, required materials, step-by-step activities, and evaluation."
        ],
        "concept_explanation": [
            f"ক্লাস {grade} এর শিক্ষার্থীদের জন্য '{chapter}' বিষয়টি সহজ করে বুঝিয়ে দাও।",
            f"সহজ উদাহরণ দিয়ে '{chapter}' এর ধারণাটি বুঝিয়ে বলো।"
        ],
        "parent_call_script": [
            f"{student_name} স্কুলে ঠিকমতো আসছে না, ওর মা-বাবার সাথে কথা বলার জন্য একটি ছোট ফোনালাপ স্ক্রিপ্ট লিখে দাও।",
            f"{student_name} পড়াশোনায় মন দিচ্ছে না, ওর মা-বাবার সাথে কথা বলার একটা ছোট বাংলা ফোনালাপ দিন।"
        ],
        "grading_feedback": [
            f"একটি শিক্ষার্থীর '{chapter}' এর ওপর লেখা উত্তরপত্রে ভুল বানানের সংশোধন করে ভালো ফিডব্যাক দাও।",
            f"শ্রেণি {grade} এর পরীক্ষায় '{chapter}' এর ভুল উত্তরের ওপর শিক্ষার্থীকে কী ফিডব্যাক দেওয়া উচিত?"
        ],
        "report_card_remark": [
            f"{student_name} এর অর্ধবার্ষিক পরীক্ষার পারফরম্যান্সের ওপর ভিত্তি করে একটি পজিটিভ রিপোর্ট কার্ড রিমার্ক তৈরি করো।"
        ],
        "differentiated_material": [
            f"পিছিয়ে পড়া শিক্ষার্থীদের জন্য '{chapter}' চ্যাপ্টারটি সহজে মনে রাখার উপযোগী কিছু স্টাডি মেটেরিয়াল দিন।"
        ]
    }
    
    # Subject specific overrides
    if subject == "Mathematics" and task_type == "worksheet":
        templates["worksheet"].append(f"'{chapter}' থেকে ৫টি সরল অঙ্কের প্র্যাকটিস কোশ্চেন বানিয়ে দিন।")
        
    return random.choice(templates[task_type])

def main():
    pool = load_syllabus_pool()
    names = load_student_names()
    if not pool:
        print("Error: Syllabus chapter pool is empty.")
        return
        
    target = random.choice(pool)
    task_type = random.choice(TASK_TYPES)
    student_name = random.choice(names)
    
    simulated_prompt = generate_natural_prompt(
        target["grade"], target["subject"], target["chapter"], task_type, student_name
    )
    
    record = {
        "prompt": simulated_prompt,
        "task_type": task_type,
        "grade": target["grade"],
        "subject": target["subject"]
    }
    
    os.makedirs(os.path.dirname(PROMPTS_FILE), exist_ok=True)
    with open(PROMPTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
    print(f"Successfully simulated and appended teacher prompt: {simulated_prompt}")

if __name__ == "__main__":
    main()
