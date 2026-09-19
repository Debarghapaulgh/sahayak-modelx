"""
Dialogue Moderator and Orchestration Engine for Multi-Agent Simulation.
"""

import uuid
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from synthetictutor.core.schemas import (
    DialogueSession, TeachingPlan, StudentPersona, TeacherPersona, DialogueTurn, DialogueRole
)
from synthetictutor.simulation.teacher_agent import TeacherAgent
from synthetictutor.simulation.student_agent import StudentAgent
from synthetictutor.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class ConvergenceCheck(BaseModel):
    concept_mastered: bool = Field(..., description="True if student has articulated the core concept correctly")
    dialogue_stalled: bool = Field(..., description="True if no learning progress is occurring")
    reason: str


class DialogueModerator:
    """Monitors dialogue turns for completion criteria, concept mastery, or deadlock."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def check_convergence(
        self,
        plan: TeachingPlan,
        history: List[DialogueTurn]
    ) -> ConvergenceCheck:
        """Determines if the dialogue session should terminate early."""
        if len(history) < 4:
            return ConvergenceCheck(concept_mastered=False, dialogue_stalled=False, reason="Insufficient turns")

        history_text = "\n".join([f"{t.role.value.upper()}: {t.content}" for t in history[-4:]])

        prompt = (
            f"Target Concept: {plan.target_concept.name}\n"
            f"Learning Objective: {plan.learning_objective}\n\n"
            f"Recent Dialogue History:\n{history_text}\n\n"
            f"Evaluate if the student has reached a clear understanding/mastery of the concept, or if the conversation is stuck in a loop."
        )

        return await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=ConvergenceCheck,
            temperature=0.1
        )


class SimulationEngine:
    """Runs end-to-end multi-turn Socratic dialogue simulations."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client
        self.moderator = DialogueModerator(llm_client)

    async def run_simulation(
        self,
        plan: TeachingPlan,
        student_persona: StudentPersona,
        teacher_persona: TeacherPersona,
        language: str = "en"
    ) -> DialogueSession:
        """Executes full multi-turn dialogue simulation between teacher and student agents."""
        session_id = f"sim_{uuid.uuid4().hex[:8]}"
        teacher = TeacherAgent(teacher_persona, self.llm_client)
        student = StudentAgent(student_persona, self.llm_client)

        history: List[DialogueTurn] = []

        # Turn 1: Teacher starts with initial question from plan
        initial_turn = DialogueTurn(
            turn_number=1,
            role=DialogueRole.TEACHER,
            content=plan.starting_question,
            inner_thought="Initiating Socratic dialogue with initial probing question.",
            pedagogical_intent="initial_probe"
        )
        history.append(initial_turn)

        completed = False
        for current_turn in range(2, plan.max_turns + 1):
            # Student Turn
            student_turn = await student.generate_turn(plan, history)
            history.append(student_turn)

            # Check for early completion / mastery
            convergence = await self.moderator.check_convergence(plan, history)
            if convergence.concept_mastered or convergence.dialogue_stalled:
                logger.info(f"Session {session_id} terminating: {convergence.reason}")
                completed = convergence.concept_mastered
                break

            # Teacher Turn
            teacher_turn = await teacher.generate_turn(plan, history)
            history.append(teacher_turn)

        return DialogueSession(
            id=session_id,
            plan=plan,
            student_persona=student_persona,
            teacher_persona=teacher_persona,
            turns=history,
            completed=completed,
            language=language
        )
