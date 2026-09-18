"""
10-Stage Deterministic Validator for Structured-JSON SFT Part 1.
Implements Stages 1-10 with content-aware hard negative checks.
"""

import json
from typing import Dict, Any, List, Optional
from synthetictutor.core.schemas_part1 import Part1StructuredSFTRecord, ValidationScores
from synthetictutor.knowledge.topic_scope_lock import TopicScopeLock

class Part1StructuredValidator:
    """Deterministic Multi-Stage Structured-JSON Validator."""

    @classmethod
    def _extract_all_text_values(cls, obj: Any) -> str:
        """Recursively extracts all string values from a JSON payload (excluding keys)."""
        texts = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                texts.append(cls._extract_all_text_values(v))
        elif isinstance(obj, list):
            for item in obj:
                texts.append(cls._extract_all_text_values(item))
        elif isinstance(obj, str):
            texts.append(obj)
        elif isinstance(obj, (int, float, bool)):
            texts.append(str(obj))
        return " ".join(texts)

    @classmethod
    def validate_record(cls, record: Part1StructuredSFTRecord, seen_prompts: Optional[set] = None) -> ValidationScores:
        failures: List[str] = []
        seen_prompts = seen_prompts or set()

        user_prompt = ""
        assistant_payload = None

        for msg in record.messages:
            if msg.role == "user":
                user_prompt = msg.content if isinstance(msg.content, str) else str(msg.content)
            elif msg.role == "assistant":
                if hasattr(msg.content, "model_dump"):
                    assistant_payload = msg.content.model_dump()
                elif isinstance(msg.content, dict):
                    assistant_payload = msg.content
                elif isinstance(msg.content, str):
                    try:
                        assistant_payload = json.loads(msg.content)
                    except Exception:
                        assistant_payload = None

        # STAGE 1: JSON Parse & Type Validation
        schema_passed = bool(record.id and user_prompt and assistant_payload is not None)
        if not schema_passed:
            failures.append("Stage 1: Invalid JSON structure or missing required message roles")

        resp_type = assistant_payload.get("type") if assistant_payload else None
        if resp_type not in ["qa", "lesson_plan", "quiz"]:
            schema_passed = False
            failures.append(f"Stage 1: Invalid payload type '{resp_type}', expected 'qa', 'lesson_plan', or 'quiz'")

        # STAGE 2: Task-Specific Structural Integrity
        task_passed = True
        if resp_type == "quiz":
            questions = assistant_payload.get("questions", [])
            total_marks = assistant_payload.get("total_marks", 0)
            if not questions:
                task_passed = False
                failures.append("Stage 2: Quiz payload contains no questions")
            else:
                calc_marks = sum(q.get("marks", 0) for q in questions)
                if calc_marks != total_marks:
                    task_passed = False
                    failures.append(f"Stage 2: Quiz total_marks mismatch: declared {total_marks}, sum of questions is {calc_marks}")
                
                q_ids = [q.get("id") for q in questions]
                if len(q_ids) != len(set(q_ids)):
                    task_passed = False
                    failures.append("Stage 2: Duplicate question IDs detected in quiz")

                answer_key = assistant_payload.get("answer_key")
                if answer_key:
                    ans_ids = {a.get("question_id") for a in answer_key}
                    missing_ans = set(q_ids) - ans_ids
                    if missing_ans:
                        task_passed = False
                        failures.append(f"Stage 2: Incomplete answer key, missing answers for questions: {missing_ans}")

        elif resp_type == "lesson_plan":
            objectives = assistant_payload.get("learning_objectives", [])
            seq = assistant_payload.get("teaching_sequence", [])
            if not objectives or not seq:
                task_passed = False
                failures.append("Stage 2: Lesson plan lacks learning_objectives or teaching_sequence")

        elif resp_type == "qa":
            answer = assistant_payload.get("answer", "")
            if not answer or len(str(answer).strip()) < 5:
                task_passed = False
                failures.append("Stage 2: QA payload has empty or invalid answer")

        # STAGE 3: Curriculum Consistency
        c = record.curriculum
        curr_passed = bool(c.board and c.class_ and c.subject and c.topic)
        if not curr_passed:
            failures.append("Stage 3: Incomplete curriculum metadata")

        # STAGE 4: Topic Scope Lock & Hard Negatives (Evaluated on text values only)
        scope = TopicScopeLock.resolve_topic(c.class_, c.subject, c.topic, c.board)
        topic_passed = True
        content_text = cls._extract_all_text_values(assistant_payload) if assistant_payload else ""
        for hn in scope.hard_negatives:
            if hn.lower() in content_text.lower():
                topic_passed = False
                failures.append(f"Stage 4: Hard negative '{hn}' detected for requested topic '{c.topic}'")
                break

        # STAGE 5: Source Grounding & Visual Dependency
        src = record.source
        source_passed = True
        if src.visual_dependency == "REQUIRED" and "চিত্র" not in content_text and "ছক" not in content_text:
            source_passed = False
            failures.append("Stage 5: Visual dependency is REQUIRED but generated without visual context")

        # STAGE 6: Local Context Validation
        loc = record.local_context
        loc_passed = True
        if loc.mode not in ["NONE", "GENERIC_STATE"] and loc.verified_local_facts == [] and "কাল্পনিক" not in content_text:
            loc_passed = False
            failures.append("Stage 6: Real local claims must be supported by verified_local_facts or labeled hypothetical")

        # STAGE 7: Factual / Mathematical Integrity
        fact_passed = True
        if "NaN" in content_text or "???" in content_text:
            fact_passed = False
            failures.append("Stage 7: Broken notation or Unicode corruption detected in JSON payload")

        # STAGE 8: Grade Appropriateness
        grade_passed = True
        if c.class_ <= 2 and len(content_text.split()) > 600:
            grade_passed = False
            failures.append("Stage 8: Primary Class I-II response is excessively long")

        # STAGE 9: Deduplication
        dup_passed = True
        prompt_norm = user_prompt.strip().lower()
        if prompt_norm in seen_prompts:
            dup_passed = False
            failures.append("Stage 9: Exact duplicate prompt detected")

        # STAGE 10: Overall status
        overall = (
            schema_passed and task_passed and curr_passed and topic_passed and
            source_passed and loc_passed and fact_passed and grade_passed and dup_passed
        )

        return ValidationScores(
            schema_passed=schema_passed,
            curriculum_alignment=curr_passed,
            topic_alignment=topic_passed,
            source_groundedness=source_passed,
            local_groundedness=loc_passed,
            factual_correctness=fact_passed,
            instruction_following=task_passed,
            grade_appropriateness=grade_passed,
            duplicate_free=dup_passed,
            overall_passed=overall,
            failure_reasons=failures
        )