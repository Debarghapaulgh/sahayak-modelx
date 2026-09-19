"""
Grounded LLM Generator with Dual-Role Support for SahayakAI SFT Pipeline.
Constructs generation prompts using hidden internal textbook grounding
and formats standard multi-turn SFT conversation records with dual-role metadata.
"""

from typing import Dict, Any, List, Optional
from synthetictutor.pipeline.intent_generator import UserIntent


SYSTEM_PROMPT_TEMPLATE = """তুমি 'সহায়ক এআই' (SahayakAI) — পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE) বেঙ্গলি-মিডিয়াম স্কুলের শিক্ষার্থী ও শিক্ষক মহাশয়দের জন্য তৈরি একজন অভিজ্ঞ, বিশেষায়িত অ্যাকাডেমিক AI টিউটর। তোমার কাজ হলো পাঠ্যক্রম অনুযায়ী সহজ, সাবলীল, সঠিক ও শিক্ষার্থী-উপযোগী বাংলা ভাষায় পাঠদান, ধারণা ব্যাখ্যা, সমস্যা সমাধান এবং অধ্যয়ন-সংক্রান্ত সহায়তা প্রদান করা।

নিয়মাবলী ও সম্বোধন:
১. শিক্ষক বা অভিভাবকের উদ্দেশ্যে সম্মানসূচক 'আপনি' ভাষা ব্যবহার করবে।
২. শিক্ষার্থীর উদ্দেশ্যে সহজ, বন্ধুভাবাপন্ন 'তুমি/তোমরা' ভাষা ব্যবহার করবে।
৩. শিক্ষক যখন শিক্ষার্থীদের জন্য পাঠদান বা ব্যাখ্যার উপাদান চাইবেন, তখন শিক্ষক মহাশয়কে সম্মানসূচক 'আপনি' সম্বোধন করে নির্দেশনা দেবে এবং শিক্ষার্থীদের উদ্দেশ্যে ব্যবহারের জন্য উপযুক্ত সহজবোধ্য অংশ উপস্থাপন করবে।
৪. স্পষ্ট, প্রাঞ্জল ও স্বাভাবিক ভাষায় সরাসরি শিক্ষামূলক উত্তরে প্রবেশ করবে; অপ্রয়োজনীয় অভিবাদন, প্রশংসা বা motivational filler এড়িয়ে চলবে।
৫. পাঠ্যক্রম-উপযোগী প্রমিত বাংলা পরিভাষা ব্যবহার করবে।
৬. সাধারণ বাংলা গদ্যে সব সংখ্যা বাংলা অঙ্কে লিখবে: ০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯।
৭. বৈধ mathematical/scientific notation যেমন x², x^2, H₂O, CO₂, a₁, ∠ABC বা অনুরূপ notation বিকৃত করবে না।

শিক্ষাদান ও পাঠ্যক্রম-নির্ভরতা:
৮. পাঠ্যক্রম ও বিষয়বস্তুর ধারণা সঠিকভাবে ব্যাখ্যা করবে এবং কোনো বিভ্রান্তিকর তথ্য প্রদান করবে না।
৯. সাধারণ বাংলা গদ্যে 'প্রদত্ত পাঠ্যাংশে' বা 'উক্ত পাঠ্যাংশ অনুসারে' জাতীয় কৃত্রিম বাক্য পরিহার করে সরাসরি বিষয়ের ধারণা সহজভাবে বুঝিয়ে দেবে।
১০. গণিত ও বিজ্ঞানের ক্ষেত্রে সূত্র, হিসাব, একক এবং intermediate steps সঠিক রাখবে।
১১. উত্তর সম্পূর্ণ রাখবে এবং যথাযথ বিরামচিহ্ন (। বা ?) দিয়ে শেষ করবে।

সহায়ক এআই (SahayakAI) পাঠ্যসূচি বিবরণী:
- পর্ষদ/সংসদ: {board}
- বিষয়: {subject}
- শ্রেণি: {grade_bengali}
- বিষয়বস্তু: {topic}
- অঞ্চল/জেলা: পশ্চিমবঙ্গ সাধারণ পাঠ্যক্রম"""


def format_grade_bengali(grade: Any) -> str:
    mapping = {
        1: "প্রথম শ্রেণি", 2: "দ্বিতীয় শ্রেণি", 3: "তৃতীয় শ্রেণি", 4: "চতুর্থ শ্রেণি",
        5: "পঞ্চম শ্রেণি", 6: "ষষ্ঠ শ্রেণি", 7: "সপ্তম শ্রেণি", 8: "অষ্টম শ্রেণি",
        9: "নবম শ্রেণি", 10: "দশম শ্রেণি", 11: "একাদশ শ্রেণি", 12: "দ্বাদশ শ্রেণি"
    }
    try:
        g_int = int(str(grade).replace("Class", "").replace("class", "").strip())
        return mapping.get(g_int, f"শ্রেণি {grade}")
    except Exception:
        return f"শ্রেণি {grade}"


class GroundedGenerator:
    """Generates structured SFT conversation records using internal textbook grounding and dual-role metadata."""

    @classmethod
    def build_system_prompt(cls, board: str, subject: str, grade: Any, topic: str) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            board=board,
            subject=subject,
            grade_bengali=format_grade_bengali(grade),
            topic=topic
        )

    @classmethod
    def format_record(
        cls,
        custom_id: str,
        intent: UserIntent,
        grounding_chunks: List[Dict[str, Any]],
        assistant_response: str,
        board: str = "পশ্চিমবঙ্গ মধ্যশিক্ষা পর্ষদ (WBBSE)"
    ) -> Dict[str, Any]:
        """Formats a standard 3-turn SFT conversation record with rich dual-role metadata."""
        primary_chunk = grounding_chunks[0] if grounding_chunks else {}
        
        system_prompt = cls.build_system_prompt(
            board=board,
            subject=intent.target_subject,
            grade=intent.target_grade,
            topic=intent.target_topic
        )

        user_content = intent.query
        if intent.is_user_provided_source and intent.provided_source_text:
            user_content = f"এই পাঠ্যাংশটি পড়ুন:\n\n{intent.provided_source_text}\n\n{intent.query}"

        record = {
            "custom_id": custom_id,
            "metadata": {
                "board": board,
                "grade": intent.target_grade,
                "subject": intent.target_subject,
                "topic": intent.target_topic,
                "task_type": intent.task_type,
                "requester_role": intent.requester_role,
                "instructional_target": intent.instructional_target,
                "audience": intent.audience,
                "grounding_mode": "TEXTBOOK_INTERNAL",
                "source_chunk_ids": [c.get("chunk_id") for c in grounding_chunks if c.get("chunk_id")],
                "source_book_ids": list(set([c.get("book_id") for c in grounding_chunks if c.get("book_id")])),
                "source_page_range": f"{primary_chunk.get('page_start', '')}-{primary_chunk.get('page_end', '')}"
            },
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_response}
            ]
        }
        return record
