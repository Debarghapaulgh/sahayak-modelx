"""
Structured-JSON Part 1 SFT Pipeline Orchestrator.
Orchestrates generation, 10-stage validation, and partitioned export of 1,500 structured JSON SFT records.
"""

import os
import json
from typing import Dict, Any, List, Optional
from synthetictutor.core.schemas_part1 import Part1StructuredSFTRecord
from synthetictutor.knowledge.curriculum_manifest import CurriculumManifest
from synthetictutor.evaluation.part1_validator import Part1StructuredValidator

class StructuredPart1Pipeline:
    """Orchestrator for Structured-JSON SFT Part 1."""

    def __init__(self, output_dir: str = "datasets/textbook_sft_part1"):
        self.output_dir = output_dir
        os.makedirs(os.path.join(output_dir, "qa"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "lesson_plans"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "quizzes"), exist_ok=True)
        
        self.seen_prompts = set()
        self.qa_records: List[Part1StructuredSFTRecord] = []
        self.lp_records: List[Part1StructuredSFTRecord] = []
        self.quiz_records: List[Part1StructuredSFTRecord] = []
        self.review_records: List[Part1StructuredSFTRecord] = []
        self.hard_negatives: List[Dict[str, Any]] = []

    def process_and_validate_record(self, record: Part1StructuredSFTRecord) -> Part1StructuredSFTRecord:
        """Run 10-stage validation on a structured SFT candidate record."""
        scores = Part1StructuredValidator.validate_record(record, seen_prompts=self.seen_prompts)
        record.validation = scores
        
        user_prompt = ""
        for m in record.messages:
            if m.role == "user":
                user_prompt = m.content if isinstance(m.content, str) else str(m.content)
        self.seen_prompts.add(user_prompt.strip().lower())

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
        """Export all structured final files, manifests, and audit reports."""
        artifacts = {}

        # 1. Task-Specific Structured Files
        qa_path = os.path.join(self.output_dir, "qa", "qa_structured_final.jsonl")
        with open(qa_path, "w", encoding="utf-8") as f:
            for r in self.qa_records:
                f.write(r.model_dump_json(by_alias=True) + "\n")
        artifacts["qa_structured_final"] = qa_path

        lp_path = os.path.join(self.output_dir, "lesson_plans", "lesson_plan_structured_final.jsonl")
        with open(lp_path, "w", encoding="utf-8") as f:
            for r in self.lp_records:
                f.write(r.model_dump_json(by_alias=True) + "\n")
        artifacts["lesson_plan_structured_final"] = lp_path

        quiz_path = os.path.join(self.output_dir, "quizzes", "quiz_structured_final.jsonl")
        with open(quiz_path, "w", encoding="utf-8") as f:
            for r in self.quiz_records:
                f.write(r.model_dump_json(by_alias=True) + "\n")
        artifacts["quiz_structured_final"] = quiz_path

        # 2. Combined Master Structured File
        combined_path = os.path.join(self.output_dir, "part1_combined_structured.jsonl")
        with open(combined_path, "w", encoding="utf-8") as f:
            for r in self.qa_records + self.lp_records + self.quiz_records:
                f.write(r.model_dump_json(by_alias=True) + "\n")
        artifacts["part1_combined_structured"] = combined_path

        # 3. Review File
        review_path = os.path.join(self.output_dir, "part1_review.jsonl")
        with open(review_path, "w", encoding="utf-8") as f:
            for r in self.review_records:
                f.write(r.model_dump_json(by_alias=True) + "\n")
        artifacts["part1_review"] = review_path

        # 4. Curriculum Manifest
        curr_manifest_path = os.path.join(self.output_dir, "curriculum_manifest.json")
        CurriculumManifest.export_manifest(curr_manifest_path)
        artifacts["curriculum_manifest"] = curr_manifest_path

        # 5. Audit Report
        total_approved = len(self.qa_records) + len(self.lp_records) + len(self.quiz_records)
        total_proc = total_approved + len(self.review_records)
        audit_path = os.path.join(self.output_dir, "part1_audit.json")
        audit_data = {
            "total_processed": total_proc,
            "total_approved": total_approved,
            "total_review": len(self.review_records),
            "qa_count": len(self.qa_records),
            "lesson_plan_count": len(self.lp_records),
            "quiz_count": len(self.quiz_records),
            "acceptance_rate": total_approved / max(1, total_proc),
            "allocation_matrix": {
                "Primary (I-V)": sum(1 for r in self.qa_records + self.lp_records + self.quiz_records if r.curriculum.class_ <= 5),
                "Upper Primary (VI-VIII)": sum(1 for r in self.qa_records + self.lp_records + self.quiz_records if 6 <= r.curriculum.class_ <= 8),
                "Secondary (IX-X)": sum(1 for r in self.qa_records + self.lp_records + self.quiz_records if 9 <= r.curriculum.class_ <= 10),
                "Higher Secondary (XI-XII)": sum(1 for r in self.qa_records + self.lp_records + self.quiz_records if r.curriculum.class_ >= 11)
            }
        }
        with open(audit_path, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        artifacts["part1_audit"] = audit_path

        return artifacts