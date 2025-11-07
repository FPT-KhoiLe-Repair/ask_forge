# backend/app/services/llm/router.py
from typing import Optional, Callable
import logging

from ask_forge.backend.app.services.llm.base import LLMProvider
from ask_forge.backend.app.services.llm.registry import get_registry

logger = logging.getLogger(__name__)


class LLMRouter:
    """Route requests to appropriate LLM provider"""

    def __init__(self):
        self.registry = get_registry()
        self._default_provider = "gemini_service"  # Fallback
        self._routing_policies: list[Callable] = []

    def add_policy(self, policy: Callable[[dict], Optional[str]]):
        """Add routing policy (e.g., route by lang, task type)"""
        self._routing_policies.append(policy)

    async def route(self, context: dict) -> LLMProvider:
        """
        Select provider based on context.

        context = {
            "task": "chat" | "question_generation" | "summary",
            "lang": "vi" | "en",
            "latency_requirement": "low" | "high",
            "prefer_local": bool
        }
        """
        # Run policies in order
        for policy in self._routing_policies:
            provider_name = policy(context)
            if provider_name:
                provider = self.registry.get(provider_name)
                if provider:
                    logger.info(f"🎯 Routed to: {provider_name}")
                    return provider
                else:
                    logger.warning(f"⚠️ Provider '{provider_name}' not found in registry")

        # Fallback
        logger.warning(f"⚠️ No policy matched, using default: {self._default_provider}")
        return self.registry.get(self._default_provider)


# ===== Routing Policies =====

def prefer_local_for_qg(context: dict) -> Optional[str]:
    """
    ✅ Prefer HF local model for Question Generation (reduce API costs)

    Matches task name from worker.py
    """
    if context.get("task") == "question_generation":
        # ✅ Use correct registry name
        return "question_generator_service"
    return None


def prefer_gemini_for_chat(context: dict) -> Optional[str]:
    """Gemini for chat (low latency, high quality)"""
    if context.get("task") == "chat":
        return "gemini_service"
    return None