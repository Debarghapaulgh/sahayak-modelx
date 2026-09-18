"""
create_wbbse_topic_indices.py
Generates official WBBSE Class 9 and 10 topic index YAML files for missing subjects
(Physical Science, Life Science, History, Geography).
"""

import yaml
from pathlib import Path

TOPIC_DIR = Path(__file__).parent / "northbengal-dataset-forge-2026-08-19" / \
            "northbengal-dataset-forge" / "forge" / "config" / "wbbse_topics"
TOPIC_DIR.mkdir(parents=True, exist_ok=True)

# 1. Class 9 Physical Science
cl9_phys_sci = {
    "subject": "Physical_Science",
    "grade": 9,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "পরিমাপ ও একক (Measurement and Units)", "chapter": "অধ্যায় ১", "subtopics": ["ভৌত রাশি", "একক ও মাত্রা", "পরিমাপের যন্ত্র"]},
        {"name": "পদার্থের গঠন ও ধর্ম (Structure and Properties of Matter)", "chapter": "অধ্যায় ২", "subtopics": ["ঘনত্ব ও আপেক্ষিক গুরুত্ব", "বায়ুমণ্ডলের চাপ", "পাস্কালের সূত্র", "আর্কিমিডিসের নীতি ও প্লবতা", "পৃষ্ঠটান ও সান্দ্রতা"]},
        {"name": "পরমাণুর গঠন (Atomic Structure)", "chapter": "অধ্যায় ৩", "subtopics": ["পরমাণুর উপাদান (ইলেকট্রন, প্রোটন, নিউট্রন)", "রাদারফোর্ড ও বোরের পরমাণু মডেল", "আইসোটোপ, আইসোবার, আইসোটোন"]},
        {"name": "বল ও গতি (Force and Motion)", "chapter": "অধ্যায় ৪", "subtopics": ["নিউটন-এর গতিসূত্রসমূহ", "ভরবেগ ও ভরবেগ সংরক্ষণ নীতি", "কার্য, ক্ষমতা ও শক্তি"]},
        {"name": "শ্রবণ ও শব্দ (Sound)", "chapter": "অধ্যায় ৫", "subtopics": ["শব্দতরঙ্গ ও গতিবেগ", "প্রতিধ্বনি ও তার ব্যবহার", "শ্রাব্যতার সীমা"]},
        {"name": "তাপ (Heat)", "chapter": "অধ্যায় ৬", "subtopics": ["তাপ ও তাপমাত্রা", "লীন তাপ", "ক্যালোরিমিতি"]},
        {"name": "দ্রবণ, অ্যাসিড, ক্ষার ও লবণ (Solutions, Acids, Bases & Salts)", "chapter": "অধ্যায় ৭", "subtopics": ["দ্রবণ ও দ্রাব্যতা", "pH স্কেল", "অ্যাসিড-ক্ষারের বিক্রিয়া", "প্রশমন বিক্রিয়া"]}
    ]
}

# 2. Class 10 Physical Science
cl10_phys_sci = {
    "subject": "Physical_Science",
    "grade": 10,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "পরিবেশের জন্য ভাবনা (Concerns about Our Environment)", "chapter": "অধ্যায় ১", "subtopics": ["বায়ুমণ্ডলের স্তরবিন্যাস", "গ্রিনহাউস প্রভাব ও বিশ্ব উষ্ণায়ন", "শক্তি সম্পদের টেকসই ব্যবহার"]},
        {"name": "গ্যাসের আচরণ (Behaviour of Gases)", "chapter": "অধ্যায় ২", "subtopics": ["বয়লের সূত্র", "চার্লসের সূত্র", "আদর্শ গ্যাস সমীকরণ (PV = nRT)", "গ্যাসের অণুর গতি তত্ত্ব"]},
        {"name": "রাসায়নিক গণনা (Chemical Calculations)", "chapter": "অধ্যায় ৩", "subtopics": ["ভরের সংরক্ষণ সূত্র", "মোল ধারণা", "রাসায়নিক সমীকরণ থেকে ভর ও আয়তন গণনা"]},
        {"name": "আলো (Light)", "chapter": "অধ্যায় ৪", "subtopics": ["আলোর প্রতিফলন ও গোলীয় দর্পণ", "আলোর প্রতিসরণ ও লেন্স", "আলোর বিচ্ছুরণ ও বর্ণালী"]},
        {"name": "চলতড়িৎ (Current Electricity)", "chapter": "অধ্যায় ৫", "subtopics": ["ওহমের সূত্র ও রোধ", "রোধের সমবায় (শ্রেণি ও সমান্তরাল)", "তড়িৎ ক্ষমতা ও গৃহস্থালির তড়িৎ বর্তনী", "তড়িৎচুম্বকত্ব"]},
        {"name": "পর্যায় সারণি ও মৌলদের ধর্মের পর্যায়বৃত্ততা (Periodic Table)", "chapter": "অধ্যায় ৬", "subtopics": ["মেন্ডেলিফ ও আধুনিক পর্যায় সূত্র", "পর্যায়বৃত্ত ধর্ম (পরমাণু ব্যাসার্ধ, তড়িৎ ঋণাত্মকতা, জারণ-বিজারণ)"]},
        {"name": "আয়নীয় ও সমযোজী বন্ধন (Ionic and Covalent Bonding)", "chapter": "অধ্যায় ৭", "subtopics": ["আয়নীয় যৌগ গঠন", "সমযোজী যৌগ গঠন", "যৌগের ধর্ম তুলনা"]},
        {"name": "তড়িৎপ্রবাহ ও রাসায়নিক বিক্রিয়া (Electrolysis)", "chapter": "অধ্যায় ৮", "subtopics": ["তড়িৎ বিশ্লেষণ প্রক্রিয়া", "ক্যাথোড ও অ্যানোড বিক্রিয়া", "তড়িৎ লেপন (Electroplating)"]},
        {"name": "পরীক্ষাগার ও রাসায়নিক শিল্পে অজৈব রসায়ন (Inorganic Chemistry)", "chapter": "অধ্যায় ৯", "subtopics": ["অ্যামোনিয়া, হাইড্রোজেন সালফাইড, নাইট্রোজেন প্রস্তুতি", "শিল্পোৎপাদন (H2SO4, HNO3)"]},
        {"name": "ধাতুবিদ্যা (Metallurgy)", "chapter": "অধ্যায় ১০", "subtopics": ["ধাতুর আকরিক", "লোহা, অ্যালুমিনিয়াম, তামা নিষ্কাশন", "সংকর ধাতু ও ক্ষয় রোধ"]},
        {"name": "জৈব রসায়ন (Organic Chemistry)", "chapter": "অধ্যায় ১১", "subtopics": ["হাইড্রোকার্বন (অ্যালকেন, অ্যালকিন, অ্যালকাইন)", "ফাংশনাল গ্রুপ", "মিথেন, ইথেন, ইথিলিন, অ্যাসিটিলিন"]}
    ]
}

# 3. Class 9 Life Science
cl9_life_sci = {
    "subject": "Life_Science",
    "grade": 9,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "জীবন ও তার বৈচিত্র্য (Life and Its Diversity)", "chapter": "অধ্যায় ১", "subtopics": ["জীবনের লক্ষণ", "ট্যাক্সোনোমি ও শ্রেণিবিন্যাস", "উদ্ভিদ ও প্রাণী রাজ্যের প্রধান পর্বসমূহ"]},
        {"name": "জীবসংগঠনের স্তর (Levels of Organization of Life)", "chapter": "অধ্যায় ২", "subtopics": ["কোষীয় অঙ্গাণু (সাইটোপ্লাজম, নিউক্লিয়াস, মাইটোকন্ড্রিয়া)", "উদ্ভিদ ও প্রাণী কলা (টিস্যু)", "মানব দেহের প্রধান অঙ্গসমূহ"]},
        {"name": "জৈবনিক প্রক্রিয়া (Physiological Processes of Life)", "chapter": "অধ্যায় ৩", "subtopics": ["শালোকসংশ্লেষ (Photosynthesis)", "শ্বসন (Respiration)", "সংবহন ও রক্ত (Circulation & Blood)", "রেচন (Excretion)"]},
        {"name": "স্বাস্থ্য ও রোগ (Health and Diseases)", "chapter": "অধ্যায় ৪", "subtopics": ["অনাক্রম্যতা ও ভ্যাক্সিন", "সংক্রামক রোগ (ম্যালেরিয়া, ডেঙ্গু, যক্ষ্মা)", "জনস্বাস্থ্য ও পরিচ্ছন্নতা"]},
        {"name": "মানুষ ও পরিবেশ (Human and Environment)", "chapter": "অধ্যায় ৫", "subtopics": ["প্রাকৃতিক সম্পদ ও তার প্রাকৃতিক ব্যবহার", "পরিবেশ দূষণ ও সংরক্ষণ"]}
    ]
}

# 4. Class 10 Life Science
cl10_life_sci = {
    "subject": "Life_Science",
    "grade": 10,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "জীবজগতে নিয়ন্ত্রণ ও সমন্বয় (Control and Coordination in Living Organisms)", "chapter": "অধ্যায় ১", "subtopics": ["উদ্ভিদের সংবেদনশীলতা ও ট্রপিক চলন", "উদ্ভিদ হরমোন (অক্সিন, জিব্বেরেলিন, সাইটোকাইনিন)", "প্রাণী হরমোন ও থাইরয়েড/ইনসুলিন", "মানব স্নায়ুতন্ত্র ও নেত্রপেশি/দৃষ্টি"]},
        {"name": "জীবনের ধারাবাহিকতা (Continuity of Life)", "chapter": "অধ্যায় ২", "subtopics": ["কোষ বিভাজন (মাইটোসিস ও মায়োসিস)", "অঙ্গজ, অয়ৌন ও যৌন জনন", "উদ্ভিদের বৃদ্ধি ও বিকাশ"]},
        {"name": "বংশগতি এবং কয়েকটি সাধারণ জিনগত রোগ (Heredity and Genetic Diseases)", "chapter": "অধ্যায় ৩", "subtopics": ["মেনডেলের বংশগতি সূত্র (একসংকর ও দ্বিসংকর জনন)", "লিঙ্গ নির্ধারণ", "থ্যালাসেমিয়া, হিমোফিলিয়া, বর্ণান্ধতা"]},
        {"name": "অভিব্যক্তি ও অভিযোজন (Evolution and Adaptation)", "chapter": "অধ্যায় ৪", "subtopics": ["জীবনের উৎপত্তি ও ল্যামার্কবাদ/ডারউইনবাদ", "অভিযোজন (উট, সুন্দরী গাছ, রুই মাছের পটকা, শিম্পাঞ্জি)"]},
        {"name": "পরিবেশ, তার সম্পদ এবং তাদের সংরক্ষণ (Environment and Conservation)", "chapter": "অধ্যায় ৫", "subtopics": ["নাইট্রোজেন চক্র", "পরিবেশ দূষণ ও বায়োডাইভারসিটি হটস্পট", "যৌথ বন ব্যবস্থাপনা (JFM) ও PBR"]}
    ]
}

# 5. Class 9 History
cl9_hist = {
    "subject": "History",
    "grade": 9,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "ফরাসি বিপ্লবের বিভিন্ন দিক (French Revolution)", "chapter": "অধ্যায় ১", "subtopics": ["ফরাসি সমাজের স্তরবিন্যাস", "দার্শনিকদের অবদান", "বাস্তিল দুর্গের পতন ও মানবাধিকার ঘোষণা"]},
        {"name": "নেপোলিয়নীয় সাম্রাজ্য ও জাতীয়তাবাদ (Napoleonic Era)", "chapter": "অধ্যায় ২", "subtopics": ["কোড নেপোলিয়ন", "মহাদেশীয় ব্যবস্থা", "নেপোলিয়নের পতন"]},
        {"name": "ঊনবিংশ শতকের ইউরোপ (19th Century Europe)", "chapter": "অধ্যায় ৩", "subtopics": ["ভিয়েনা সম্মেলন", "মেটারনিক ব্যবস্থা", "১৮৪৮ সালের জুলাই ও ফেব্রুয়ারি বিপ্লব"]},
        {"name": "শিল্প বিপ্লব, ঔপনিবেশিকতাবাদ ও সাম্রাজ্যবাদ (Industrial Revolution & Imperialism)", "chapter": "অধ্যায় ৪", "subtopics": ["শিল্প বিপ্লবের কারখানা ব্যবস্থা", "ইউরোপীয় সাম্রাজ্যবাদ ও এশিয়া-আফ্রিকা দখল"]},
        {"name": "প্রথম বিশ্বযুদ্ধ ও পরবর্তীকাল (World War I)", "chapter": "অধ্যায় ৫", "subtopics": ["প্রথম বিশ্বযুদ্ধের কারণ ও পরিণতি", "ভার্সাই চুক্তি", "রাশিয়াতে বলশেভিক বিপ্লব (১৯১৭)"]},
        {"name": "দ্বিতীয় বিশ্বযুদ্ধ ও পরিবেশ (World War II)", "chapter": "অধ্যায় ৬", "subtopics": ["ফ্যাসিবাদ ও নাসিবাদ (মুসোলিনি ও হিটলার)", "দ্বিতীয় বিশ্বযুদ্ধের সূচনা ও অক্ষশক্তি-মিত্রশক্তি"]},
        {"name": "জাতিসংঘ ও আন্তর্জাতিক সংস্থা (United Nations)", "chapter": "অধ্যায় ৭", "subtopics": ["লীগ অফ নেশনস-এর ব্যর্থতা", "সম্মিলিত জাতিপুঞ্জ গঠন ও নিরাপত্তা পরিষদ"]}
    ]
}

# 6. Class 10 History
cl10_hist = {
    "subject": "History",
    "grade": 10,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "ইতিহাসের ধারণা (Ideas of History)", "chapter": "অধ্যায় ১", "subtopics": ["আধুনিক ইতিহাস চর্চার পদ্ধতি", "খাদ্য, পোশাক, খেলাধুলা ও নারী ইতিহাস", "স্থানীয় ইতিহাস ও স্মৃতিকথা"]},
        {"name": "সংস্কার: বৈশিষ্ট্য ও পর্যালোচনা (Reforms: Characteristics & Observations)", "chapter": "অধ্যায় ২", "subtopics": ["১৯ শতকের বঙ্কিম-বিদ্যাসাগর-রামমোহন যুগ", "ব্রাহ্মসমাজ ও ইয়ং বেঙ্গল আন্দোলন", "উডের ডেসপ্যাচ ও পাশ্চাত্য শিক্ষা"]},
        {"name": "প্রতিরোধ ও বিদ্রোহ: বৈশিষ্ট্য ও বিশ্লেষণ (Resistance and Rebellion)", "chapter": "অধ্যায় ৩", "subtopics": ["সাঁওতাল বিদ্রোহ, কোল বিদ্রোহ, চুয়ার বিদ্রোহ", "নীল বিদ্রোহ ও ওয়াহাবি/ফরায়েজি আন্দোলন"]},
        {"name": "সংঘবদ্ধতার গোড়ার কথা (Early Stages of Collective Action)", "chapter": "অধ্যায় ৪", "subtopics": ["১৮৫৭ সালের মহাবিদ্রোহ", "মহারানির ঘোষণাপত্র", "ভারত সভা ও হিন্দু মেলা"]},
        {"name": "বিকল্প চিন্তা ও উদ্যোগ (Mid 19th to Early 20th Century)", "chapter": "অধ্যায় ৫", "subtopics": ["বাংলায় ছাপাখানার বিকাশ (ইউ রায় অ্যান্ড সন্স)", "বিজ্ঞান শিক্ষা (বসুপোস্ট গ্রাজুয়েট ইনস্টিটিউট, আইএসিএস)", "কারিগরি শিক্ষা (বেঙ্গল টেকনিক্যাল ইনস্টিটিউট)"]},
        {"name": "বিংশ শতকের ভারতে কৃষক, শ্রমিক ও বামপন্থী আন্দোলন (Peasant & Left Movements)", "chapter": "অধ্যায় ৬", "subtopics": ["অসহযোগ ও আইন অমান্য আন্দোলনে কৃষক", "ভারত ছাড়ো আন্দোলন", "ভারতে বামপন্থী রাজপথ ও মিরাট ষড়যন্ত্র মামলা"]},
        {"name": "বিংশ শতকের ভারতে নারী, ছাত্র ও প্রান্তিক জনগোষ্ঠীর আন্দোলন (Women, Students & Dalit Movements)", "chapter": "অধ্যায় ৭", "subtopics": ["সশস্ত্র বিপ্লবী আন্দোলনে নারী ও ছাত্র (প্রীতিলতা, কল্পনা দত্ত)", "অ্যান্টি সার্কুলার সোসাইটি", "দলিত আন্দোলন ও আম্বেদকর"]},
        {"name": "উত্তর-ঔপনিবেশিক ভারত: দ্বিতীয় দ্বিতীয়ার্ধ (Post-Colonial India 1947-1964)", "chapter": "অধ্যায় ৮", "subtopics": ["দেশীয় রাজ্যের অন্তর্ভুক্তি (হায়দরাবাদ, কাশ্মীর, জুনাগড়)", "উদ্বাস্তু সমস্যা ও পুনর্বাসন", "ভাষাভিত্তিক রাজ্য পুনর্গঠন কমিশন"]}
    ]
}

# 7. Class 9 Geography
cl9_geog = {
    "subject": "Geography",
    "grade": 9,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "গ্রহ রূপে পৃথিবী (Earth as a Planet)", "chapter": "অধ্যায় ১", "subtopics": ["পৃথিবীর আকার ও গোলীয় প্রমাণ", "দিগন্তরেখা ও জিপিএস"]},
        {"name": "পৃথিবীর গতিসমূহ (Movements of the Earth)", "chapter": "অধ্যায় ২", "subtopics": ["আহ্নিক গতি ও বার্ষিক গতি", "দিনরাত্রি হ্রাস-বৃদ্ধি ও ঋতুপরিবর্তন"]},
        {"name": "পৃথিবীর স্থান নির্ণয় (Determining Location on Earth)", "chapter": "অধ্যায় ৩", "subtopics": ["অক্ষরেখা ও দ্রাঘিমারেখা", "স্থানীয় সময় ও প্রমাণ সময়", "প্রতিপাদ স্থান"]},
        {"name": "ভূমি রূপ গঠনকারী প্রক্রিয়া ও পৃথিবীর বিভিন্ন ভূমিরূপ (Geomorphic Processes & Landforms)", "chapter": "অধ্যায় ৪", "subtopics": ["পর্বত ( ভঙ্গিল, সঞ্চয়জাত, স্তূপ)", "মালভূমি ও সমভূমি"]},
        {"name": " আবহবিকার (Weathering)", "chapter": "অধ্যায় ৫", "subtopics": ["যান্ত্রিক আবহবিকার", "রাসায়নিক আবহবিকার", "মৃত্তিকা গঠন"]},
        {"name": "দুর্যোগ ও বিপর্যয় (Hazards and Disasters)", "chapter": "অধ্যায় ৬", "subtopics": ["ভূমিকম্প, বন্যা, খরা, ধস", "উত্তরবঙ্গের পাহাড়ি ধস ও দুর্যোগ ব্যবস্থাপনা"]},
        {"name": "মানচিত্র ও স্কেল (Map and Scale)", "chapter": "অধ্যায় ৭", "subtopics": ["মানচিত্রের প্রকারভেদ", "স্কেলের ব্যবহার ও স্কেল রূপান্তর"]},
        {"name": "পশ্চিমবঙ্গ (West Bengal)", "chapter": "অধ্যায় ৮", "subtopics": ["অবস্থান ও প্রশাসনিক বিভাগ", "প্রাকৃতিক পরিবেশ (ভূপ্রকৃতি, নদনদী, জলবায়ু, মৃত্তিকা, স্বাভাবিক উদ্ভিদ)", "উত্তরবঙ্গের পার্বত্য অঞ্চল ও সমভূমি", "অর্থনৈতিক পরিবেশ (কৃষি, শিল্প, জনসংখ্যা)"]}
    ]
}

# 8. Class 10 Geography
cl10_geog = {
    "subject": "Geography",
    "grade": 10,
    "board": "WBBSE",
    "medium": "Bengali",
    "topics": [
        {"name": "বহির্জাত প্রক্রিয়া ও তাদের দ্বারা সৃষ্ট ভূমিরূপ (Exogenetic Processes & Landforms)", "chapter": "অধ্যায় ১", "subtopics": ["নদীর ক্ষয় ও সঞ্চয়জাত ভূমিরূপ", "হিমবাহের ক্ষয় ও সঞ্চয়জাত ভূমিরূপ", "বায়ুর ক্ষয় ও সঞ্চয়জাত ভূমিরূপ"]},
        {"name": "বায়ুমণ্ডল (Atmosphere)", "chapter": "অধ্যায় ২", "subtopics": ["বায়ুমণ্ডলের উষ্ণতা ও বিশ্ব উষ্ণায়ন", "বায়ুচাপ বলয় ও নিয়ত বায়ুপ্রবাহ", "মৌসুমি বায়ু ও ঘূর্ণবাত"]},
        {"name": "বারিমণ্ডল (Hydrosphere)", "chapter": "অধ্যায় ৩", "subtopics": ["সমুদ্রস্রোত ও তার প্রভাব", "জোয়ার-ভাটা (মুখ্য ও গৌণ জোয়ার)"]},
        {"name": "বর্জ্য ব্যবস্থাপনা (Waste Management)", "chapter": "অধ্যায় ৪", "subtopics": ["বর্জ্যের উৎস ও প্রকারভেদ", "বর্জ্যের প্রভাব ও বর্জ্য ব্যবস্থাপনার ৩R পদ্ধতি"]},
        {"name": "ভারত: প্রাকৃতিক ও অর্থনৈতিক পরিবেশ (India)", "chapter": "অধ্যায় ৫", "subtopics": ["প্রাকৃতিক পরিবেশ (ভূপ্রকৃতি, নদনদী, জলবায়ু, মৃত্তিকা, স্বাভাবিক উদ্ভিদ)", "কৃষি (ধান, গম, চা, পাট চাষের অনুকূল পরিবেশ)", "শিল্প (লোহা-ইস্পাত, তথ্যপ্রযুক্তি শিল্প)", "জনসংখ্যা ও পরিবহন"]},
        {"name": "উপগ্রহ চিত্র ও ভূবৈচিত্র্যসূচক মানচিত্র (Satellite Imagery & Topographic Maps)", "chapter": "অধ্যায় ৬", "subtopics": ["উপগ্রহ চিত্র গ্রহণের পর্যায়", "টোপোগ্রাফিকাল ম্যাপ পাঠ ও স্কেল"]}
    ]
}

ALL_FILES = [
    ("wbbse_class_9_physical_science.yaml", cl9_phys_sci),
    ("wbbse_class_10_physical_science.yaml", cl10_phys_sci),
    ("wbbse_class_9_life_science.yaml", cl9_life_sci),
    ("wbbse_class_10_life_science.yaml", cl10_life_sci),
    ("wbbse_class_9_history.yaml", cl9_hist),
    ("wbbse_class_10_history.yaml", cl10_hist),
    ("wbbse_class_9_geography.yaml", cl9_geog),
    ("wbbse_class_10_geography.yaml", cl10_geog),
]

for filename, data in ALL_FILES:
    out_path = TOPIC_DIR / filename
    out_path.write_text(yaml.dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"Created topic index: {out_path.name}")

print("\nAll 8 WBBSE Class 9 & 10 topic index YAML files successfully created!")