"""
ShareGPT SFT Dataset Exporter for SyntheticTutor.
"""

import json
import os
from typing import List
from synthetictutor.core.schemas import DialogueSession


class ShareGPTExporter:
    """Exports evaluated DialogueSessions to standard ShareGPT SFT JSONL format."""

    def export(self, sessions: List[DialogueSession], output_path: str) -> str:
        """Exports sessions to output_path JSONL file."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        records = []
        for s in sessions:
            conversations = []
            for t in s.turns:
                from_role = "human" if t.role.value == "student" else "gpt"
                conversations.append({
                    "from": from_role,
                    "value": t.content
                })

            records.append({
                "id": s.id,
                "target_concept": s.plan.target_concept.name,
                "language": s.language,
                "conversations": conversations,
                "metadata": {
                    "grade_level": s.student_persona.grade_level,
                    "teaching_style": s.teacher_persona.teaching_style,
                    "learning_objective": s.plan.learning_objective
                }
            })

        with open(output_path, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        return output_path
