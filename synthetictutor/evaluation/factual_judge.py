"""
Factual Accuracy Judge: Verifies textbook grounding and guards against hallucinations.
"""

from synthetictutor.core.schemas import DialogueSession, MetricResult
from synthetictutor.llm.base import BaseLLMClient
from pydantic import BaseModel, Field


class JudgeSchema(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="1.0 = completely factually sound, 0.0 = severe hallucinations")
    passed: bool
    feedback: str


class FactualAccuracyJudge:
    """Evaluates whether all educational statements in the dialogue align with textbook factuality."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def evaluate(self, session: DialogueSession, source_context: str) -> MetricResult:
        dialogue_text = "\n".join([f"{t.role.value.upper()}: {t.content}" for t in session.turns])

        prompt = (
            f"Source Textbook Context:\n{source_context[:3000]}\n\n"
            f"Dialogue to Evaluate:\n{dialogue_text}\n\n"
            f"Verify if the teacher's explanations and guided facts are accurate according to the textbook context."
        )
        system = "You are a factual correctness judge for educational dialogues. Evaluate strict scientific/mathematical accuracy."

        res: JudgeSchema = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=JudgeSchema,
            system_instruction=system,
            temperature=0.1
        )
        return MetricResult(
            name="factual_accuracy",
            score=res.score,
            passed=res.passed and res.score >= 0.8,
            feedback=res.feedback
        )
