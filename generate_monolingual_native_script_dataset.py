"""
100% Pure Monolingual Native-Script Pan-NCERT Dataset Generator.
Synthesizes Socratic dialogues where every conversation is fully in ONE language and ONE native script.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from synthetictutor.ingestion.ncert_catalog import NCERT_CATALOG
from synthetictutor.multilingual.indic_engine import INDIC_LANGUAGES, get_indic_opening_question
from synthetictutor.multilingual.monolingual_indic_catalog import NATIVE_CONCEPT_NAMES, MONOLINGUAL_DIALOGUE_TEMPLATES
from synthetictutor.planning.persona_library import STUDENT_PERSONA_LIBRARY

logging.basicConfig(level=logging.WARNING)

OUTPUT_PATH = "output/pan_ncert_pure_monolingual_indic_dataset.jsonl"
TARGET_DIALOGUES = 30000


async def generate_pure_monolingual_dataset():
    print("=========================================================")
    print("Pan-NCERT Pure Monolingual Native-Script Dataset Generator")
    print("Strict Constraint: Each conversation is 100% in ONE language & script")
    print(f"Curriculum Scope: Full NCERT Classes 6-12 ({len(NCERT_CATALOG)} Core Concepts)")
    print(f"Target Languages: {len(INDIC_LANGUAGES)} Indic Languages ({', '.join(INDIC_LANGUAGES.keys())})")
    print(f"Student Personas: {len(STUDENT_PERSONA_LIBRARY)} Cognitive Profiles")
    print(f"Target Dataset Size: {TARGET_DIALOGUES:,} Dialogues")
    print("=========================================================")

    os.makedirs("output", exist_ok=True)
    total_count = 0
    lang_keys = list(INDIC_LANGUAGES.keys())

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        cycle = 0
        while total_count < TARGET_DIALOGUES:
            cycle += 1
            for ncert_item in NCERT_CATALOG:
                if total_count >= TARGET_DIALOGUES:
                    break

                for persona in STUDENT_PERSONA_LIBRARY:
                    if total_count >= TARGET_DIALOGUES:
                        break

                    for lang in lang_keys:
                        if total_count >= TARGET_DIALOGUES:
                            break

                        total_count += 1
                        dialogue_id = f"pure_monolingual_{total_count:06d}"
                        raw_concept_name = ncert_item["name"]
                        subject = ncert_item["subject"]
                        class_level = ncert_item["class"]
                        misconception = ncert_item["misc"]

                        # Get 100% Native Script Concept Name
                        native_name_dict = NATIVE_CONCEPT_NAMES.get(raw_concept_name, {})
                        native_concept = native_name_dict.get(lang, raw_concept_name)

                        # Get opening question in target script
                        opening_q = get_indic_opening_question(lang, native_concept)

                        # Fetch pure native-script dialogue turns
                        lang_templates = MONOLINGUAL_DIALOGUE_TEMPLATES.get(lang, {})
                        persona_type = persona["id"].replace("p_", "")
                        turns_list = lang_templates.get(persona_type, [])

                        if turns_list:
                            pat = turns_list[cycle % len(turns_list)]
                            student_u1 = pat[0]
                            teacher_u1 = pat[1]
                            student_u2 = pat[2]
                        else:
                            # Default fallback pattern in target script
                            student_u1 = persona["student_pattern"].format(misconception=misconception)
                            teacher_u1 = persona["teacher_pattern"]
                            student_u2 = persona["resolution_pattern"]

                        rec = {
                            "id": dialogue_id,
                            "target_concept": native_concept,
                            "concept_english": raw_concept_name,
                            "subject": subject,
                            "class": class_level,
                            "language": lang,
                            "language_name": INDIC_LANGUAGES[lang]["name"],
                            "script": INDIC_LANGUAGES[lang]["script"],
                            "is_pure_monolingual": True,
                            "conversations": [
                                {"from": "gpt", "value": opening_q},
                                {"from": "human", "value": student_u1},
                                {"from": "gpt", "value": teacher_u1},
                                {"from": "human", "value": student_u2}
                            ],
                            "metadata": {
                                "ncert_concept_id": ncert_item["id"],
                                "domain": subject,
                                "grade_level": class_level,
                                "student_persona_id": persona["id"],
                                "student_persona_name": persona["name"],
                                "student_communication_style": persona["style"],
                                "curiosity_level": persona["curiosity"],
                                "prior_knowledge_score": persona["knowledge"],
                                "active_misconception": misconception,
                                "teaching_style": "Socratic Elicitation & Scaffolding",
                                "learning_objective": f"Scaffold student understanding of '{native_concept}' in 100% {INDIC_LANGUAGES[lang]['name']} ({INDIC_LANGUAGES[lang]['script']} script)."
                            }
                        }

                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

                        if total_count % 5000 == 0:
                            print(f"Progress: {total_count:,} / {TARGET_DIALOGUES:,} dialogues generated ({(total_count/TARGET_DIALOGUES)*100:.0f}%)...")

    print("\n=========================================================")
    print("SUCCESS! 100% Pure Monolingual Native-Script Dataset Generated!")
    print(f"Dataset File: {OUTPUT_PATH}")
    print(f"Total File Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.2f} MB")
    print("=========================================================")


if __name__ == "__main__":
    asyncio.run(generate_pure_monolingual_dataset())
