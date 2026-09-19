"""
Evaluation package for synthetic dialogue verification and quality guardrails.
"""

from synthetictutor.evaluation.factual_judge import FactualAccuracyJudge
from synthetictutor.evaluation.pedagogical_judge import PedagogicalQualityJudge, AnswerLeakageJudge
from synthetictutor.evaluation.composite_evaluator import CompositeEvaluator

__all__ = [
    "FactualAccuracyJudge",
    "PedagogicalQualityJudge",
    "AnswerLeakageJudge",
    "CompositeEvaluator",
]
