#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scrub_pii.py
Scrubs PII (Personally Identifiable Information) such as phone numbers, emails, 
and real names from the dataset before training.
"""

import os
import sys
import json
import re

# Phone number matching (Indian formats + general)
PHONE_REGEX = re.compile(r'(\+91[\-\s]?)?[6-9]\d{9}|\b\d{5}[\-\s]?\d{5}\b')
# Email matching
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def scrub_text(text, allowed_names):
    if not text:
        return ""
        
    # Replace emails
    text = EMAIL_REGEX.sub("[EMAIL]", text)
    # Replace phone numbers
    text = PHONE_REGEX.sub("[PHONE]", text)
    
    # Simple name scrubbing: replace any name in global list that is not in the allowed names list
    # with a generic term [Student] or [শিক্ষার্থী] in Bengali tasks
    try:
        pack_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locale-packs", "north-bengal.json")
        with open(pack_path, "r", encoding="utf-8") as f:
            pack = json.load(f)
        all_pools = []
        for pool in pack.get("student_names", {}).values():
            all_pools.extend(pool)
            
        # Forbidden names: names from other districts/pools that might have leaked
        forbidden_names = set(all_pools) - set(allowed_names)
        for f_name in forbidden_names:
            if f_name in text:
                text = text.replace(f_name, "[শিক্ষার্থী]")
    except Exception:
        pass
        
    return text

def scrub_record(record):
    if "context" not in record:
        return record
        
    context = record["context"]
    allowed_names = context.get("student_names", [])
    
    # Scrub prompt
    if "prompt" in record:
        record["prompt"] = scrub_text(record["prompt"], allowed_names)
        
    # Scrub ideal_response
    if "ideal_response" in record:
        record["ideal_response"] = scrub_text(record["ideal_response"], allowed_names)
        
    return record

def main():
    if len(sys.argv) < 3:
        print("Usage: python scrub_pii.py <input_jsonl> <output_jsonl>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(1)
        
    print(f"Scrubbing PII from {input_file} ...")
    
    records_processed = 0
    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
        for line in infile:
            if not line.strip():
                continue
            try:
                record = json.loads(line.strip())
                cleaned_record = scrub_record(record)
                outfile.write(json.dumps(cleaned_record, ensure_ascii=False) + "\n")
                records_processed += 1
            except Exception as e:
                print(f"Error parsing line: {e}")
                
    print(f"PII Scrubbing Complete. Cleaned {records_processed} records. Output saved to {output_file} ✅")

if __name__ == "__main__":
    main()
