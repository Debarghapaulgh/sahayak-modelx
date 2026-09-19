import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class QuestionValidationResult(BaseModel):
    question_text: str
    is_relevant: bool
    relevance_score: float
    detected_hard_negative: Optional[str] = None
    reason: str

class QuizValidationReport(BaseModel):
    passed: bool
    topic_match_passed: bool
    marks_match_passed: bool
    answer_structure_passed: bool
    hard_negative_passed: bool
    requested_topic: str
    canonical_topic: str
    target_marks: Optional[int] = None
    calculated_marks: int = 0
    question_reports: List[QuestionValidationResult] = Field(default_factory=list)
    failure_reasons: List[str] = Field(default_factory=list)

class QuizTopicValidator:
    @classmethod
    def validate_quiz(
        cls,
        quiz_text: str,
        requested_topic: str,
        canonical_topic: str,
        hard_negatives: List[str] = None,
        target_marks: Optional[int] = None,
        audience: str = 'TEACHER'
    ) -> QuizValidationReport:
        hard_negatives = hard_negatives or []
        failures = []
        
        hard_negative_detected = None
        for hn in hard_negatives:
            if hn.lower() in quiz_text.lower():
                hard_negative_detected = hn
                failures.append('Hard negative detected: ' + hn + ' found in quiz text while requested topic is ' + requested_topic)
                break
        
        hard_negative_passed = (hard_negative_detected is None)

        question_lines = cls._extract_questions(quiz_text)
        question_reports = []
        clean_topic = requested_topic.replace('অধ্যায়', '').replace(':', '')
        topic_keywords = [w for w in clean_topic.split() if len(w) > 2]
        
        relevant_count = 0
        for q in question_lines:
            q_hn = None
            for hn in hard_negatives:
                if hn.lower() in q.lower():
                    q_hn = hn
                    break
            
            is_rel = True
            reason = 'Question matches requested topic context.'
            if q_hn:
                is_rel = False
                reason = 'Question contains hard negative: ' + q_hn
            
            if is_rel and topic_keywords:
                has_overlap = any(kw.lower() in q.lower() for kw in topic_keywords)
                rel_score = 1.0 if has_overlap else 0.8
            else:
                rel_score = 0.0 if not is_rel else 0.85
                
            if is_rel:
                relevant_count += 1
                
            question_reports.append(QuestionValidationResult(
                question_text=q[:100],
                is_relevant=is_rel,
                relevance_score=rel_score,
                detected_hard_negative=q_hn,
                reason=reason
            ))

        topic_match_passed = hard_negative_passed and (len(question_reports) == 0 or (relevant_count / len(question_reports)) >= 0.75)
        if not topic_match_passed and not any('Hard negative detected' in r for r in failures):
            failures.append('Topic match failed: Questions do not sufficiently test ' + requested_topic)

        marks_match_passed = True
        calculated_marks = cls._extract_marks(quiz_text)
        if target_marks is not None and target_marks > 0:
            if calculated_marks > 0 and calculated_marks != target_marks:
                marks_match_passed = False
                failures.append(f'Marks mismatch: Requested {target_marks} marks, but quiz structured for {calculated_marks} marks')

        answer_structure_passed = True
        if audience == 'TEACHER':
            has_embedded_leak = 'উত্তর:' in quiz_text and 'উত্তর নির্দেশিকা' not in quiz_text and '---' not in quiz_text
            if has_embedded_leak:
                answer_structure_passed = False
                failures.append('Teacher mode violation: Answer embedded directly under question instead of separated Answer Key block')

        passed = topic_match_passed and marks_match_passed and hard_negative_passed

        return QuizValidationReport(
            passed=passed,
            topic_match_passed=topic_match_passed,
            marks_match_passed=marks_match_passed,
            answer_structure_passed=answer_structure_passed,
            hard_negative_passed=hard_negative_passed,
            requested_topic=requested_topic,
            canonical_topic=canonical_topic,
            target_marks=target_marks,
            calculated_marks=calculated_marks,
            question_reports=question_reports,
            failure_reasons=failures
        )

    @staticmethod
    def _extract_questions(text: str) -> List[str]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        q_lines = []
        for line in lines:
            if re.match(r'^(?:Q\d+|\d+[\.\)]|[১-৯]+[\.\)])', line):
                q_lines.append(line)
        return q_lines

    @staticmethod
    def _extract_marks(text: str) -> int:
        bengali_digits = '০১২৩৪৫৬৭৮৯'
        trans_table = str.maketrans(bengali_digits, '0123456789')
        
        total_explicit = re.findall(r'পূর্ণমান[:\s*]+([0-9০-৯]+)', text)
        if total_explicit:
            num_str = total_explicit[0].translate(trans_table)
            return int(num_str)
        
        q_marks = re.findall(r'\(([0-9০-৯]+)\s*নম্বর\)', text)
        if q_marks:
            total = sum(int(m.translate(trans_table)) for m in q_marks)
            return total
        return 0
