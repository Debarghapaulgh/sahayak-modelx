"""
Hugging Face ChatML & Parquet Dataset Exporter for SyntheticTutor.
"""

import json
import os
from typing import List
from synthetictutor.core.schemas import DialogueSession


class ChatMLExporter:
    """Exports evaluated DialogueSessions to ChatML standard format."""

    def export(self, sessions: List[DialogueSession], output_path: str) -> str:
        """Exports sessions to output_path JSONL file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        records = []
        for s in sessions:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a Socratic tutor teaching {s.plan.target_concept.name}. Guide the student through questioning."
                }
            ]
            for t in s.turns:
                role = "user" if t.role.value == "student" else "assistant"
                messages.append({
                    "role": role,
                    "content": t.content
                })

            records.append({
                "id": s.id,
                "messages": messages,
                "concept_id": s.plan.target_concept.id,
                "language": s.language
            })

        with open(output_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        return output_path
