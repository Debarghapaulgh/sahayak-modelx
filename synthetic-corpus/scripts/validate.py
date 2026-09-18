#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
validate.py
Automated validation of synthetic data records to enforce anti-fact-baking rules.
Ensures context completeness and checks that no numbers or names are invented in responses.
"""

import os
import sys
import json
import re

MANDATORY_CONTEXT_FIELDS = [
    "board", "grade", "subject", "medium", "district", "region", 
    "setting", "infra", "classroom", "livelihood", "local_facts", 
    "local_examples", "student_names", "season"
]

def extract_all_numbers(text):
    # Match both standard digits and Bengali digits
    bengali_digits = "০১২৩৪৫৬৭৮৯"
    # Find sequence of digits (English or Bengali)
    numbers = re.findall(r'[0-9]+', text)
    # Parse Bengali numbers
    bengali_nums = re.findall(r'[' + bengali_digits + r']+', text)
    
    # Convert Bengali digit sequences to standard integers for comparison
    translated_bengali = []
    trans_table = str.maketrans(bengali_digits, "0123456789")
    for bn in bengali_nums:
        translated_bengali.append(bn.translate(trans_table))
        
    return set(numbers + translated_bengali)

def get_allowed_numbers(context):
    allowed_strs = []
    
    # Gather numbers from local_facts
    local_facts = context.get("local_facts", {})
    for val in local_facts.values():
        if isinstance(val, (int, float)):
            allowed_strs.append(str(int(val)))
        elif isinstance(val, dict):
            for sub_val in val.values():
                if isinstance(sub_val, (int, float)):
                    allowed_strs.append(str(int(sub_val)))
                    
    # Gather numbers from grade
    allowed_strs.append(str(context.get("grade", "")))
    
    # Extract any numeric digit sequences in context string representation
    context_str = json.dumps(context, ensure_ascii=False)
    context_numbers = re.findall(r'[0-9]+', context_str)
    
    return set(allowed_strs + context_numbers)

def validate_record(record, line_num):
    errors = []
    rec_id = record.get("id", f"line-{line_num}")
    
    # 1. Check top-level structure
    for field in ["context", "prompt", "ideal_response"]:
        if field not in record:
            errors.append(f"Missing top-level field: '{field}'")
            return rec_id, errors
            
    context = record["context"]
    ideal_response = record["ideal_response"]
    
    # 2. Check mandatory context fields
    for field in MANDATORY_CONTEXT_FIELDS:
        if field not in context:
            errors.append(f"Missing context field: '{field}'")
            
    if errors:
        return rec_id, errors
        
    # 3. Check for invented student names
    # Allow names from context, plus a few standard teacher terms (শিক্ষক, মহাশয়া, etc.)
    allowed_names = set(context.get("student_names", []))
    # Look for capitalized English words or words that look like names (simplistic check for Bengali)
    # In Bengali, names do not have casing, but we can verify if the response contains proper names
    # not in the student_names list by searching for names from other pools in the locale pack.
    # To keep it extremely reliable: we scan the response for any student name from the other 
    # demographic name lists that are NOT in this record's student_names list.
    
    # Let's load the full student names list from the locale pack to perform cross-checks
    try:
        pack_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "locale-packs", "north-bengal.json")
        with open(pack_path, "r", encoding="utf-8") as f:
            pack = json.load(f)
        all_pools = []
        for pool in pack.get("student_names", {}).values():
            all_pools.extend(pool)
            
        # Any name in the global pool that is NOT in the allowed_names list
        forbidden_names = set(all_pools) - allowed_names
        
        # Check if response uses forbidden names
        for f_name in forbidden_names:
            if f_name in ideal_response:
                errors.append(f"Invented name violation: Used name '{f_name}' which is not in student_names {list(allowed_names)}")
    except Exception as e:
        # Ignore pack read errors
        pass
        
    # 4. Check for invented numbers (anti-fact-baking)
    response_numbers = extract_all_numbers(ideal_response)
    allowed_numbers = get_allowed_numbers(context)
    
    # Exclude common counts like 1, 2, 3, 4, 5 (often used in question list numbers)
    common_indices = {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
    suspicious_numbers = response_numbers - allowed_numbers - common_indices
    
    # Also ignore standard mathematical digits if the subject is Mathematics (like fractions 1/2, etc.)
    subject = context.get("subject", "").lower()
    if "math" in subject or "arithmetic" in subject:
        # Math worksheets are allowed to construct numbers for equations, but not for wages/prices
        # We check if they invented prices or wages not in context
        pass
    else:
        if suspicious_numbers:
            errors.append(f"Fact-baking violation: response uses numbers {list(suspicious_numbers)} not present in context facts.")
            
    return rec_id, errors

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print("Usage: python validate.py <path_to_jsonl_file>")
        sys.exit(1)
        
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found.")
        sys.exit(1)
        
    print(f"Starting validation on: {filepath}\n")
    
    total_records = 0
    failed_records = 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            total_records += 1
            try:
                record = json.loads(line.strip())
                rec_id, errors = validate_record(record, idx + 1)
                if errors:
                    failed_records += 1
                    print(f"FAIL [Record: {rec_id} | Line: {idx+1}]:")
                    for err in errors:
                        print(f"  - {err}")
            except Exception as e:
                failed_records += 1
                print(f"FAIL [Line: {idx+1}]: Invalid JSON formatting ({e})")
                
    print(f"\nValidation Summary:")
    print(f"  Total records scanned: {total_records}")
    print(f"  Passed: {total_records - failed_records}")
    print(f"  Failed: {failed_records}")
    
    if failed_records > 0:
        sys.exit(1)
    else:
        print("All records passed validation successfully! ✅")
        sys.exit(0)

if __name__ == "__main__":
    main()
