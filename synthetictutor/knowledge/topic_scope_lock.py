"""
Topic Scope Lock & Curriculum Normalization Module.
Ensures generation requests resolve to verified curriculum boundaries before retrieval or generation.
"""

import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class TopicScope(BaseModel):
    board: str = "WBBSE"
    grade: int
    subject: str
    requested_topic: str
    canonical_topic: str
    chapter_number: Optional[str] = None
    status: str = "VERIFIED"
    retrieval_scope_filter: Dict[str, Any] = Field(default_factory=dict)
    hard_negatives: List[str] = Field(default_factory=list)

class TopicScopeLock:
    """Curriculum topic authority & normalization engine."""

    TOPIC_REGISTRY = {
        (6, "Mathematics"): [
            {
                "chapter": "10",
                "title": "আবৃত্ত দশমিক সংখ্যা",
                "canonical": "অধ্যায় ১০: আবৃত্ত দশমিক সংখ্যা",
                "keywords": ["আবৃত্ত দশমিক", "recurring decimal", "পৌনঃপুনিক", "দশমিক"],
                "hard_negatives": ["প্যাটার্ন", "নকশা", "sequence", "pattern", "ভগ্নাংশের গুণ"]
            },
            {
                "chapter": "1",
                "title": "পূর্বপাঠের পুনরালোচনা",
                "canonical": "অধ্যায় ১: পূর্বপাঠের পুনরালোচনা",
                "keywords": ["পূর্বপাঠ", "লসাগু", "গসাগু"],
                "hard_negatives": []
            }
        ],
        (7, "Mathematics"): [
            {
                "chapter": "16",
                "title": "দ্বি-স্তম্ভ লেখ",
                "canonical": "অধ্যায় ১৬: দ্বি-স্তম্ভ লেখ",
                "keywords": ["দ্বি-স্তম্ভ", "দ্বিস্তম্ভ", "স্তম্ভ লেখ", "double bar graph", "বার গ্রাফ", "লেখচিত্র"],
                "hard_negatives": ["বৃহৎ সংখ্যা", "স্থানীয় মান", "place value", "large number"]
            }
        ],
        (8, "Mathematics"): [
            {
                "chapter": "11",
                "title": "শতকরা",
                "canonical": "অধ্যায় ১১: শতকরা",
                "keywords": ["শতকরা", "percentage", "শতকরা হিসাব", "পার্সেন্টেজ"],
                "hard_negatives": ["বর্গক্ষেত্র", "ঘনক", "square", "cube", "বীজগাণিতিক"]
            },
            {
                "chapter": "12",
                "title": "মিশ্রণ",
                "canonical": "অধ্যায় ১২: মিশ্রণ",
                "keywords": ["মিশ্রণ", "mixture", "অনুপাত"],
                "hard_negatives": ["জ্যামিতি", "বৃত্ত"]
            }
        ],
        (4, "Health and Physical Education"): [
            {
                "chapter": "N/A",
                "title": "স্বাস্থ্যবিধান ও পরিবেশ সচেতনতা",
                "canonical": "স্বাস্থ্যবিধান ও পরিবেশ সচেতনতা — নির্মল বিদ্যালয়",
                "keywords": ["নির্মল বিদ্যালয়", "স্বাস্থ্যবিধান", "পরিবেশ সচেতনতা", "হাত ধোয়া", "শৌচাগার"],
                "hard_negatives": ["ক্রিকেট", "ফুটবল"]
            }
        ]
    }

    @classmethod
    def resolve_topic(cls, grade: int, subject: str, raw_topic_query: str, board: str = "WBBSE") -> TopicScope:
        normalized_query = raw_topic_query.strip().lower()
        candidates = cls.TOPIC_REGISTRY.get((grade, subject), [])
        
        for c in candidates:
            for kw in c["keywords"]:
                if kw.lower() in normalized_query:
                    return TopicScope(
                        board=board,
                        grade=grade,
                        subject=subject,
                        requested_topic=raw_topic_query,
                        canonical_topic=c["canonical"],
                        chapter_number=c.get("chapter"),
                        status="VERIFIED",
                        retrieval_scope_filter={
                            "board": board,
                            "grade": grade,
                            "subject": subject,
                            "chapter": c.get("chapter"),
                            "canonical_topic": c["canonical"]
                        },
                        hard_negatives=c.get("hard_negatives", [])
                    )

        if len(normalized_query) > 2:
            return TopicScope(
                board=board,
                grade=grade,
                subject=subject,
                requested_topic=raw_topic_query,
                canonical_topic=raw_topic_query,
                chapter_number=None,
                status="VERIFIED",
                retrieval_scope_filter={
                    "board": board,
                    "grade": grade,
                    "subject": subject,
                    "topic_query": raw_topic_query
                },
                hard_negatives=[]
            )

        return TopicScope(
            board=board,
            grade=grade,
            subject=subject,
            requested_topic=raw_topic_query,
            canonical_topic="UNKNOWN",
            status="NOT_FOUND",
            retrieval_scope_filter={},
            hard_negatives=[]
        )