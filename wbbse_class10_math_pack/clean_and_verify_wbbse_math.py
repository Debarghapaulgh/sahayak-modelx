"""
clean_and_verify_wbbse_math.py
Post-processor & Verifier for WBBSE Class 10 Math Dataset

Usage:
    python clean_and_verify_wbbse_math.py
"""

import os
import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

script_dir = os.path.dirname(os.path.abspath(__file__))
chat_input = os.path.join(script_dir, "wbbse-class10-math-sft-chat.jsonl")
clean_output = os.path.join(script_dir, "wbbse-class10-math-sft-chat-clean.jsonl")

DIGIT_MAP = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

def normalize_bengali_digits(text: str) -> str:
    if not text:
        return text
    # Replace standalone digits
    return text.translate(DIGIT_MAP)

def verify_and_clean():
    if not os.path.exists(chat_input):
        print(f"Input file not found: {chat_input}")
        return

    print(f"Reading SFT Chat dataset from {chat_input}...")
    records = []
    with open(chat_input, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    records.append(data)
                except Exception as e:
                    print(f"JSON Parse Error line {line_no}: {e}")

    print(f"Total Raw Records Read: {len(records)}")

    seen_prompts = set()
    clean_records = []
    ascii_digit_fix_count = 0

    for item in records:
        messages = item.get("messages", [])
        if len(messages) < 3:
            continue

        sys_msg = messages[0].get("content", "")
        user_msg = messages[1].get("content", "")
        asst_msg = messages[2].get("content", "")

        prompt_key = user_msg.strip()[:150]
        if prompt_key in seen_prompts:
            continue
        seen_prompts.add(prompt_key)

        # Normalize stray digits in assistant response
        normalized_asst = normalize_bengali_digits(asst_msg)
        if normalized_asst != asst_msg:
            ascii_digit_fix_count += 1

        cleaned_item = {
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": normalized_asst}
            ]
        }
        clean_records.append(cleaned_item)

    print(f"Deduplicated Unique Records: {len(clean_records)}")
    print(f"Records normalized for Bengali Digits: {ascii_digit_fix_count}")

    with open(clean_output, 'w', encoding='utf-8') as f:
        for item in clean_records:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nVerification Complete! Clean dataset written to: {clean_output}")
    print(f"Final Clean Record Count: {len(clean_records)}")

if __name__ == "__main__":
    verify_and_clean()
