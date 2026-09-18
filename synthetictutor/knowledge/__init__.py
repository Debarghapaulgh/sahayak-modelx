"""
Knowledge representation package for SyntheticTutor.
"""

try:
    from synthetictutor.knowledge.graph import KnowledgeGraph
except ImportError:
    KnowledgeGraph = None

try:
    from synthetictutor.knowledge.extractor import ConceptExtractor
except ImportError:
    ConceptExtractor = None

from synthetictutor.knowledge.textbook_retriever import TextbookRetriever
from synthetictutor.knowledge.locale_retriever import LocaleRetriever
from synthetictutor.knowledge.grounding_compatibility_gate import GroundingCompatibilityGate

__all__ = ["TextbookRetriever", "LocaleRetriever", "GroundingCompatibilityGate", "KnowledgeGraph", "ConceptExtractor"]


