"""
Pedagogical Quality Judge and Answer Leakage Judge.
"""

from synthetictutor.core.schemas import DialogueSession, MetricResult
from synthetictutor.llm.base import BaseLLMClient
from pydantic import BaseModel, Field


class JudgeSchema(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    feedback: str


class PedagogicalQualityJudge:
    """Evaluates Socratic questioning, scaffolding quality, and encouragement."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def evaluate(self, session: DialogueSession) -> MetricResult:
        dialogue_text = "\n".join([f"{t.role.value.upper()}: {t.content}" for t in session.turns])

        prompt = (
            f"Target Concept: {session.plan.target_concept.name}\n"
            f"Learning Objective: {session.plan.learning_objective}\n\n"
            f"Dialogue:\n{dialogue_text}\n\n"
            f"Evaluate the Socratic quality of the teacher. Did the teacher ask thought-provoking, guiding questions?"
        )
        system = "You are a senior pedagogical expert. Rate Socratic teaching effectiveness."

        res: JudgeSchema = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=JudgeSchema,
            system_instruction=system,
            temperature=0.1
        )
        return MetricResult(
            name="pedagogical_quality",
            score=res.score,
            passed=res.passed and res.score >= 0.75,
            feedback=res.feedback
        )


class AnswerLeakageJudge:
    """Guards against answer leakage — ensuring teacher doesn't give direct answers prematurely."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def evaluate(self, session: DialogueSession) -> MetricResult:
        # Check first 3 teacher turns to see if teacher blurted out definition
        teacher_turns = [t for t in session.turns if t.role.value == "teacher"][:3]
        early_text = "\n".join([t.content for t in teacher_turns])

        prompt = (
            f"Target Concept: {session.plan.target_concept.name}\n"
            f"Concept Definition: {session.plan.target_concept.description}\n\n"
            f"Early Teacher Turns:\n{early_text}\n\n"
            f"Did the teacher directly explain or define the answer in these early turns instead of asking questions? "
            f"Set passed=False if answer leakage occurred."
        )
        system = "You are an anti-answer-leakage auditor. Detect premature direct answer reveals."

        res: JudgeSchema = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=JudgeSchema,
            system_instruction=system,
            temperature=0.1
        )
        return MetricResult(
            name="anti_leakage",
            score=res.score,
            passed=res.passed,
            feedback=res.feedback
        )
