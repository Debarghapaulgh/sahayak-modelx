import json
import os
import random
import sys
import argparse
import asyncio

# Configure UTF-8 stdout for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_PACK_PATH = os.path.join(BASE_DIR, "locale-packs", "north-bengal.json")
RESULTS_FILE = os.path.join(BASE_DIR, "prompts", "candidate-results.jsonl")
SFT_CHAT_FILE = os.path.join(BASE_DIR, "prompts", "candidate-sft-chat.jsonl")

# Ensure synthetictutor path is in sys.path
sys.path.append(os.path.dirname(BASE_DIR))
from synthetictutor.llm.openai_client import OpenAICompatibleClient

try:
    from scripts.scrub_pii import scrub_text
except ModuleNotFoundError:
    try:
        from scrub_pii import scrub_text
    except ModuleNotFoundError:
        def scrub_text(text, allowed): return text

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
    templates = {
        "worksheet": [
            f"শ্রেণি {grade} এর {subject} বিষয়ের '{chapter}' চ্যাপ্টারের ওপর ৫টি ছোট প্রশ্ন ও তাদের সঠিক উত্তর তৈরি করে দাও।",
            f"শ্রেণি {grade} এর {subject} বিষয়ের '{chapter}' থেকে ৫টি ছোট প্রশ্ন ও উত্তরের একটি ওয়ার্কশিট তৈরি করো।"
        ],
        "lesson_plan": [
            f"শ্রেণি {grade} এর {subject} ক্লাসে '{chapter}' পড়ানোর জন্য একটি ৪০ মিনিটের সম্পূর্ণ লেসন প্ল্যান তৈরি করো।",
            f"'{chapter}' চ্যাপ্টারটি পড়ানোর জন্য একটি ৩০ মিনিটের ক্লাস লেসন প্ল্যান বানিয়ে দিন।"
        ],
        "concept_explanation": [
            f"ক্লাস {grade} এর শিক্ষার্থীদের জন্য '{chapter}' বিষয়টি সহজ ভাষায় বুঝিয়ে দাও যাতে তারা সহজে বুঝতে পারে।",
            f"সহজ উদাহরণ দিয়ে '{chapter}' এর ধারণাটি বুঝিয়ে বলো।"
        ],
        "parent_call_script": [
            f"{student_name} স্কুলে ঠিকমতো আসছে না, ওর মা-বাবার সাথে কথা বলার জন্য শিক্ষকের উপযোগী একটি ফোনালাপের ডায়ালগ স্ক্রিপ্ট লিখে দাও।",
            f"{student_name} পড়াশোনায় মন দিচ্ছে না, ওর মা-বাবার সাথে কথা বলার একটা ছোট বাংলা ফোনালাপ স্ক্রিপ্ট দিন।"
        ],
        "grading_feedback": [
            f"একটি শিক্ষার্থী পরীক্ষায় '{chapter}' এর প্রশ্নের ভুল উত্তর দিয়েছে। তাকে খাতার ওপর লিখে দেওয়ার মতো একটি স্পষ্ট ও সংশোধনমূলক ফিডব্যাক লিখে দাও।",
            f"পরীক্ষায় '{chapter}' এর অঙ্ক ভুল করার পর শিক্ষার্থীকে খাতার নিচে দেওয়ার মতো একটি সংশোধনমূলক ফিডব্যাক তৈরি করো।"
        ],
        "report_card_remark": [
            f"{student_name} এর অর্ถมศึกษา পরীক্ষার পারফরম্যান্সের ওপর ভিত্তি করে একটি পজিティブ রিপোর্ট কার্ড রিমার্ক তৈরি করো।"
        ],
        "differentiated_material": [
            f"পিছিয়ে পড়া শিক্ষার্থীদের সহজে শেখানোর জন্য '{chapter}' চ্যাপ্টারের ওপর একটি সহজ নোট বা স্টাডি মেটেরিয়াল লিখে দিন।"
        ]
    }
    if subject == "Mathematics" and task_type == "worksheet":
        templates["worksheet"].append(f"'{chapter}' থেকে ৫টি সরল অঙ্কের প্র্যাকটিস কোশ্চেন ও উত্তর বানিয়ে দিন।")
        
    return random.choice(templates[task_type])

def format_response_generator(prompt_text, task_type):
    system_prompt = (
        "System: You are an expert school teaching assistant for WBBSE (West Bengal Board), Bengali-medium in North Bengal.\n"
        "Your task is to write the direct, copy-pasteable content (like the actual worksheet, the actual explanation, the actual feedback, or the actual script) in Bengali matching the teacher's request.\n"
        "Crucial Rule: Do NOT write meta-instructions, advice for the teacher, or lists of tips on 'how' to do it. Instead, write the actual content itself that the teacher can copy, print, or use immediately. Ensure the output is complete and does not cut off. For English language topics, write the instructions/headings in Bengali and only the English passage/exercises in English.\n\n"
        f"Teacher Request: {prompt_text}\n\n"
        "Assistant Response:"
    )
    return system_prompt

def validate_record_quality(prompt, response, grade, subject, task_type):
    # Rule 1: Completeness
    response_clean = response.strip()
    if not response_clean:
        return False, "Empty response"
    
    last_char = response_clean[-1]
    if last_char not in ['।', '.', '?', '!', '\"', '\'', ')', ']']:
        return False, f"Truncation detected (ends with '{last_char}')"
        
    # Rule 2: Grade consistency
    grade_words = {
        1: ["শ্রেণি ২", "শ্রেণি ৩", "শ্রেণি ৪", "শ্রেণি ৫", "শ্রেণি ৬", "class 2", "class 3", "class 4", "class 5"],
        2: ["শ্রেণি ১", "শ্রেণি ৩", "শ্রেণি ৪", "শ্রেণি ৫", "শ্রেণি ৬", "class 1", "class 3", "class 4", "class 5"],
        3: ["শ্রেণি ১", "শ্রেণি ২", "শ্রেণি ৪", "শ্রেণি ৫", "শ্রেণি ৬", "class 1", "class 2", "class 4", "class 5", "class 10", "দশম"],
        4: ["শ্রেণি ৫", "class 5", "class 10", "দশম"],
        5: ["ষষ্ঠ", "সপ্তম", "অষ্টম", "শ্রেণি ৬", "শ্রেণি ৭", "শ্রেণি ৮", "class 6", "class 7", "class 8"]
    }
    forbidden_terms = grade_words.get(grade, [])
    for term in forbidden_terms:
        if term in response:
            return False, f"Grade mismatch (contains forbidden term '{term}' for grade {grade})"
            
    # Rule 3: Parent call script role
    if task_type == "parent_call_script":
        teacher_indicators = ["শিক্ষক", "শিক্ষিকা", "দিদিমণি", "মাষ্টার", "স্কুল", "ক্লাস", "পড়াশোনা"]
        has_teacher = any(ind in response for ind in teacher_indicators)
        if not has_teacher:
            return False, "Parent call script missing teacher's presence"
            
    # Rule 4: Rule of Three ("ত্রৈরাশিক") math grounding
    if "ত্রৈরাশিক" in prompt or "ত্রৈরাশিক" in response:
        math_terms = ["অনুপাত", "সমানুপাত", "গুণ", "ভাগ", "সংখ্যা", "মান"]
        has_math = any(t in response for t in math_terms)
        mixture_terms = ["চিনি", "নুন", "শরবত", "ওআরএস", "মিশ্রণ"]
        has_mixture = any(t in response for t in mixture_terms)
        if has_mixture and not has_math:
            return False, "Hallucinated 'ত্রৈরাশিক' as chemistry mixture"

    return True, "Passed"

async def generate_text_with_backoff(client, prompt, retries=5, initial_backoff=4):
    for attempt in range(retries):
        try:
            res = await client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2048
            )
            return res
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "limit" in err_str or "rate" in err_str:
                sleep_time = initial_backoff * (2 ** attempt)
                print(f"Rate limit hit (429). Retrying in {sleep_time} seconds... (Attempt {attempt+1}/{retries})")
                await asyncio.sleep(sleep_time)
            else:
                raise e
    raise Exception("Max retries exceeded for API call due to persistent rate limit errors.")

async def generate_single_record(client, pool, names, idx, total, is_cloud):
    max_generation_attempts = 3
    for attempt in range(max_generation_attempts):
        target = random.choice(pool)
        task_type = random.choice(TASK_TYPES)
        student_name = random.choice(names)
        
        simulated_prompt = generate_natural_prompt(
            target["grade"], target["subject"], target["chapter"], task_type, student_name
        )
                
        full_prompt = format_response_generator(simulated_prompt, task_type)
        try:
            response_text = await generate_text_with_backoff(client, full_prompt)
            ideal_response = response_text.strip()
            
            # Apply pacing delay after the API call
            if is_cloud:
                await asyncio.sleep(5)
                
            if not ideal_response:
                continue
                
            # Perform Quality Gate Verification
            passed, reason = validate_record_quality(
                simulated_prompt, ideal_response, target["grade"], target["subject"], task_type
            )
            
            if not passed:
                print(f"[{idx}/{total}] Rejected: {reason}. Retrying (Attempt {attempt+1}/{max_generation_attempts})...")
                continue
                
            # PII Scrubbing
            scrubbed_prompt = scrub_text(simulated_prompt, names)
            scrubbed_response = scrub_text(ideal_response, names)
            
            # Save to Database
            record_id = f"northbengal-synthetic-{random.randint(100000, 999999)}"
            db_record = {
                "id": record_id,
                "task_type": task_type,
                "context": {
                    "board": "WBBSE",
                    "grade": target["grade"],
                    "subject": target["subject"],
                    "chapter": target["chapter"]
                },
                "prompt": scrubbed_prompt,
                "ideal_response": scrubbed_response,
                "status": "candidate"
            }
            
            with open(RESULTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(db_record, ensure_ascii=False) + "\n")
                
            # Save to 2-Turn SFT Training Chat
            chat_record = {
                "messages": [
                    {"role": "user", "content": scrubbed_prompt},
                    {"role": "assistant", "content": scrubbed_response}
                ]
            }
            
            with open(SFT_CHAT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(chat_record, ensure_ascii=False) + "\n")
                
            print(f"[{idx}/{total}] Generated successfully! ID: {record_id} | Prompt: {scrubbed_prompt[:40]}...")
            return True
            
        except Exception as e:
            print(f"[{idx}/{total}] Failed during attempt: {e}")
            if is_cloud:
                await asyncio.sleep(5)
            
    print(f"[{idx}/{total}] Skipping: Could not generate a high-quality sample after {max_generation_attempts} attempts.")
    return False

async def main():
    parser = argparse.ArgumentParser(description="SahayakAI Master Dataset Generator Pipeline")
    parser.add_argument("--num_records", type=int, default=10, help="Number of records to generate")
    parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "gemini", "groq", "openrouter"], help="API Provider")
    parser.add_argument("--model", type=str, default=None, help="Override default model name")
    parser.add_argument("--base_url", type=str, default=None, help="Override default API base URL")
    args = parser.parse_args()
    
    # Resolve API configurations based on selected provider
    provider = args.provider.lower()
    
    # Defaults configuration table
    configs = {
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "model": "sarg-base:latest",
            "key_env": None
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.0-flash",
            "key_env": "GEMINI_API_KEY"
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile",
            "key_env": "GROQ_API_KEY"
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "meta-llama/llama-3.3-70b-instruct",
            "key_env": "OPENROUTER_API_KEY"
        }
    }
    
    selected_cfg = configs[provider]
    base_url = args.base_url or selected_cfg["base_url"]
    model_name = args.model or selected_cfg["model"]
    
    # Check for API key if running a cloud provider
    api_key = "EMPTY"
    if selected_cfg["key_env"]:
        api_key = os.environ.get(selected_cfg["key_env"]) or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(f"Error: API Key not found in environment. Please set either '{selected_cfg['key_env']}' or 'OPENAI_API_KEY'.")
            sys.exit(1)
            
    is_cloud = provider != "ollama"
    
    pool = load_syllabus_pool()
    names = load_student_names()
    if not pool:
        print("Error: Syllabus chapter pool is empty.")
        return
        
    print(f"Starting pipeline generation. Target size: {args.num_records} records.")
    print(f"Provider: {provider.upper()} | Model: '{model_name}'")
    print(f"API Endpoint: {base_url}")
    if is_cloud:
        print("Cloud API detected. Activating pacing delay (5s) to prevent rate limits.")
        
    client = OpenAICompatibleClient(base_url=base_url, model_name=model_name, api_key=api_key)
    
    success_count = 0
    for i in range(1, args.num_records + 1):
        success = await generate_single_record(client, pool, names, i, args.num_records, is_cloud)
        if success:
            success_count += 1
            
    print(f"\nPipeline finished. Generated {success_count} / {args.num_records} successfully.")
    print(f"Raw database: {RESULTS_FILE}")
    print(f"SFT training file: {SFT_CHAT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
