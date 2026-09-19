"""
Persona Factory for creating student and teacher agent profiles.
"""

import random
from typing import List, Optional
from synthetictutor.core.schemas import StudentPersona, TeacherPersona, Misconception


class PersonaFactory:
    """Generates authentic student and Socratic teacher personas for dialogue simulation."""

    STUDENT_STYLES = [
        "hesitant and prone to guessing",
        "inquisitive and demanding deep explanations",
        "over-confident with a hidden misconception",
        "literal-minded beginner needing concrete analogies",
        "brief and taciturn learner"
    ]

    TEACHER_STYLES = [
        "Socratic Elicitation (questions leading to self-discovery)",
        "Guided Scaffolding (step-by-step hints)",
        "Misconception Reframing (asking counter-example questions)",
        "Conceptual Analogy Facilitator"
    ]

    @classmethod
    def create_student_persona(
        self,
        persona_id: str,
        name: str = "Student",
        grade_level: str = "Grade 9",
        target_misconceptions: Optional[List[Misconception]] = None,
        style: Optional[str] = None
    ) -> StudentPersona:
        """Constructs a customized student persona."""
        return StudentPersona(
            id=persona_id,
            name=name,
            grade_level=grade_level,
            prior_knowledge_score=round(random.uniform(0.2, 0.6), 2),
            active_misconceptions=target_misconceptions or [],
            curiosity_level=round(random.uniform(0.5, 0.9), 2),
            communication_style=style or random.choice(self.STUDENT_STYLES)
        )

    @classmethod
    def create_teacher_persona(
        self,
        persona_id: str = "teacher_socratic_01",
        name: str = "Socratic Tutor",
        teaching_style: Optional[str] = None
    ) -> TeacherPersona:
        """Constructs a Socratic teacher persona."""
        return TeacherPersona(
            id=persona_id,
            name=name,
            teaching_style=teaching_style or random.choice(self.TEACHER_STYLES),
            scaffolding_patience=0.9,
            tone="encouraging, curious, and non-judgmental"
        )
