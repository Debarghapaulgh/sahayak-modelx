#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_robustness_100.py
Runs a loop 100 times, generating random contexts for all grades (1-10) and
all WBBSE subjects (including split sciences) to verify that there are no
missing chapters, key errors, or demographic mismatches in north-bengal.json.
"""

import os
import sys
import random

# Import from generate_candidate
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from generate_candidate import load_locale_pack, build_context, format_system_prompt

def run_100_checks():
    print("Initializing WBBSE Syllabus Robustness Test (100 Iterations)...")
    
    try:
        pack = load_locale_pack()
    except Exception as e:
        print(f"Failed to load locale pack: {e}")
        return False

    subjects_pool = [
        "Mathematics", 
        "Science", 
        "Physical Science", 
        "Life Science", 
        "Bengali", 
        "English", 
        "History", 
        "Geography"
    ]
    
    success_count = 0
    errors = []

    for i in range(1, 101):
        grade = random.randint(1, 10)
        subject = random.choice(subjects_pool)
        
        # Adjust subject validity based on WBBSE curriculum split rules
        # Rule 1: History and Geography only exist for Grades 6-10
        if subject in ["History", "Geography"] and grade < 6:
            # Re-map to a valid primary subject
            subject = random.choice(["Mathematics", "Science", "Bengali", "English"])
            
        # Rule 2: Physical/Life Science only exist for Grades 9-10
        if subject in ["Physical Science", "Life Science"] and grade < 9:
            # Re-map to unified Science for 1-8
            subject = "Science"
        elif subject == "Science" and grade >= 9:
            # Re-map to split Science for 9-10
            subject = random.choice(["Physical Science", "Life Science"])
            
        # Choose a random mock prompt text
        mock_prompt = f"Mock prompt for {subject} Grade {grade} lesson plan."
        task_type = random.choice(["worksheet", "explanation", "parent_call_script"])

        try:
            # Build context dynamically
            context = build_context(pack, grade, subject)
            
            # Verify context contents
            assert context["board"] == "WBBSE"
            assert context["grade"] == grade
            assert context["subject"] == subject
            assert len(context["student_names"]) == 4
            
            # Check syllabus availability
            subject_map = {"mathematics": "math"}
            clean_sub = subject.lower().replace(" ", "_")
            prefix = subject_map.get(clean_sub, clean_sub)
            expected_key = f"{prefix}_grade{grade}"
            
            # Confirm the JSON key exists and is non-empty
            chapters = pack["syllabus"].get(expected_key, [])
            if not chapters:
                errors.append(f"Iteration {i}: Missing or empty chapters for syllabus key '{expected_key}'")
                continue
                
            assert context["target_chapter"] in chapters
            
            # Format candidate prompt
            prompt = format_system_prompt(context, mock_prompt, task_type)
            assert len(prompt) > 0
            
            success_count += 1
            
        except AssertionError as ae:
            errors.append(f"Iteration {i} failed assertion: {ae}")
        except Exception as e:
            errors.append(f"Iteration {i} raised exception ({subject} G{grade}): {e}")

    print("\n=== TEST RESULTS ===")
    print(f"Successful runs: {success_count}/100")
    if errors:
        print(f"Encountered {len(errors)} errors:")
        for err in errors[:10]:
            print(f" - {err}")
        if len(errors) > 10:
            print(f" ... and {len(errors) - 10} more.")
        return False
    else:
        print("All 100 loops executed with 100% database match and 0 errors!")
        return True

if __name__ == "__main__":
    success = run_100_checks()
    sys.exit(0 if success else 1)
