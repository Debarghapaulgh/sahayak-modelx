"""
Multilingual Adaptation Layer for Indic Languages and Code-Switching (e.g., Hinglish).
"""

import copy
from typing import List
from synthetictutor.core.schemas import DialogueSession, DialogueTurn
from synthetictutor.llm.base import BaseLLMClient
from pydantic import BaseModel, Field


class TranslationResponse(BaseModel):
    translated_turns: List[str] = Field(..., description="List of translated utterances maintaining turn order")


class IndicTranslator:
    """Adapts English Socratic dialogues into Indic target languages (e.g., Hindi, Tamil, Hinglish)."""

    INDIC_LANGUAGE_NAMES = {
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "bn": "Bengali",
        "mr": "Marathi",
        "kn": "Kannada",
        "hinglish": "Hinglish (Hindi written in Roman script mixed with natural English technical terms)"
    }

    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    async def translate_session(
        self,
        session: DialogueSession,
        target_language_code: str = "hi"
    ) -> DialogueSession:
        """Translates a DialogueSession into the specified target language while preserving technical accuracy."""
        lang_name = self.INDIC_LANGUAGE_NAMES.get(target_language_code.lower(), target_language_code)

        turns_text = "\n".join([f"Turn {t.turn_number} ({t.role.value}): {t.content}" for t in session.turns])

        prompt = (
            f"Translate the following educational Socratic dialogue into {lang_name}.\n"
            f"Keep technical terms (like 'gravity', 'acceleration', 'force') natural and clear to student.\n"
            f"Preserve the turn order and speaker roles exactly.\n\n"
            f"Dialogue:\n{turns_text}\n"
        )
        system = f"You are a native educational translator specializing in {lang_name}. Ensure natural educational dialogue."

        res: TranslationResponse = await self.llm_client.generate_structured(
            prompt=prompt,
            response_schema=TranslationResponse,
            system_instruction=system,
            temperature=0.3
        )

        translated_session = session.model_copy(deep=True)
        translated_session.language = target_language_code

        for i, new_text in enumerate(res.translated_turns):
            if i < len(translated_session.turns):
                translated_session.turns[i].content = new_text

        return translated_session
