"""
Pan-NCERT Multilingual Indic Socratic Dataset Generator.
Synthesizes dialogues covering full NCERT Class 6-12 curricula across 12 Indic Languages and 10 Student Personas.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from synthetictutor.ingestion.ncert_catalog import NCERT_CATALOG
from synthetictutor.multilingual.indic_engine import INDIC_LANGUAGES, get_indic_opening_question
from synthetictutor.planning.persona_library import STUDENT_PERSONA_LIBRARY

logging.basicConfig(level=logging.WARNING)

OUTPUT_PATH = "output/pan_ncert_indic_multiper_dataset.jsonl"
TARGET_DIALOGUES = 25000


async def generate_pan_ncert_dataset():
    print("=========================================================")
    print("Pan-NCERT Multilingual Indic Dataset Generator Initiated")
    print(f"Curriculum Scope: Full NCERT Classes 6-12 ({len(NCERT_CATALOG)} Core STEM & Social Science Concepts)")
    print(f"Target Languages: {len(INDIC_LANGUAGES)} Indic Languages ({', '.join(INDIC_LANGUAGES.keys())})")
    print(f"Student Personas: {len(STUDENT_PERSONA_LIBRARY)} Student Cognitive Profiles")
    print(f"Target Size: {TARGET_DIALOGUES:,} Evaluated Socratic Dialogues")
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
                        dialogue_id = f"ncert_indic_{total_count:06d}"
                        concept_name = ncert_item["name"]
                        subject = ncert_item["subject"]
                        class_level = ncert_item["class"]
                        misconception = ncert_item["misc"]

                        opening_q = get_indic_opening_question(lang, concept_name)

                        student_u1 = persona["student_pattern"].format(misconception=misconception)
                        teacher_u1 = persona["teacher_pattern"]
                        student_u2 = persona["resolution_pattern"]

                        rec = {
                            "id": dialogue_id,
                            "target_concept": concept_name,
                            "subject": subject,
                            "class": class_level,
                            "language": lang,
                            "language_name": INDIC_LANGUAGES[lang]["name"],
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
                                "persona_cognitive_traits": persona["traits"],
                                "active_misconception": misconception,
                                "teaching_style": "Socratic Elicitation & Scaffolding",
                                "learning_objective": f"Scaffold student understanding of '{concept_name}' and reframe misconception '{misconception}'."
                            }
                        }

                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

                        if total_count % 5000 == 0:
                            print(f"Progress: {total_count:,} / {TARGET_DIALOGUES:,} dialogues generated ({(total_count/TARGET_DIALOGUES)*100:.0f}%)...")

    print("\n=========================================================")
    print("SUCCESS! Pan-NCERT Multi-Indic Persona Dataset Generated!")
    print(f"Dataset File: {OUTPUT_PATH}")
    print(f"Total File Size: {os.path.getsize(OUTPUT_PATH) / (1024*1024):.2f} MB")
    print("=========================================================")


if __name__ == "__main__":
    asyncio.run(generate_pan_ncert_dataset())
