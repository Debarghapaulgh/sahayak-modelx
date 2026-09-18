"""
Core Domain Schemas and Data Models for SyntheticTutor.

Uses Pydantic V2 for strict type safety, validation, and serialization.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field, ConfigDict


class BloomLevel(str, Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class Misconception(BaseModel):
    """Represents a common student misconception regarding a concept."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique ID of the misconception")
    description: str = Field(..., description="Description of the flawed reasoning")
    typical_trigger: str = Field(default="", description="Question or context that triggers this misconception")
    correct_conception: str = Field(..., description="The scientifically/pedagogically accurate concept")


class Concept(BaseModel):
    """Represents a single educational concept extracted from curriculum sources."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique identifier for the concept (e.g. concept_gravity_01)")
    name: str = Field(..., description="Title/name of the concept")
    description: str = Field(..., description="Comprehensive explanation of the concept")
    domain: str = Field(default="Science", description="Subject area (e.g., Physics, Mathematics)")
    grade_level: str = Field(default="Grade 9", description="Target curriculum grade level")
    prerequisite_ids: List[str] = Field(default_factory=list, description="IDs of concepts required prior to learning this")
    misconceptions: List[Misconception] = Field(default_factory=list, description="Common misconceptions")
    bloom_level: BloomLevel = Field(default=BloomLevel.UNDERSTAND, description="Target cognitive level")
    source_chapter: Optional[str] = Field(default=None, description="Source textbook chapter reference")


class ConceptGraphData(BaseModel):
    """Serialized representation of a Concept Directed Acyclic Graph (DAG)."""
    concepts: Dict[str, Concept] = Field(..., description="Map of concept ID to Concept object")
    edges: List[Tuple[str, str]] = Field(..., description="List of (prerequisite_id, concept_id) dependency pairs")


class StudentPersona(BaseModel):
    """Persona configuration for the simulated Student Agent."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str = Field(default="Learner")
    grade_level: str = Field(default="Grade 9")
    prior_knowledge_score: float = Field(default=0.5, ge=0.0, le=1.0, description="0.0 = total novice, 1.0 = advanced")
    active_misconceptions: List[Misconception] = Field(default_factory=list)
    curiosity_level: float = Field(default=0.7, ge=0.0, le=1.0)
    communication_style: str = Field(default="conversational", description="e.g., hesitant, inquisitive, brief, expressive")


class TeacherPersona(BaseModel):
    """Persona configuration for the Socratic Teacher Agent."""
    model_config = ConfigDict(frozen=True)

    id: str
    name: str = Field(default="Socratic Tutor")
    teaching_style: str = Field(default="Socratic Elicitation", description="e.g., Guided Elicitation, Analogical Reasoning")
    scaffolding_patience: float = Field(default=0.9, ge=0.0, le=1.0, description="Higher = more guiding questions before explanation")
    tone: str = Field(default="encouraging and curious")


class TeachingPlan(BaseModel):
    """Pedagogical roadmap for a single Socratic tutoring dialogue session."""
    id: str
    target_concept: Concept
    prerequisite_concepts: List[Concept] = Field(default_factory=list)
    target_misconceptions: List[Misconception] = Field(default_factory=list)
    learning_objective: str
    starting_question: str
    max_turns: int = Field(default=10, ge=2, le=30)


class DialogueRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    SYSTEM = "system"


class DialogueTurn(BaseModel):
    """Single turn in an educational dialogue session."""
    turn_number: int
    role: DialogueRole
    content: str = Field(..., description="Visible utterance spoken by the agent")
    inner_thought: Optional[str] = Field(default=None, description="Chain-of-Thought / pedagogical reasoning before output")
    pedagogical_intent: Optional[str] = Field(default=None, description="e.g. 'probe_misconception', 'scaffold_hint', 'affirm'")


class DialogueSession(BaseModel):
    """Full simulated dialogue conversation along with session provenance."""
    id: str
    plan: TeachingPlan
    student_persona: StudentPersona
    teacher_persona: TeacherPersona
    turns: List[DialogueTurn] = Field(default_factory=list)
    completed: bool = Field(default=False)
    language: str = Field(default="en", description="Language code e.g. 'en', 'hi', 'ta', 'hinglish'")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MetricResult(BaseModel):
    """Result of a single evaluation metric check."""
    name: str
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    feedback: str


class EvaluationReport(BaseModel):
    """Overall multi-judge evaluation report for a DialogueSession."""
    session_id: str
    overall_score: float = Field(..., ge=0.0, le=1.0)
    passed_all_guardrails: bool
    metrics: Dict[str, MetricResult] = Field(default_factory=dict)
    rejection_reasons: List[str] = Field(default_factory=list)


class ExportFormat(str, Enum):
    SHAREGPT = "sharegpt"
    CHATML = "chatml"
    PARQUET = "parquet"
    HUGGINGFACE = "huggingface"
