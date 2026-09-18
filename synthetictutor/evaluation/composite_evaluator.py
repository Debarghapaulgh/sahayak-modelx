"""
Composite Evaluator for aggregating multi-judge verification scorecards.
"""

from typing import List, Dict
from synthetictutor.core.schemas import DialogueSession, EvaluationReport, MetricResult
from synthetictutor.evaluation.factual_judge import FactualAccuracyJudge
from synthetictutor.evaluation.pedagogical_judge import PedagogicalQualityJudge, AnswerLeakageJudge
from synthetictutor.llm.base import BaseLLMClient


class CompositeEvaluator:
    """Aggregates multi-stage guardrail judges to produce an overall EvaluationReport."""

    def __init__(self, llm_client: BaseLLMClient):
        self.factual_judge = FactualAccuracyJudge(llm_client)
        self.pedagogical_judge = PedagogicalQualityJudge(llm_client)
        self.leakage_judge = AnswerLeakageJudge(llm_client)

    async def evaluate_session(
        self,
        session: DialogueSession,
        source_context: str = ""
    ) -> EvaluationReport:
        """Runs all judges and calculates aggregate pass/fail decision."""
        metrics: Dict[str, MetricResult] = {}
        rejection_reasons: List[str] = []

        # 1. Factual Accuracy Check
        fact_res = await self.factual_judge.evaluate(session, source_context or session.plan.target_concept.description)
        metrics["factual_accuracy"] = fact_res
        if not fact_res.passed:
            rejection_reasons.append(f"Factual inaccuracy: {fact_res.feedback}")

        # 2. Pedagogical Quality Check
        ped_res = await self.pedagogical_judge.evaluate(session)
        metrics["pedagogical_quality"] = ped_res
        if not ped_res.passed:
            rejection_reasons.append(f"Low pedagogical quality: {ped_res.feedback}")

        # 3. Answer Leakage Check
        leak_res = await self.leakage_judge.evaluate(session)
        metrics["anti_leakage"] = leak_res
        if not leak_res.passed:
            rejection_reasons.append(f"Answer leakage detected: {leak_res.feedback}")

        scores = [m.score for m in metrics.values()]
        overall_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        passed_all = len(rejection_reasons) == 0

        return EvaluationReport(
            session_id=session.id,
            overall_score=overall_score,
            passed_all_guardrails=passed_all,
            metrics=metrics,
            rejection_reasons=rejection_reasons
        )
