"""
Abstract base class for LLM provider implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMClient(ABC):
    """Abstract base LLM client ensuring consistent interface across providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate raw text response from the LLM model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        """Generate structured response validated against a Pydantic schema."""
        pass
