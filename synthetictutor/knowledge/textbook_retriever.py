"""
Textbook Retriever Engine for SahayakAI Grounding-First SFT Pipeline.
Provides indexed lexical (BM25) and hierarchical curriculum retrieval across
the verified WBBSE textbook source pool.
"""

import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict


class BengaliTokenizer:
    """Lightweight Bengali and English tokenizer with punctuation stripping."""

    PUNCT_PATTERN = re.compile(r'[\s।,\.\?!:;\-\(\)\[\]\{\}"\'`\«\»—_/\\]+')

    STOPWORDS = {
        'এই', 'একটি', 'হলো', 'হলে', 'হয়', 'হয়ে', 'থেকে', 'করে', 'করা', 'কি', 'কী',
        'যে', 'যা', 'যার', 'যাকে', 'এবং', 'ও', 'বা', 'আর', 'না', 'নয়', 'জন্য',
        'দিয়ে', 'মতো', 'কোনো', 'কিছু', 'তা', 'তার', 'তাকে', 'তারা', 'তাদের', 'তুমি',
        'তোমার', 'তোমাকে', 'তোমরা', 'তোমাদের', 'আমি', 'আমার', 'আমাকে', 'আমরা', 'আমাদের',
        'আপনি', 'আপনার', 'আপনাকে', 'আপনারা', 'আপনাদের', 'সে', 'এখানে', 'সেখানে',
        'the', 'is', 'a', 'an', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at'
    }

    @classmethod
    def tokenize(cls, text: str) -> List[str]:
        if not text:
            return []
        tokens = [t.strip().lower() for t in cls.PUNCT_PATTERN.split(text) if t.strip()]
        return [t for t in tokens if len(t) > 1 and t not in cls.STOPWORDS]


class BM25Index:
    """In-memory BM25 index over textbook chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: List[int] = []
        self.doc_token_counts: List[Counter] = []
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
        self.idf: Dict[str, float] = {}

    def fit(self, tokenized_docs: List[List[str]]):
        self.corpus_size = len(tokenized_docs)
        if self.corpus_size == 0:
            return
        self.doc_lengths = [len(doc) for doc in tokenized_docs]
        self.avg_doc_len = sum(self.doc_lengths) / self.corpus_size
        self.doc_token_counts = [Counter(doc) for doc in tokenized_docs]

        df: Dict[str, int] = defaultdict(int)
        for doc_id, token_counts in enumerate(self.doc_token_counts):
            for token, freq in token_counts.items():
                self.inverted_index[token].append((doc_id, freq))
                df[token] += 1

        for token, freq in df.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def search(self, query_tokens: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        scores = defaultdict(float)
        query_counts = Counter(query_tokens)

        for token, q_tf in query_counts.items():
            if token not in self.inverted_index:
                continue
            idf_val = self.idf[token]
            for doc_id, tf in self.inverted_index[token]:
                doc_len = self.doc_lengths[doc_id]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                scores[doc_id] += idf_val * (numerator / denominator)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class TextbookRetriever:
    """Curriculum-aware multi-tier textbook retriever."""

    def __init__(self, source_pool_path: str = "wbbse_sft_source_pool.jsonl"):
        self.source_pool_path = Path(source_pool_path)
        self.records: List[Dict[str, Any]] = []
        self.bm25 = BM25Index()
        self._load_and_index()

    def _load_and_index(self):
        if not self.source_pool_path.exists():
            raise FileNotFoundError(f"Textbook source pool not found at: {self.source_pool_path}")

        tokenized_docs = []
        with open(self.source_pool_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                rec = json.loads(line)
                rec["_pool_index"] = idx
                self.records.append(rec)

                # Combine searchable text: topic + chapter + subject + source_text
                searchable_text = f"{rec.get('subject', '')} {rec.get('chapter', '')} {rec.get('topic', '')} {rec.get('source_text', '')}"
                tokenized_docs.append(BengaliTokenizer.tokenize(searchable_text))

        self.bm25.fit(tokenized_docs)

    def retrieve(
        self,
        query: str,
        grade: Optional[Any] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching textbook chunks using intent query & optional metadata filters.
        """
        query_tokens = BengaliTokenizer.tokenize(query)
        if topic:
            query_tokens.extend(BengaliTokenizer.tokenize(topic) * 2)

        bm25_results = self.bm25.search(query_tokens, top_k=top_k * 5)

        matched_chunks = []
        for doc_id, score in bm25_results:
            if score < min_score:
                continue

            rec = self.records[doc_id]

            # Grade filter
            if grade is not None:
                rec_grade = str(rec.get("grade", "")).strip()
                target_grade = str(grade).replace("Class", "").replace("class", "").strip()
                if rec_grade and target_grade and rec_grade != target_grade:
                    continue

            # Subject filter (case-insensitive fuzzy substring)
            if subject:
                rec_subj = (rec.get("subject") or "").lower()
                target_subj = subject.lower()
                if target_subj not in rec_subj and rec_subj not in target_subj:
                    continue

            result_rec = dict(rec)
            result_rec["retrieval_score"] = round(score, 4)
            matched_chunks.append(result_rec)

            if len(matched_chunks) >= top_k:
                break

        return matched_chunks

    def retrieve_multi_chunk(
        self,
        query: str,
        grade: Optional[Any] = None,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        max_chunks: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieves contiguous or highly relevant multi-chunks for complex tasks (e.g. Lesson Plans).
        """
        primary_chunks = self.retrieve(query, grade=grade, subject=subject, topic=topic, top_k=1)
        if not primary_chunks:
            return []

        primary = primary_chunks[0]
        book_id = primary.get("book_id")
        chapter = primary.get("chapter")
        page_start = primary.get("page_start", 0)

        # Look for contiguous chunks in the same book/chapter
        contiguous_chunks = [primary]
        for rec in self.records:
            if len(contiguous_chunks) >= max_chunks:
                break
            if rec.get("chunk_id") == primary.get("chunk_id"):
                continue
            if rec.get("book_id") == book_id and rec.get("chapter") == chapter:
                rec_p_start = rec.get("page_start", 0)
                if abs(rec_p_start - page_start) <= 5:
                    c_rec = dict(rec)
                    c_rec["retrieval_score"] = primary["retrieval_score"] * 0.9
                    contiguous_chunks.append(c_rec)

        return contiguous_chunks
