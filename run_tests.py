"""
Zero-dependency test runner for SyntheticTutor.
"""

import sys
import asyncio
import traceback

from tests.unit.test_schemas import test_concept_schema_instantiation, test_persona_creation
from tests.unit.test_knowledge_graph import test_knowledge_graph_topological_sort, test_knowledge_graph_cycle_detection
from tests.unit.test_pipeline_mock import test_batch_pipeline_runner_end_to_end
from tests.unit.test_ncert_localized_qa import (
    test_locale_json_structure, test_context_flattening_retrieval,
    test_sarg_export_format, test_pdf_extraction_fallback, test_run_pipeline_mock
)


def run_all_tests():
    print("=" * 60)
    print("Running SyntheticTutor Test Suite")
    print("=" * 60)

    passed = 0
    failed = 0

    sync_tests = [
        ("test_concept_schema_instantiation", test_concept_schema_instantiation),
        ("test_persona_creation", test_persona_creation),
        ("test_knowledge_graph_topological_sort", test_knowledge_graph_topological_sort),
        ("test_knowledge_graph_cycle_detection", test_knowledge_graph_cycle_detection),
        ("test_locale_json_structure", test_locale_json_structure),
        ("test_context_flattening_retrieval", test_context_flattening_retrieval),
        ("test_sarg_export_format", test_sarg_export_format),
        ("test_pdf_extraction_fallback", test_pdf_extraction_fallback),
    ]

    for name, test_func in sync_tests:
        try:
            test_func()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            failed += 1

    async_tests = [
        ("test_batch_pipeline_runner_end_to_end", test_batch_pipeline_runner_end_to_end),
        ("test_run_pipeline_mock", test_run_pipeline_mock),
    ]

    for name, async_func in async_tests:
        try:
            asyncio.run(async_func())
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
