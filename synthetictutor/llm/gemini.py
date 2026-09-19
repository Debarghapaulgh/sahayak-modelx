"""
Google Gemini API Client Implementation for SyntheticTutor.
"""

import os
import json
import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from synthetictutor.llm.base import BaseLLMClient
from synthetictutor.core.exceptions import LLMProviderError

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiLLMClient(BaseLLMClient):
    """LLM Client for Google Gemini API models."""

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            env_file = os.path.join(os.getcwd(), ".env")
            if os.path.exists(env_file):
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("GEMINI_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1].strip()
                            break
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from google import genai
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                # Fallback to default credentials environment
                self._client = genai.Client()
        except Exception as e:
            logger.warning(f"Failed to initialize google-genai Client: {e}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        if not self._client:
            raise LLMProviderError("Gemini client is not initialized. Ensure GEMINI_API_KEY is configured.")
        
        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction
        config["temperature"] = temperature
        config["max_output_tokens"] = max_tokens

        import asyncio
        fallback_models = [self.model_name, "gemini-2.5-flash-lite", "gemini-2.5-pro"]
        last_err = None
        for attempt in range(3):
            for m in fallback_models:
                try:
                    response = self._client.models.generate_content(
                        model=m,
                        contents=prompt,
                        config=config
                    )
                    return response.text or ""
                except Exception as ex:
                    last_err = ex
                    if "429" in str(ex) or "RESOURCE_EXHAUSTED" in str(ex):
                        logger.warning(f"Gemini model {m} hit 429 quota (attempt {attempt+1}/3). Waiting 20s for rate limit window to reset...")
                        await asyncio.sleep(20)
                        continue
                    raise ex
        raise LLMProviderError(f"Gemini API generation failed across models: {last_err}") from last_err

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        if not self._client:
            raise LLMProviderError("Gemini client is not initialized. Ensure GEMINI_API_KEY is configured.")

        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        full_prompt = (
            f"{prompt}\n\n"
            f"You MUST respond ONLY with valid JSON matching the following schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include any pre-amble, markdown fences outside json, or explanation."
        )

        try:
            raw_text = await self.generate_text(
                prompt=full_prompt,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=2048,
            )
            clean_text = raw_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            data = json.loads(clean_text.strip())
            return response_schema.model_validate(data)
        except Exception as e:
            raise LLMProviderError(f"Gemini structured generation failed for schema {response_schema.__name__}: {e}") from e
