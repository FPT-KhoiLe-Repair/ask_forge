# backend/app/services/llm/router.py
from typing import Optional, Callable
import logging

from ask_forge.backend.app.services.llm.base import LLMProvider
from ask_forge.backend.app.services.llm.registry import get_registry

logger = logging.getLogger(__name__)


class LLMRouter:
    """Route requests đến LLM provider phù hợp"""

    def __init__(self):
        self.registry = get_registry()
        self._default_provider = "gemini"  # Fallback
        self._routing_policies: list[Callable] = []

    def add_policy(self, policy: Callable[[dict], Optional[str]]):
        """Thêm routing policy (ví dụ: route theo lang, task type)"""
        self._routing_policies.append(policy)

    async def route(self, context: dict) -> LLMProvider:
        """
        Chọn provider dựa trên context.

        context = {
            "task": "chat" | "qg" | "summary",
            "lang": "vi" | "en",
            "latency_requirement": "low" | "high",
            "prefer_local": bool
        }
        """
        # Chạy policies theo thứ tự
        for policy in self._routing_policies:
            provider_name = policy(context)
            if provider_name:
                provider = self.registry.get(provider_name)
                if provider:
                    logger.info(f"🎯 Routed to: {provider_name}")
                    return provider

        # Fallback
        logger.warning(f"⚠️ No policy matched, using default: {self._default_provider}")
        return self.registry.get(self._default_provider)


# Ví dụ policies
def prefer_local_for_qg(context: dict) -> Optional[str]:
    """Ưu tiên HF local cho QG (giảm cost)"""
    if context.get("task") == "question_generation" and context.get("prefer_local"):
        return "hf_question_generator_service"
    return None


def prefer_gemini_for_chat(context: dict) -> Optional[str]:
    """Gemini cho chat (latency thấp, quality cao)"""
    if context.get("task") == "chat":
        return "gemini_service"
    return None