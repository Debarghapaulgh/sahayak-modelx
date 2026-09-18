"""
Automated Test Suite for Grounding-First Request-Driven SFT Pipeline with Dual-Role Support.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, '.')

from synthetictutor.knowledge.textbook_retriever import TextbookRetriever, BengaliTokenizer
from synthetictutor.knowledge.grounding_compatibility_gate import GroundingCompatibilityGate
from synthetictutor.pipeline.intent_generator import IntentGenerator, UserIntent
from synthetictutor.pipeline.grounded_generator import GroundedGenerator
from synthetictutor.evaluation.grounding_first_validator import GroundingFirstValidator
from synthetictutor.pipeline.grounding_first_pipeline import GroundingFirstPipeline


class TestGroundingFirstPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.source_pool_path = "wbbse_sft_source_pool.jsonl"
        cls.retriever = TextbookRetriever(cls.source_pool_path)
        cls.gate = GroundingCompatibilityGate(min_overlap_threshold=0.2)
        cls.validator = GroundingFirstValidator()
        cls.pipeline = GroundingFirstPipeline(cls.source_pool_path)

    def test_01_retriever_precision(self):
        """Test targeted retrieval precision for specific curriculum topics."""
        res_math = self.retriever.retrieve("আবৃত্ত দশমিক সংখ্যা", grade=6, top_k=2)
        self.assertGreater(len(res_math), 0)
        self.assertEqual(res_math[0]["grade"], 6)
        self.assertIn("আবৃত্ত দশমিক", res_math[0]["topic"])

        res_eng = self.retriever.retrieve("Autumn poem John Clare", grade=9, top_k=1)
        self.assertGreater(len(res_eng), 0)
        self.assertEqual(res_eng[0]["subject"], "English")
        self.assertIn("Autumn", res_eng[0]["topic"])

    def test_02_compatibility_gate_rejection_on_mismatch(self):
        """Test that compatibility gate rejects topic and subject mismatches."""
        math_chunk = self.retriever.retrieve("আবৃত্ত দশমিক সংখ্যা", grade=6, top_k=1)[0]
        
        # Subject mismatch
        res_sub_mismatch = self.gate.evaluate(
            "সালোকসংশ্লেষ প্রক্রিয়া বুঝিয়ে দাও",
            math_chunk,
            target_subject="Life Science"
        )
        self.assertFalse(res_sub_mismatch.is_compatible)
        self.assertEqual(res_sub_mismatch.status, "REJECT")

        # Topic mismatch within same subject
        res_topic_mismatch = self.gate.evaluate(
            "পীথাগোরাসের উপপাদ্য প্রমাণ করো",
            math_chunk,
            target_subject="Mathematics"
        )
        self.assertFalse(res_topic_mismatch.is_compatible)
        self.assertEqual(res_topic_mismatch.status, "REJECT")

    def test_03_compatibility_gate_pass_on_aligned_context(self):
        """Test that compatibility gate approves genuinely aligned query & chunk."""
        math_chunk = self.retriever.retrieve("আবৃত্ত দশমিক সংখ্যা", grade=6, top_k=1)[0]
        res_pass = self.gate.evaluate(
            "আবৃত্ত দশমিক সংখ্যাকে সামান্য ভগ্নাংশে রূপান্তর করার নিয়ম বুঝিয়ে দিন।",
            math_chunk,
            target_subject="Mathematics",
            target_grade=6
        )
        self.assertTrue(res_pass.is_compatible)
        self.assertEqual(res_pass.status, "PASS")

    def test_04_dual_role_intent_generator(self):
        """Test teacher-centric intent synthesis and cleanliness."""
        # Teacher -> Student target
        intent_teacher = IntentGenerator.synthesize_intent(
            subject="Mathematics",
            grade=6,
            topic="অধ্যায় ১০: আবৃত্ত দশমিক সংখ্যা",
            task_type="CONCEPT_EXPLANATION",
            requester_role="TEACHER",
            instructional_target="STUDENT"
        )
        self.assertEqual(intent_teacher.requester_role, "TEACHER")
        self.assertEqual(intent_teacher.instructional_target, "STUDENT")
        self.assertNotIn("পাঠ্যাংশ:", intent_teacher.query)
        self.assertIn("আবৃত্ত দশমিক", intent_teacher.query)

        # Student -> Student target
        intent_student = IntentGenerator.synthesize_intent(
            subject="Mathematics",
            grade=6,
            topic="অধ্যায় ১০: আবৃত্ত দশমিক সংখ্যা",
            task_type="CONCEPT_EXPLANATION",
            requester_role="STUDENT"
        )
        self.assertEqual(intent_student.requester_role, "STUDENT")
        self.assertEqual(intent_student.instructional_target, "STUDENT")

    def test_05_multi_chunk_retrieval(self):
        """Test multi-chunk contiguous retrieval for complex pedagogical tasks."""
        multi_chunks = self.retriever.retrieve_multi_chunk(
            query="Autumn poem John Clare",
            grade=9,
            subject="English",
            topic="Autumn (John Clare)",
            max_chunks=3
        )
        self.assertGreaterEqual(len(multi_chunks), 1)
        self.assertLessEqual(len(multi_chunks), 3)

    def test_06_end_to_end_pipeline_flow(self):
        """Test full pipeline processing with dual-role metadata."""
        intent = UserIntent(
            query="ষষ্ঠ শ্রেণির শিক্ষার্থীদের জন্য আবৃত্ত দশমিক সংখ্যা কীভাবে ভগ্নাংশে প্রকাশ করতে হয়, তা ক্লাসে বোঝানোর একটি সহজ পদ্ধতি বুঝিয়ে দিন।",
            target_subject="Mathematics",
            target_grade=6,
            target_topic="অধ্যায় ১০: আবৃত্ত দশমিক সংখ্যা",
            task_type="CONCEPT_EXPLANATION",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            audience="শিক্ষক মহাশয় / শিক্ষাবিদ"
        )
        record = self.pipeline.process_intent(intent, custom_id="test_rec_dual_role_001")
        self.assertIn("messages", record)
        self.assertEqual(len(record["messages"]), 3)
        self.assertEqual(record["metadata"]["requester_role"], "TEACHER")
        self.assertEqual(record["metadata"]["instructional_target"], "STUDENT")
        self.assertTrue(record["validation"]["passed"])


if __name__ == "__main__":
    unittest.main()
