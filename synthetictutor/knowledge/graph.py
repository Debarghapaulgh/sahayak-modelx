"""
Knowledge Representation Module: NetworkX-backed Concept Directed Acyclic Graph (DAG).
"""

import networkx as nx
from typing import List, Dict, Optional, Set
from synthetictutor.core.schemas import Concept, ConceptGraphData
from synthetictutor.core.exceptions import GraphValidationError


class KnowledgeGraph:
    """Manages concept dependency DAG and prerequisite topological ordering."""

    def __init__(self):
        self._graph = nx.DiGraph()
        self._concepts: Dict[str, Concept] = {}

    def add_concept(self, concept: Concept):
        """Adds a concept node and its prerequisite directed edges to the graph."""
        self._concepts[concept.id] = concept
        self._graph.add_node(concept.id, name=concept.name, concept=concept)

        for prereq_id in concept.prerequisite_ids:
            # Edge points from prerequisite -> target concept
            self._graph.add_edge(prereq_id, concept.id)

    def validate(self):
        """Validates that the concept graph is a valid Directed Acyclic Graph (DAG)."""
        # Ensure all referenced prerequisite nodes exist
        for concept_id, concept in self._concepts.items():
            for prereq_id in concept.prerequisite_ids:
                if prereq_id not in self._concepts:
                    raise GraphValidationError(
                        f"Concept '{concept.name}' ({concept_id}) references missing prerequisite concept ID: '{prereq_id}'"
                    )

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self._graph):
            cycles = list(nx.simple_cycles(self._graph))
            raise GraphValidationError(f"Cyclic dependency detected in concept graph: {cycles}")

    def get_topological_teaching_order(self) -> List[Concept]:
        """Returns concepts ordered by prerequisite dependency (topological sort)."""
        self.validate()
        sorted_ids = list(nx.topological_sort(self._graph))
        return [self._concepts[cid] for cid in sorted_ids if cid in self._concepts]

    def get_prerequisites(self, concept_id: str) -> List[Concept]:
        """Returns direct and ancestor prerequisite concepts for a given concept."""
        if concept_id not in self._concepts:
            raise GraphValidationError(f"Concept ID '{concept_id}' not found in knowledge graph.")

        ancestors = nx.ancestors(self._graph, concept_id)
        return [self._concepts[aid] for aid in ancestors if aid in self._concepts]

    def to_schema(self) -> ConceptGraphData:
        """Serializes KnowledgeGraph into Pydantic schema."""
        edges = list(self._graph.edges())
        return ConceptGraphData(concepts=self._concepts, edges=edges)

    @classmethod
    def from_schema(cls, data: ConceptGraphData) -> "KnowledgeGraph":
        """Reconstructs KnowledgeGraph from Pydantic schema."""
        kg = cls()
        for concept in data.concepts.values():
            kg.add_concept(concept)
        kg.validate()
        return kg
