import argparse
import asyncio
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from pydantic import BaseModel

sys.stdout.reconfigure(encoding='utf-8')

# Universal LLM Generator Script for SahayakAI CBSE Bengali SFT Dataset
# Native support for Qwen (Alibaba Cloud ModelStudio/DashScope), Gemini, OpenAI, Groq, Anthropic, OpenRouter, DeepSeek.

CANDIDATES_FILE = "sample_input_candidates.jsonl"
OUTPUT_CHAT_FILE = "northbengal-sft-chat-bengali-clean.jsonl"

DISTRICT_BN = {
    'darjeeling': 'দার্জিলিং',
    'kalimpong': 'কালিম্পং',
    'coochbehar': 'কোচবিহার',
    'cooch behar': 'কোচবিহার',
    'jalpaiguri': 'জলপাইগুড়ি',
    'alipurduar': 'আলিপুরদুয়ার',
    'malda': 'মালদা',
    'uttardinajpur': 'উত্তর দিনাজপুর',
    'uttar dinajpur': 'উত্তর দিনাজপুর',
    'dakshindinajpur': 'দক্ষিণ দিনাজপুর',
    'dakshin dinajpur': 'দক্ষিণ দিনাজপুর',
    'siliguri': 'শিলিগুড়ি'
}

GRADE_BN = {
    '1': '১ম', '2': '২য়', '3': '৩য়', '4': '৪র্থ', '5': '৫ম',
    '6': '৬ষ্ঠ', '7': '৭ম', '8': '৮ম', '9': '৯ম', '10': '১০ম',
    '11': 'একাদশ', '12': 'দ্বাদশ'
}

SUBJECT_BN_EN = {
    'math': 'গণিত (Mathematics)',
    'mathematics': 'গণিত (Mathematics)',
    'science': 'বিজ্ঞান (Science)',
    'physics': 'ভৌত বিজ্ঞান (Physics)',
    'chemistry': 'রসায়ন (Chemistry)',
    'biology': 'জীবন বিজ্ঞান (Biology)',
    'geography': 'ভূগোল (Geography)',
    'history': 'ইতিহাস (History)',
    'economics': 'অর্থনীতি (Economics)',
    'english': 'ইংরেজি (English)',
    'social science': 'সমাজবিজ্ঞান (Social Science)',
    'socialstudies': 'সমাজবিজ্ঞান (Social Science)',
    'social sc': 'সমাজবিজ্ঞান (Social Science)'
}

BENGALI_SYSTEM_PREAMBLE = """তুমি 'সহায়ক এআই' (Sahayak AI) — পশ্চিমবঙ্গ ও উত্তরবঙ্গের সিবিএসই (CBSE / NCERT) বেঙ্গলি মিডিয়াম স্কুলের শিক্ষার্থী ও শিক্ষক মহাশয়দের সহায়তার জন্য তৈরি এক অত্যন্ত অভিজ্ঞ, বিশেষ শিক্ষণ সাহায্যকারী AI টিউটর।
তোমার কাজ হলো উত্তরবঙ্গের শিক্ষার্থীদের (যেমন: শিলিগুড়ি, জলপাইগুড়ি, দার্জিলিং, কালিম্পং, কোচবিহার, আলিপুরদুয়ার, মালদা, দক্ষিণ ও উত্তর দিনাজপুর) সিবিএসই/এনসিইআরটি (CBSE/NCERT) পাঠ্যসূচি অনুযায়ী সহজ, সাবলীল এবং সঠিক বাংলা ভাষায় (বাংলা লিপি ও সংখ্যা) পাঠদান ও সহায়তা করা।

নিয়মাবলী ও সম্বোধন বিধি:
১. শিক্ষক মহাশয় / অভিভাবকের উদ্দেশ্যে অনুরোধের ক্ষেত্রে: সর্বদা শ্রদ্ধাসূচক ও সম্মানীয় বাক্য গঠন ব্যবহার করবে ('আপনি' সম্বোধন: 'লিখুন', 'বলুন', 'করুন', 'লেখেন')।
২. শিক্ষার্থীদের উদ্দেশ্যে শিক্ষা ও পরামর্শের ক্ষেত্রে: সহজ, বন্ধুভাবাপন্ন ও প্রাত্যহিক বাক্য গঠন ব্যবহার করবে ('তুমি/তোমরা' সম্বোধন: 'লেখো', 'বলো', 'করো', 'দেখো', 'লিখলো')।
৩. সমস্ত সংখ্যা বাংলা লিপিতে লিখবে (০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯)।
৪. সিবিএসই/এনসিইআরটি পাঠ্যক্রমের সঠিক বাংলা পরিভাষা ব্যবহার করবে (যেমন: ল.সা.গু., গ.সা.গু., ভগ্নাংশ, সমীকরণ, ক্ষেত্রফল, পরিসীমা, সালোকসংশ্লেষ, কোশ, অম্ল, ক্ষারক, বাস্তুতন্ত্র)।
৫. একজন বন্ধুভাবাপন্ন ও শ্রদ্ধাশীল সহায়ক AI হিসেবে সর্বদা স্পষ্ট, সহজ ও প্রাণবন্ত ভঙ্গিতে উত্তর প্রদান করবে।"""

def build_sys_prompt(rec: dict) -> str:
    c_dict = rec.get('cell', {})
    ctx_dict = rec.get('context', {})
    
    subj_raw = ctx_dict.get('subject') or c_dict.get('subject', 'Science')
    grade_raw = str(ctx_dict.get('grade') or c_dict.get('grade', '9'))
    topic_raw = ctx_dict.get('topic') or c_dict.get('topic_name', 'পাঠ্য বিষয়')
    dist_raw = ctx_dict.get('district') or c_dict.get('district', 'দার্জিলিং')
    
    subj_bn = SUBJECT_BN_EN.get(str(subj_raw).lower(), f"{subj_raw} ({subj_raw})")
    grade_bn = GRADE_BN.get(grade_raw, f"{grade_raw}-তম")
    dist_bn = DISTRICT_BN.get(str(dist_raw).lower(), str(dist_raw))
    
    return f"""{BENGALI_SYSTEM_PREAMBLE}

সহায়ক এআই (Sahayak AI) সিবিএসই / এনসিইআরটি (CBSE / NCERT) পাঠ্যসূচি বিবরণী:
- বিষয়: {subj_bn}
- শ্রেণি: {grade_bn} শ্রেণি (CBSE/NCERT)
- বিষয়বস্তু: {topic_raw}
- অঞ্চল/জেলা: {dist_bn}"""

PROMPT_TEMPLATE = """You are an expert West Bengal Master Teacher in CBSE / NCERT Bengali Medium.
Your task is to re-write and transcreate the following English CBSE prompt and response into 100% FLUID, NATURAL, GRAMMATICALLY PERFECT West Bengal Bengali (বাংলা লিপি).

CRITICAL RULES:
1. USER PROMPT:
   - Must be a natural query or request in West Bengal Bengali without addressing AI as 'শিক্ষক মহাশয়' or 'প্রিয় শিক্ষক'.
   - Examples: "একাদশ শ্রেণির অর্থনীতির জন্য...", "সহায়ক এআই, শ্রেণি ৯-এর বিজ্ঞানের...", "সমকোণী ত্রিভুজের..."

2. GRAMMAR & VERB AGREEMENT (VERY IMPORTANT):
   - Non-human / inanimate 3rd person subjects (villi, organs, cell, temperature, pressure, enzyme, speed): Use standard 3rd person verbs ('কমায়', 'বাড়ায়', 'দেখায়', 'সাহায্য করে'). NEVER use 'কমান', 'বাড়ান', 'দেখান', 'করেন'!
   - Student characters (Sujan, Sonam, Dawa, Lakpa, Pemba): Use standard 3rd person verbs ('বলল', 'বলে', 'কমায়').

3. NUMERALS & DIALECT:
   - 100% Bengali script digits (০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯).
   - Use 'জল' for water (NEVER 'পানি').

Output JSON format:
{
  "bengali_prompt": "...",
  "bengali_response": "..."
}

English Prompt: {eng_prompt}
English Response: {eng_response}
"""

def clean_text_grammar(text: str) -> str:
    if not text:
        return text
    text = text.replace('\u09af\u09bc', '\u09df')
    text = re.sub(r'কমান,\s*ফলে', 'কমায়, ফলে', text)
    text = re.sub(r'বাড়ান,\s*ফলে', 'বাড়ায়, ফলে', text)
    text = re.sub(r"এখানে\s+'কমান'\s*\((?:decrease|ডিক্রিজ)\)", "এখানে 'কমায়' (decrease)", text)
    text = re.sub(r"এখানে\s+'কমান'", "এখানে 'কমায়'", text)
    text = re.sub(r'কমান\s+না\b', 'কমায় না', text)
    text = re.sub(r'বাড়ান\s+না\b', 'বাড়ায় না', text)
    text = re.sub(r'আপনি/করুন', 'আপনি', text)
    text = re.sub(r'তুমি/তোমরা', 'তুমি', text)
    return text.strip()

def detect_provider_and_key(cli_key=None, cli_provider=None):
    key = cli_key
    provider = cli_provider

    if not key:
        for env_var, prov in [
            ("DASHSCOPE_API_KEY", "qwen"),
            ("QWEN_API_KEY", "qwen"),
            ("GEMINI_API_KEY", "gemini"),
            ("GOOGLE_API_KEY", "gemini"),
            ("OPENAI_API_KEY", "openai"),
            ("GROQ_API_KEY", "groq"),
            ("OPENROUTER_API_KEY", "openrouter")
        ]:
            if os.environ.get(env_var):
                key = os.environ.get(env_var)
                if not provider:
                    provider = prov
                break

    if not key:
        print("\n--- LLM API Key Setup ---")
        print("Supported providers: qwen (Alibaba Cloud ModelStudio), gemini, openai, groq, openrouter")
        key = input("Enter your API Key: ").strip()
        if not key:
            raise ValueError("API Key is required!")

    if not provider:
        if key.startswith("sk-ws-"):
            provider = "qwen"
        elif key.startswith("gsk_"):
            provider = "groq"
        elif key.startswith("sk-or-"):
            provider = "openrouter"
        elif key.startswith("AQ.") or key.startswith("AIza"):
            provider = "gemini"
        else:
            provider = "qwen"

    return provider.lower(), key

def call_qwen_api(key: str, prompt_text: str, model_name: str = "qwen-plus"):
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.1
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Authorization', f'Bearer {key}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data['choices'][0]['message']['content']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Universal CBSE Bengali SFT Dataset Generator (Qwen / Gemini / OpenAI / Groq)")
    parser.add_argument("--api-key", type=str, help="API Key")
    parser.add_argument("--provider", type=str, help="Provider name (qwen, gemini, openai, groq, openrouter)")
    parser.add_argument("--model", type=str, default="qwen-plus", help="Model name (e.g. qwen-plus, qwen-turbo, qwen2.5-72b-instruct)")
    parser.add_argument("--input", type=str, default=CANDIDATES_FILE, help="Path to input candidates jsonl")
    parser.add_argument("--output", type=str, default=OUTPUT_CHAT_FILE, help="Path to output chat jsonl")
    args = parser.parse_args()

    provider, key = detect_provider_and_key(args.api_key, args.provider)
    print(f"✅ Provider Selected: {provider.upper()}")
    print(f"🔑 Key Loaded: {key[:8]}...{key[-4:]}")

    if provider == "qwen":
        print(f"🌐 Target Endpoint: https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions")
        print(f"🤖 Model: {args.model}")
        print("\nTesting Qwen Connection...")
        sample_res = call_qwen_api(key, "Say Hello in Bengali script.", args.model)
        print(f"Response from Qwen: {sample_res}")
