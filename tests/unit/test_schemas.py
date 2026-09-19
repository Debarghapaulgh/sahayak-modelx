"""
Unit tests for SyntheticTutor domain schemas.
"""

from synthetictutor.core.schemas import (
    Concept, Misconception, BloomLevel, StudentPersona, TeacherPersona, TeachingPlan
)


def test_concept_schema_instantiation():
    m = Misconception(
        id="misc_01",
        description="Heavier objects fall faster than lighter objects in vacuum.",
        typical_trigger="Dropping a feather and a hammer",
        correct_conception="All objects accelerate at g regardless of mass in a vacuum."
    )
    c = Concept(
        id="concept_freefall_01",
        name="Free Fall",
        description="Motion under gravity alone.",
        domain="Physics",
        grade_level="Grade 9",
        prerequisite_ids=[],
        misconceptions=[m],
        bloom_level=BloomLevel.UNDERSTAND
    )
    assert c.name == "Free Fall"
    assert len(c.misconceptions) == 1
    assert c.bloom_level == BloomLevel.UNDERSTAND


def test_persona_creation():
    student = StudentPersona(id="s1", name="Rahul", grade_level="Grade 9")
    assert student.name == "Rahul"
    assert 0.0 <= student.prior_knowledge_score <= 1.0

    teacher = TeacherPersona(id="t1", name="Dr. Socratic")
    assert teacher.name == "Dr. Socratic"
