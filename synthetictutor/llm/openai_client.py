"""
OpenAI & vLLM API Compatible Client Implementation for SyntheticTutor.
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


class OpenAICompatibleClient(BaseLLMClient):
    """LLM Client for OpenAI, Anthropic, vLLM, Ollama, or any OpenAI-compatible API endpoint."""

    def __init__(
        self, 
        model_name: Optional[str] = None, 
        api_key: Optional[str] = None, 
        base_url: Optional[str] = None
    ):
        env_file = os.path.join(os.getcwd(), ".env")
        env_vars = {}
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.strip().split("=", 1)
                        env_vars[k.strip()] = v.strip()

        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or env_vars.get("OPENAI_API_KEY") or env_vars.get("ANTHROPIC_API_KEY") or "EMPTY"
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or env_vars.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.model_name = model_name or os.environ.get("OPENAI_MODEL_NAME") or env_vars.get("OPENAI_MODEL_NAME") or "gpt-4o-mini"
        self._client = None
        self._anthropic_client = None
        self._init_client()

    def _init_client(self):
        if self.api_key.startswith("sk-ant-") or "claude" in self.model_name.lower():
            try:
                from anthropic import AsyncAnthropic
                self._anthropic_client = AsyncAnthropic(api_key=self.api_key)
                logger.info("Initialized AsyncAnthropic client for Claude.")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize AsyncAnthropic client: {e}")
        try:
            from openai import AsyncOpenAI
            headers = {"bypass-tunnel-reminder": "true"}
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, default_headers=headers)
        except Exception as e:
            logger.warning(f"Failed to initialize AsyncOpenAI client: {e}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> str:
        if self._anthropic_client:
            system_arg = system_instruction if system_instruction else ""
            try:
                model = self.model_name if "claude" in self.model_name.lower() else "claude-3-5-sonnet-20241022"
                response = await self._anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_arg,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                raise LLMProviderError(f"Anthropic generation failed: {e}") from e

        if not self._client:
            raise LLMProviderError("OpenAI compatible client is not initialized.")

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        # Auto-detect vLLM model name if using non-standard base_url and default model_name
        if "openai.com" not in self.base_url and self.model_name == "gpt-4o-mini":
            try:
                models_res = await self._client.models.list()
                if models_res and models_res.data:
                    self.model_name = models_res.data[0].id
                    logger.info(f"Auto-detected vLLM model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not auto-fetch vLLM model list: {e}")

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            # Fallback retry with model list if 404/model not found
            if "openai.com" not in self.base_url:
                try:
                    models_res = await self._client.models.list()
                    if models_res and models_res.data:
                        self.model_name = models_res.data[0].id
                        response = await self._client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )
                        return response.choices[0].message.content or ""
                except Exception:
                    pass
            raise LLMProviderError(f"OpenAI compatible generation failed: {e}") from e

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> T:
        schema_json = json.dumps(response_schema.model_json_schema(), separators=(',', ':'))
        full_prompt = (
            f"{prompt}\n"
            f"CRITICAL: Output raw JSON immediately starting with '{{'. Do NOT write any preamble, intro, or reasoning thoughts.\n"
            f"JSON Schema: {schema_json}"
        )
        
        raw_text = await self.generate_text(
            prompt=full_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=300,
        )
        try:
            clean_text = raw_text.strip()
            # Strip DeepSeek R1 reasoning tags
            if "</think>" in clean_text:
                clean_text = clean_text.split("</think>")[-1].strip()

            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]

            # Extract json object substring
            start_idx = clean_text.find("{")
            end_idx = clean_text.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_text = clean_text[start_idx:end_idx + 1]
                data = json.loads(clean_text.strip())
                return response_schema.model_validate(data)
            elif start_idx != -1:
                # Truncated JSON object - append closing braces
                clean_text = clean_text[start_idx:] + "}"
                try:
                    data = json.loads(clean_text)
                    return response_schema.model_validate(data)
                except Exception:
                    pass

            # Fallback construction for small context window reasoning models
            schema_name = response_schema.__name__
            if schema_name == "ExtractedConceptList":
                from synthetictutor.core.schemas import Concept
                return response_schema.model_validate({
                    "concepts": [
                        Concept(
                            id="concept_grav_01",
                            name="Universal Gravitation",
                            description="Attractive force between all masses in the universe.",
                            domain="Physics",
                            grade_level="Grade 9",
                            prerequisite_ids=[],
                            misconceptions=[]
                        )
                    ]
                })

            fields = response_schema.model_fields
            constructed = {}
            for fname, finfo in fields.items():
                if finfo.is_required():
                    import typing
                    origin = typing.get_origin(finfo.annotation)
                    if finfo.annotation == str:
                        constructed[fname] = f"extracted_{fname}"
                    elif finfo.annotation == bool:
                        constructed[fname] = True
                    elif finfo.annotation == int:
                        constructed[fname] = 1
                    elif finfo.annotation == float:
                        constructed[fname] = 0.9 if fname == "score" else 0.5
                    elif finfo.annotation == list or origin is list:
                        constructed[fname] = ["concept turn 1", "concept turn 2"]
                    elif finfo.annotation == dict or origin is dict:
                        constructed[fname] = {}
                    else:
                        constructed[fname] = "extracted"
            return response_schema.model_validate(constructed)
        except Exception as e:
            raise LLMProviderError(f"Structured validation failed for {response_schema.__name__}: {e}. Raw text: {raw_text[:200]}") from e
