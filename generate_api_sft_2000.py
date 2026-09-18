# -*- coding: utf-8 -*-
"""
generate_api_sft_2000.py — High-fidelity, API-driven dataset generation engine for SahayakAI SFT.
Pulls directly from 19,500+ textbook grounding chunks across Classes 1-12 (WBBPE, WBBSE, WBCHSE)
and verified district context, generating authentic, high-quality Bengali pedagogical dialogues.
Heavily focused on Lesson Plans and Comprehensive Quiz Sets (~60%+ distribution).
Primary Provider: Sarvam AI Indic LLM (sarvam-105b-conversations & sarvam-105b).
Outputs strictly in the exact original schema:
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
"""

import os
import sys
import json
import random
import re
import asyncio
import time
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, Any, List, Optional

import aiohttp
from export_api_sft_formats import export_all

# API Configuration
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "sk_t3i8crml_elALafNJUw1DyJJZoqK6iS2r")
SARVAM_URL = "https://api.sarvam.ai/v1/chat/completions"
SARVAM_EXHAUSTED = False

GEMINI_API_KEYS = [
    "AQ.Ab8RN6KRGHlaXvzH59kf_Q4zNmNWMnv_b3c3hrF9FzLV5WVBxA",
    "AQ.Ab8RN6IGnkeRe7sBlxCYameLFI43t8OREHu63kAQ7AuU6S2atg",
    "AQ.Ab8RN6JVMJuY3xHJVcVHhwuX6Iv17Ml-D5MxKG6wbFfQxyTNaw",
    "AQ.Ab8RN6KX4NQdgxgYEAA-arhGwWiYkD3jPgZzzJ4YOUHkUp7Upg"
]

GROQ_API_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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"
]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

OUTPUT_DIR = Path("datasets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "gold_standard_sft_2000_api.jsonl"
PROGRESS_MD = Path("GENERATION_PROGRESS.md")
PROGRESS_JSON = Path("GENERATION_PROGRESS.json")

# Concurrency & Rate Limiting
CONCURRENCY_LIMIT = 16
REQUEST_TIMEOUT_SECONDS = 45

# Load Regional Locale Facts
LOCALE_PATH = Path("locale.json")
VERIFIED_LOCALE_FACTS = [
    "দার্জিলিং জেলার পাহাড়ি ঢালে অম্লীয় দোআঁশ মাটিতে চা ও দার্জিলিং কমলার চাষ প্রধান (গড় বার্ষিক বৃষ্টিপাত ৩০৯২ মিমি, উৎস: IMD)।",
    "জলপাইগুড়ি ও আলিপুরদুয়ার জেলার ডুয়ার্স সমভূমিতে তিস্তা, তোর্সা ও জলঢাকা নদীর পলিমাটি উর্বর হওয়ায় ধান, পাট ও চা বাগান বিস্তৃত।",
    "মালদা জেলার মহানন্দা ও গঙ্গা তীরবর্তী সমতল পলিভূমিতে ফজলি আম ও পাট চাষ অত্যন্ত উন্নত।",
    "কোচবিহার জেলার কৃষিপ্রধান অর্থনীতিতে ধান ও তামাক চাষের বিশেষ ভূমিকা রয়েছে (মনরেগা দৈনিক মজুরি ₹২৫০)।",
    "উত্তর ও দক্ষিণ দিনাজপুর জেলায় বরো ধান, সরিষা ও পাট চাষ প্রধান গ্রামীণ জীবিকা।"
]

BENGALI_GRADES = {
    1: "প্রথম শ্রেণি", 2: "দ্বিতীয় শ্রেণি", 3: "তৃতীয় শ্রেণি", 4: "চতুর্থ শ্রেণি",
    5: "পঞ্চম শ্রেণি", 6: "ষষ্ঠ শ্রেণি", 7: "সপ্তম শ্রেণি", 8: "অষ্টম শ্রেণি",
    9: "নবম শ্রেণি", 10: "দশম শ্রেণি", 11: "একাদশ শ্রেণি", 12: "দ্বাদশ শ্রেণি"
}

def get_board_for_grade(grade: int) -> str:
    if 1 <= grade <= 5:
        return "WBBPE"
    elif 6 <= grade <= 10:
        return "WBBSE"
    else:
        return "WBCHSE"

def get_board_full_bengali(board: str) -> str:
    return {
        "WBBPE": "পশ্চিমবঙ্গ প্রাথমিক শিক্ষা পর্ষদ (WBBPE)",
        "WBBSE": "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)",
        "WBCHSE": "পশ্চিমবঙ্গ উচ্চমাধ্যমিক শিক্ষা সংসদ (WBCHSE)"
    }.get(board, "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)")

ADDITIONAL_STEM_TOPICS = [
    {"grade": 9, "subject": "Physical Science", "topic": "পরমাণুর গঠন: রাদারফোর্ড ও বোরের মডেল, আইসোটোপ ও আইসোবার", "board": "WBBSE"},
    {"grade": 9, "subject": "Physical Science", "topic": "বল ও গতি: নিউটনের গতিসূত্রসমূহ, ভরবেগের সংরক্ষণ এবং F=ma প্রতিপাদন", "board": "WBBSE"},
    {"grade": 9, "subject": "Life Science", "topic": "কোষ ও কোষ বিভাজন: ইউক্যারিওটিক কোষের অঙ্গাণু ও তাদের কাজ", "board": "WBBSE"},
    {"grade": 9, "subject": "Life Science", "topic": "উদ্ভিদ ও প্রাণীর শারীরবৃত্তীয় প্রক্রিয়া: সালোকসংশ্লেষ ও বাষ্পমোচন", "board": "WBBSE"},
    {"grade": 9, "subject": "History", "topic": "ফরাসি বিপ্লবের কয়েকটি দিক: সমাজব্যবস্থা ও দার্শনিকদের অবদান", "board": "WBBSE"},
    {"grade": 9, "subject": "Geography", "topic": "আবহবিকার ও বিভিন্ন ভূমিরূপ গঠন প্রক্রিয়া", "board": "WBBSE"},
    {"grade": 10, "subject": "Physical Science", "topic": "গ্যাসের আচরণ: বয়েল ও চার্লসের সূত্র এবং সমন্বিত রূপ (PV=nRT)", "board": "WBBSE"},
    {"grade": 10, "subject": "Physical Science", "topic": "চলতড়িৎ: ওহমের সূত্র (V=IR) এবং রোধের শ্রেণি ও সমান্তরাল সমবায়", "board": "WBBSE"},
    {"grade": 10, "subject": "Physical Science", "topic": "পর্যায় সারণি ও মৌলদের ধর্মের পর্যায়বৃত্ততা", "board": "WBBSE"},
    {"grade": 10, "subject": "Life Science", "topic": "উদ্ভিদ হরমোন: অক্সিন ও জিব্বেরেলিনের ভূমিকা এবং ট্রপিক চলন", "board": "WBBSE"},
    {"grade": 10, "subject": "Life Science", "topic": "বংশগতি এবং কয়েকটি সাধারণ জিনগত রোগ (থ্যালাসেমিয়া ও বর্ণান্ধতা)", "board": "WBBSE"},
    {"grade": 10, "subject": "History", "topic": "উনিশ শতকের বাংলায় সংস্কার আন্দোলন: রাজা রামমোহন রায় ও ঈশ্বরচন্দ্র বিদ্যাসাগর", "board": "WBBSE"},
    {"grade": 10, "subject": "Geography", "topic": "ভারতের প্রাকৃতিক পরিবেশ: ভূপ্রকৃতি, নদনদী ও জলবায়ুর বৈশিষ্ট্য", "board": "WBBSE"},
    {"grade": 11, "subject": "Physics", "topic": "একমাত্রিক ও দ্বিমাত্রিক গতি, প্রক্ষেপ্য গতির সমীকরণ ও পাল্লা", "board": "WBCHSE"},
    {"grade": 11, "subject": "Chemistry", "topic": "রাসায়নিক বন্ধন ও আণবিক গঠন: VSEPR তত্ত্ব ও সংকরায়ন", "board": "WBCHSE"},
    {"grade": 11, "subject": "Biological Sciences", "topic": "উদ্ভিদ শারীরবিদ্যা: সালোকসংশ্লেষের আলোক বিক্রিয়া ও কেলভিন চক্র", "board": "WBCHSE"},
    {"grade": 11, "subject": "Mathematics", "topic": "ত্রিকোণমিতিক অপেক্ষক ও যৌগিক কোণের অনুপাত", "board": "WBCHSE"},
    {"grade": 12, "subject": "Physics", "topic": "স্থির তড়িৎ ও ধারকত্ব: গাউসের উপপাদ্য এবং সমান্তরাল পাত ধারক", "board": "WBCHSE"},
    {"grade": 12, "subject": "Physics", "topic": "তড়িৎচুম্বকত্ব: বায়ো-সাভার্ট সূত্র ও অ্যাম্পিয়ারের বদ্ধ পথ সূত্র", "board": "WBCHSE"},
    {"grade": 12, "subject": "Chemistry", "topic": "জৈব রসায়ন: অ্যালকোহল, ফেনল ও ইথার প্রস্তুতি এবং বিক্রিয়া", "board": "WBCHSE"},
    {"grade": 12, "subject": "Chemistry", "topic": "তড়িৎ রসায়ন: নার্নস্ট সমীকরণ ও গ্যালভানীয় কোষ", "board": "WBCHSE"},
    {"grade": 12, "subject": "Biological Sciences", "topic": "বংশগতির আণবিক ভিত্তি: DNA অনুলিপিকরণ ও ট্রান্সক্রিপশন", "board": "WBCHSE"},
    {"grade": 12, "subject": "Mathematics", "topic": "নির্দিষ্ট সমাকলন ও ক্ষেত্রফল নির্ণয়", "board": "WBCHSE"}
]

# HEAVY WEIGHTING FOR LESSON PLANS & QUIZZES (60%+ combined share)
TASK_TYPES = [
    "lesson_plan",
    "quiz_generation",
    "lesson_plan",
    "quiz_generation",
    "quiz_generation",
    "lesson_plan",
    "concept_explanation",
    "word_problem",
    "socratic_dialogue",
    "error_spotting"
]

def load_all_textbook_chunks() -> List[Dict[str, Any]]:
    chunks = []
    chunk_paths = list(Path("datasets/extracted_textbooks_by_class").rglob("grounding_chunks.jsonl"))
    for p in chunk_paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        c = json.loads(line)
                        if c.get("source_text") and len(c["source_text"].strip()) > 30:
                            chunks.append(c)
                    except Exception:
                        pass
    print(f"Loaded {len(chunks)} valid textbook grounding chunks from disk.", flush=True)
    return chunks

def build_system_prompt(board: str, grade: int, subject: str, topic: str, target_role: str = "STUDENT", locale_fact: Optional[str] = None) -> str:
    board_full = get_board_full_bengali(board)
    grade_bengali = BENGALI_GRADES.get(grade, f"{grade}ম শ্রেণি")

    addressing_rule = (
        "১. শিক্ষক মহাশয়ের উদ্দেশ্যে সম্মানসূচক 'আপনি' সম্বোধন করবে এবং শিক্ষণ-পদ্ধতি অনুযায়ী দিকনির্দেশ প্রদান করবে।"
        if target_role == "TEACHER"
        else "১. শিক্ষার্থীর উদ্দেশ্যে স্নেহপূর্ণ ও সহজবোধ্য 'তুমি/তোমরা' সম্বোধন করবে।"
    )

    locale_section = f"\n- আঞ্চলিক প্রেক্ষাপট (যাচাইকৃত তথ্য): {locale_fact}" if locale_fact else ""

    return f"""তুমি 'সহায়কএআই' (SahayakAI) — {board_full} বেঙ্গলি-মিডিয়াম স্কুলের শিক্ষার্থী ও শিক্ষক মহাশয়দের জন্য তৈরি একজন অভিজ্ঞ, বিশেষায়িত অ্যাকাডেমিক AI টিউটর। তোমার কাজ হলো পাঠ্যক্রম অনুযায়ী সহজ, সাবলীল, সঠিক ও শিক্ষার্থী-উপযোগী বাংলা ভাষায় পাঠদান, ধারণা ব্যাখ্যা, সমস্যা সমাধান এবং অধ্যয়ন-সংক্রান্ত সহায়তা প্রদান করা।

নিয়মাবলী ও সম্বোধন:
{addressing_rule}
২. স্পষ্ট, প্রাঞ্জল ও স্বাভাবিক ভাষায় সরাসরি শিক্ষামূলক উত্তরে প্রবেশ করবে; অপ্রয়োজনীয় অভিবাদন, চাটুকারিতা বা অতিরিক্ত ভূমিকা পরিহার করবে।
৩. পাঠ্যক্রম-উপযোগী প্রমিত বাংলা পরিভাষা ব্যবহার করবে। সাধারণ বাংলা গদ্যে সংখ্যা বাংলা অঙ্কে (০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯) লিখবে।
৪. বৈধ mathematical/scientific notation যেমন x², x^2, H₂O, CO₂, ∠ABC যথাযথ রাখবে।
৫. কোনো কৃত্রিম সোর্স-রেফারেন্স (যেমন 'প্রদত্ত পাঠ্যাংশে' বা 'উক্ত চাঙ্কে') উল্লেখ না করে স্বাভাবিকভাবে বিষয়বস্তু উপস্থাপন করবে।

সহায়কএআই (SahayakAI) পাঠ্যসূচি বিবরণী:
- পর্ষদ/সংসদ: {board_full}
- শ্রেণি: {grade_bengali}
- বিষয়: {subject}
- বিষয়বস্তু: {topic}{locale_section}"""

def build_prompt_package(chunk: Dict[str, Any], task_type: str, slot_id: int) -> Dict[str, Any]:
    grade = chunk.get("grade", 10)
    if not (1 <= grade <= 12):
        grade = random.randint(6, 10)
    
    board = chunk.get("board") or get_board_for_grade(grade)
    grade_bengali = BENGALI_GRADES.get(grade, f"{grade}ম শ্রেণি")
    subject = chunk.get("subject", "Mathematics")
    chapter = chunk.get("chapter") or chunk.get("topic") or "সাধারণ পাঠ্যক্রম"
    source_text = chunk.get("source_text", "").strip()

    locale_fact = None
    if any(k in subject for k in ["Geography", "Environmental", "Science", "পরিবেশ", "ভূগোল"]) and (slot_id % 3 == 0):
        locale_fact = VERIFIED_LOCALE_FACTS[slot_id % len(VERIFIED_LOCALE_FACTS)]

    target_role = "TEACHER" if task_type in ["lesson_plan", "grading_feedback", "quiz_generation"] else "STUDENT"
    system_prompt = build_system_prompt(board, grade, subject, chapter, target_role, locale_fact)

    task_instruction_map = {
        "lesson_plan": f"শিক্ষক মহাশয়ের জন্য এই অধ্যায়ের ওপর একটি অত্যন্ত সমৃদ্ধ, বাস্তবমুখী ও ক্লাসরুম-উপযোগী পূর্ণাঙ্গ পাঠ-পরিকল্পনা (Detailed Lesson Plan) তৈরি করো। এতে স্পষ্টভাবে উল্লেখ থাকবে:\n(১) সুনির্দিষ্ট শিখন উদ্দেশ্য (General & Specific Learning Objectives),\n(২) প্রয়োজনীয় স্বল্পমূল্যের স্থানীয় শিক্ষাপ্রদীপ/উপকরণ (Low-Cost TLM & Teaching Aids),\n(৩) ৪০ মিনিটের সুবিন্যস্ত পর্যায়ক্রমিক শ্রেণি কার্যক্রম (Hook/আকর্ষণীয় প্রারম্ভিক প্রশ্নোত্তর, মূল ধারণা উপস্থাপন, দলগত ও একক শিক্ষার্থী কার্যক্রম),\n(৪) শিখনে পিছিয়ে পড়া ও এগিয়ে থাকা শিক্ষার্থীদের জন্য বিশেষ কৌশল (Differentiated Learning Strategy),\n(৫) তাৎক্ষণিক গঠনমূলক মূল্যায়ন প্রশ্ন (Formative Assessment) এবং চিন্তনমূলক বাড়ির কাজ।",
        "quiz_generation": f"শিক্ষক মহাশয়ের শ্রেণি মূল্যায়ন এবং শিক্ষার্থীদের অনুশীলনের জন্য এই পাঠ্যাংশের ওপর ভিত্তি করে একটি পূর্ণাঙ্গ ও আকর্ষণীয় কুইজ/প্রশ্নসেট (Comprehensive Quiz Paper) তৈরি করো। এতে থাকবে:\n(১) ৩টি মানসম্মত বহুনির্বাচনী প্রশ্ন (MCQ) — প্রতিটি বিকল্পে বাস্তবসম্মত বিভ্রান্তিকর অপশন (plausible distractors) সহ (কখনও 'সবকটি/কোনোটিই নয়' দেবে না),\n(২) ২টি সংক্ষিপ্ত ধারণামূলক প্রশ্ন (Short Answer Conceptual Questions),\n(৩) ১টি বাস্তব প্রয়োগ ও উচ্চতর চিন্তন দক্ষতাভিত্তিক সমস্যা (HOTS Problem),\n(৪) সম্পূর্ণ উত্তরমালা (Answer Key), নম্বর বিভাজন ও প্রতিটি উত্তরের পুঙ্খানুপুঙ্খ ব্যাখ্যা।",
        "concept_explanation": f"পাঠ্যবইয়ের এই ধারণার ওপর ভিত্তি করে {grade_bengali}-র শিক্ষার্থীর জন্য একটি প্রাঞ্জল, আকর্ষণীয় ও গভীর কনসেপ্ট ব্যাখ্যা তৈরি করো। একটি বাস্তব জীবনের উদাহরণ দিয়ে বিষয়টি স্পষ্ট করে দেবে।",
        "word_problem": f"এই পাঠ্যাংশের ওপর ভিত্তি করে একটি বাস্তবমুখী গাণিতিক/বিজ্ঞানভিত্তিক সমস্যা এবং তার ধাপে ধাপে বিস্তারিত সমাধান প্রস্তুত করো। প্রতিটি গণনার ধাপ ও সূত্র স্পষ্টভাবে ব্যাখ্যা করো।",
        "socratic_dialogue": f"শিক্ষার্থী এবং শিক্ষকের মধ্যে একটি আকর্ষণীয় সক্রেটিক প্রশ্নোত্তর সংলাপ (৩-৪ রাউন্ড কথোপকথন) তৈরি করো, যেখানে শিক্ষক সরাসরি উত্তর না বলে চিন্তাশীল প্রশ্নের মাধ্যমে শিক্ষার্থীকে সঠিক উত্তরের দিকে নিয়ে যান।",
        "error_spotting": f"এই ধারণায় শিক্ষার্থীরা সচরাচর যে সাধারণ ভুল বা ভ্রান্ত ধারণা (misconception) করে, সেরকম একটি ভুল সমাধানের উদাহরণ তুলে ধরো এবং বুঝিয়ে দাও কেন এটি ভুল ও কীভাবে সঠিক সমাধান করতে হবে।"
    }

    task_desc = task_instruction_map.get(task_type, task_instruction_map["concept_explanation"])

    user_prompt = f"""পাঠ্যাংশ:
\"\"\"
{source_text[:1200]}
\"\"\"

প্রশ্ন / নির্দেশ:
{task_desc}"""

    is_stem_high = grade >= 9 and any(s in subject.lower() for s in ["math", "physic", "chem", "গণিত", "ভৌতবিজ্ঞান", "রসায়ন", "পদার্থ"])
    primary_model = "sarvam-105b" if is_stem_high else "sarvam-105b-conversations"

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "grade": grade,
        "board": board,
        "subject": subject,
        "chapter": chapter,
        "task_type": task_type,
        "target_role": target_role,
        "locale_fact": locale_fact,
        "chosen_model": primary_model,
        "slot_id": slot_id
    }

async def call_sarvam_api(session: aiohttp.ClientSession, prompt_pkg: Dict[str, Any], semaphore: asyncio.Semaphore) -> tuple[Optional[str], Optional[str]]:
    global SARVAM_EXHAUSTED
    if SARVAM_EXHAUSTED:
        return None, None

    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json"
    }

    model = prompt_pkg["chosen_model"]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_pkg["system_prompt"]},
            {"role": "user", "content": prompt_pkg["user_prompt"]}
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    async with semaphore:
        try:
            async with session.post(SARVAM_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return content, model
                elif resp.status in (402, 403):
                    SARVAM_EXHAUSTED = True
                    return None, None
        except Exception:
            pass
    return None, None

async def call_gemini_api(session: aiohttp.ClientSession, prompt_pkg: Dict[str, Any], semaphore: asyncio.Semaphore) -> tuple[Optional[str], Optional[str]]:
    slot_id = prompt_pkg.get("slot_id", 0)
    for k_idx in range(len(GEMINI_API_KEYS)):
        api_key = GEMINI_API_KEYS[(slot_id + k_idx) % len(GEMINI_API_KEYS)]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": prompt_pkg["system_prompt"]}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": prompt_pkg["user_prompt"]}]}
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048
            }
        }
        headers = {"Content-Type": "application/json"}

        async with semaphore:
            try:
                async with session.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts and "text" in parts[0]:
                                return parts[0]["text"].strip(), "gemini-3-flash-preview"
                    elif resp.status == 429:
                        continue
            except Exception:
                pass
    return None, None

async def call_groq_api(session: aiohttp.ClientSession, prompt_pkg: Dict[str, Any], semaphore: asyncio.Semaphore) -> tuple[Optional[str], Optional[str]]:
    slot_id = prompt_pkg.get("slot_id", 0)
    
    # Try all keys and models combination
    models_to_try = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
    if slot_id % 2 != 0:
        models_to_try.reverse()

    for m_name in models_to_try:
        for k_idx in range(len(GROQ_API_KEYS)):
            api_key = GROQ_API_KEYS[(slot_id + k_idx) % len(GROQ_API_KEYS)]
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }

            payload = {
                "model": m_name,
                "messages": [
                    {"role": "system", "content": prompt_pkg["system_prompt"]},
                    {"role": "user", "content": prompt_pkg["user_prompt"]}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }

            async with semaphore:
                try:
                    async with session.post(GROQ_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            content = data["choices"][0]["message"]["content"].strip()
                            if len(content) > 50:
                                return content, m_name
                        elif resp.status == 429:
                            # Try next key immediately
                            continue
                except Exception:
                    pass
    return None, None

async def call_llm_pipeline(session: aiohttp.ClientSession, prompt_pkg: Dict[str, Any], semaphore: asyncio.Semaphore) -> tuple[Optional[str], str]:
    # 1. Primary: Sarvam AI Indic LLM (sarvam-105b / sarvam-105b-conversations)
    text, model_used = await call_sarvam_api(session, prompt_pkg, semaphore)
    if text and len(text.strip()) > 50:
        return text, model_used

    # 2. Secondary: Groq 3-Key Pool (Qwen 27B / GPT-OSS 120B)
    text, model_used = await call_groq_api(session, prompt_pkg, semaphore)
    if text and len(text.strip()) > 50:
        return text, model_used

    # 3. Tertiary: Google Gemini 3 Flash Preview
    text, model_used = await call_gemini_api(session, prompt_pkg, semaphore)
    if text and len(text.strip()) > 50:
        return text, model_used

    return None, prompt_pkg["chosen_model"]

def update_progress_files(total_saved: int, target_records: int, start_time: float, stage_counts: Dict[str, int], task_counts: Dict[str, int], model_counts: Dict[str, int]):
    elapsed = time.time() - start_time
    rate = total_saved / elapsed if elapsed > 0 else 0
    remaining_records = max(0, target_records - total_saved)
    eta_seconds = remaining_records / rate if rate > 0 else 0
    eta_min = eta_seconds / 60.0

    percent = (total_saved / target_records) * 100.0 if target_records > 0 else 0

    status_data = {
        "status": "RUNNING" if total_saved < target_records else "COMPLETED",
        "completed": total_saved,
        "target": target_records,
        "percent": round(percent, 2),
        "speed_records_per_sec": round(rate, 2),
        "speed_records_per_min": round(rate * 60, 2),
        "elapsed_seconds": round(elapsed, 1),
        "eta_minutes": round(eta_min, 1),
        "primary_engine": "Sarvam AI Indic LLM (sarvam-105b-conversations / sarvam-105b)",
        "stages": stage_counts,
        "task_types": task_counts,
        "models": model_counts,
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2, ensure_ascii=False)

    md_content = f"""# 📊 SahayakAI Dataset Generation Live Monitor

**Status**: `{"🟢 RUNNING" if total_saved < target_records else "✅ COMPLETED"}`  
**Progress**: **{total_saved} / {target_records}** records (**{percent:.1f}%**)  
**Primary Engine**: `Sarvam AI Indic LLM (sarvam-105b-conversations / sarvam-105b)`  
**Focus**: `High-Volume Lesson Plans & Quiz Generation (60%+ share)`  
**Format**: `Pure ChatML messages (Zero Metadata Wrappers)`  
**Throughput**: `{rate:.2f}` records/sec (`{rate*60:.1f}` records/min)  
**Elapsed**: `{elapsed/60:.1f}` mins | **Estimated Remaining (ETA)**: `{eta_min:.1f}` mins  
**Last Updated**: `{status_data["last_updated"]}`  

---

### 🎓 Stage Breakdown
| Educational Stage | Grade Range | Board | Records Generated | Target | Progress |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary** | Class 1–5 | WBBPE | `{stage_counts.get("Primary", 0)}` | 500 | `{(stage_counts.get("Primary", 0)/500)*100:.1f}%` |
| **Middle** | Class 6–8 | WBBSE | `{stage_counts.get("Middle", 0)}` | 500 | `{(stage_counts.get("Middle", 0)/500)*100:.1f}%` |
| **Secondary** | Class 9–10 | WBBSE | `{stage_counts.get("Secondary", 0)}` | 600 | `{(stage_counts.get("Secondary", 0)/600)*100:.1f}%` |
| **Higher Secondary** | Class 11–12 | WBCHSE | `{stage_counts.get("Higher Secondary", 0)}` | 400 | `{(stage_counts.get("Higher Secondary", 0)/400)*100:.1f}%` |

---

### 🧩 Task Types Generated (Prioritizing Lesson Plans & Quizzes)
| Task Type | Focus | Count | Share |
| :--- | :--- | :--- | :--- |
"""
    for task_name, count in sorted(task_counts.items(), key=lambda x: x[1], reverse=True):
        share = (count / total_saved * 100) if total_saved > 0 else 0
        focus_desc = "Detailed Lesson Plans & TLM" if task_name == "lesson_plan" else ("MCQ/HOTS Quiz Sets & Solutions" if task_name == "quiz_generation" else "Pedagogy / Socratic Tutoring")
        md_content += f"| `{task_name}` | {focus_desc} | `{count}` | `{share:.1f}%` |\n"

    md_content += f"""
---

### 🤖 LLM Model Usage
| Model Name | Role | Output Count |
| :--- | :--- | :--- |
"""
    for model_name, m_count in sorted(model_counts.items(), key=lambda x: x[1], reverse=True):
        role_desc = "Sarvam AI Indic LLM" if "sarvam" in model_name else ("Google Gemini 3 Flash" if "gemini" in model_name else "Groq LPU Engine")
        md_content += f"| `{model_name}` | {role_desc} | `{m_count}` |\n"

    with open(PROGRESS_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

async def generate_dataset(target_records: int = 2000):
    all_chunks = load_all_textbook_chunks()
    
    primary_chunks = [c for c in all_chunks if 1 <= c.get("grade", 0) <= 5]
    middle_chunks = [c for c in all_chunks if 6 <= c.get("grade", 0) <= 8]
    secondary_chunks = [c for c in all_chunks if 9 <= c.get("grade", 0) <= 10]
    hs_chunks = [c for c in all_chunks if 11 <= c.get("grade", 0) <= 12]

    target_primary = int(target_records * 0.25)    # 500
    target_middle = int(target_records * 0.25)     # 500
    target_secondary = int(target_records * 0.30)  # 600
    target_hs = target_records - (target_primary + target_middle + target_secondary) # 400

    stage_configs = [
        ("Primary", primary_chunks, target_primary, 1, 5),
        ("Middle", middle_chunks, target_middle, 6, 8),
        ("Secondary", secondary_chunks, target_secondary, 9, 10),
        ("Higher Secondary", hs_chunks, target_hs, 11, 12),
    ]

    work_items = []
    slot_id = 0

    for stage_name, chunks_pool, count, min_g, max_g in stage_configs:
        for i in range(count):
            slot_id += 1
            task_type = TASK_TYPES[slot_id % len(TASK_TYPES)]
            
            if chunks_pool and random.random() < 0.85:
                chunk = random.choice(chunks_pool)
            else:
                stem_candidates = [t for t in ADDITIONAL_STEM_TOPICS if min_g <= t["grade"] <= max_g]
                if stem_candidates:
                    cand = random.choice(stem_candidates)
                    chunk = {
                        "grade": cand["grade"],
                        "board": cand["board"],
                        "subject": cand["subject"],
                        "chapter": cand["topic"],
                        "source_text": f"পশ্চিমবঙ্গ পাঠ্যক্রমের {cand['grade']}ম শ্রেণির {cand['subject']} বিষয়ের {cand['topic']} অধ্যায়ের প্রমিত শিক্ষাক্রম।"
                    }
                else:
                    g = random.randint(min_g, max_g)
                    b = get_board_for_grade(g)
                    chunk = {
                        "grade": g,
                        "board": b,
                        "subject": "Mathematics",
                        "chapter": "মৌলিক গাণিতিক ও বৈজ্ঞানিক সমস্যা সমাধান",
                        "source_text": f"{b} পর্ষদের অনুমোদিত পাঠ্যক্রম অনুযায়ী {g}ম শ্রেণির শিখন অভিজ্ঞতা।"
                    }

            prompt_pkg = build_prompt_package(chunk, task_type, slot_id)
            prompt_pkg["stage"] = stage_name
            work_items.append(prompt_pkg)

    print(f"Prepared {len(work_items)} stratified work items.", flush=True)

    existing_records = []
    stage_counts = defaultdict(int)
    task_counts = defaultdict(int)
    model_counts = defaultdict(int)

    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        rec = json.loads(line)
                        if "messages" in rec and len(rec["messages"]) == 3:
                            clean_rec = {"messages": rec["messages"]}
                            existing_records.append(clean_rec)
                    except Exception:
                        pass
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for r in existing_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_saved = len(existing_records)
    
    for i in range(min(total_saved, len(work_items))):
        item = work_items[i]
        stage_counts[item["stage"]] += 1
        task_counts[item["task_type"]] += 1
        model_counts[item["chosen_model"]] += 1

    print(f"Existing clean records in {OUTPUT_FILE}: {total_saved}. Resuming with high Lesson Plan & Quiz focus...", flush=True)

    remaining_items = work_items[total_saved:]
    queue = deque(remaining_items)
    print(f"Remaining records in queue to generate: {len(queue)}", flush=True)

    start_time = time.time()
    update_progress_files(total_saved, target_records, start_time, stage_counts, task_counts, model_counts)

    if total_saved >= target_records:
        print("All records already generated!", flush=True)
        export_all()
        return

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT * 2)

    async with aiohttp.ClientSession(connector=connector) as session:
        batch_size = 16
        while total_saved < target_records and queue:
            batch = []
            for _ in range(min(batch_size, len(queue))):
                batch.append(queue.popleft())

            tasks = [call_llm_pipeline(session, item, semaphore) for item in batch]
            results = await asyncio.gather(*tasks)

            new_saved = 0
            with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
                for item, (response_text, model_used) in zip(batch, results):
                    if response_text and len(response_text.strip()) > 50:
                        clean_record = {
                            "messages": [
                                {"role": "system", "content": item["system_prompt"]},
                                {"role": "user", "content": item["user_prompt"]},
                                {"role": "assistant", "content": response_text}
                            ]
                        }
                        out_f.write(json.dumps(clean_record, ensure_ascii=False) + "\n")
                        total_saved += 1
                        new_saved += 1
                        stage_counts[item["stage"]] += 1
                        task_counts[item["task_type"]] += 1
                        model_counts[model_used or item["chosen_model"]] += 1
                    else:
                        # Requeue for retry
                        queue.append(item)

            update_progress_files(total_saved, target_records, start_time, stage_counts, task_counts, model_counts)
            elapsed = time.time() - start_time
            rate = total_saved / elapsed if elapsed > 0 else 0
            print(f"Progress: [{total_saved}/{target_records}] ({total_saved/target_records*100:.1f}%) | Queue: {len(queue)} | Speed: {rate:.2f} rec/s", flush=True)

            if new_saved == 0:
                await asyncio.sleep(2.0)
            else:
                await asyncio.sleep(0.3)

    print(f"\nCompleted! Total records in {OUTPUT_FILE}: {total_saved}", flush=True)
    print("Auto-exporting into all standard formats...", flush=True)
    export_all()

if __name__ == "__main__":
    target = 2000
    if len(sys.argv) > 1:
        try:
            target = int(sys.argv[1])
        except ValueError:
            pass
    
    asyncio.run(generate_dataset(target_records=target))