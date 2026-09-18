"""
Student Agent for dialogue simulation.
"""

from typing import List
from pydantic import BaseModel, Field
from synthetictutor.core.schemas import StudentPersona, TeachingPlan, DialogueTurn, DialogueRole
from synthetictutor.llm.base import BaseLLMClient


class StudentResponseSchema(BaseModel):
    inner_thought: str = Field(..., description="Student's internal mental state or confusion")
    understanding_state: str = Field(..., description="e.g. confused, partial_realization, misconception_active, mastered")
    response_text: str = Field(..., description="The spoken student response")


class StudentAgent:
    """Simulates an authentic student expressing realistic learning curves and misconceptions."""

    def __init__(self, persona: StudentPersona, llm_client: BaseLLMClient):
        self.persona = persona
        self.llm_client = llm_client

    async def generate_turn(
        self,
        plan: TeachingPlan,
        history: List[DialogueTurn]
    ) -> DialogueTurn:
        """Generates the next student response turn."""
        history_text = "\n".join([f"{t.role.value.upper()}: {t.content}" for t in history])

        misconceptions_text = "\n".join([f"- {m.description} (Trigger: {m.typical_trigger})" for m in self.persona.active_misconceptions])

        system_instruction = (
            f"You are simulating a {self.persona.grade_level} student named {self.persona.name}.\n"
            f"Communication Style: {self.persona.communication_style}\n"
            f"Active Misconceptions:\n{misconceptions_text or 'None'}\n\n"
            f"RULES:\n"
            f"1. Respond authentically as a student. Do not sound like an AI assistant or teacher.\n"
            f"2. If you hold a misconception, express it naturally when questioned.\n"
            f"3. Reach breakthroughs only when guided by a good Socratic hint from the teacher.\n"
            f"4. Keep utterances realistic and appropriate for a {self.persona.grade_level} student.\n"
        )

        prompt = (
            f"Target Concept: {plan.target_concept.name}\n\n"
            f"Dialogue History:\n{history_text}\n\n"
            f"Respond to the teacher's last question."
        )

        resp: StudentResponseSchema = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=StudentResponseSchema,
            system_instruction=system_instruction,
            temperature=0.8
        )

        turn_num = len(history) + 1
        return DialogueTurn(
            turn_number=turn_num,
            role=DialogueRole.STUDENT,
            content=resp.response_text,
            inner_thought=resp.inner_thought,
            pedagogical_intent=resp.understanding_state
        )
