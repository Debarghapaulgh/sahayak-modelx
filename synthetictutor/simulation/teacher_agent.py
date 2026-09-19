"""
Socratic Teacher Agent for dialogue simulation.
"""

from typing import List
from pydantic import BaseModel, Field
from synthetictutor.core.schemas import TeacherPersona, TeachingPlan, DialogueTurn, DialogueRole
from synthetictutor.llm.base import BaseLLMClient


class TeacherResponseSchema(BaseModel):
    inner_thought: str = Field(..., description="Pedagogical reasoning before speaking")
    pedagogical_intent: str = Field(..., description="e.g. probe_misconception, scaffold_hint, affirm, counter_example")
    response_text: str = Field(..., description="The spoken response to the student")


class TeacherAgent:
    """Simulates a Socratic Teacher who guides student learning without revealing answers directly."""

    def __init__(self, persona: TeacherPersona, llm_client: BaseLLMClient):
        self.persona = persona
        self.llm_client = llm_client

    async def generate_turn(
        self,
        plan: TeachingPlan,
        history: List[DialogueTurn]
    ) -> DialogueTurn:
        """Generates the next Socratic teacher turn."""
        history_text = "\n".join([f"{t.role.value.upper()}: {t.content}" for t in history])

        system_instruction = (
            f"You are {self.persona.name}, an expert Socratic educator.\n"
            f"Teaching Style: {self.persona.teaching_style}\n"
            f"Tone: {self.persona.tone}\n\n"
            f"RULES:\n"
            f"1. NEVER state the final answer or definition directly to the student.\n"
            f"2. Ask probing, scaffolded questions that help the student deduce the truth themselves.\n"
            f"3. If the student displays a misconception, present a gentle counter-example or leading scenario.\n"
            f"4. Keep responses concise (1-3 sentences).\n"
        )

        prompt = (
            f"Target Concept: {plan.target_concept.name}\n"
            f"Description: {plan.target_concept.description}\n"
            f"Learning Objective: {plan.learning_objective}\n"
            f"Target Misconceptions to Address: {[m.description for m in plan.target_misconceptions]}\n\n"
            f"Dialogue History:\n{history_text}\n\n"
            f"Generate your next teacher turn."
        )

        resp: TeacherResponseSchema = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=TeacherResponseSchema,
            system_instruction=system_instruction,
            temperature=0.7
        )

        turn_num = len(history) + 1
        return DialogueTurn(
            turn_number=turn_num,
            role=DialogueRole.TEACHER,
            content=resp.response_text,
            inner_thought=resp.inner_thought,
            pedagogical_intent=resp.pedagogical_intent
        )
