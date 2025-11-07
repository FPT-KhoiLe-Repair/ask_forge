# backend/app/services/llm/adapters/gemini.py
import asyncio
from typing import AsyncIterator
import google.genai as genai

from ask_forge.backend.app.services.llm.base import LLMProvider
from ask_forge.backend.app.core.config import settings


class GeminiAdapter(LLMProvider):
    def __init__(self):
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._model_name = settings.GEMINI_MODEL_NAME

    async def generate(self, prompt: str, **kwargs) -> str:
        loop = asyncio.get_running_loop()
        # Gemini SDK chưa async native → wrap in executor
        response = await loop.run_in_executor(
            None,
            lambda: self._client.models.generate_content(
                model=self._model_name,
                contents=prompt
            )
        )
        return getattr(response, "text", "")

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        def sync_gen():
            stream = self._client.models.generate_content_stream(
                model=self._model_name,
                contents=prompt,
            )
            for event in stream:
                chunk = getattr(event, "text", None)
                if chunk:
                    yield chunk

        for chunk in sync_gen():  # chạy sync
            yield chunk  # yield từng token ra ngoài (bắt SSE gửi ngay)
            await asyncio.sleep(0)  # nhường event loop

    @property
    def model_name(self) -> str:
        return f"gemini:{self._model_name}"

    @property
    def supports_streaming(self) -> bool:
        return True