"""
Unit tests for KnowledgeGraph DAG builder, topological sort, and cycle validation.
"""

import pytest
from synthetictutor.core.schemas import Concept
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.core.exceptions import GraphValidationError


def test_knowledge_graph_topological_sort():
    c1 = Concept(id="c1", name="Force", description="Push or pull", prerequisite_ids=[])
    c2 = Concept(id="c2", name="Mass", description="Quantity of matter", prerequisite_ids=[])
    c3 = Concept(id="c3", name="Acceleration", description="Rate of change of velocity", prerequisite_ids=[])
    c4 = Concept(id="c4", name="Gravity Force", description="Attraction force", prerequisite_ids=["c1", "c2", "c3"])

    kg = KnowledgeGraph()
    kg.add_concept(c1)
    kg.add_concept(c2)
    kg.add_concept(c3)
    kg.add_concept(c4)

    teaching_order = kg.get_topological_teaching_order()
    ids = [c.id for c in teaching_order]

    assert ids.index("c1") < ids.index("c4")
    assert ids.index("c2") < ids.index("c4")
    assert ids.index("c3") < ids.index("c4")


def test_knowledge_graph_cycle_detection():
    c1 = Concept(id="c1", name="A", description="A", prerequisite_ids=["c2"])
    c2 = Concept(id="c2", name="B", description="B", prerequisite_ids=["c1"])

    kg = KnowledgeGraph()
    kg.add_concept(c1)
    kg.add_concept(c2)

    with pytest.raises(GraphValidationError, match="Cyclic dependency"):
        kg.get_topological_teaching_order()
