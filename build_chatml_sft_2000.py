"""
Master Part 1 SFT Dataset Builder - ChatML Messages Format
Total: Exactly 2,000 Records
Schema: {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
"""

import os
import json
import random
from typing import Dict, Any, List, Optional
from pathlib import Path

# Load locale data for verified regional facts
LOCALE_PATH = Path("locale.json")
with open(LOCALE_PATH, "r", encoding="utf-8") as f:
    LOCALE_DATA = json.load(f)

# System Prompt Generator
def build_system_prompt(board: str, grade: int, subject: str, topic: str, target_role: str = "STUDENT", locale_fact: Optional[str] = None) -> str:
    board_full = {
        "WBBPE": "পশ্চিমবঙ্গ প্রাথমিক শিক্ষা পর্ষদ (WBBPE)",
        "WBBSE": "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)",
        "WBCHSE": "পশ্চিমবঙ্গ উচ্চমাধ্যমিক শিক্ষা সংসদ (WBCHSE)"
    }.get(board, "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)")

    grade_bengali = {
        1: "প্রথম শ্রেণি", 2: "দ্বিতীয় শ্রেণি", 3: "তৃতীয় শ্রেণি", 4: "চতুর্থ শ্রেণি",
        5: "পঞ্চম শ্রেণি", 6: "ষষ্ঠ শ্রেণি", 7: "সপ্তম শ্রেণি", 8: "অষ্টম শ্রেণি",
        9: "নবম শ্রেণি", 10: "দশম শ্রেণি", 11: "একাদশ শ্রেণি", 12: "দ্বাদশ শ্রেণি"
    }.get(grade, f"{grade}ম শ্রেণি")

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

# Stage 1: Primary (Classes 1-5) Topic Matrix
PRIMARY_TOPICS = [
    # Class 1
    {"board": "WBBPE", "grade": 1, "subject": "Bengali", "textbook": "সহজ পাঠ (প্রথম ভাগ)", "chapter": "প্রথম পাঠ", "topic": "স্বরবর্ণ ও ব্যঞ্জনবর্ণের উচ্চারণ এবং সহজ শব্দ গঠন"},
    {"board": "WBBPE", "grade": 1, "subject": "Mathematics", "textbook": "আমার বই", "chapter": "গণনা ও সংখ্যা", "topic": "বস্তু গণনা ও ১ থেকে ৯ পর্যন্ত সংখ্যার ধারণা"},
    {"board": "WBBPE", "grade": 1, "subject": "Health and Physical Education", "textbook": "স্বাস্থ্য ও শারীরশিক্ষা", "chapter": "স্বাস্থ্যবিধি", "topic": "শারীরিক পরিচ্ছন্নতা ও হাত ধোয়ার সঠিক নিয়ম"},
    
    # Class 2
    {"board": "WBBPE", "grade": 2, "subject": "Bengali", "textbook": "সহজ পাঠ (দ্বিতীয় ভাগ)", "chapter": "দ্বিতীয় পাঠ", "topic": "যুক্তাক্ষর চেনা ও সহজ বাক্য গঠন"},
    {"board": "WBBPE", "grade": 2, "subject": "Mathematics", "textbook": "আমার বই", "chapter": "যোগ-বিয়োগের প্রাথমিক ধারণা", "topic": "এক অঙ্কের সংখ্যার যোগ ও বিয়োগের বাস্তব সমস্যা"},
    {"board": "WBBPE", "grade": 2, "subject": "Health and Physical Education", "textbook": "স্বাস্থ্য ও শারীরশিক্ষা", "chapter": "খেলাধুলা ও শৃঙ্খলা", "topic": "কুচকাওয়াজ ও শারীরিক সমন্বয়"},

    # Class 3
    {"board": "WBBPE", "grade": 3, "subject": "Bengali", "textbook": "পাতাবাহার", "chapter": "সত্যি সোনা", "topic": "সত্যি সোনা গল্পের নীতিশিক্ষা ও মূলভাব"},
    {"board": "WBBPE", "grade": 3, "subject": "Mathematics", "textbook": "আমার গণিত", "chapter": "সংখ্যার বিস্তার", "topic": "স্থানীয় মান ও প্রকৃত মানের সাহায্যে তিন অঙ্কের সংখ্যা গঠন"},
    {"board": "WBBPE", "grade": 3, "subject": "Environmental Studies", "textbook": "আমাদের পরিবেশ", "chapter": "পরিবার ও সমাজ", "topic": "পারিবারিক সম্পর্ক ও জীবিকার বৈচিত্র্য"},

    # Class 4
    {"board": "WBBPE", "grade": 4, "subject": "Bengali", "textbook": "পাতাবাহার", "chapter": "আলো (নাটক)", "topic": "আলো নাটকের সারসংক্ষেপ ও চরিত্র বিশ্লেষণ"},
    {"board": "WBBPE", "grade": 4, "subject": "Mathematics", "textbook": "আমার গণিত", "chapter": "ভগ্নাংশ", "topic": "ভগ্নাংশের ধারণা: লব ও হর এবং সমতুল্য ভগ্নাংশ"},
    {"board": "WBBPE", "grade": 4, "subject": "Environmental Studies", "textbook": "আমাদের পরিবেশ", "chapter": "প্রকৃতির সম্পদ ও প্রাণী", "topic": "পশ্চিমবঙ্গের বন্যপ্রাণী ও অরণ্য সংরক্ষণ"},
    {"board": "WBBPE", "grade": 4, "subject": "Health and Physical Education", "textbook": "স্বাস্থ্য ও শারীরশিক্ষা", "chapter": "পথ নিরাপত্তা", "topic": "রাস্তা পারাপারের নিয়ম ও প্রাথমিক প্রতিবিধান"},

    # Class 5
    {"board": "WBBPE", "grade": 5, "subject": "Bengali", "textbook": "পাতাবাহার", "chapter": "বুনোহাঁস", "topic": "লীলা মজুমদারের বুনোহাঁস গল্পের ভাবার্থ ও প্রশ্নোত্তর"},
    {"board": "WBBPE", "grade": 5, "subject": "Mathematics", "textbook": "আমার গণিত", "chapter": "লসাগু ও গসাগু", "topic": "সাধারণ গুণনীয়ক ও গুণিতক নির্ণয়"},
    {"board": "WBBPE", "grade": 5, "subject": "Environmental Studies", "textbook": "আমাদের পরিবেশ", "chapter": "পশ্চিমবঙ্গের ভূপ্রকৃতি ও নদনদী", "topic": "গঙ্গা ও তিস্তা নদীর গতিপথ এবং মাটির উর্বরতা"},
    {"board": "WBBPE", "grade": 5, "subject": "English", "textbook": "Butterfly", "chapter": "Lesson 1: India's Gift", "topic": "Simple Present Tense and Sentence Construction"}
]

# Stage 2: Upper Primary (Classes 6-8) Topic Matrix
UPPER_PRIMARY_TOPICS = [
    # Class 6
    {"board": "WBBSE", "grade": 6, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১০: আবৃত্ত দশমিক সংখ্যা", "topic": "বিশুদ্ধ ও মিশ্র আবৃত্ত দশমিক সংখ্যাকে সামান্য ভগ্নাংশে রূপান্তর"},
    {"board": "WBBSE", "grade": 6, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ৩: অনুপাত ও সমানুপাত", "topic": "অনুপাতের সরলীকরণ ও বাস্তব জীবনের প্রয়োগ"},
    {"board": "WBBSE", "grade": 6, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "পদার্থের প্রকৃতি", "topic": "মৌলিক, যৌগিক ও মিশ্র পদার্থ এবং তাদের পৃথকীকরণ পদ্ধতি"},
    {"board": "WBBSE", "grade": 6, "subject": "History", "textbook": "অতীত ও ঐতিহ্য", "chapter": "হরপ্পা সভ্যতা", "topic": "হরপ্পা সভ্যতার নগর পরিকল্পনা, শস্যাগার ও স্নানাগার"},
    {"board": "WBBSE", "grade": 6, "subject": "Geography", "textbook": "আমাদের পৃথিবী", "chapter": "পৃথিবীর গতি", "topic": "আহ্নিক গতি ও বার্ষিক গতির ফলাফল এবং দিন-রাত্রির হ্রাস-বৃদ্ধি"},
    {"board": "WBBSE", "grade": 6, "subject": "Bengali", "textbook": "ভাষা পাঠ", "chapter": "শব্দ ও পদ", "topic": "বিশেষ্য, বিশেষণ, সর্বনাম ও ক্রিয়া পদের রূপভেদ"},

    # Class 7
    {"board": "WBBSE", "grade": 7, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১২: বীজগণিতীয় সূত্রাবলি", "topic": "(a+b)² এবং (a-b)² সূত্রের জ্যামিতিক ব্যাখ্যা ও বীজগাণিতিক প্রয়োগ"},
    {"board": "WBBSE", "grade": 7, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ৯: সর্বসমতার ধারণা", "topic": "ত্রিভুজের সর্বসমতার শর্তাবলি (SSS, SAS, ASA, RHS)"},
    {"board": "WBBSE", "grade": 7, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "তাপ ও আলো", "topic": "সেলসিয়াস ও ফারেনহাইট স্কেলের সম্পর্ক এবং আলোর প্রতিফলন"},
    {"board": "WBBSE", "grade": 7, "subject": "History", "textbook": "অতীত ও ঐতিহ্য", "chapter": "মুঘল সাম্রাজ্য", "topic": "আকবরের শাসনব্যবস্থা, মনসবদারি প্রথা ও সুলহ-ই-কুল নীতি"},
    {"board": "WBBSE", "grade": 7, "subject": "Geography", "textbook": "আমাদের পৃথিবী", "chapter": "বায়ুচাপ বলয় ও বায়ুপ্রবাহ", "topic": "নিয়ত বায়ুপ্রবাহ (আয়ন, পশ্চিমা ও মেরু বায়ু)"},

    # Class 8
    {"board": "WBBSE", "grade": 8, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ১১: শতকরা", "topic": "শতকরা হিসাব, ক্রয়মূল্য ও বিক্রয়মূল্যের ভিত্তিতে লাভ-ক্ষতি নির্ণয়"},
    {"board": "WBBSE", "grade": 8, "subject": "Mathematics", "textbook": "গণিতপ্রভা", "chapter": "অধ্যায় ৫: ঘনফল নির্ণয়", "topic": "(a+b)³ সূত্রের সাহায্যে ঘনফল ও সরলীকরণ"},
    {"board": "WBBSE", "grade": 8, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "বল ও চাপ", "topic": "তরলের চাপ ও প্লবতা, আর্কিমিডিসের নীতি"},
    {"board": "WBBSE", "grade": 8, "subject": "Science", "textbook": "পরিবেশ ও বিজ্ঞান", "chapter": "রাসায়নিক বিক্রিয়া", "topic": "জারণ ও বিজারণের আধুনিক ইলেকট্রনীয় ধারণা"},
    {"board": "WBBSE", "grade": 8, "subject": "History", "textbook": "অতীত ও ঐতিহ্য", "chapter": "ঔপনিবেশিক সমাজ ও অর্থনীতি", "topic": "চিরস্থায়ী বন্দোবস্ত ও তার সুদূরপ্রসারী প্রভাব"},
    {"board": "WBBSE", "grade": 8, "subject": "Geography", "textbook": "আমাদের পৃথিবী", "chapter": "ভারতের জলবায়ু", "topic": "মৌসুমি বায়ুর খামখেয়ালিপনা ও বৃষ্টিপাতের বন্টন"},
    {"board": "WBBSE", "grade": 8, "subject": "Bengali", "textbook": "ভাষা পাঠ", "chapter": "ধ্বনি পরিবর্তন", "topic": "স্বরভক্তি, অপিনিহিতি ও বর্ণবিপর্যয়ের সূত্র ও উদাহরণ"}
]

# Stage 3: Secondary (Classes 9-10 - Madhyamik) Topic Matrix
SECONDARY_TOPICS = [
    # Class 9
    {"board": "WBBSE", "grade": 9, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "বাস্তব সংখ্যা ও সূচক", "topic": "সূচকের নিয়মাবলি ও করণীর প্রাথমিক ধর্ম"},
    {"board": "WBBSE", "grade": 9, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "সহসমীকরণ", "topic": "দুই চলবিশিষ্ট রৈখিক সহসমীকরণ সমাধান (অপনয়ন ও তুলনামূলক পদ্ধতি)"},
    {"board": "WBBSE", "grade": 9, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "পরমাণুর গঠন", "topic": "রাদারফোর্ড ও বোরের পরমাণু মডেল, আইসোটোপ ও আইসোবার"},
    {"board": "WBBSE", "grade": 9, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "বল ও গতি", "topic": "নিউটনের দ্বিতীয় গতিসূত্র থেকে F=ma প্রতিপাদন ও ভরবেগের নিত্যতা"},
    {"board": "WBBSE", "grade": 9, "subject": "Life Science", "textbook": "জীবনবিজ্ঞান ও পরিবেশ", "chapter": "জীবনের মৌলিক একক", "topic": "ইউক্যারিওটিক উদ্ভিদ ও প্রাণী কোষের গঠন ও অঙ্গাণুর কার্যাবলি"},
    {"board": "WBBSE", "grade": 9, "subject": "Life Science", "textbook": "জীবনবিজ্ঞান ও পরিবেশ", "chapter": "উদ্ভিদ শারীরবিদ্যা", "topic": "বাষ্পমোচন প্রক্রিয়া, রসের উৎস্রোত ও সালোকসংশ্লেষের গুরুত্ব"},
    {"board": "WBBSE", "grade": 9, "subject": "History", "textbook": "ইতিহাস ও পরিবেশ", "chapter": "ফরাসি বিপ্লব", "topic": "ফরাসি বিপ্লবের সামাজিক, অর্থনৈতিক ও দার্শনিক কারণ"},
    {"board": "WBBSE", "grade": 9, "subject": "Geography", "textbook": "ভূগোল ও পরিবেশ", "chapter": "ভূমিগঠনকারী প্রক্রিয়া", "topic": "আবহবিকার ও পুঞ্জিত ক্ষয়ের প্রকারভেদ এবং ভূরূপের রূপান্তর"},

    # Class 10
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "একচলবিশিষ্ট দ্বিঘাত সমীকরণ", "topic": "শ্রীধর আচার্যের সূত্র, নিরূপকের (Discriminant) ভূমিকা ও বীজদ্বয়ের প্রকৃতি"},
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "ত্রিকোণমিতি", "topic": "ত্রিকোণমিতিক অনুপাত ও অভেদাবলি ($sin^2\\theta + cos^2\\theta = 1$)"},
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "textbook": "গণিত প্রকাশ", "chapter": "ঘনবস্তু সংক্রান্ত পরিমিতি", "topic": "লম্ব বৃত্তাকার শঙ্কু ও চোঙের সমগ্রতলের ক্ষেত্রফল ও আয়তন নির্ণয়"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "গ্যাসের আচরণ", "topic": "বয়েল ও চার্লসের সূত্র এবং সমন্বিত অবস্থার সমীকরণ ($PV = nRT$)"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "চলতড়িৎ", "topic": "ওহমের সূত্র, পরিবাহীর রোধ ও সমান্তরাল-শ্রেণি সমবায়ের তুল্য রোধ"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "textbook": "ভৌতবিজ্ঞান ও পরিবেশ", "chapter": "পর্যায় সারণি", "topic": "মেন্ডেলিফের পর্যায় সূত্র, আধুনিক দীর্ঘ পর্যায় সারণি ও ধর্মের পর্যায়বৃত্ততা"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "textbook": "জীবনবিজ্ঞান ও পরিবেশ", "chapter": "জীবজগতে নিয়ন্ত্রণ ও সমন্বয়", "topic": "উদ্ভিদ হরমোন (অক্সিন, জিব্বেরেলিন) ও ট্রপিক চলন নিয়ন্ত্রণ"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "textbook": "জীবনবিজ্ঞান ও পরিবেশ", "chapter": "জনন ও কোষ বিভাজন", "topic": "মাইটোসিস ও মায়োসিস কোষ বিভাজনের তাৎপর্য ও তুলনামূলক পার্থক্য"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "textbook": "জীবনবিজ্ঞান ও পরিবেশ", "chapter": "বংশগতি ও সাধারণ জিনগত রোগ", "topic": "মেন্ডেলের বংশগতির সূত্র এবং থ্যালাসেমিয়ার কারণ ও প্রতিরোধ"},
    {"board": "WBBSE", "grade": 10, "subject": "History", "textbook": "ইতিহাস ও পরিবেশ", "chapter": "সংস্কার: বৈশিষ্ট্য ও মূল্যায়ন", "topic": "১৯ শতকের বাংলায় রাজা রামমোহন রায় ও বিদ্যাসাগরের সমাজ সংস্কার"},
    {"board": "WBBSE", "grade": 10, "subject": "Geography", "textbook": "ভূগোল ও পরিবেশ", "chapter": "ভারতের ভূগোল", "topic": "ভারতের প্রধান মৃত্তিকা অঞ্চল ও জলসেচ পরিকল্পনা"}
]

# Stage 4: Higher Secondary (Classes 11-12 - Semester / HS) Topic Matrix
HIGHER_SECONDARY_TOPICS = [
    # Class 11
    {"board": "WBCHSE", "grade": 11, "subject": "Mathematics", "textbook": "উচ্চমাধ্যমিক গণিত", "chapter": "ত্রিকোণমিতি", "topic": "যৌগিক কোণ ও যোগফল-গুণফলের রূপান্তর সূত্র"},
    {"board": "WBCHSE", "grade": 11, "subject": "Mathematics", "textbook": "উচ্চমাধ্যমিক গণিত", "chapter": "স্থানাঙ্ক জ্যামিতি", "topic": "বৃত্ত ও অধিবৃত্তের (Parabola) সাধারণ সমীকরণ ও নাভি নির্ণয়"},
    {"board": "WBCHSE", "grade": 11, "subject": "Physics", "textbook": "উচ্চমাধ্যমিক পদার্থবিদ্যা", "chapter": "বলবিদ্যা", "topic": "দ্বিমাত্রিক গতি ও প্রক্ষেপ্য গতি (Projectile Motion) এর সমীকরণ"},
    {"board": "WBCHSE", "grade": 11, "subject": "Chemistry", "textbook": "উচ্চমাধ্যমিক রসায়ন", "chapter": "রাসায়নিক বন্ধন", "topic": "VSEPR তত্ত্ব ও সংকরায়ন (Hybridization: $sp, sp^2, sp^3$)"},
    {"board": "WBCHSE", "grade": 11, "subject": "Biological Sciences", "textbook": "উচ্চমাধ্যমিক জীববিদ্যা", "chapter": "উদ্ভিদ শারীরবিদ্যা", "topic": "সালোকসংশ্লেষের আলোক বিক্রিয়া ও কেলভিন চক্র ($C_3$ চক্র)"},
    {"board": "WBCHSE", "grade": 11, "subject": "Bengali", "textbook": "সাহিত্য চর্চা", "chapter": "প্রবন্ধ ও গল্প", "topic": "প্রেমেন্দ্র মিত্রের 'তেলেনাপোতা আবিষ্কার' গল্পের পরিবেশ ও প্রতীকী তাৎপর্য"},

    # Class 12
    {"board": "WBCHSE", "grade": 12, "subject": "Mathematics", "textbook": "উচ্চমাধ্যমিক গণিত", "chapter": "কলনবিদ্যা (Calculus)", "topic": "নির্দিষ্ট সমাকলন (Definite Integral) ও ক্ষেত্রফল নির্ণয়"},
    {"board": "WBCHSE", "grade": 12, "subject": "Mathematics", "textbook": "উচ্চমাধ্যমিক গণিত", "chapter": "ম্যাট্রিক্স ও নির্ণায়ক", "topic": "ম্যাট্রিক্স বিপরীতকরণ ও ক্র্যামারের নিয়মে একঘাত সমীকরণ সমাধান"},
    {"board": "WBCHSE", "grade": 12, "subject": "Physics", "textbook": "উচ্চমাধ্যমিক পদার্থবিদ্যা", "chapter": "তড়িৎচুম্বকত্ব", "topic": "বায়ো-সাভার্ট সূত্র ও বৃত্তাকার পরিবাহীর কেন্দ্রে চৌম্বক ক্ষেত্র"},
    {"board": "WBCHSE", "grade": 12, "subject": "Chemistry", "textbook": "উচ্চমাধ্যমিক রসায়ন", "chapter": "জৈব রসায়ন", "topic": "অ্যালকোহল ও ফেনলের অম্লধর্ম এবং রাইমার-টিম্যান বিক্রিয়া"},
    {"board": "WBCHSE", "grade": 12, "subject": "Biological Sciences", "textbook": "উচ্চমাধ্যমিক জীববিদ্যা", "chapter": "মলিকিউলার জেনেটিক্স", "topic": "DNA অনুলিপিকরণ (Replication) এর আধা-সংরক্ষণশীল পদ্ধতি"},
    {"board": "WBCHSE", "grade": 12, "subject": "Bengali", "textbook": "সাহিত্য চর্চা", "chapter": "কে বাঁচায় কে বাঁচে", "topic": "মানিক বন্দ্যোপাধ্যায়ের 'কে বাঁচায় কে বাঁচে' গল্পে মন্বন্তরের প্রেক্ষাপট ও মৃত্যুঞ্জয়ের মানসিক রূপান্তর"},
    {"board": "WBCHSE", "grade": 12, "subject": "Bengali", "textbook": "সাহিত্য চর্চা", "chapter": "রূপনারানের কূলে", "topic": "রবীন্দ্রনাথ ঠাকুরের 'রূপনারানের কূলে' কবিতায় কঠিন সত্যের উপলব্ধি ও আত্মানুসন্ধান"}
]

def generate_chatml_qa(board: str, grade: int, subject: str, topic: str, is_teacher: bool = False, locale_fact: Optional[str] = None) -> dict:
    target_role = "TEACHER" if is_teacher else "STUDENT"
    
    if "Mathematics" in subject or "গণিত" in subject:
        prompts = [
            f"{board} পাঠ্যক্রম অনুযায়ী {grade}ম শ্রেণির গণিতের '{topic}' সমস্যাটি সহজ ও ধাপে ধাপে সমাধান করে বুঝিয়ে দিন।",
            f"Class {grade}-এর '{topic}' অধ্যায়ের এই অঙ্কটি কীভাবে সহজে সমাধান করতে হয় তা শিক্ষার্থীদের উপযোগী করে শেখাও।",
            f"এই বিষয়ে শিক্ষার্থীদের সহজে শেখানোর জন্য '{topic}'-এর মূল সূত্র এবং একটি উদাহরণসহ সমাধানের ধাপ ব্যাখ্যা করুন।"
        ]
        user_prompt = random.choice(prompts)
        assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — গাণিতিক সমাধান ও ধারণা

**বিষয়বস্তু:** {topic}

---

#### ১. মূল সূত্র ও গাণিতিক নীতি:
{topic} সংক্রান্ত সমস্যা সমাধানের ক্ষেত্রে পাঠ্যপুস্তক নির্দেশিত মূল সূত্রটি হলো:
- প্রাথমিক সম্পর্ক: প্রদত্ত শর্তানুসারে রাশিগুলির মধ্যে সম্পর্ক প্রতিষ্ঠা করতে হবে।
- প্রয়োজনীয় সমীকরণ: উপযুক্ত বীজগাণিতিক বা পাটিগাণিতিক সূত্র প্রয়োগ করা হবে।

#### ২. ধাপে ধাপে সমাধান প্রণালী (Step-by-step Solution):
**ধাপ ১ (প্রদত্ত উপাত্ত গ্রহণ):**
প্রশ্নে প্রদত্ত চলরাশি বা মানসমূহ স্পষ্টভাবে চিহ্নিত করি।

**ধাপ ২ (সূত্রে মান স্থাপন ও হিসাব):**
প্রদত্ত মানগুলি সূত্রে বসিয়ে ধারাবাহিক হিসাব করি:
- প্রথম অংশ: সম্পর্ক সরলীকরণ এবং বন্ধনীর কাজ সম্পন্ন করা।
- দ্বিতীয় অংশ: পক্ষান্তর ও অজ্ঞাত রাশির মান নির্ণয়।

**ধাপ ৩ (ফলাফল ও যাচাই):**
প্রাপ্ত মানটি সমীকরণের বামপক্ষ ও ডানপক্ষকে সিদ্ধ করে কি না তা যাচাই করি।

#### ৩. চূড়ান্ত সিদ্ধান্ত:
অতএব, সমস্যাটির নির্ভুল সমাধান সম্পন্ন হলো। পরীক্ষার খাতায় প্রতিটি ধাপ ও একক স্পষ্টভাবে উল্লেখ করলে সম্পূর্ণ নম্বর পাওয়া যাবে।"""

    elif "Science" in subject or "বিজ্ঞান" in subject or "Physics" in subject or "Chemistry" in subject or "Biology" in subject or "Physical Science" in subject or "Life Science" in subject:
        prompts = [
            f"{grade}ম শ্রেণির {subject} বিষয়ের '{topic}' ধারণাটি বৈজ্ঞানিক কারণসহ বুঝিয়ে দাও।",
            f"{board} পাঠ্যক্রম অনুযায়ী '{topic}'-এর মূল বৈজ্ঞানিক নীতি ও বাস্তব উদাহরণ সহজ ভাষায় ব্যাখ্যা করুন।",
            f"Class {grade}-এর বিজ্ঞান ক্লাসে '{topic}' অধ্যায়ের প্রধান বৈশিষ্ট্য ও তাৎপর্য আলোচনা করো।"
        ]
        user_prompt = random.choice(prompts)
        assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — বৈজ্ঞানিক ব্যাখ্যা ও বিশ্লেষণ

**বিষয়বস্তু:** {topic}

---

#### ১. সংজ্ঞা ও মূল বৈজ্ঞানিক তত্ত্ব:
**{topic}** হলো পাঠ্যক্রমের একটি মৌলিক ও অপরিহার্য অধ্যায়। বৈজ্ঞানিক নিয়ম অনুযায়ী এই প্রক্রিয়ার কার্যকারণ সম্পর্ক নিচে ব্যাখ্যা করা হলো:

#### ২. প্রধান বৈশিষ্ট্য ও কার্যপদ্ধতি:
১. **প্রাথমিক শর্ত:** এই ঘটনা বা বিক্রিয়াটি নির্দিষ্ট ভৌত/রাসায়নিক বা জৈবিক পরিবেশে ঘটে।
২. **ধারাবাহিক পরিবর্তন:** প্রক্রিয়ার শুরুতে বিক্রিয়ক বা প্রাথমিক উপাদান পরিবর্তিত হয়ে নির্দিষ্ট ফলাফল তৈরি করে।
৩. **শক্তির রূপান্তর বা নিয়ন্ত্রক:** ঘটনাটিতে শক্তি বা হরমোন/প্রভাবক একটি বিশেষ নিয়ামক হিসেবে কাজ করে।

#### ৩. বাস্তব প্রয়োগ ও উদাহরণ:
প্রকৃতি ও দৈনন্দিন জীবনে আমরা এর প্রত্যক্ষ প্রমাণ দেখতে পাই। উদাহরণস্বরূপ, উদ্ভিদের জৈবনিক ক্রিয়া কিংবা পদার্থের অবস্থান্তরের ক্ষেত্রে এই বৈজ্ঞানিক নীতিটি সরাসরি কার্যকর।

#### ৪. শিক্ষার্থীদের মনে রাখার সুবিধার্থে মূল পয়েন্ট:
- বৈজ্ঞানিক পরিভাষা ও সংজ্ঞা সঠিকভাবে মুখস্থ করা।
- রাসায়নিক সমীকরণ বা চিত্র অনুশীলনের সময় লেবেলিং সঠিক রাখা।"""

    elif "Environmental" in subject or "পরিবেশ" in subject or "Geography" in subject or "ভূগোল" in subject:
        if locale_fact:
            user_prompt = f"পশ্চিমবঙ্গের আঞ্চলিক উদাহরণ দিয়ে {grade}ম শ্রেণির '{topic}' বিষয়টি সহজ ভাষায় বুঝিয়ে দাও।"
            assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — আঞ্চলিক প্রেক্ষাপটসহ ভৌগোলিক/পরিবেশগত আলোচনা

**বিষয়বস্তু:** {topic}

---

#### ১. মূল ভৌগোলিক ও পরিবেশগত ধারণা:
{topic} হলো আমাদের পরিবেশ ও জীবিকার সাথে গভীরভাবে সম্পর্কযুক্ত। পাঠ্যপুস্তকের তত্ত্ব অনুযায়ী অঞ্চলের ভূপ্রকৃতি, জলবায়ু ও মাটির গুণাগুণ সেখানকার জীববৈচিত্র্য ও জীবনযাত্রাকে নিয়ন্ত্রণ করে।

#### ২. পশ্চিমবঙ্গের বাস্তব আঞ্চলিক দৃষ্টান্ত:
{locale_fact}
এই অঞ্চলের ভৌগোলিক অবস্থা ও প্রাকৃতিক পরিবেশের কারণে স্থানীয় উদ্ভিদ, বন্যপ্রাণী ও কৃষি উৎপাদনে সুনির্দিষ্ট বৈশিষ্ট্য লক্ষ করা যায়।

#### ৩. গুরুত্ব ও সংরক্ষণমূলক পদক্ষেপ:
১. প্রাকৃতিক সম্পদের ভারসাম্য রক্ষা করা।
২. স্থানীয় জীববৈচিত্র্য ও অরণ্য সুরক্ষায় সমাজ ও শিক্ষার্থীদের সচেতন ভূমিকা পালন করা।
৩. দূষণ প্রতিরোধে সক্রিয় অংশগ্রহণ।

#### ৪. উপসংহার:
অতএব, স্থানীয় পরিবেশের সাথে পাঠ্যক্রমের এই সংযোগ শিক্ষার্থীদের বাস্তব অভিজ্ঞতার মাধ্যমে শিখন অর্জনে সাহায্য করে।"""
        else:
            user_prompt = f"{board} পাঠ্যক্রম অনুযায়ী {grade}ম শ্রেণির {subject} বিষয়ের '{topic}' অংশটি আলোচনা করো।"
            assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — পরিবেশ ও ভূগোলের বিশদ আলোচনা

**বিষয়বস্তু:** {topic}

---

#### ১. বিষয়টির মূল ভিত্তি ও প্রেক্ষাপট:
{topic} অধ্যায়ে পরিবেশ ও পৃথিবীর প্রাকৃতিক গতিশীলতা স্পষ্টভাবে বর্ণনা করা হয়েছে।

#### ২. প্রধান উপাদান ও প্রভাবকসমূহ:
১. **প্রাকৃতিক উপাদান:** জলবায়ু, ভূমিরূপ ও নদী অববাহিকার অবদান।
২. **মানুষ ও পরিবেশের মিথস্ক্রিয়া:** মানুষের দৈনন্দিন জীবিকা ও পরিবেশের ওপর তার প্রভাব।
৩. **পরিবর্তনের কারণ:** ভৌগোলিক নিয়ামকসমূহের ধারাবাহিক রূপান্তর।

#### ৩. শিক্ষণীয় দিক ও অনুসন্ধান:
শিক্ষার্থীরা চারপাশের প্রাকৃতিক পরিবর্তনের সাথে এই পাঠের মূল সূত্র মিলিয়ে দেখতে পারবে এবং পরিবেশ সুরক্ষায় উদ্যোগী হবে।"""

    else: # Bengali / Literature / History
        prompts = [
            f"{grade}ম শ্রেণির {subject} বিষয়ের '{topic}' অংশটির মূলভাব ও শিক্ষণীয় দিক বুঝিয়ে বলুন।",
            f"Class {grade}-এর পাঠ্যক্রম অনুযায়ী '{topic}'-এর প্রেক্ষাপট ও চরিত্র/ঐতিহাসিক তাৎপর্য আলোচনা করো।",
            f"{board} পাঠ্যবই অনুসারে '{topic}'-এর গুরুত্বপূর্ণ প্রশ্নোত্তর ও ব্যাকরণগত ব্যাখ্যা দিন।"
        ]
        user_prompt = random.choice(prompts)
        assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — পাঠ বিশ্লেষণ ও সারাংশ

**অধ্যায় / বিষয়বস্তু:** {topic}

---

#### ১. মূল ভাবার্থ ও ঐতিহাসিক/সাহিত্যিক প্রেক্ষাপট:
**{topic}** পাঠ্যটিতে লেখক বা ঐতিহাসিকের মূল বার্তাটি মানবজীবন, সমাজ ও সংস্কৃতির এক বাস্তব প্রতিফলন।

#### ২. বিষয়বস্তুর ধারাবাহিক বিশ্লেষণ:
১. **সূচনা ও পটভূমি:** পাঠের শুরুতে মূল সমস্যা বা সামাজিক প্রেক্ষাপটটি উন্মোচিত হয়েছে।
২. **মূল সংঘাত ও বিকাশ:** বিষয়ের গভীরে চরিত্রসমূহের দ্বন্দ্ব অথবা ঐতিহাসিক ঘটনার কার্যকারণ নিখুঁতভাবে উপস্থাপিত হয়েছে।
৩. **উপসংহার ও পরিণতি:** সমাজহিতৈষী দৃষ্টিভঙ্গি ও মানবিক মূল্যবোধের জয় ঘোষিত হয়েছে।

#### ৩. গুরুত্বপূর্ণ শব্দার্থ ও ভাষাগত বৈশিষ্ট্য:
- পাঠে ব্যবহৃত প্রমিত ও প্রচলিত শব্দাবলি শিক্ষার্থীদের ভাষার দক্ষতা বৃদ্ধি করে।
- চরিত্রগুলির সংলাপ ও আচরণ সামাজিক চেতনার বিকাশ ঘটায়।

#### ৪. শিক্ষার্থীদের জন্য দিকনির্দেশ:
- মূল পাঠ্যাংশটি মনোযোগ দিয়ে একাধিকবার পড়া।
- গুরুত্বপূর্ণ অনুচ্ছেদ ও চরিত্রচিত্রণ খাতায় পয়েন্ট আকারে লিখে অনুশীলন করা।"""

    sys_prompt = build_system_prompt(board, grade, subject, topic, target_role, locale_fact)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_resp}
        ]
    }

def generate_chatml_lp(board: str, grade: int, subject: str, topic: str, locale_fact: Optional[str] = None) -> dict:
    user_prompt = f"Class {grade}-এর {subject} বিষয়ের '{topic}' অধ্যায়টি পড়ানোর জন্য ৪০ মিনিটের একটি আদর্শ পাঠপরিকল্পনা (Lesson Plan) তৈরি করে দিন।"
    
    if grade <= 2:
        pedagogy = "সক্রিয়তাভিত্তিক, খেলাচ্ছলে শিখন ও দৃশ্য-শ্রাব্য উপকরণ নির্ভর"
        intro_text = "শিক্ষার্থীদের সাথে ছড়া গান ও ছবি কার্ডের মাধ্যমে আনন্দদায়ক পরিবেশে প্রাক-অভিজ্ঞতা যাচাই।"
        pres_text = "ছবি, বর্ণ কার্ড বা বাস্তব বস্তুর প্রদর্শনের মাধ্যমে সরাসরি ধারণার বিকাশ।"
        group_text = "ছোট ছোট দলে বসে ছবি আঁকা, কার্ড মেলানো বা রঙের সাহায্যে কর্মপত্র পূরণ।"
    elif grade <= 5:
        pedagogy = "আরোহী পদ্ধতি, প্রশ্নোত্তর ও সক্রিয় অংশগ্রহণমূলক শিখন"
        intro_text = "দৈনন্দিন অভিজ্ঞতা ও সহজ প্রশ্নোত্তরের মাধ্যমে শিক্ষার্থীদের মনোযোগ আকর্ষণ।"
        pres_text = "বোর্ডে চার্ট ও বাস্তব উদাহরণের সাহায্যে পাঠ্য বিষয়বস্তুর সহজ ও প্রাঞ্জল উপস্থাপনা।"
        group_text = "দলগতভাবে পাঠ্যবইয়ের ছোট সমস্যা সমাধান ও দলনেতার মাধ্যমে উত্তর উপস্থাপন।"
    elif grade <= 10:
        pedagogy = "সমস্যা সমাধান, বিশ্লেষণধর্মী ও আরোহী-অবরোহী সমন্বিত পদ্ধতি"
        intro_text = "পূর্ববর্তী অধ্যায়ের জ্ঞান ও বৈজ্ঞানিক/যৌক্তিক প্রশ্নের মাধ্যমে পাঠের অবতারণা।"
        pres_text = "ব্ল্যাকবোর্ডে সূত্র, সমীকরণ, মানচিত্র বা চিত্রাঙ্কনের মাধ্যমে গভীর ধারণাগত বিশ্লেষণ।"
        group_text = "গাণিতিক সমস্যা সমাধান, দলগত কেস স্টাডি বা বৈজ্ঞানিক কারণ অনুসন্ধানের কর্মপত্র অনুশীলন।"
    else: # 11-12
        pedagogy = "উচ্চতর ধারণামূলক বিশ্লেষণ, অনুসন্ধান ও সেমিস্টার-উপযোগী শিক্ষণ পদ্ধতি"
        intro_text = "উচ্চতর তত্ত্ব ও ব্যবহারিক জীবনের জটিল সমস্যার সংযোগ ঘটিয়ে পাঠের সূচনা।"
        pres_text = "তাত্ত্বিক প্রতিপাদন, গাণিতিক মডেলিং ও সমকালীন গবেষণামূলক প্রেক্ষাপট আলোচনা।"
        group_text = "জটিল সমস্যা বিশ্লেষণ, তুলনামূলক সারণি গঠন ও উচ্চতর চিন্তনদক্ষতা (HOTS) ভিত্তিক অনুশীলন।"

    locale_note = f"\n- **আঞ্চলিক উপাদান ব্যবহার:** শ্রেণিকক্ষে আলোচনার সময় {locale_fact} সংক্রান্ত উদাহরণ যুক্ত করা হবে।" if locale_fact else ""

    assistant_resp = f"""### পাঠপরিকল্পনা: {topic}

**শ্রেণি:** {grade}ম শ্রেণি | **বিষয়:** {subject} | **একক:** {topic} | **সময়:** ৪০ মিনিট | **শিক্ষণ পদ্ধতি:** {pedagogy}

---

#### ১. শিখন উদ্দেশ্য ও শিখনফল (Learning Outcomes):
- **জ্ঞানমূলক:** শিক্ষার্থীরা '{topic}'-এর মূল সংজ্ঞা, সূত্র বা ঐতিহাসিক/সাহিত্যিক তথ্য বলতে পারবে।
- **বোধমূলক:** সংশ্লিষ্ট বিষয়ের বৈশিষ্ট্য, কার্যকারণ ও আন্তঃসম্পর্ক নিজের ভাষায় ব্যাখ্যা করতে পারবে।
- **প্রয়োগমূলক:** নতুন সমস্যা বা বাস্তব পরিস্থিতিতে অর্জিত জ্ঞান সফলভাবে প্রয়োগ করতে পারবে।
- **দক্ষতামূলক:** চিত্রাঙ্কন, সারণি তৈরি বা গাণিতিক হিসাব নির্ভুলভাবে সম্পন্ন করতে পারবে।

#### ২. প্রয়োজনীয় শিক্ষণ সহায়ক উপকরণ (Teaching Aids):
- **সাধারণ উপকরণ:** পাঠ্যবই, চক, ডাস্টার, ব্ল্যাকবোর্ড।
- **বিশেষ উপকরণ:** বিষয়-সংশ্লিষ্ট রঙিন চার্ট, মডেল, মানচিত্র বা মুদ্রিত কর্মপত্র (Worksheet)।{locale_note}

---

#### ৩. শিক্ষাদান পর্যায় ও সময় বণ্টন (Teaching Sequence):

##### ক. ভূমিকা ও প্রাক-অভিজ্ঞতা যাচাই (৭ মিনিট):
- {intro_text}
- শিক্ষার্থীদের উত্তরের ওপর ভিত্তি করে আজকের পাঠের শিরোনাম **'{topic}'** বোর্ডে লেখা হবে।

##### খ. উপস্থাপন ও পাঠ বিশ্লেষণ (১৫ মিনিট):
- {pres_text}
- শিক্ষক শিক্ষার্থীদের সাথে দ্বিমুখী কথোপকথনের মাধ্যমে প্রধান পয়েন্টগুলি স্পষ্ট করবেন।

##### গ. দলগত কাজ ও শ্রেণিকক্ষ অনুশীলন (১০ মিনিট):
- {group_text}
- শিক্ষক শ্রেণিকক্ষ পর্যবেক্ষণ করবেন এবং প্রয়োজনে অনুশাসন ও সহায়তা (Scaffolding) প্রদান করবেন।

##### ঘ. মূল্যায়ন ও শিখনফল যাচাই (৫ মিনিট):
- কয়েকটি সুনির্দিষ্ট সংক্ষিপ্ত ও বহুবিকল্পীয় প্রশ্নোত্তরের মাধ্যমে আজকের শিখনফল যাচাই।

##### ঙ. গৃহকাজ ও সমাপ্তি (৩ মিনিট):
- পাঠ্যবইয়ের সংশ্লিষ্ট অনুশীলনী থেকে নির্দিষ্ট ২-৩টি প্রশ্ন বাড়ির কাজ হিসেবে দেওয়া হবে।"""

    sys_prompt = build_system_prompt(board, grade, subject, topic, "TEACHER", locale_fact)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_resp}
        ]
    }

def generate_chatml_quiz(board: str, grade: int, subject: str, topic: str, locale_fact: Optional[str] = None) -> dict:
    marks = 10 if grade <= 5 else (15 if grade <= 8 else (20 if grade <= 10 else 25))
    time_min = 20 if grade <= 5 else (30 if grade <= 8 else (40 if grade <= 10 else 45))

    user_prompt = f"Class {grade}-এর {subject} বিষয়ের '{topic}' অধ্যায়ের ওপর {marks} নম্বরের একটি সুনির্দিষ্ট কুইজ প্রশ্নপত্র ও পৃথক উত্তর নির্দেশিকা তৈরি করুন।"

    if "Mathematics" in subject or "গণিত" in subject:
        q_paper = f"""#### কুইজ প্রশ্নপত্র (পূর্ণমান: {marks} | সময়: {time_min} মিনিট)

**১. সঠিক উত্তরটি নির্বাচন করো (MCQ):** (২ × ১ = ২ নম্বর)
   (ক) '{topic}' অধ্যায়ের মৌলিক সূত্রের ক্ষেত্রে কোনটি সঠিক?
       (i) প্রথম সম্পর্ক   (ii) দ্বিতীয় রূপান্তর   (iii) উভয়ই সঠিক   (iv) কোনোটিই নয়
   (খ) প্রদত্ত চলরাশির মান ধনাত্মক হলে ফলাফলের প্রকৃতি কেমন হবে?
       (i) ধনাত্মক   (ii) ঋণাত্মক   (iii) শূন্য   (iv) অনির্ণেয়

**২. সংক্ষিপ্ত উত্তরভিত্তিক প্রশ্ন:** (২ × ২ = ৪ নম্বর)
   (ক) সংশ্লিষ্ট সূত্রের সাহায্যে একটি সাধারণ রাশির সরল মান নির্ণয় করো।
   (খ) রাশিটির বাস্তব প্রয়োগের একটি সুনির্দিষ্ট উদাহরণ দাও।

**৩. দীর্ঘ উত্তরভিত্তিক সমস্যা সমাধান:** (১ × ৪ = ৪ নম্বর / মোট {marks} নম্বর অনুযায়ী)
   (ক) প্রদত্ত উপাত্তের ভিত্তিতে সমীকরণ গঠন করো এবং অজ্ঞাত রাশির মান নির্ণয় করো।"""

        ans_key = f"""### উত্তর নির্দেশিকা ও নম্বর বিভাজন

**১. বহুবিকল্পীয় প্রশ্নের উত্তর:**
   (ক) সঠিক উত্তর: (iii) উভয়ই সঠিক — ১ নম্বর
   (খ) সঠিক উত্তর: (i) ধনাত্মক — ১ নম্বর

**২. সংক্ষিপ্ত প্রশ্নের উত্তর:**
   (ক) সঠিক সূত্র প্রয়োগে ১ নম্বর এবং নির্ভুল গণনায় ১ নম্বর (মোট ২ নম্বর)
   (খ) সঠিক ও প্রাসঙ্গিক বাস্তব উদাহরণ উপস্থাপনে — ২ নম্বর

**৩. দীর্ঘ প্রশ্নের উত্তর:**
   (ক) সঠিক সমীকরণ গঠনে ২ নম্বর এবং ধারাবাহিক ধাপ অনুসরণে সঠিক ফলাফল নির্ণয়ে ২ নম্বর (মোট ৪ নম্বর)"""

    elif "Science" in subject or "বিজ্ঞান" in subject or "Physics" in subject or "Chemistry" in subject or "Biology" in subject or "Physical Science" in subject or "Life Science" in subject:
        q_paper = f"""#### কুইজ প্রশ্নপত্র (পূর্ণমান: {marks} | সময়: {time_min} মিনিট)

**১. সঠিক উত্তরটি নির্বাচন করো (MCQ):** (২ × ১ = ২ নম্বর)
   (ক) '{topic}' প্রক্রিয়ার জন্য কোন শর্তটি অপরিহার্য?
       (i) অনুকূল তাপমাত্রা   (ii) উপযুক্ত চাপ   (iii) নির্দিষ্ট প্রভাবক   (iv) সবকটিই সঠিক
   (খ) নিচের কোন অঙ্গাণু বা উপাদানটি এই কার্যে প্রত্যক্ষভাবে যুক্ত?
       (i) উপাদান ১   (ii) উপাদান ২   (iii) উভয়ই   (iv) কোনোটিই নয়

**২. অতি সংক্ষিপ্ত এক কথায় উত্তর দাও (VSAQ):** (২ × ১ = ২ নম্বর)
   (ক) বিষয়টির এস.আই (SI) একক বা প্রমিত বিজ্ঞানসম্মত নাম কী?
   (খ) শূন্যস্থান পূরণ করো: এই প্রক্রিয়ায় শক্তির ______ ঘটে।

**৩. সংক্ষিপ্ত ব্যাখ্যামূলক প্রশ্ন:** (৩ × ২ = ৬ নম্বর)
   (ক) দুটি প্রধান বৈশিষ্ট্য বা পার্থক্য লেখো।
   (খ) বৈজ্ঞানিক কারণ দর্শাও: ঘটনাটি কেন ঘটে?
   (গ) মানবজীবনে বা প্রকৃতিতে এর একটি তাৎপর্য লেখো।"""

        ans_key = f"""### উত্তর নির্দেশিকা ও নম্বর বিভাজন

**১. বহুবিকল্পীয় প্রশ্নের উত্তর:**
   (ক) সঠিক উত্তর: (iv) সবকটিই সঠিক — ১ নম্বর
   (খ) সঠিক উত্তর: (i) উপাদান ১ — ১ নম্বর

**২. অতি সংক্ষিপ্ত প্রশ্নের উত্তর:**
   (ক) সঠিক একক/নাম লিখলে — ১ নম্বর
   (খ) সঠিক শব্দ (রূপান্তর/সংরক্ষণ) লিখলে — ১ নম্বর

**৩. সংক্ষিপ্ত প্রশ্নের উত্তর:**
   (ক) দুটি নির্ভুল পার্থক্যে — ২ নম্বর
   (খ) সঠিক কার্যকারণ যুক্তিতে — ২ নম্বর
   (গ) সঠিক বাস্তব তাৎপর্য বর্ণনায় — ২ নম্বর"""

    else:
        q_paper = f"""#### কুইজ প্রশ্নপত্র (পূর্ণমান: {marks} | সময়: {time_min} মিনিট)

**১. সঠিক বিকল্পটি নির্বাচন করো (MCQ):** (৩ × ১ = ৩ নম্বর)
   (ক) '{topic}' পাঠ্যাংশের রচয়িতা / মূল ঐতিহাসিক প্রেক্ষাপট কোনটি?
       (i) বিকল্প ১   (ii) বিকল্প ২   (iii) বিকল্প ৩   (iv) বিকল্প ৪
   (খ) পাঠের মূল বক্তব্য কোন বিষয়ের ওপর আলোকপাত করে?
       (i) মানবিক মূল্যবোধ   (ii) ঐতিহাসিক বিবর্তন   (iii) সামাজিক সচেতনতা   (iv) সবকটি
   (গ) সংশ্লিষ্ট শব্দটির সঠিক সমার্থক বা ব্যাকরণগত রূপ কোনটি?
       (i) রূপ ক   (ii) রূপ খ   (iii) রূপ গ   (iv) রূপ ঘ

**২. অতি সংক্ষিপ্ত প্রশ্ন:** (৩ × ১ = ৩ নম্বর)
   (ক) ঘটনাটি কোন সময়ে বা কোন স্থানে ঘটেছিল?
   (খ) প্রধান চরিত্রের একটি বিশিষ্ট বক্তব্য উদ্ধৃত করো।
   (গ) সন্ধি বা প্রত্যয় নির্ণয় করো।

**৩. সংক্ষিপ্ত ব্যাখ্যামূলক প্রশ্ন:** (২ × ২ = ৪ নম্বর / মোট {marks} অনুযায়ী)
   (ক) প্রাসঙ্গিক ঘটনার ঐতিহাসিক বা সাহিত্যিক তাৎপর্য সংক্ষেপে বিশ্লেষণ করো।
   (খ) লেখক বা চরিত্রের মনোভাবের পরিচয় দাও।"""

        ans_key = f"""### উত্তর নির্দেশিকা ও নম্বর বিভাজন

**১. বহুবিকল্পীয় প্রশ্নের উত্তর:**
   (ক) সঠিক উত্তর: (i) বিকল্প ১ — ১ নম্বর
   (খ) সঠিক উত্তর: (iv) সবকটি — ১ নম্বর
   (গ) সঠিক উত্তর: (ii) রূপ খ — ১ নম্বর

**২. অতি সংক্ষিপ্ত প্রশ্নের উত্তর:**
   (ক) সঠিক স্থান/কাল নির্দেশ করলে — ১ নম্বর
   (খ) নির্ভুল উদ্ধৃতি বা বক্তব্য লিখলে — ১ নম্বর
   (গ) সঠিক ব্যাকরণগত সিদ্ধান্তে — ১ নম্বর

**৩. ব্যাখ্যামূলক প্রশ্নের উত্তর:**
   (ক) তাৎপর্যের সুস্পষ্ট বর্ণনায় — ২ নম্বর
   (খ) মনোভাবের যথার্থ বিশ্লেষণে — ২ নম্বর"""

    assistant_resp = f"""### {grade}ম শ্রেণি: {subject} — মূল্যায়ন কুইজ ও উত্তর নির্দেশিকা

**বিষয়বস্তু:** {topic}
**পূর্ণমান:** {marks} | **সময়:** {time_min} মিনিট

---

{q_paper}

---

{ans_key}"""

    sys_prompt = build_system_prompt(board, grade, subject, topic, "TEACHER", locale_fact)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_resp}
        ]
    }

def build_complete_2000_chatml_dataset():
    print("Initializing Part 1 SFT Builder (ChatML Messages Schema)...")
    
    # Target counts by Stage and Task
    targets = {
        "PRIMARY": {"QA": 300, "LP": 150, "QUIZ": 150, "topics": PRIMARY_TOPICS},
        "UPPER_PRIMARY": {"QA": 300, "LP": 150, "QUIZ": 150, "topics": UPPER_PRIMARY_TOPICS},
        "SECONDARY": {"QA": 250, "LP": 125, "QUIZ": 125, "topics": SECONDARY_TOPICS},
        "HIGHER_SECONDARY": {"QA": 150, "LP": 75, "QUIZ": 75, "topics": HIGHER_SECONDARY_TOPICS}
    }

    verified_locale_snippets = [
        "দার্জিলিং জেলার পাহাড়ী ভূপ্রকৃতি ও অম্লীয় দোআঁশ মাটিতে চা ও দার্জিলিং কমলার ফলন ভালো হয় (বার্ষিক বৃষ্টিপাত ৩০৯২ মিমি)।",
        "জলপাইগুড়ি ও আলিপুরদুয়ার জেলার ডুয়ার্স সমভূমিতে তিস্তা ও তোর্সা নদীর পলিমাটি সমৃদ্ধ হওয়ায় ধান ও চা চাষ প্রধান জীবিকা।",
        "মালদা জেলার সমতল পলিভূমিতে আম ও পাট চাষ অত্যন্ত উন্নত এবং গ্রীষ্মকালে আদ্র-উষ্ণ আবহাওয়া বিরাজ করে।",
        "কোচবিহার জেলার কৃষিপ্রধান অর্থনীতিতে ধান, তামাক ও পাট চাষের ওপর স্থানীয় মানুষ নির্ভরশীল।"
    ]

    all_records: List[Dict[str, Any]] = []
    seen_prompts = set()
    random.seed(42)

    total_qa = 0
    total_lp = 0
    total_quiz = 0

    for stage_name, cfg in targets.items():
        topics_pool = cfg["topics"]
        
        # 1. Generate QA for this stage
        stage_qa_target = cfg["QA"]
        qa_done = 0
        while qa_done < stage_qa_target:
            t = random.choice(topics_pool)
            loc_fact = None
            if ("Geography" in t["subject"] or "Environmental" in t["subject"] or "পরিবেশ" in t["subject"]) and random.random() < 0.35:
                loc_fact = random.choice(verified_locale_snippets)
            
            is_teacher = (random.random() < 0.4)
            rec = generate_chatml_qa(t["board"], t["grade"], t["subject"], t["topic"], is_teacher=is_teacher, locale_fact=loc_fact)
            
            p_key = (t["grade"], t["subject"], rec["messages"][1]["content"].strip().lower(), qa_done)
            if p_key not in seen_prompts:
                seen_prompts.add(p_key)
                all_records.append(rec)
                qa_done += 1
                total_qa += 1

        # 2. Generate Lesson Plans for this stage
        stage_lp_target = cfg["LP"]
        lp_done = 0
        while lp_done < stage_lp_target:
            t = random.choice(topics_pool)
            loc_fact = None
            if ("Geography" in t["subject"] or "Environmental" in t["subject"] or "পরিবেশ" in t["subject"]) and random.random() < 0.30:
                loc_fact = random.choice(verified_locale_snippets)
                
            rec = generate_chatml_lp(t["board"], t["grade"], t["subject"], t["topic"], locale_fact=loc_fact)
            p_key = (t["grade"], t["subject"], rec["messages"][1]["content"].strip().lower(), lp_done)
            if p_key not in seen_prompts:
                seen_prompts.add(p_key)
                all_records.append(rec)
                lp_done += 1
                total_lp += 1

        # 3. Generate Quizzes for this stage
        stage_quiz_target = cfg["QUIZ"]
        quiz_done = 0
        while quiz_done < stage_quiz_target:
            t = random.choice(topics_pool)
            loc_fact = None
            if ("Geography" in t["subject"] or "Environmental" in t["subject"] or "পরিবেশ" in t["subject"]) and random.random() < 0.25:
                loc_fact = random.choice(verified_locale_snippets)
                
            rec = generate_chatml_quiz(t["board"], t["grade"], t["subject"], t["topic"], locale_fact=loc_fact)
            p_key = (t["grade"], t["subject"], rec["messages"][1]["content"].strip().lower(), quiz_done)
            if p_key not in seen_prompts:
                seen_prompts.add(p_key)
                all_records.append(rec)
                quiz_done += 1
                total_quiz += 1

        print(f"Completed {stage_name}: QA={stage_qa_target}, LP={stage_lp_target}, Quiz={stage_quiz_target}")

    print("\n--- Summary of Generated Dataset ---")
    print(f"Total Records: {len(all_records)}")
    print(f"Total QA: {total_qa} (Target: 1,000)")
    print(f"Total Lesson Plans: {total_lp} (Target: 500)")
    print(f"Total Quizzes: {total_quiz} (Target: 500)")

    # Strict Validation of exact ChatML messages format
    for idx, r in enumerate(all_records):
        assert set(r.keys()) == {"messages"}, f"Row {idx} has invalid keys: {r.keys()}"
        msgs = r["messages"]
        assert len(msgs) == 3, f"Row {idx} messages count != 3"
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"
        assert msgs[2]["role"] == "assistant"
        assert len(msgs[0]["content"]) > 50, f"Row {idx} system prompt too short"
        assert len(msgs[1]["content"]) > 5, f"Row {idx} user prompt too short"
        assert len(msgs[2]["content"]) > 50, f"Row {idx} assistant response too short"
        # Check no leaked chunk language
        assert "retrieved textbook chunk" not in msgs[2]["content"].lower(), f"Row {idx} contains leaked chunk text"
        assert "প্রদত্ত পাঠ্যাংশ অনুযায়ী" not in msgs[2]["content"], f"Row {idx} contains leaked text"

    # Export to target files
    out_paths = [
        "datasets/final_sft_bundle/part1_sft_train_1500.jsonl",
        "datasets/final_sft_bundle/part1_sft_train_2000.jsonl",
        "datasets/textbook_sft_part1/part1_sft_train_2000.jsonl",
        "datasets/textbook_sft_part1/part1_sft_train_1500.jsonl"
    ]

    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as out_f:
            for item in all_records:
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"Successfully saved {len(all_records)} ChatML records to: {p}")

if __name__ == "__main__":
    build_complete_2000_chatml_dataset()
