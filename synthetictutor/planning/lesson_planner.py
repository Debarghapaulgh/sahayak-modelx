"""
Lesson Planner for designing Socratic teaching plans.
"""

from typing import List, Optional
from synthetictutor.core.schemas import Concept, TeachingPlan, Misconception
from synthetictutor.knowledge.graph import KnowledgeGraph


class LessonPlanner:
    """Generates structured Socratic TeachingPlans grounded in concept DAG dependencies."""

    def __init__(self, knowledge_graph: KnowledgeGraph):
        self.kg = knowledge_graph

    def create_plan(
        self,
        target_concept: Concept,
        selected_misconceptions: Optional[List[Misconception]] = None,
        max_turns: int = 10
    ) -> TeachingPlan:
        """Constructs a TeachingPlan for a given target concept."""
        prereqs = self.kg.get_prerequisites(target_concept.id)
        misconceptions = selected_misconceptions or target_concept.misconceptions

        learning_obj = (
            f"Guide student to discover and explain '{target_concept.name}' "
            f"using Socratic questioning while addressing misconceptions."
        )
        starting_q = (
            f"When you think about {target_concept.name.lower()}, what comes to your mind?"
        )

        return TeachingPlan(
            id=f"plan_{target_concept.id}",
            target_concept=target_concept,
            prerequisite_concepts=prereqs,
            target_misconceptions=misconceptions,
            learning_objective=learning_obj,
            starting_question=starting_q,
            max_turns=max_turns
        )
