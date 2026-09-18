"""
Unit Tests for Structured-JSON SFT Part 1 Pipeline.
"""

import unittest
import os
import json
from synthetictutor.core.schemas_part1 import (
    Part1StructuredSFTRecord, CurriculumMetadata, SourceMetadata,
    LocalContextMetadata, StructuredMessage,
    QAResponsePayload, LessonPlanResponsePayload, LessonTeachingStep,
    QuizResponsePayload, QuizQuestion, QuizAnswerKey
)
from synthetictutor.knowledge.curriculum_manifest import CurriculumManifest
from synthetictutor.pipeline.structured_part1_pipeline import StructuredPart1Pipeline

class TestStructuredPart1Pipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = StructuredPart1Pipeline(output_dir="datasets/textbook_sft_part1_test")

    def test_qa_structured_record_validation(self):
        qa_payload = QAResponsePayload(
            type="qa",
            answer="আদি-স্বরলোপ হলো শব্দের শুরুতে থাকা স্বরধ্বনির লোপ পাওয়ার নিয়ম। যেমন: অলাবু > লাবু > লাউ।"
        )
        rec = Part1StructuredSFTRecord(
            id="part1_qa_test_001",
            task_type="QA",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumMetadata(
                board="WBBSE",
                stage="UPPER_PRIMARY",
                class_=8,
                subject="Bengali",
                textbook="ভাষা পাঠ",
                chapter="প্রথম অধ্যায়",
                topic="দল ও ধ্বনি পরিবর্তন"
            ),
            source=SourceMetadata(textbook_source_chunks=["chunk_1"]),
            local_context=LocalContextMetadata(),
            messages=[
                StructuredMessage(role="user", content="আদি-স্বরলোপ বুঝিয়ে দিন।"),
                StructuredMessage(role="assistant", content=qa_payload)
            ]
        )
        processed = self.pipeline.process_and_validate_record(rec)
        self.assertTrue(processed.validation.overall_passed)
        self.assertEqual(len(self.pipeline.qa_records), 1)

    def test_quiz_structured_marks_validation(self):
        quiz_payload = QuizResponsePayload(
            type="quiz",
            title="দ্বি-স্তম্ভ লেখ কুইজ",
            instructions="সমস্ত প্রশ্নের উত্তর দাও।",
            total_marks=10,
            questions=[
                QuizQuestion(id=1, question_type="MCQ", question="দ্বি-স্তম্ভ লেখ কী?", marks=4),
                QuizQuestion(id=2, question_type="SHORT_ANSWER", question="স্কেল নির্বাচন", marks=6)
            ],
            answer_key=[
                QuizAnswerKey(question_id=1, answer="উত্তর ১"),
                QuizAnswerKey(question_id=2, answer="উত্তর ২")
            ]
        )
        rec = Part1StructuredSFTRecord(
            id="part1_quiz_test_001",
            task_type="QUIZ",
            requester_role="TEACHER",
            instructional_target="STUDENT",
            curriculum=CurriculumMetadata(
                board="WBBSE",
                stage="UPPER_PRIMARY",
                class_=7,
                subject="Mathematics",
                textbook="গণিতপ্রভা",
                chapter="অধ্যায় ১৬",
                topic="দ্বি-স্তম্ভ লেখ"
            ),
            source=SourceMetadata(textbook_source_chunks=["chunk_2"]),
            local_context=LocalContextMetadata(),
            messages=[
                StructuredMessage(role="user", content="দ্বি-স্তম্ভ লেখ কুইজ দিন।"),
                StructuredMessage(role="assistant", content=quiz_payload)
            ]
        )
        processed = self.pipeline.process_and_validate_record(rec)
        self.assertTrue(processed.validation.overall_passed)
        self.assertEqual(len(self.pipeline.quiz_records), 1)

    def test_quiz_marks_mismatch_fails(self):
        bad_quiz = QuizResponsePayload(
            type="quiz",
            title="ভুল কুইজ",
            instructions="নির্দেশনা",
            total_marks=15,  # declared 15
            questions=[
                QuizQuestion(id=1, question_type="SHORT_ANSWER", question="প্রশ্ন ১", marks=4)  # sum is 4
            ]
        )
        rec = Part1StructuredSFTRecord(
            id="part1_quiz_bad",
            task_type="QUIZ",
            curriculum=CurriculumMetadata(board="WBBSE", stage="UPPER_PRIMARY", class_=7, subject="Mathematics", textbook="গণিতপ্রভা", chapter="অধ্যায় ১৬", topic="দ্বি-স্তম্ভ লেখ"),
            source=SourceMetadata(textbook_source_chunks=["chunk_bad"]),
            local_context=LocalContextMetadata(),
            messages=[
                StructuredMessage(role="user", content="১৫ নম্বরের কুইজ দিন।"),
                StructuredMessage(role="assistant", content=bad_quiz)
            ]
        )
        processed = self.pipeline.process_and_validate_record(rec)
        self.assertFalse(processed.validation.overall_passed)
        self.assertFalse(processed.validation.instruction_following)
        self.assertEqual(len(self.pipeline.review_records), 1)

if __name__ == '__main__':
    unittest.main()