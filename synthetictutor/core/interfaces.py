"""
Core Abstract Interfaces and Protocols for SyntheticTutor.

Decouples core business logic from specific implementations (LLMs, Parsers, Exporters).
"""

from typing import Protocol, List, Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel
from synthetictutor.core.schemas import (
    Concept, ConceptGraphData, TeachingPlan, StudentPersona, 
    TeacherPersona, DialogueSession, EvaluationReport, ExportFormat
)

T = TypeVar("T", bound=BaseModel)


class LLMClientProtocol(Protocol):
    """Abstract interface for LLM interaction."""

    async def generate_text(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        ...

    async def generate_structured(
        self, 
        prompt: str, 
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> T:
        ...


class IngestorProtocol(Protocol):
    """Interface for curriculum ingestion parsers."""

    def parse_source(self, source_path: str) -> str:
        ...


class ConceptExtractorProtocol(Protocol):
    """Interface for extracting concepts and DAGs from raw text."""

    async def extract_concepts(self, text: str, domain: str, grade_level: str) -> List[Concept]:
        ...


class DialogueSimulatorProtocol(Protocol):
    """Interface for simulating multi-turn teacher-student dialogues."""

    async def simulate_session(
        self, 
        plan: TeachingPlan, 
        student_persona: StudentPersona, 
        teacher_persona: TeacherPersona
    ) -> DialogueSession:
        ...


class EvaluatorProtocol(Protocol):
    """Interface for evaluating synthetic dialogue sessions."""

    async def evaluate(self, session: DialogueSession, source_context: str) -> EvaluationReport:
        ...


class ExporterProtocol(Protocol):
    """Interface for exporting dialogue datasets into SFT formats."""

    def export(
        self, 
        sessions: List[DialogueSession], 
        output_path: str, 
        format_type: ExportFormat
    ) -> str:
        ...
