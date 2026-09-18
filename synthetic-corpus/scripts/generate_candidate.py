#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_candidate.py
Generates the context-injected LLM prompts using the rich demographics,
occupations, names, and syllabi from north-bengal.json.
"""

import os
import json
import random
import sys

# Define base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_PACK_PATH = os.path.join(BASE_DIR, "locale-packs", "north-bengal.json")

def load_locale_pack():
    if not os.path.exists(LOCALE_PACK_PATH):
        raise FileNotFoundError(f"Locale pack not found at {LOCALE_PACK_PATH}. Run step 1 first.")
    with open(LOCALE_PACK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_context(pack, grade, subject, district=None, livelihood=None):
    """
    Dynamically builds a context block by selecting geographically and demographically
    consistent facts, names, and occupations based on the chosen district.
    """
    # 1. Select District
    if not district:
        district = random.choice(pack["districts"])
    
    # 2. Select Setting and Classroom format
    setting = random.choice(pack["settings"])
    infra = random.sample(pack["infra_defaults"], k=random.randint(1, 2))
    classroom = random.choice(["single_grade", "multi_grade"])
    
    # 3. Determine consistent Livelihoods, Examples, Names, and Seasons based on geography
    student_names = []
    local_examples = []
    livelihoods_list = []
    season = ""
    local_facts = {"currency": "INR"}
    
    # Darjeeling / Kalimpong (Hills)
    if district in ["Darjeeling", "Kalimpong"]:
        livelihoods_pool = ["orange_orchardist", "cardamom_farmer", "floriculturist", "homestay_host", "tea_garden_plucker"]
        if not livelihood or livelihood not in livelihoods_pool:
            livelihood = random.choice(livelihoods_pool)
        
        # Name mix: 70% Gorkha/Nepali, 30% Lepcha/Bhutia
        names_pool = pack["student_names"]["gorkha_nepali"] + pack["student_names"]["lepcha_bhutia"]
        student_names = random.sample(names_pool, k=4)
        
        # Examples
        local_examples = [ex for ex in pack["local_examples"] if ex in ["orange orchard", "cardamom", "cinchona bark", "homestay register", "toy train", "tea leaves"]]
        
        # Season
        if livelihood == "orange_orchardist":
            season = "orange_picking_season"
        else:
            season = "plucking_season"
            
    # Malda (Mangoes & Silk)
    elif district == "Malda":
      livelihoods_pool = ["sericulturist", "mango_orchardist", "toto_driver"]
      if not livelihood or livelihood not in livelihoods_pool:
          livelihood = random.choice(livelihoods_pool)
      
      # Name mix: 60% Bengali Muslim, 40% Bengali Hindu
      names_pool = pack["student_names"]["bengali_muslim"] + pack["student_names"]["bengali"]
      student_names = random.sample(names_pool, k=4)
      local_examples = [ex for ex in pack["local_examples"] if ex in ["Fazli mango", "silk cocoon", "paddy field"]]
      season = "mango_harvest_season"
      
    # Cooch Behar (Jute & Betel Nut)
    elif district == "Cooch Behar":
      livelihoods_pool = ["jute_farmer", "betel_nut_grower", "bhawaiya_musician", "bamboo_craftsman"]
      if not livelihood or livelihood not in livelihoods_pool:
          livelihood = random.choice(livelihoods_pool)
          
      # Name mix: 50% Rajbanshi, 30% Bengali Muslim, 20% Bengali Hindu
      names_pool = pack["student_names"]["rajbanshi"] + pack["student_names"]["bengali_muslim"] + pack["student_names"]["bengali"]
      student_names = random.sample(names_pool, k=4)
      local_examples = [ex for ex in pack["local_examples"] if ex in ["jute fiber bundle", "supari tree", "Bhawaiya dotara", "bamboo mat"]]
      
      if livelihood == "jute_farmer":
          season = "jute_rotting_season"
      else:
          season = "plucking_season"
          
    # Jalpaiguri, Alipurduar, Dinajpurs (Dooars Plains)
    else:
      livelihoods_pool = ["tea_garden_plucker", "stone_quarry_worker", "bamboo_craftsman", "forest_guard"]
      if not livelihood or livelihood not in livelihoods_pool:
          livelihood = random.choice(livelihoods_pool)
          
      # Determine name mix based on specific district
      if district in ["Uttar Dinajpur", "Dakshin Dinajpur"]:
          # High proportion of Bengali Muslim & Rajbanshi/Bengali Hindu
          names_pool = pack["student_names"]["bengali_muslim"] + pack["student_names"]["rajbanshi"] + pack["student_names"]["bengali"]
      else:
          # Jalpaiguri & Alipurduar (Dooars tea belt): high Adivasi/Sadri, Rajbanshi, and Bengali
          names_pool = pack["student_names"]["adivasi_sadri"] + pack["student_names"]["rajbanshi"] + pack["student_names"]["bengali"] + pack["student_names"]["bengali_muslim"]
          
      student_names = random.sample(names_pool, k=4)
      local_examples = [ex for ex in pack["local_examples"] if ex in ["tea leaves", "plucking basket", "riverbed boulder pile", "river Teesta", "bamboo mat"]]
      season = "plucking_season"

    # 4. Map occupation-specific wages and facts
    livelihoods_list.append(livelihood)
    occ_detail = pack["occupations_detail"].get(livelihood, {})
    
    if "daily_wage_inr" in occ_detail:
        local_facts["daily_wage"] = occ_detail["daily_wage_inr"]
    elif "estimated_daily_income_inr" in occ_detail:
        local_facts["estimated_daily_income"] = occ_detail["estimated_daily_income_inr"]
    else:
        local_facts["daily_wage"] = pack["local_facts"]["tea_garden_daily_wage"]
        
    # Append custom pricing facts matching the selected examples
    for item, price in pack["local_facts"]["common_prices"].items():
        if item == "toto_fare" and livelihood == "toto_driver":
            local_facts[item] = price
        elif item == "supari_bundle" and livelihood == "betel_nut_grower":
            local_facts[item] = price
        elif item == "jute_bundle" and livelihood == "jute_farmer":
            local_facts[item] = price
        elif item in ["notebook", "pen", "kg_rice"]:
            local_facts[item] = price

    # 5. Extract Syllabus Chapters
    subject_map = {
        "mathematics": "math",
        "math": "math",
        "science": "science",
        "physical_science": "physical_science",
        "life_science": "life_science",
        "bengali": "bengali",
        "english": "english",
        "history": "history",
        "geography": "geography"
    }
    clean_subject = subject.lower().replace(" ", "_")
    prefix = subject_map.get(clean_subject, clean_subject)
    syllabus_key = f"{prefix}_grade{grade}"
    chapters_pool = pack["syllabus"].get(syllabus_key, [])
    
    # 6. Build the Context Object
    context = {
        "board": pack["board"],
        "grade": grade,
        "subject": subject,
        "medium": pack["medium"],
        "district": district,
        "region": pack["region"],
        "setting": setting,
        "infra": infra,
        "classroom": classroom,
        "livelihood": livelihoods_list,
        "local_facts": local_facts,
        "local_examples": local_examples,
        "student_names": student_names,
        "season": pack["season_calendar"].get(season, season),
        "target_chapter": random.choice(chapters_pool) if chapters_pool else None
    }
    
    return context

def format_system_prompt(prompt_text, task_type):
    system_prompt = (
        "System: You are an expert school teaching assistant for WBBSE (West Bengal Board), Bengali-medium in North Bengal.\n"
        "Your task is to write correct, pedagogical content (like worksheets, explanations, scripts) in Bengali matching the teacher's request.\n\n"
        f"Teacher Request: {prompt_text}\n\n"
        "Assistant Response:"
    )
    return system_prompt

def main():
    # Force UTF-8 output encoding for terminals
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

    if len(sys.argv) < 5:
        print("Usage: python generate_candidate.py <grade> <subject> <task_type> <prompt_text>")
        print("Example: python generate_candidate.py 5 Mathematics worksheet \"ভাগ অংকের ৫টি প্রশ্ন দিন\"")
        sys.exit(1)
        
    grade = int(sys.argv[1])
    subject = sys.argv[2]
    task_type = sys.argv[3]
    prompt_text = sys.argv[4]
    
    try:
        full_prompt = format_system_prompt(prompt_text, task_type)
        
        print("\n--- GENERATED PROMPT ---\n")
        print(full_prompt)
        print("\n------------------------\n")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
