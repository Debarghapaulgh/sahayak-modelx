"""
Concept-aware text chunking for educational curriculum materials.
"""

from typing import List, Dict, Any


class EducationalChunker:
    """Splits textbook chapters into semantically coherent educational sections."""

    def __init__(self, target_chunk_size: int = 1500, overlap: int = 200):
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunks text based on paragraph boundaries while preserving metadata."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_chunk = []
        current_length = 0

        for p in paragraphs:
            p_len = len(p)
            if current_length + p_len > self.target_chunk_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "chunk_id": f"chunk_{len(chunks) + 1}",
                    "content": chunk_text,
                    "metadata": metadata
                })
                # Keep last paragraph for overlap
                current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
                current_length = sum(len(x) for x in current_chunk)

            current_chunk.append(p)
            current_length += p_len

        if current_chunk:
            chunks.append({
                "chunk_id": f"chunk_{len(chunks) + 1}",
                "content": "\n\n".join(current_chunk),
                "metadata": metadata
            })

        return chunks
