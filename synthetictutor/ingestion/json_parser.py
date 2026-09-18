"""
Curriculum document parser for structured JSON and plain text textbook chapters.
"""

import json
import os
from typing import Dict, Any, List
from synthetictutor.core.exceptions import IngestionError


class TextbookParser:
    """Parser for reading and normalizing textbook sources."""

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Reads a JSON or text file and returns standardized chapter payload."""
        if not os.path.exists(file_path):
            raise IngestionError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            return self._parse_json(file_path)
        else:
            return self._parse_text(file_path)

    def _parse_json(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Ensure standard fields
            return {
                "chapter_title": data.get("title", os.path.basename(file_path)),
                "domain": data.get("domain", "Science"),
                "grade_level": data.get("grade_level", "Grade 9"),
                "content": data.get("content", ""),
                "sections": data.get("sections", []),
            }
        except Exception as e:
            raise IngestionError(f"Failed to parse JSON textbook source: {e}") from e

    def _parse_text(self, file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            filename = os.path.basename(file_path)
            return {
                "chapter_title": filename.rsplit(".", 1)[0].replace("_", " ").title(),
                "domain": "General Science",
                "grade_level": "Grade 9",
                "content": text,
                "sections": [{"title": "Full Content", "text": text}],
            }
        except Exception as e:
            raise IngestionError(f"Failed to parse text file: {e}") from e
