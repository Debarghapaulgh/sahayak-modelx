"""
Ingestion module for parsing textbook sources and chunking.
"""

from synthetictutor.ingestion.json_parser import TextbookParser
from synthetictutor.ingestion.text_chunker import EducationalChunker

__all__ = ["TextbookParser", "EducationalChunker"]
