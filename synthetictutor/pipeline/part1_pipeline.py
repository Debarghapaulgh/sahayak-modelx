"""
Master Part 1 SFT Pipeline Orchestrator.
Orchestrates Request-First, Topic-Locked, Curriculum-Grounded Dataset Generation for Part 1.
"""

import os
import json
from typing import Dict, Any, List, Optional
from synthetictutor.core.schemas_part1 import (
    Part1SFTRecord, CurriculumMetadata, SourceMetadata,
    LocalContextMetadata, QAMetadata, LessonPlanMetadata,
    QuizMetadata, ValidationScores
)
from synthetictutor.knowledge.curriculum_manifest import CurriculumManifest
from synthetictutor.knowledge.topic_scope_lock import TopicScopeLock
from synthetictutor.evaluation.part1_validator import Part1Validator

class Part1Pipeline:
    """Orchestrator for SahayakAI SFT Part 1 Generation & Validation."""

    def __init__(self, output_dir: str = "datasets/textbook_sft_part1"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.seen_prompts = set()
        self.qa_records: List[Part1SFTRecord] = []
        self.lp_records: List[Part1SFTRecord] = []
        self.quiz_records: List[Part1SFTRecord] = []
        self.review_records: List[Part1SFTRecord] = []
        self.hard_negatives: List[Dict[str, Any]] = []

    def process_and_validate_record(self, record: Part1SFTRecord) -> Part1SFTRecord:
        """Run 10-stage validation on a candidate record."""
        scores = Part1Validator.validate_record(record, seen_prompts=self.seen_prompts)
        record.validation = scores
        self.seen_prompts.add(record.user_prompt.strip().lower())
        
        if scores.overall_passed:
            if record.task_type == "QA":
                self.qa_records.append(record)
            elif record.task_type == "LESSON_PLAN":
                self.lp_records.append(record)
            elif record.task_type == "QUIZ":
                self.quiz_records.append(record)
        else:
            self.review_records.append(record)
            
        return record

    def export_dataset_artifacts(self) -> Dict[str, str]:
        """Export all split files, manifests, and audit reports."""
        artifacts = {}
        
        # 1. Export Task-Specific Final Files
        qa_path = os.path.join(self.output_dir, "qa_final.jsonl")
        with open(qa_path, "w", encoding="utf-8") as f:
            for r in self.qa_records:
                f.write(r.model_dump_json() + "\n")
        artifacts["qa_final"] = qa_path

        lp_path = os.path.join(self.output_dir, "lesson_plan_final.jsonl")
        with open(lp_path, "w", encoding="utf-8") as f:
            for r in self.lp_records:
                f.write(r.model_dump_json() + "\n")
        artifacts["lesson_plan_final"] = lp_path

        quiz_path = os.path.join(self.output_dir, "quiz_final.jsonl")
        with open(quiz_path, "w", encoding="utf-8") as f:
            for r in self.quiz_records:
                f.write(r.model_dump_json() + "\n")
        artifacts["quiz_final"] = quiz_path

        # 2. Export Review & Excluded Files
        review_path = os.path.join(self.output_dir, "part1_review.jsonl")
        with open(review_path, "w", encoding="utf-8") as f:
            for r in self.review_records:
                f.write(r.model_dump_json() + "\n")
        artifacts["part1_review"] = review_path

        # 3. Export Curriculum Manifest
        curr_manifest_path = os.path.join(self.output_dir, "curriculum_manifest.json")
        CurriculumManifest.export_manifest(curr_manifest_path)
        artifacts["curriculum_manifest"] = curr_manifest_path

        # 4. Export Part 1 Audit & Summary
        audit_path = os.path.join(self.output_dir, "part1_audit.json")
        audit_data = {
            "total_processed": len(self.qa_records) + len(self.lp_records) + len(self.quiz_records) + len(self.review_records),
            "total_approved": len(self.qa_records) + len(self.lp_records) + len(self.quiz_records),
            "total_review": len(self.review_records),
            "qa_count": len(self.qa_records),
            "lesson_plan_count": len(self.lp_records),
            "quiz_count": len(self.quiz_records),
            "acceptance_rate": (len(self.qa_records) + len(self.lp_records) + len(self.quiz_records)) / max(1, len(self.qa_records) + len(self.lp_records) + len(self.quiz_records) + len(self.review_records))
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        artifacts["part1_audit"] = audit_path

        return artifacts