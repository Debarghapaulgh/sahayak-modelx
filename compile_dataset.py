import os
import json
import sys

def convert_sarg_record(record, index):
    x = record.get("x", "")
    y = record.get("y", "")
    category = record.get("category", "")
    
    system_prompt = (
        "You are SARG, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": x},
        {"role": "assistant", "content": y}
    ]
    
    is_class_6_8 = any(c in x for c in ["Class 6", "Class 7", "Class 8", "कक्षा 6", "कक्षा 7", "कक्षा 8"])
    is_class_9_10 = any(c in x for c in ["Class 9", "Class 10", "कक्षा 9", "कक्षा 10"])
    is_class_11_12 = any(c in x for c in ["Class 11", "Class 12", "कक्षा 11", "कक्षा 12"])
    
    entry_type_mod = index % 5
    
    if category == "nsfw" or entry_type_mod == 4:
        meta_category = "NSFW/Safety Test"
        task_type = "Refuse Request"
        if index % 2 == 0:
            target_length = "Extra Long (Multi-page format)"
        else:
            target_length = "Short (1-2 paragraphs)"
    elif category == "off-topic" or entry_type_mod == 3:
        meta_category = "Non-Academic/Casual"
        task_type = "Refuse Request"
        target_length = "Short (1-2 paragraphs)"
    elif category == "identity" or entry_type_mod == 2:
        meta_category = "Identity/Meta"
        task_type = "Explain Concept"
        target_length = "Short (1-2 paragraphs)"
    else:
        is_test_prep = entry_type_mod == 1 or any(term in x.lower() for term in ["prep", "exam", "step-by-step", "परीक्षा", "तैयारी", "தேர்வு", "படிபடியாக"])
        if is_class_6_8 or (index % 3 == 0):
            meta_category = "Borderline Applied"
        else:
            meta_category = "Strict Academic"
            
        if is_test_prep:
            task_type = "Lesson Plan"
            if is_class_11_12:
                target_length = "Extra Long (Multi-page format)"
            else:
                target_length = "Long (Detailed sections)"
        else:
            if is_class_11_12:
                task_type = "Generate Report"
                target_length = "Extra Long (Multi-page format)"
            elif is_class_9_10:
                task_type = "Solve Question"
                target_length = "Long (Detailed sections)"
            else:
                task_type = "Explain Concept"
                target_length = "Short (1-2 paragraphs)"
                
    return {
        "messages": messages,
        "meta": {
            "category": meta_category,
            "task_type": task_type,
            "target_length": target_length
        }
    }

def convert_persona_record(record, index):
    convs = record.get("conversations", [])
    metadata = record.get("metadata", {})
    target_concept = record.get("target_concept", "")
    grade_level = metadata.get("grade_level", "")
    
    system_prompt = (
        "You are SARG, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    greeting_lang = record.get("language", "en")
    if greeting_lang == "hi":
        user_greeting = f"नमस्ते, आइए {grade_level} के {target_concept} विषय पर चर्चा करें।"
    elif greeting_lang == "hinglish":
        user_greeting = f"Hello, let's learn about {target_concept} in {grade_level}."
    elif greeting_lang == "ta":
        user_greeting = f"வணக்கம், {grade_level} வகுப்பில் உள்ள {target_concept} தலைப்பைப் பற்றி படிப்போம்."
    else:
        user_greeting = f"Hello, let's learn about {target_concept} in {grade_level}."
        
    messages.append({"role": "user", "content": user_greeting})
    
    for turn in convs:
        role = turn.get("from", "")
        val = turn.get("value", "")
        if role == "gpt" or role == "assistant":
            messages.append({"role": "assistant", "content": val})
        else:
            messages.append({"role": "user", "content": val})
            
    if any(g in grade_level for g in ["Class 6", "Class 7", "Class 8", "Grade 6", "Grade 7", "Grade 8"]):
        meta_category = "Borderline Applied"
    else:
        meta_category = "Strict Academic"
        
    task_type = "Lesson Plan"
    target_length = "Long (Detailed sections)"
    
    return {
        "messages": messages,
        "meta": {
            "category": meta_category,
            "task_type": task_type,
            "target_length": target_length
        }
    }

def convert_localised_record(record, index):
    convs = record.get("conversations", [])
    metadata = record.get("metadata", {})
    target_concept = record.get("target_concept", "")
    board = record.get("board", "cbse")
    
    system_prompt = (
        "You are SARG, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for turn in convs:
        role = turn.get("from", "")
        val = turn.get("value", "")
        if role == "gpt" or role == "assistant":
            messages.append({"role": "assistant", "content": val})
        else:
            messages.append({"role": "user", "content": val})
            
    meta_category = "Borderline Applied" if board != "cbse" else "Strict Academic"
    task_type = "Explain Concept"
    target_length = "Long (Detailed sections)"
    
    return {
        "messages": messages,
        "meta": {
            "category": meta_category,
            "task_type": task_type,
            "target_length": target_length
        }
    }

def convert_comprehensive_record(record, index):
    convs = record.get("conversations", [])
    metadata = record.get("metadata", {})
    category = metadata.get("category", "Strictly Academic")
    target_length = metadata.get("target_length", "Medium (1-2 paragraphs)")
    board = record.get("board", "cbse")
    
    system_prompt = (
        "You are SARG, a specialized academic tutor. You treat all practical, applied, "
        "and technical subjects as valid academic inquiries. Whenever asked for detailed "
        "or complex documentation, you output thoroughly structured academic reports."
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    
    for turn in convs:
        role = turn.get("from", "")
        val = turn.get("value", "")
        if role == "gpt" or role == "assistant":
            messages.append({"role": "assistant", "content": val})
        else:
            messages.append({"role": "user", "content": val})
            
    if category == "NSFW/Safety Test":
        meta_category = "NSFW/Safety Test"
        task_type = "Refuse Request"
    elif category == "Non-Academic/Casual":
        meta_category = "Non-Academic/Casual"
        task_type = "Refuse Request"
    elif category == "Identity/Meta":
        meta_category = "Identity/Meta"
        task_type = "Explain Concept"
    else:
        meta_category = "Borderline Applied" if board != "cbse" else "Strict Academic"
        task_type = "Explain Concept" if category == "Strictly Academic" else "Solve Question"
        
    return {
        "messages": messages,
        "meta": {
            "category": meta_category,
            "task_type": task_type,
            "target_length": target_length
        }
    }

def main():
    # Make paths relative to repository root
    sarg_input_path = "output/sarg_llm_finetuning_dataset.jsonl"
    sarg_input_path_alt = "sarg_llama_synthetic (1).jsonl"
    persona_input_path = "output/synthetic_tutor_extensive_persona_dataset.jsonl"
    monolingual_input_path = "output/pan_ncert_pure_monolingual_indic_dataset.jsonl"
    localised_input_path = "output/localised_sarg_dialogues.jsonl"
    simulated_input_path = "output/localised_socratic_simulation.jsonl"
    comprehensive_input_path = "output/comprehensive_spectrum_dialogues.jsonl"
    aikosh_input_path = "output/aikosh_compiled_dataset_for_SargLLM.jsonl"
    
    output_path = "output/sarg_llama_synthetic_compiled.jsonl"
    
    print("Beginning compiled dataset generation...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    compiled_records = []
    total_count = 0
    
    # 1. Process SARG LLM Dataset (40,000 records)
    target_sarg_path = sarg_input_path if os.path.exists(sarg_input_path) else (sarg_input_path_alt if os.path.exists(sarg_input_path_alt) else None)
    if target_sarg_path:
        print(f"Adding records from: {target_sarg_path}")
        sarg_count = 0
        with open(target_sarg_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_sarg_record(record, index)
                    compiled_records.append(converted)
                    sarg_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing SARG record {index}: {e}")
        print(f"Added {sarg_count} SARG LLM records.")
    else:
        print("Warning: SARG LLM input path not found. Skipping.")

    # 2. Process Student Persona Dataset (15,000 records)
    if os.path.exists(persona_input_path):
        print(f"Adding records from: {persona_input_path}")
        persona_count = 0
        with open(persona_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_persona_record(record, index)
                    compiled_records.append(converted)
                    persona_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing Persona record {index}: {e}")
        print(f"Added {persona_count} Student Persona records.")
    else:
        print("Warning: Student Persona input path not found. Skipping.")

    # 3. Process Monolingual Indic Dataset (30,000 records)
    if os.path.exists(monolingual_input_path):
        print(f"Adding records from: {monolingual_input_path}")
        mono_count = 0
        with open(monolingual_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_persona_record(record, index)
                    compiled_records.append(converted)
                    mono_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing Monolingual record {index}: {e}")
        print(f"Added {mono_count} Monolingual Indic records.")
    else:
        print("Warning: Monolingual Indic input path not found. Skipping.")
        
    # 4. Process Localised SARG dialogues (Template version)
    if os.path.exists(localised_input_path):
        print(f"Adding records from: {localised_input_path}")
        loc_count = 0
        with open(localised_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_localised_record(record, index)
                    compiled_records.append(converted)
                    loc_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing Localised record {index}: {e}")
        print(f"Added {loc_count} Localised SARG records.")
    else:
        print("Warning: Localised SARG dialogues input path not found. Skipping.")

    # 5. Process Localised Simulated Socratic dialogues (Simulation version)
    if os.path.exists(simulated_input_path):
        print(f"Adding records from: {simulated_input_path}")
        sim_count = 0
        with open(simulated_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_localised_record(record, index)
                    compiled_records.append(converted)
                    sim_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing Simulated record {index}: {e}")
        print(f"Added {sim_count} Localised Simulated SARG records.")
    else:
        print("Warning: Localised Simulated SARG dialogues input path not found. Skipping.")
        
    # 6. Process Comprehensive Spectrum dialogues
    if os.path.exists(comprehensive_input_path):
        print(f"Adding records from: {comprehensive_input_path}")
        comp_count = 0
        with open(comprehensive_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    converted = convert_comprehensive_record(record, index)
                    compiled_records.append(converted)
                    comp_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing Comprehensive record {index}: {e}")
        print(f"Added {comp_count} Comprehensive Spectrum records.")
    else:
        print("Warning: Comprehensive Spectrum dialogues input path not found. Skipping.")

    # 7. Process Valuable AIKosh datasets (5,700+ records)
    if os.path.exists(aikosh_input_path):
        print(f"Adding records from: {aikosh_input_path}")
        aikosh_count = 0
        with open(aikosh_input_path, "r", encoding="utf-8") as f_in:
            for index, line in enumerate(f_in):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    compiled_records.append(record)
                    aikosh_count += 1
                    total_count += 1
                except Exception as e:
                    print(f"Error parsing AIKosh record {index}: {e}")
        print(f"Added {aikosh_count} Valuable AIKosh records.")
    else:
        print("Warning: Valuable AIKosh compiled input path not found. Skipping.")

    # Implement global dataset shuffling to prevent catastrophic forgetting
    print("Shuffling compiled records globally to prevent catastrophic forgetting...")
    import random
    random.seed(42) # Deterministic shuffle for reproducibility
    random.shuffle(compiled_records)
    
    print(f"Writing {len(compiled_records)} shuffled records to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f_out:
        for record in compiled_records:
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f"Successfully compiled and shuffled {total_count} records into {output_path}.")
    
    # Copy to Downloads and Desktop
    user_profile = os.environ.get("USERPROFILE", "C:\\Users\\HP")
    downloads_path = os.path.join(user_profile, "Downloads", "sarg_llama_synthetic_compiled.jsonl")
    desktop_path = os.path.join(user_profile, "Desktop", "sarg_llama_synthetic_compiled.jsonl")
    
    try:
        import shutil
        shutil.copy2(output_path, downloads_path)
        print(f"Copied to: {downloads_path}")
    except Exception as e:
        print(f"Failed to copy to Downloads: {e}")
        
    try:
        import shutil
        shutil.copy2(output_path, desktop_path)
        print(f"Copied to: {desktop_path}")
    except Exception as e:
        print(f"Failed to copy to Desktop: {e}")

if __name__ == "__main__":
    main()
