"""
Concept Extractor: Extracts concepts, prerequisites, misconceptions, and Bloom levels from curriculum text.
"""

from typing import List
from pydantic import BaseModel, Field
from synthetictutor.core.schemas import Concept, Misconception, BloomLevel
from synthetictutor.llm.base import BaseLLMClient
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.core.exceptions import ExtractionError


class ExtractedConceptList(BaseModel):
    """Container schema for structured LLM response."""
    concepts: List[Concept] = Field(..., description="List of extracted educational concepts")


class ConceptExtractor:
    """Uses an LLM client to analyze curriculum content and construct a structured KnowledgeGraph."""

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def extract_from_text(
        self,
        text: str,
        domain: str = "Science",
        grade_level: str = "Grade 9"
    ) -> KnowledgeGraph:
        """Extracts concepts and constructs a validated KnowledgeGraph."""
        prompt = (
            f"Analyze the following educational text from a {grade_level} {domain} curriculum.\n"
            f"Identify all key concepts, their descriptions, prerequisite relationships, "
            f"common student misconceptions, and the target Bloom's Taxonomy cognitive level.\n\n"
            f"Text Source:\n{text[:350]}\n"
        )
        system_instruction = (
            "You are an expert curriculum designer and educational knowledge graph architect. "
            "Extract distinct, granular educational concepts. Ensure prerequisite relationships form a valid DAG without cycles."
        )

        try:
            result: ExtractedConceptList = await self.llm_client.generate_structured(
                prompt=prompt,
                response_schema=ExtractedConceptList,
                system_instruction=system_instruction,
                temperature=0.1
            )
        except Exception as e:
            raise ExtractionError(f"Concept extraction failed: {e}") from e

        kg = KnowledgeGraph()
        for concept in result.concepts:
            kg.add_concept(concept)

        # Validate graph consistency
        try:
            kg.validate()
        except Exception as e:
            # Clean up missing prerequisite edges if any exist
            valid_ids = set(result.concepts[i].id for i in range(len(result.concepts)))
            kg_clean = KnowledgeGraph()
            for concept in result.concepts:
                clean_prereqs = [pid for pid in concept.prerequisite_ids if pid in valid_ids and pid != concept.id]
                clean_concept = concept.model_copy(update={"prerequisite_ids": clean_prereqs})
                kg_clean.add_concept(clean_concept)
            kg = kg_clean

        return kg
