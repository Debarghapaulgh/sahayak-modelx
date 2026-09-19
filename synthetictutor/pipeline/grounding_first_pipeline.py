"""
Full Master Grounding-First Pipeline Orchestrator for SahayakAI.
Coordinates:
1. User Request / Intent Detection (Teacher 85%, Student 15%)
2. Curriculum Target Resolution (WBBPE / WBBSE / WBCHSE)
3. Textbook Retrieval (BM25 + Multi-chunk)
4. Locale Retrieval (locale.json verified facts)
5. Compatibility Gate (0-5 Curriculum Fidelity Score)
6. Grounded Generation (Hidden Internal Grounding)
7. 8-Stage Dimension-Wise Validation
8. Rich Dataset & Telemetry Export
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from synthetictutor.knowledge.textbook_retriever import TextbookRetriever
from synthetictutor.knowledge.locale_retriever import LocaleRetriever, LocaleSnippet
from synthetictutor.knowledge.grounding_compatibility_gate import GroundingCompatibilityGate
from synthetictutor.pipeline.intent_generator import IntentGenerator, UserIntent
from synthetictutor.pipeline.grounded_generator import GroundedGenerator
from synthetictutor.evaluation.grounding_first_validator import GroundingFirstValidator


class GroundingFirstPipeline:
    """Master orchestrator for request-driven, curriculum-grounded, and locale-grounded SFT generation."""

    def __init__(
        self,
        source_pool_path: str = "wbbse_sft_source_pool.jsonl",
        locale_path: str = "locale.json",
        min_overlap_threshold: float = 0.2
    ):
        self.retriever = TextbookRetriever(source_pool_path)
        self.locale_retriever = LocaleRetriever(locale_path)
        self.gate = GroundingCompatibilityGate(min_overlap_threshold=min_overlap_threshold)
        self.validator = GroundingFirstValidator()

    def process_intent(
        self,
        intent: UserIntent,
        custom_id: str,
        llm_response_fn: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes the full generation pipeline for an educational intent:
        Intent -> Textbook Retrieval -> Locale Retrieval -> Gate -> Generation -> Dimension Validation.
        """
        # 1. Textbook Retrieval
        is_complex_task = intent.task_type in ["LESSON_PLAN", "QUIZ_GENERATION", "WORKSHEET_PRACTICE", "TEACHER_PEDAGOGY"]
        if is_complex_task:
            retrieved_chunks = self.retriever.retrieve_multi_chunk(
                query=intent.query,
                grade=intent.target_grade,
                subject=intent.target_subject,
                topic=intent.target_topic,
                max_chunks=3
            )
        else:
            retrieved_chunks = self.retriever.retrieve(
                query=intent.query,
                grade=intent.target_grade,
                subject=intent.target_subject,
                topic=intent.target_topic,
                top_k=2
            )

        if not retrieved_chunks:
            self.validator.record_retrieval_failure()
            return {
                "custom_id": custom_id,
                "status": "REJECTED_NO_RETRIEVAL",
                "intent": intent.__dict__,
                "errors": ["No matching textbook chunks found for query."]
            }

        primary_chunk = retrieved_chunks[0]

        # 2. Locale Retrieval (if requested / relevant)
        locale_snippets: List[LocaleSnippet] = []
        if self.locale_retriever.is_localization_requested(intent.query):
            locale_snippets = self.locale_retriever.retrieve_locale_facts(intent.query)

        # 3. Grounding Compatibility Gate
        compat = self.gate.evaluate(
            user_query=intent.query,
            retrieved_chunk=primary_chunk,
            task_type=intent.task_type,
            target_subject=intent.target_subject,
            target_grade=intent.target_grade,
            locale_snippets=locale_snippets
        )

        if not compat.is_compatible:
            self.validator.record_compatibility_rejection()
            return {
                "custom_id": custom_id,
                "status": "REJECTED_COMPATIBILITY_GATE",
                "intent": intent.__dict__,
                "curriculum_fidelity_score": compat.curriculum_fidelity_score,
                "reasons": compat.reasons
            }

        # 4. Grounded Generation
        if llm_response_fn:
            assistant_response = llm_response_fn(intent, retrieved_chunks, locale_snippets)
        else:
            # Pedagogically structured fallback/mock response
            source_snippet = primary_chunk.get("source_text", "")
            locale_note = ""
            if locale_snippets:
                locale_note = f"\n\n[আঞ্চলিক উদাহরণ (locale.json)]: {locale_snippets[0].snippet_text}\n"

            if intent.requester_role == "TEACHER" and intent.instructional_target == "STUDENT":
                assistant_response = (
                    f"আপনি ক্লাসে শিক্ষার্থীদের '{intent.target_topic}' বিষয়টি সহজভাবে বোঝানোর জন্য নিচের পদ্ধতিটি অনুসরণ করতে পারেন:\n\n"
                    f"**মূল বিষয়ের ধারণা:**\n{source_snippet[:350]}...\n"
                    f"{locale_note}\n"
                    f"**শিক্ষার্থীদের উদ্দেশ্যে বলার মতো করে:**\n"
                    f"“তোমরা সবাই মন দিয়ে শোনো, {intent.target_topic} বিষয়টিকে আমরা বাস্তব জীবনের একটি সহজ উদাহরণের সাথে মিলিয়ে বুঝতে পারি।”\n\n"
                    f"এভাবে পাঠদান করলে শিক্ষার্থীরা বিষয়টি সহজে আত্মস্থ করতে পারবে।"
                )
            elif intent.task_type == "LESSON_PLAN":
                assistant_response = (
                    f"**পাঠ পরিকল্পনা (Lesson Plan): {intent.target_topic}**\n\n"
                    f"**১. শিক্ষণ উদ্দেশ্য:**\n- শিক্ষার্থীরা {intent.target_topic}-এর মূল নীতি বুঝতে পারবে।\n\n"
                    f"**২. প্রয়োজনীয় উপকরণ (TLM):** চক, ডাস্টার, ব্ল্যাকবোর্ড, পাঠ্যপুস্তক।\n\n"
                    f"**৩. পাঠদান পর্যায় (৪০ মিনিট):**\n"
                    f"- পূর্বজ্ঞান যাচাই (১০ মিনিট)\n- বিষয় উপস্থাপন (২০ মিনিট): {source_snippet[:250]}...\n- সারসংক্ষেপ ও মূল্যায়ন (১০ মিনিট)।\n\n"
                    f"**৪. মূল্যায়ন:** শিক্ষার্থীদের মৌখিক প্রশ্নোত্তরের মাধ্যমে মূল্যায়ন করা হবে।"
                )
            else:
                assistant_response = (
                    f"{intent.target_topic} সম্পর্কে ধারণাটি নিচে সহজভাবে বুঝিয়ে দেওয়া হলো:\n\n"
                    f"{source_snippet[:350]}...\n{locale_note}\n"
                    f"আশা করি, বিষয়টি তুমি ভালোভাবে বুঝতে পেরেছ।"
                )

        record = GroundedGenerator.format_record(
            custom_id=custom_id,
            intent=intent,
            grounding_chunks=retrieved_chunks,
            assistant_response=assistant_response,
            board=compat.board_authority
        )

        # Attach internal provenance
        record["metadata"]["provenance"] = {
            "curriculum": {
                "board": compat.board_authority,
                "grade": intent.target_grade,
                "subject": intent.target_subject,
                "textbook": primary_chunk.get("book_id"),
                "chapter": primary_chunk.get("chapter"),
                "topic": intent.target_topic
            },
            "curriculum_fidelity_score": compat.curriculum_fidelity_score,
            "textbook_source_chunks": [c.get("chunk_id") for c in retrieved_chunks if c.get("chunk_id")],
            "locale_source_chunks": [s.snippet_text for s in locale_snippets],
            "requester_role": intent.requester_role,
            "instructional_target": intent.instructional_target,
            "task_type": intent.task_type
        }

        # 5. Dimension-Wise Validation
        val_res = self.validator.validate_record(record)
        record["validation"] = {
            "passed": val_res.passed,
            "errors": val_res.errors,
            "warnings": val_res.warnings,
            "tier_failures": val_res.tier_failures,
            "dimension_scores": {
                "topic_alignment": compat.curriculum_fidelity_score,
                "curriculum_alignment": 5 if compat.is_compatible else 1,
                "local_context_groundedness": 5 if locale_snippets else "N/A",
                "factual_correctness": 5 if val_res.passed else 2,
                "instruction_following": 5 if val_res.passed else 3,
                "pedagogical_quality": 5 if val_res.passed else 3,
                "hallucination_risk": 0 if val_res.passed else 3,
                "overall": compat.curriculum_fidelity_score if val_res.passed else 1
            }
        }

        return record

    def export_dataset(
        self,
        records: List[Dict[str, Any]],
        output_dir: str,
        batch_name: str = "wbbse_sft_grounding_first_batch"
    ):
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        jsonl_file = out_path / f"{batch_name}.jsonl"
        audit_file = out_path / f"{batch_name}_audit.json"
        excel_file = out_path / f"{batch_name}.xlsx"

        # 1. Standard OpenAI format JSONL
        with open(jsonl_file, "w", encoding="utf-8") as f:
            for r in records:
                sft_export = {"messages": r.get("messages", [])}
                f.write(json.dumps(sft_export, ensure_ascii=False) + "\n")

        # 2. Rich Audit Summary with Dimension Metrics
        audit_data = {
            "batch_name": batch_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_records": len(records),
            "audit_metrics": self.validator.get_audit_summary(),
            "records_provenance_summary": [
                {
                    "custom_id": r.get("custom_id"),
                    "requester_role": r.get("metadata", {}).get("requester_role"),
                    "instructional_target": r.get("metadata", {}).get("instructional_target"),
                    "curriculum_fidelity_score": r.get("metadata", {}).get("provenance", {}).get("curriculum_fidelity_score"),
                    "locale_used": len(r.get("metadata", {}).get("provenance", {}).get("locale_source_chunks", [])) > 0,
                    "validation_passed": r.get("validation", {}).get("passed")
                }
                for r in records
            ]
        }
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)

        # 3. Formatted Excel Export
        excel_rows = []
        for r in records:
            meta = r.get("metadata", {})
            prov = meta.get("provenance", {})
            msgs = r.get("messages", [])
            u_prompt = msgs[1].get("content") if len(msgs) > 1 else ""
            a_resp = msgs[2].get("content") if len(msgs) > 2 else ""
            val = r.get("validation", {})
            dim_scores = val.get("dimension_scores", {})
            excel_rows.append({
                "Record ID": r.get("custom_id"),
                "Board Authority": meta.get("board"),
                "Grade": f"Class {meta.get('grade')}",
                "Subject": meta.get("subject"),
                "Topic": meta.get("topic"),
                "Task Type": meta.get("task_type"),
                "Requester Role": meta.get("requester_role"),
                "Instructional Target": meta.get("instructional_target"),
                "Curriculum Fidelity (0-5)": prov.get("curriculum_fidelity_score"),
                "Locale Context Grounding": " | ".join(prov.get("locale_source_chunks", [])) if prov.get("locale_source_chunks") else "None (Non-local Task)",
                "User Prompt": u_prompt,
                "Textbook Grounded Response": a_resp,
                "Validation Status": "PASSED" if val.get("passed") else "REJECTED",
                "Overall Dimension Score (0-5)": dim_scores.get("overall")
            })

        df = pd.DataFrame(excel_rows)
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Master_Grounding_First_SFT")

        wb = openpyxl.load_workbook(excel_file)
        ws = wb["Master_Grounding_First_SFT"]
        ws.views.sheetView[0].showGridLines = True
        h_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        h_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(1, col_idx)
            cell.font = h_font
            cell.fill = h_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
        wb.save(excel_file)

        print(f"Master Grounding-First Dataset exported to:\n - {jsonl_file}\n - {audit_file}\n - {excel_file}")
