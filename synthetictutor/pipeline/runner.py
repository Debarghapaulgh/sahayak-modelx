"""
Async Batch Pipeline Execution Engine for SyntheticTutor.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from synthetictutor.core.schemas import DialogueSession, EvaluationReport
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.planning.lesson_planner import LessonPlanner
from synthetictutor.planning.persona_factory import PersonaFactory
from synthetictutor.simulation.engine import SimulationEngine
from synthetictutor.evaluation.composite_evaluator import CompositeEvaluator
from synthetictutor.multilingual.translator import IndicTranslator
from synthetictutor.export.sharegpt import ShareGPTExporter
from synthetictutor.export.huggingface import ChatMLExporter
from synthetictutor.llm.base import BaseLLMClient

logger = logging.getLogger(__name__)


class BatchPipelineRunner:
    """Async batch execution engine with concurrency rate limiting and quality filter guardrails."""

    def __init__(self, llm_client: BaseLLMClient, max_concurrency: int = 5):
        self.llm_client = llm_client
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.simulation_engine = SimulationEngine(llm_client)
        self.evaluator = CompositeEvaluator(llm_client)
        self.translator = IndicTranslator(llm_client)

    async def process_concept(
        self,
        kg: KnowledgeGraph,
        concept_id: str,
        target_languages: Optional[List[str]] = None
    ) -> List[DialogueSession]:
        """Generates, evaluates, and translates Socratic dialogues for a single target concept."""
        async with self.semaphore:
            concept = kg._concepts[concept_id]
            planner = LessonPlanner(kg)
            plan = planner.create_plan(concept)

            student_persona = PersonaFactory.create_student_persona(
                persona_id=f"student_{concept_id}",
                target_misconceptions=concept.misconceptions
            )
            teacher_persona = PersonaFactory.create_teacher_persona(
                persona_id=f"teacher_{concept_id}"
            )

            logger.info(f"Simulating session for concept: {concept.name}")
            session = await self.simulation_engine.run_simulation(plan, student_persona, teacher_persona)

            # Quality Evaluation
            eval_report: EvaluationReport = await self.evaluator.evaluate_session(session)
            if not eval_report.passed_all_guardrails:
                logger.warning(f"Session {session.id} rejected by guardrails: {eval_report.rejection_reasons}")
                return []

            results = [session]

            # Multilingual Adaptation if requested
            if target_languages:
                for lang in target_languages:
                    if lang.lower() != "en":
                        logger.info(f"Translating session {session.id} into {lang}")
                        trans_session = await self.translator.translate_session(session, lang)
                        results.append(trans_session)

            return results

    async def run_pipeline(
        self,
        kg: KnowledgeGraph,
        target_languages: Optional[List[str]] = None,
        sharegpt_output: str = "output/synthetic_sharegpt.jsonl",
        chatml_output: str = "output/synthetic_chatml.jsonl"
    ) -> Dict[str, Any]:
        """Runs the entire pipeline across all concepts in the KnowledgeGraph."""
        concepts = kg.get_topological_teaching_order()
        logger.info(f"Starting pipeline run across {len(concepts)} concepts.")

        tasks = [self.process_concept(kg, c.id, target_languages) for c in concepts]
        nested_sessions = await asyncio.gather(*tasks)

        all_valid_sessions: List[DialogueSession] = [
            session for sublist in nested_sessions for session in sublist
        ]

        logger.info(f"Pipeline completed: {len(all_valid_sessions)} high-quality sessions retained.")

        # Export Datasets
        sharegpt_path = ShareGPTExporter().export(all_valid_sessions, sharegpt_output)
        chatml_path = ChatMLExporter().export(all_valid_sessions, chatml_output)

        return {
            "total_generated": len(all_valid_sessions),
            "sharegpt_path": sharegpt_path,
            "chatml_path": chatml_path
        }
