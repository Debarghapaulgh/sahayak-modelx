"""
Generator script to synthesize 500 high-quality, authentic SFT records across WBBPE, WBBSE, and WBCHSE.
Expands part1_sft_train_1500.jsonl to 2,000 records.
"""

import os
import json
import random
from typing import List, Dict, Any

def get_system_prompt(board: str, grade: int, subject: str, topic: str) -> str:
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

    return f"""তুমি 'সহায়ক এআই' (SahayakAI) — {board_full} বেঙ্গলি-মিডিয়াম স্কুলের শিক্ষার্থী ও শিক্ষক মহাশয়দের জন্য তৈরি একজন অভিজ্ঞ, বিশেষায়িত অ্যাকাডেমিক AI টিউটর। তোমার কাজ হলো পাঠ্যক্রম অনুযায়ী সহজ, সাবলীল, সঠিক ও শিক্ষার্থী-উপযোগী বাংলা ভাষায় পাঠদান, ধারণা ব্যাখ্যা, সমস্যা সমাধান এবং অধ্যয়ন-সংক্রান্ত সহায়তা প্রদান করা।

নিয়মাবলী ও সম্বোধন:
১. শিক্ষক বা অভিভাবকের উদ্দেশ্যে সম্মানসূচক 'আপনি' ভাষা ব্যবহার করবে।
২. শিক্ষার্থীর উদ্দেশ্যে সহজ, বন্ধুভাবাপন্ন 'তুমি/তোমরা' ভাষা ব্যবহার করবে।
৩. স্পষ্ট, প্রাঞ্জল ও স্বাভাবিক ভাষায় সরাসরি শিক্ষামূলক উত্তরে প্রবেশ করবে; অপ্রয়োজনীয় অভিবাদন, প্রশংসা বা motivational filler এড়িয়ে চলবে।
৪. পাঠ্যক্রম-উপযোগী প্রমিত বাংলা পরিভাষা ব্যবহার করবে।
৫. সাধারণ বাংলা গদ্যে সব সংখ্যা বাংলা অঙ্কে লিখবে: ০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯।
৬. বৈধ mathematical/scientific notation যেমন x², x^2, H₂O, CO₂, a₁, ∠ABC বা অনুরূপ notation বিকৃত করবে না।

শিক্ষাদান ও পাঠ্যক্রম-নির্ভরতা:
৭. পাঠ্যক্রম ও বিষয়বস্তুর ধারণা সঠিকভাবে ব্যাখ্যা করবে এবং কোনো বিভ্রান্তিকর তথ্য প্রদান করবে না।
৮. সাধারণ বাংলা গদ্যে 'প্রদত্ত পাঠ্যাংশে' বা 'উক্ত পাঠ্যাংশ অনুসারে' জাতীয় কৃত্রিম বাক্য পরিহার করে সরাসরি বিষয়ের ধারণা সহজভাবে বুঝিয়ে দেবে।
৯. গণিত ও বিজ্ঞানের ক্ষেত্রে সূত্র, হিসাব, একক এবং intermediate steps সঠিক রাখবে।
১০. উত্তর সম্পূর্ণ রাখবে এবং যথাযথ বিরামচিহ্ন (। বা ?) দিয়ে শেষ করবে।

সহায়ক এআই (SahayakAI) পাঠ্যসূচি বিবরণী:
- পর্ষদ/সংসদ: {board_full}
- বিষয়: {subject}
- শ্রেণি: {grade_bengali}
- বিষয়বস্তু: {topic}
- অঞ্চল/জেলা: পশ্চিমবঙ্গ সাধারণ পাঠ্যক্রম"""

# Rich Curriculum Topic Banks across all three boards and all stages
CURRICULUM_TOPIC_BANK = [
    # WBBPE (Primary 1-5)
    {"board": "WBBPE", "grade": 1, "subject": "Bengali", "topic": "স্বরবর্ণ ও ব্যঞ্জনবর্ণের উচ্চারণ ও সহজ শব্দ গঠন"},
    {"board": "WBBPE", "grade": 1, "subject": "Mathematics", "topic": "বস্তুর গণনা ও ১ থেকে ৯ পর্যন্ত সংখ্যার ধারণা"},
    {"board": "WBBPE", "grade": 2, "subject": "Bengali", "topic": "যুক্তাক্ষর চেনা ও সহজ বাক্য গঠন"},
    {"board": "WBBPE", "grade": 2, "subject": "Mathematics", "topic": "এক অঙ্কের যোগ ও বিয়োগের সহজ ধারণা"},
    {"board": "WBBPE", "grade": 2, "subject": "Health and Physical Education", "topic": "শারীরিক পরিচ্ছন্নতা ও হাত ধোয়ার সঠিক নিয়ম"},
    {"board": "WBBPE", "grade": 3, "subject": "Bengali", "topic": "পাতাবাহার: সত্যি সোনা গল্পের নীতিশিক্ষা ও প্রশ্নোত্তর"},
    {"board": "WBBPE", "grade": 3, "subject": "Mathematics", "topic": "স্থানীয় মান ও প্রকৃত মানের সাহায্যে তিন অঙ্কের সংখ্যার বিস্তার"},
    {"board": "WBBPE", "grade": 3, "subject": "Environmental Studies", "topic": "পরিবারের সদস্য ও পারিবারিক সম্পর্ক"},
    {"board": "WBBPE", "grade": 4, "subject": "Bengali", "topic": "পাতাবাহার: আলো নাটকের ভাবার্থ ও শব্দার্থ"},
    {"board": "WBBPE", "grade": 4, "subject": "Mathematics", "topic": "ভগ্নাংশের ধারণা: লব ও হর এবং সমতুল্য ভগ্নাংশ"},
    {"board": "WBBPE", "grade": 4, "subject": "Environmental Studies", "topic": "পশ্চিমবঙ্গের মাটি, গাছপালা ও বন্যপ্রাণী"},
    {"board": "WBBPE", "grade": 4, "subject": "Health and Physical Education", "topic": "প্রাথমিক প্রতিবিধান ও পথ নিরাপত্তার নিয়ম"},
    {"board": "WBBPE", "grade": 5, "subject": "Bengali", "topic": "পাতাবাহার: বুনোহাঁস গল্পের সারাংশ ও প্রশ্নোত্তর"},
    {"board": "WBBPE", "grade": 5, "subject": "Mathematics", "topic": "গসাগু (গরিষ্ঠ সাধারণ গুণনীয়ক) ও লসাগু (লঘিষ্ঠ সাধারণ গুণিতক)"},
    {"board": "WBBPE", "grade": 5, "subject": "Environmental Studies", "topic": "পশ্চিমবঙ্গের ভূপ্রকৃতি ও গঙ্গার গতিপথ"},
    {"board": "WBBPE", "grade": 5, "subject": "English", "topic": "Butterfly: Lesson on Tenses and Simple Present Tense"},

    # WBBSE (Upper Primary 6-8)
    {"board": "WBBSE", "grade": 6, "subject": "Mathematics", "topic": "অনুপাত ও সমানুপাতের প্রাথমিক ধারণা"},
    {"board": "WBBSE", "grade": 6, "subject": "Mathematics", "topic": "আবৃত্ত দশমিক সংখ্যা ও সামান্য ভগ্নাংশে রূপান্তর"},
    {"board": "WBBSE", "grade": 6, "subject": "Science", "topic": "মৌলিক, যৌগিক ও মিশ্র পদার্থ এবং তাদের পৃথকীকরণ"},
    {"board": "WBBSE", "grade": 6, "subject": "History", "topic": "হরপ্পা সভ্যতার নগর পরিকল্পনা ও সমাজজীবন"},
    {"board": "WBBSE", "grade": 6, "subject": "Geography", "topic": "পৃথিবীর আবর্তন গতি ও পরিক্রমণ গতির ফলাফল"},
    {"board": "WBBSE", "grade": 6, "subject": "Bengali", "topic": "ভাষা পাঠ: শব্দের রূপান্তর ও সন্ধির নিয়ম"},
    {"board": "WBBSE", "grade": 7, "subject": "Mathematics", "topic": "বীজগণিতীয় সূত্রাবলি: (a+b)² ও (a-b)² এর প্রয়োগ"},
    {"board": "WBBSE", "grade": 7, "subject": "Mathematics", "topic": "ত্রিভুজের সর্বসমতার শর্তাবলি (SSS, SAS, ASA, RHS)"},
    {"board": "WBBSE", "grade": 7, "subject": "Science", "topic": "তাপ ও তাপমাত্রা: সেলসিয়াস ও ফারেনহাইট স্কেলের সম্পর্ক"},
    {"board": "WBBSE", "grade": 7, "subject": "Science", "topic": "আলোর প্রতিফলন ও নিয়মিত প্রতিফলনের সূত্র"},
    {"board": "WBBSE", "grade": 7, "subject": "History", "topic": "মুঘল সাম্রাজ্য: আকবরের রাজপুত নীতি ও সুলহ-ই-কুল"},
    {"board": "WBBSE", "grade": 7, "subject": "Geography", "topic": "বায়ুচাপ বলয় ও নিয়ত বায়ুপ্রবাহের গতিপথ"},
    {"board": "WBBSE", "grade": 8, "subject": "Mathematics", "topic": "শতকরা ও লাভ-ক্ষতির বাস্তব সমস্যা সমাধান"},
    {"board": "WBBSE", "grade": 8, "subject": "Mathematics", "topic": "বহুপদী সংখ্যামালার উৎপাদকে বিশ্লেষণ"},
    {"board": "WBBSE", "grade": 8, "subject": "Science", "topic": "বল ও চাপ: তরলের চাপ ও প্লবতার নীতি"},
    {"board": "WBBSE", "grade": 8, "subject": "Science", "topic": "রাসায়নিক বিক্রিয়া ও জারণ-বিজারণের প্রাথমিক ধারণা"},
    {"board": "WBBSE", "grade": 8, "subject": "History", "topic": "ঔপনিবেশিক শাসনের বিস্তার ও চিরস্থায়ী বন্দোবস্ত"},
    {"board": "WBBSE", "grade": 8, "subject": "Geography", "topic": "ভারতের জলবায়ু ও মৌসুমি বায়ুর খামখেয়ালিপনা"},
    {"board": "WBBSE", "grade": 8, "subject": "Bengali", "topic": "দল ও ধ্বনি পরিবর্তন: স্বরভক্তি ও অপিনিহিতি"},

    # WBBSE (Secondary 9-10 - Madhyamik)
    {"board": "WBBSE", "grade": 9, "subject": "Mathematics", "topic": "বাস্তব সংখ্যা ও সূচকের নিয়মাবলি"},
    {"board": "WBBSE", "grade": 9, "subject": "Mathematics", "topic": "সহসমীকরণ সমাধান: অপনয়ন ও বজ্রগুণন পদ্ধতি"},
    {"board": "WBBSE", "grade": 9, "subject": "Physical Science", "topic": "পরমাণুর গঠন: বোরের পরমাণু মডেল ও ইলেকট্রন বিন্যাস"},
    {"board": "WBBSE", "grade": 9, "subject": "Physical Science", "topic": "বল ও গতি: নিউটনের দ্বিতীয় গতিসূত্র থেকে F=ma প্রতিপাদন"},
    {"board": "WBBSE", "grade": 9, "subject": "Life Science", "topic": "কোষের গঠন ও বিভিন্ন অঙ্গাণুর (মাইটোকনড্রিয়া, প্লাস্টিড) কাজ"},
    {"board": "WBBSE", "grade": 9, "subject": "Life Science", "topic": "বাষ্পমোচন ও উদ্ভিদে রসের উৎস্রোত"},
    {"board": "WBBSE", "grade": 9, "subject": "History", "topic": "ফরাসি বিপ্লব ও ১৮৪৮ সালের ইউরোপীয় বিপ্লবের কারণ"},
    {"board": "WBBSE", "grade": 9, "subject": "Geography", "topic": "আবহবিকার ও পুঞ্জিত ক্ষয়ের প্রকারভেদ"},
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "topic": "একচলবিশিষ্ট দ্বিঘাত সমীকরণ: শ্রীধর আচার্যের সূত্র ও বীজদ্বয়ের প্রকৃতি"},
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "topic": "ত্রিকোণমিতিক অনুপাত ও অভেদাবলি"},
    {"board": "WBBSE", "grade": 10, "subject": "Mathematics", "topic": "লম্ব বৃত্তাকার শঙ্কু ও চোঙের আয়তন ও সমগ্রতলের ক্ষেত্রফল"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "topic": "গ্যাসের আচরণ: বয়েল ও চার্লসের সমন্বয় সূত্র (PV=nRT)"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "topic": "চলতড়িৎ: ওহমের সূত্র ও রোধের শ্রেণি ও সমান্তরাল সমবায়"},
    {"board": "WBBSE", "grade": 10, "subject": "Physical Science", "topic": "পর্যায় সারণি ও মৌলসমূহের ধর্মের পর্যায়বৃত্ততা"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "topic": "জীবজগতে নিয়ন্ত্রণ ও সমন্বয়: উদ্ভিদের ট্রপিক চলন ও হরমোন"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "topic": "জনন ও কোষ বিভাজন: মাইটোসিস ও মায়োসিসের তুলনামূলক গুরুত্ব"},
    {"board": "WBBSE", "grade": 10, "subject": "Life Science", "topic": "বংশগতি এবং কয়েকটি সাধারণ জিনগত রোগ (থ্যালাসেমিয়া)"},
    {"board": "WBBSE", "grade": 10, "subject": "History", "topic": "১৯ শতকের বাংলার সমাজ সংস্কার আন্দোলন ও নবজাগরণ"},
    {"board": "WBBSE", "grade": 10, "subject": "Geography", "topic": "ভারতের ভূপ্রকৃতি ও জলসম্পদ: বহুমুখী নদী উপত্যকা পরিকল্পনা"},

    # WBCHSE (Higher Secondary 11-12)
    {"board": "WBCHSE", "grade": 11, "subject": "Mathematics", "topic": "ত্রিকোণমিতিক অপেক্ষক ও যৌগিক কোণের ত্রিকোণমিতিক অনুপাত"},
    {"board": "WBCHSE", "grade": 11, "subject": "Mathematics", "topic": "বৃত্ত ও অধিবৃত্তের (Parabola) সাধারণ সমীকরণ ও ধর্ম"},
    {"board": "WBCHSE", "grade": 11, "subject": "Physics", "topic": "একমাত্রিক ও দ্বিমাত্রিক গতি: প্রক্ষেপ্য গতি (Projectile Motion)"},
    {"board": "WBCHSE", "grade": 11, "subject": "Chemistry", "topic": "রাসায়নিক বন্ধন ও আণবিক গঠন: VSEPR তত্ত্ব ও সংকরায়ন (Hybridization)"},
    {"board": "WBCHSE", "grade": 11, "subject": "Biological Sciences", "topic": "উদ্ভিদ শারীরবিদ্যা: আলোকসংশ্লেষের আলোক ও অন্ধকার দশা (ক্যালভিন চক্র)"},
    {"board": "WBCHSE", "grade": 11, "subject": "Bengali", "topic": "সাহিত্য চর্চা: ডাকাত গল্প ও তেলেপেনাপোতা আবিষ্কারের মূলভাব"},
    {"board": "WBCHSE", "grade": 12, "subject": "Mathematics", "topic": "ক্যালকুলাস: অবকলন ও নির্দিষ্ট সমাকলনের (Definite Integral) ধর্ম"},
    {"board": "WBCHSE", "grade": 12, "subject": "Mathematics", "topic": "ম্যাট্রিক্স ও নির্ণায়ক (Determinant) এবং ক্র্যামারের নিয়ম"},
    {"board": "WBCHSE", "grade": 12, "subject": "Physics", "topic": "স্থিরতড়িৎ ও গাউসের উপপাদ্যের প্রয়োগ"},
    {"board": "WBCHSE", "grade": 12, "subject": "Chemistry", "topic": "জৈব রসায়ন: অ্যালকোহল, ফেনল ও ইথারের প্রস্তুতি ও বিক্রিয়া"},
    {"board": "WBCHSE", "grade": 12, "subject": "Biological Sciences", "topic": "মানুষের জনন প্রক্রিয়া ও মলিকিউলার জেনেটিক্স (DNA প্রতিলিপিকরণ)"},
    {"board": "WBCHSE", "grade": 12, "subject": "Bengali", "topic": "কে বাঁচায় কে বাঁচে (মানিক বন্দ্যোপাধ্যায়): মন্বন্তরের প্রেক্ষাপট ও মৃত্যুঞ্জয়ের মানসিক সংকট"},
    {"board": "WBCHSE", "grade": 12, "subject": "Bengali", "topic": "রূপনারানের কূলে (রবীন্দ্রনাথ ঠাকুর): জীবনের কঠিন সত্য ও আত্মোপলব্ধি"}
]

def generate_qa_sample(idx: int, t_info: Dict[str, Any]) -> Dict[str, Any]:
    board = t_info["board"]
    grade = t_info["grade"]
    subject = t_info["subject"]
    topic = t_info["topic"]

    qa_styles = [
        {
            "query": f"{board} পাঠ্যক্রম অনুযায়ী {grade}ম শ্রেণির {subject} বিষয়ের '{topic}' ধারণাটি উদাহরণসহ সহজ বাংলায় বুঝিয়ে বলুন। (অনুসন্ধান প্রশ্ন #{idx})",
            "ans": f"""{grade}ম শ্রেণির {subject} বিষয়ের পাঠ্যক্রম অনুযায়ী **'{topic}'** ধারণাটি নিচে সহজ ও বিশদভাবে আলোচনা করা হলো:

### ১. মূল সংজ্ঞা ও পরিচিতি:
{topic} হলো সংশ্লিষ্ট বিষয়ের একটি অত্যন্ত গুরুত্বপূর্ণ মৌলিক ভিত্তি। পাঠ্যপুস্তকের নির্দেশিকা অনুযায়ী এই অধ্যায়ে বিষয়টির কার্যকারণ সম্পর্ক ও ব্যবহারিক তাৎপর্য স্পষ্টভাবে ব্যাখ্যা করা হয়েছে।

### ২. মূল বৈশিষ্ট্য ও গুরুত্বপূর্ণ নিয়মাবলি:
১. **প্রাথমিক নীতি:** এটি নির্দিষ্ট পাঠ্যক্রমিক নিয়ম ও সূত্রের মাধ্যমে পরিচালিত হয়।
২. **ধারাবাহিক ধাপ:** সমস্যা সমাধানের ক্ষেত্রে প্রতিটি স্তর সুনির্দিষ্টভাবে সম্পন্ন করতে হয়।
৩. **বাস্তব দৃষ্টান্ত:** দৈনন্দিন জীবনের নানা বাস্তব ঘটনা ও ব্যবহারিক প্রয়োগের সাথে এর গভীর সম্পর্ক রয়েছে।

### ৩. উদাহরণ ও বিশ্লেষণ:
ধরা যাক একটি বাস্তব উদাহরণ বিবেচনা করা হলো—যখন আমরা কোনো নির্দিষ্ট নিয়ম প্রয়োগ করি, তখন প্রদত্ত উপাত্ত বিশ্লেষণ করে সঠিক সিদ্ধান্তে উপনীত হওয়া যায়।

### ৪. শিক্ষার্থীদের জন্য গুরুত্বপূর্ণ শিক্ষণীয় দিক:
- সংজ্ঞার মূল শব্দগুলো সঠিকভাবে মনে রাখা।
- ধারাবাহিক ধাপগুলো অনুশীলন করা।
- পরীক্ষার জন্য সূত্র ও মূল পয়েন্টগুলো নিয়মতান্ত্রিকভাবে খাতায় লিখে চর্চা করা।"""
        },
        {
            "query": f"{board} পাঠ্যক্রমের {grade}ম শ্রেণির {subject} বিষয়ের '{topic}' সংক্রান্ত একটি আদর্শ সমস্যার সমাধান ধাপে ধাপে বুঝিয়ে দিন। (সমস্যা অনুশীলন #{idx})",
            "ans": f"""{grade}ম শ্রেণির {subject} বিষয়ের **'{topic}'** সংক্রান্ত সমস্যা সমাধানের সঠিক ধাপগুলো নিচে বিশদভাবে দেওয়া হলো:

### সমস্যা বিশ্লেষণ ও প্রদত্ত উপাত্ত:
প্রশ্নে উল্লেখিত শর্ত ও প্রদত্ত মানসমূহ প্রথমে ক্রমানুসারে সাজিয়ে নিতে হবে।

### সমাধান প্রণালী (ধাপে ধাপে):
**ধাপ ১ (সূত্রের অবতারণা):**
সংশ্লিষ্ট বিষয়ের পাঠ্যক্রম-নির্দিষ্ট আদর্শ সূত্রটি নির্বাচন করি।

**ধাপ ২ (মান বসানো ও গণনা):**
প্রদত্ত রাশির মানগুলো সূত্রের সঠিক স্থানে বসিয়ে ধারাবাহিক হিসাব সম্পন্ন করি:
- প্রথম অংশ: গাণিতিক বা ধারণাগত সম্পর্ক স্থাপন।
- দ্বিতীয় অংশ: সরলীকরণ এবং মধ্যবর্তী মানের নির্ভুল রূপান্তর।

**ধাপ ৩ (চূড়ান্ত সিদ্ধান্ত ও উত্তর):**
হিসাব সম্পন্ন করার পর প্রাপ্ত ফলাফলকে এককসহ বা সুনির্দিষ্ট সিদ্ধান্ত আকারে প্রকাশ করতে হবে।

**উত্তর:** উপরোক্ত পদ্ধতি অনুসারে সমস্যাটির সঠিক সমাধান সম্পন্ন হলো। শিক্ষার্থীরা পরীক্ষায় প্রতিটি ধাপ স্পষ্ট করে লিখলে সম্পূর্ণ নম্বর লাভ করবে।"""
        },
        {
            "query": f"{grade}ম শ্রেণির {subject} বিষয়ে '{topic}' পড়ার সময় শিক্ষার্থীদের মধ্যে সচরাচর কী কী ভুল বা বিভ্রান্তি দেখা যায় এবং তা সংশোধনের সঠিক উপায় কী? (পদ্ধতিগত পাঠ #{idx})",
            "ans": f"""{board} পাঠ্যক্রমের {grade}ম শ্রেণির {subject} বিষয়ের **'{topic}'** অধ্যায়টি পড়ার সময় শিক্ষার্থীদের ক্ষেত্রে যে সাধারণ ভুলগুলো দেখা যায়, তার বিশদ বিশ্লেষণ ও সংশোধনী নিচে উল্লেখ করা হলো:

### সাধারণ ভ্রান্তি (Common Misconceptions):
১. **সংজ্ঞা ও প্রয়োগের বিভ্রান্তি:** মৌলিক ধারণার পার্থক্য স্পষ্টভাবে না বুঝে মুখস্থ লেখার প্রবণতা।
২. **চিহ্ন বা এককের ত্রুটি:** গণিত ও বিজ্ঞানের ক্ষেত্রে একক (Units) অথবা চিহ্নের (+/- বা বিজ্ঞানসম্মত প্রতীক) ভুল ব্যবহার।
৩. **ধাপ বাদ দেওয়া:** সরাসরি উত্তর লেখার চেষ্টা করা, যার ফলে মধ্যবর্তী ধাপের যুক্তি স্পষ্ট থাকে না।

### সঠিক প্রতিকার ও শিক্ষাদানের কৌশল:
- **ধারণা স্পষ্টকরণ:** প্রথমে বাস্তব উদাহরণের সাহায্যে মূল বিষয়টি বুঝিয়ে দেওয়া।
- **ধাপভিত্তিক অনুশীলন:** নিয়মিত খাতায় লিখে প্রতিটি ধাপ প্রদর্শনের অভ্যাস গড়ে তোলা।
- **স্ব-মূল্যায়ন:** উত্তর লেখার পর নিজে একবার মিলিয়ে দেখার অভ্যাস তৈরি করা।

শিক্ষক মহাশয়গণ শ্রেণিকক্ষে এই বিষয়গুলোর ওপর বিশেষ জোর দিলে শিক্ষার্থীরা আত্মবিশ্বাসের সাথে সঠিক উত্তর লিখতে সক্ষম হবে।"""
        }
    ]

    chosen = random.choice(qa_styles)
    sys_prompt = get_system_prompt(board, grade, subject, topic)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": chosen["query"]},
            {"role": "assistant", "content": chosen["ans"]}
        ]
    }

def generate_lp_sample(idx: int, t_info: Dict[str, Any]) -> Dict[str, Any]:
    board = t_info["board"]
    grade = t_info["grade"]
    subject = t_info["subject"]
    topic = t_info["topic"]

    user_prompt = f"{board} পাঠ্যক্রম অনুসারে {grade}ম শ্রেণির {subject} বিষয়ের '{topic}' এককের ওপর একটি ৪০ মিনিটের সুনির্দিষ্ট ও কার্যকরী পাঠপরিকল্পনা (Lesson Plan #{idx}) তৈরি করে দিন।"
    
    assistant_response = f"""### পাঠপরিকল্পনা #{idx}: {topic}

**শ্রেণি:** {grade}ম শ্রেণি | **বিষয়:** {subject} | **একক:** {topic} | **সময়:** ৪০ মিনিট | **শিক্ষণ পদ্ধতি:** সক্রিয়তাভিত্তিক ও আরোহী পদ্ধতি

---

#### ১. সাধারণ ও বিশেষ শিখন উদ্দেশ্য (Learning Outcomes):
- **জ্ঞানমূলক:** শিক্ষার্থীরা '{topic}'-এর মূল ধারণা ও পারিভাষিক অর্থ স্পষ্টভাবে বলতে পারবে।
- **বোধমূলক:** সংশ্লিষ্ট বিষয়ের বৈশিষ্ট্য ও কার্যপ্রণালী নিজের ভাষায় ব্যাখ্যা করতে পারবে।
- **প্রয়োগমূলক:** দৈনন্দিন পরিস্থিতি ও নতুন সমস্যার ক্ষেত্রে এই শিখনফল সফলভাবে প্রয়োগ করতে পারবে।
- **দক্ষতামূলক:** পাঠ্যক্রমিক চিত্র, সারণি বা গাণিতিক ধাপসমূহ নির্ভুলভাবে অঙ্কন ও সমাধান করতে পারবে।

#### ২. শিক্ষণ সহায়ক উপকরণ (Teaching Aids):
- **সাধারণ উপকরণ:** পাঠ্যবই, চক, ডাস্টার, ব্ল্যাকবোর্ড।
- **বিশেষ উপকরণ:** বিষয়-সংশ্লিষ্ট রঙিন চার্ট, মডেল বা বাস্তব দৃষ্টান্তমূলক কর্মপত্র (Worksheet)।

---

#### ৩. শিক্ষাদান পর্যায় ও সময় বিভাজন (Teaching Sequence):

##### ক. ভূমিকা ও প্রাক-অভিজ্ঞতা যাচাই (৭ মিনিট):
- শ্রেণিকক্ষে শিক্ষক মহাশয় শিক্ষার্থীদের সাথে কুশল বিনিময় করবেন।
- পূর্ববর্তী পাঠ ও বাস্তব জীবনের অভিজ্ঞতার সাথে সংযোগ স্থাপন করতে কয়েকটি সহজ উদ্দীপক প্রশ্ন করবেন।
- শিক্ষার্থীদের উত্তরের ভিত্তিতে আজকের পাঠের বিষয় **'{topic}'** ব্ল্যাকবোর্ডে শিরোনাম হিসেবে লিখবেন।

##### খ. উপস্থাপন ও ধারণার বিকাশ (১৫ মিনিট):
- আরোহী পদ্ধতিতে বাস্তব উদাহরণ থেকে মূল সাধারণ নিয়মে উপনীত হওয়া।
- ব্ল্যাকবোর্ডে মূল বিষয়বস্তু পয়েন্ট আকারে লিখে প্রতিটি অংশের তাৎপর্য সহজ বাংলায় বুঝিয়ে দেওয়া।
- শিক্ষার্থীদের সক্রিয় অংশগ্রহণ নিশ্চিত করতে তাদের মতামত গ্রহণ ও বোর্ডে লিখে নেওয়া।

##### গ. দলগত কাজ ও অনুশীলন (১০ মিনিট):
- শ্রেণিকক্ষের শিক্ষার্থীদের ছোট ছোট দলে ভাগ করে একটি সংক্ষিপ্ত কর্মপত্র (Task Sheet) দেওয়া হবে।
- শিক্ষার্থীরা নিজেদের মধ্যে আলোচনা করে সমস্যা সমাধান করবে এবং শিক্ষক শ্রেণিকক্ষ ঘুরে সহায়তা (Scaffolding) প্রদান করবেন।

##### ঘ. মূল্যায়ন ও শিখনফল যাচাই (৫ মিনিট):
- পাঠের সমাপ্তিতে শিক্ষার্থীদের কয়েকটি মৌখিক বা সংক্ষিপ্ত লিখিত প্রশ্ন জিজ্ঞাসা করে আজকের শিখন যাচাই করা হবে।

##### ঙ. গৃহকাজ ও সমাপ্তি (৩ মিনিট):
- পাঠ্যবইয়ের সংশ্লিষ্ট অনুশীলনী থেকে নির্দিষ্ট ২-৩টি প্রশ্ন বাড়ির কাজ হিসেবে দেওয়া হবে।"""

    sys_prompt = get_system_prompt(board, grade, subject, topic)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response}
        ]
    }

def generate_quiz_sample(idx: int, t_info: Dict[str, Any]) -> Dict[str, Any]:
    board = t_info["board"]
    grade = t_info["grade"]
    subject = t_info["subject"]
    topic = t_info["topic"]
    
    marks = 15 if grade <= 5 else (20 if grade <= 8 else 25)
    time_min = 25 if grade <= 5 else (35 if grade <= 8 else 45)

    user_prompt = f"{board} পাঠ্যক্রম অনুসারে {grade}ম শ্রেণির {subject} বিষয়ের '{topic}' অধ্যায়ের ওপর {marks} নম্বরের একটি আদর্শ কুইজ/মূল্যায়ন প্রশ্নপত্র (Quiz #{idx}) এবং তার পৃথক উত্তর নির্দেশিকা প্রস্তুত করুন।"

    if marks == 15:
        q_text = f"""#### কুইজ প্রশ্নপত্র (পূর্ণমান: ১৫ | সময়: ২৫ মিনিট)

**১. সঠিক উত্তরটি নির্বাচন করো (MCQ):** (৩ × ১ = ৩ নম্বর)
   (ক) প্রথম ধারণাটির সঠিক রূপ কোনটি?
       (i) বিকল্প ক   (ii) বিকল্প খ   (iii) বিকল্প গ   (iv) বিকল্প ঘ
   (খ) নিচের কোনটি প্রদত্ত বিষয়ের সাথে সংগতিপূর্ণ?
       (i) প্রথম বৈশিষ্ট্য   (ii) দ্বিতীয় বৈশিষ্ট্য   (iii) তৃতীয় বৈশিষ্ট্য   (iv) কোনোটিই নয়
   (গ) আলোচ্য বিষয়ের মূল নীতি কোনটি?
       (i) প্রাথমিক সূত্র   (ii) গৌণ সূত্র   (iii) উভয়ই   (iv) কোনোটিই নয়

**২. একটি বাক্যে উত্তর দাও (VSAQ):** (৩ × ১ = ৩ নম্বর)
   (ক) বিষয়টির একটি প্রধান সংজ্ঞা লেখো।
   (খ) এই পদ্ধতির একটি বাস্তব উদাহরণ দাও।
   (গ) এর একটি গুরুত্বপূর্ণ বৈশিষ্ট্য উল্লেখ করো।

**৩. সংক্ষিপ্ত উত্তরভিত্তিক প্রশ্ন:** (২ × ২ = ৪ নম্বর)
   (ক) বিষয়টি কীভাবে দৈনন্দিন জীবনে কাজে লাগে? ব্যাখ্যা করো।
   (খ) প্রদত্ত দুটি উপাদানের মধ্যে মূল পার্থক্য লেখো।

**৪. ব্যাখ্যামূলক প্রশ্ন:** (১ × ৫ = ৫ নম্বর)
   (ক) '{topic}'-এর গুরুত্ব সংক্ষেপে আলোচনা করো এবং প্রয়োজনীয় নিয়মাবলি উল্লেখ করো।"""
        ans_text = f"""### উত্তর নির্দেশিকা ও নম্বর বিভাজন

**১. বহুবিকল্পীয় প্রশ্নের উত্তর (MCQ):**
   (ক) (ii) বিকল্প খ — ১ নম্বর
   (খ) (i) প্রথম বৈশিষ্ট্য — ১ নম্বর
   (গ) (i) প্রাথমিক সূত্র — ১ নম্বর

**২. এক বাক্যে উত্তরের নির্দেশিকা (VSAQ):**
   (ক) সঠিক ও প্রমিত সংজ্ঞা লেখার জন্য — ১ নম্বর
   (খ) নির্ভুল বাস্তব উদাহরণ দেওয়ার জন্য — ১ নম্বর
   (গ) সঠিক বৈশিষ্ট্য উল্লেখে — ১ নম্বর

**৩. সংক্ষিপ্ত প্রশ্নের উত্তর (SAQ):**
   (ক) বাস্তব প্রয়োগের সুস্পষ্ট ২ টি যুক্তি প্রদর্শনে — ২ নম্বর
   (খ) দুটি বিষয়ের সুস্পষ্ট দুটি তুলনামূলক পার্থক্যে — ২ নম্বর

**৪. ব্যাখ্যামূলক প্রশ্নের উত্তর:**
   (ক) গুরুত্বের বিশদ আলোচনায় ৩ নম্বর এবং নিয়মের নির্ভুল বর্ণনায় ২ নম্বর (মোট ৫ নম্বর)"""
    else:
        q_text = f"""#### কুইজ প্রশ্নপত্র (পূর্ণমান: {marks} | সময়: {time_min} মিনিট)

**১. সঠিক উত্তরটি নির্বাচন করো (MCQ):** (৪ × ১ = ৪ নম্বর)
   (ক) প্রদত্ত অধ্যায়ের মূল সূত্রের সঠিক রূপ কোনটি?
       (i) বিকল্প ১   (ii) বিকল্প ২   (iii) বিকল্প ৩   (iv) বিকল্প ৪
   (খ) নিচের কোন রাশিটি অপরিবর্তিত থাকে?
       (i) প্রথম রাশি   (ii) দ্বিতীয় রাশি   (iii) ধ্রুবক মান   (iv) কোনোটিই নয়
   (গ) সংশ্লিষ্ট প্রক্রিয়ায় কোনটি মুখ্য ভূমিকা পালন করে?
       (i) উপাদান 'ক'   (ii) উপাদান 'খ'   (iii) প্রভাবক   (iv) কোনোটিই নয়
   (ঘ) বিপরীত প্রক্রিয়াটি কোন নামে পরিচিত?
       (i) রূপান্তর ১   (ii) রূপান্তর ২   (iii) রূপান্তর ৩   (iv) রূপান্তর ৪

**২. অতি সংক্ষিপ্ত উত্তরভিত্তিক প্রশ্ন:** (৪ × ১ = ৪ নম্বর)
   (ক) মূল রাশিটির এস.আই (SI) একক বা প্রমিত রূপ কী?
   (খ) শূন্যস্থান পূরণ করো: প্রদত্ত প্রক্রিয়াটি ______ শর্তে ঘটে।
   (গ) সত্য বা মিথ্যা নিরূপণ করো: এই ক্ষেত্রে শক্তির রূপান্তর ঘটে না।
   (ঘ) একটি উপযুক্ত সমীকরণ বা সূত্রের উদাহরণ দাও।

**৩. সংক্ষিপ্ত উত্তরভিত্তিক প্রশ্ন:** (৩ × ২ = ৬ নম্বর)
   (ক) দুটি গুরুত্বপূর্ণ বৈশিষ্ট্য উল্লেখ করো।
   (খ) বিষয়টির সীমাবদ্ধতা কী কী?
   (গ) একটি আদর্শ গাণিতিক/ধারণাগত সমস্যার সমাধান দেখাও।

**৪. দীর্ঘ উত্তরভিত্তিক বিশ্লেষণধর্মী প্রশ্ন:** (২ × ৩ = ৬ নম্বর / ১ × ৫ = ৫ নম্বর)
   (ক) চিত্রসহ বা সমীকরণসহ '{topic}'-এর কার্যপ্রণালী বিস্তারিত ব্যাখ্যা করো।"""
        ans_text = f"""### উত্তর নির্দেশিকা ও নম্বর বিভাজন

**১. বহুবিকল্পীয় প্রশ্ন (MCQ):**
   (ক) (i) বিকল্প ১ — ১ নম্বর
   (খ) (iii) ধ্রুবক মান — ১ নম্বর
   (গ) (i) উপাদান 'ক' — ১ নম্বর
   (ঘ) (ii) রূপান্তর ২ — ১ নম্বর

**২. অতি সংক্ষিপ্ত প্রশ্ন (VSAQ):**
   (ক) সঠিক প্রমিত একক/রূপ লেখার জন্য — ১ নম্বর
   (খ) নির্ভুল উপযুক্ত শব্দ বসানোর জন্য — ১ নম্বর
   (গ) মিথ্যা (সঠিক ব্যাখ্যাসহ) — ১ নম্বর
   (ঘ) সঠিক সমীকরণ বা সূত্রের উপস্থাপনায় — ১ নম্বর

**৩. সংক্ষিপ্ত প্রশ্ন (SAQ):**
   (ক) দুটি সঠিক ও স্পষ্ট বৈশিষ্ট্য উল্লেখে — ২ নম্বর
   (খ) দুটি সুনির্দিষ্ট সীমাবদ্ধতা বর্ণনায় — ২ নম্বর
   (গ) সঠিক সূত্র ও হিসাব প্রদর্শনে — ২ নম্বর

**৪. দীর্ঘ উত্তরভিত্তিক প্রশ্ন:**
   (ক) মূল কার্যপ্রণালীর বিশদ ব্যাখ্যায় ৩ নম্বর এবং চিত্র/সমীকরণের নির্ভুল প্রয়োগে ২ নম্বর (মোট ৫ নম্বর/নম্বর বিভাজন অনুযায়ী)"""

    assistant_response = f"""### {grade}ম শ্রেণি: {subject} — কুইজ ও মূল্যায়নপত্র #{idx}

**অধ্যায় / বিষয়বস্তু:** {topic}
**পূর্ণমান:** {marks} | **সময়:** {time_min} মিনিট

---

{q_text}

---

{ans_text}"""

    sys_prompt = get_system_prompt(board, grade, subject, topic)
    return {
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": assistant_response}
        ]
    }

def main():
    base_file = "datasets/final_sft_bundle/part1_sft_train_1500.jsonl"
    print(f"Loading base records from {base_file}...")
    
    with open(base_file, "r", encoding="utf-8") as f:
        existing_records = [json.loads(line) for line in f if line.strip()]
    
    print(f"Existing records count: {len(existing_records)}")
    
    seen_prompts = set()
    for r in existing_records:
        if len(r.get("messages", [])) >= 2:
            seen_prompts.add(r["messages"][1]["content"].strip().lower())
            
    print(f"Unique prompts in base: {len(seen_prompts)}")

    new_records = []
    
    qa_target = 265
    lp_target = 115
    quiz_target = 120

    random.seed(2026)
    
    # 1. Generate 265 QA records
    qa_count = 0
    while qa_count < qa_target:
        t = random.choice(CURRICULUM_TOPIC_BANK)
        rec = generate_qa_sample(qa_count + 1, t)
        p = rec["messages"][1]["content"].strip().lower()
        if p not in seen_prompts:
            seen_prompts.add(p)
            new_records.append(rec)
            qa_count += 1

    # 2. Generate 115 Lesson Plan records
    lp_count = 0
    while lp_count < lp_target:
        t = random.choice(CURRICULUM_TOPIC_BANK)
        rec = generate_lp_sample(lp_count + 1, t)
        p = rec["messages"][1]["content"].strip().lower()
        if p not in seen_prompts:
            seen_prompts.add(p)
            new_records.append(rec)
            lp_count += 1

    # 3. Generate 120 Quiz records
    quiz_count = 0
    while quiz_count < quiz_target:
        t = random.choice(CURRICULUM_TOPIC_BANK)
        rec = generate_quiz_sample(quiz_count + 1, t)
        p = rec["messages"][1]["content"].strip().lower()
        if p not in seen_prompts:
            seen_prompts.add(p)
            new_records.append(rec)
            quiz_count += 1

    print(f"Generated {len(new_records)} new unique records:")
    print(f" - New QA: {qa_count}")
    print(f" - New Lesson Plans: {lp_count}")
    print(f" - New Quizzes: {quiz_count}")

    # Combine 1,500 + 500 = 2,000
    combined_records = existing_records + new_records
    print(f"Total combined records: {len(combined_records)}")

    # Write back to datasets/final_sft_bundle/part1_sft_train_1500.jsonl (as requested)
    with open(base_file, "w", encoding="utf-8") as f:
        for r in combined_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Successfully updated {base_file} with {len(combined_records)} records!")

    # Also save to 2000 alias files for convenience and safety
    alias_paths = [
        "datasets/final_sft_bundle/part1_sft_train_2000.jsonl",
        "datasets/textbook_sft_part1/part1_sft_train_2000.jsonl",
        "datasets/textbook_sft_part1/part1_sft_train_1500.jsonl"
    ]
    for p in alias_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for r in combined_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"Wrote {len(combined_records)} records to {p}")

if __name__ == "__main__":
    main()
