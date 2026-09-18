"""
End-to-End Pipeline Integration Test using Mock LLM Client.
"""

import pytest
import os
import tempfile
from synthetictutor.core.schemas import Concept, Misconception
from synthetictutor.knowledge.graph import KnowledgeGraph
from synthetictutor.llm.router import MockLLMClient
from synthetictutor.pipeline.runner import BatchPipelineRunner


@pytest.mark.asyncio
async def test_batch_pipeline_runner_end_to_end():
    # Setup Concept DAG
    m = Misconception(id="m1", description="Gravity requires air", typical_trigger="Vacuum drop", correct_conception="Gravity operates in vacuum")
    c1 = Concept(id="grav_01", name="Universal Gravitation", description="Universal attractive force between masses", prerequisite_ids=[], misconceptions=[m])
    
    kg = KnowledgeGraph()
    kg.add_concept(c1)

    # Setup Mock LLM with pre-structured returns for evaluation/simulation
    mock_responses = {
        "inner_thought": "Reasoning step",
        "pedagogical_intent": "probe",
        "response_text": "What happens to the attraction when mass increases?",
        "understanding_state": "curious",
        "concept_mastered": True,
        "dialogue_stalled": False,
        "reason": "Student articulated concept correctly",
        "score": 0.9,
        "passed": True,
        "feedback": "Factually sound Socratic dialogue",
        "translated_turns": ["TEACHER: What happens to attraction when mass increases?", "STUDENT: It increases."]
    }

    mock_llm = MockLLMClient(predefined_responses=mock_responses)
    runner = BatchPipelineRunner(llm_client=mock_llm, max_concurrency=2)

    with tempfile.TemporaryDirectory() as tmpdir:
        sharegpt_file = os.path.join(tmpdir, "sharegpt.jsonl")
        chatml_file = os.path.join(tmpdir, "chatml.jsonl")

        stats = await runner.run_pipeline(
            kg,
            target_languages=["en", "hi"],
            sharegpt_output=sharegpt_file,
            chatml_output=chatml_file
        )

        assert stats["total_generated"] >= 1
        assert os.path.exists(sharegpt_file)
        assert os.path.exists(chatml_file)

        # Inspect generated ShareGPT file
        with open(sharegpt_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) >= 1
            assert "conversations" in lines[0]
