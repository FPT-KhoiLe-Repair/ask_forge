# backend/app/services/llm/registry.py
from typing import Dict, Optional
import logging

from ask_forge.backend.app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class LLMRegistry:
    """Registry quản lý các LLM providers (singleton)"""

    _instance: Optional["LLMRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers: Dict[str, LLMProvider] = {}
        return cls._instance

    def register(self, name: str, provider: LLMProvider):
        """Đăng ký provider mới"""
        self._providers[name] = provider
        logger.info(f"✅ Registered LLM provider: {name} → {provider.model_name}")

    def get(self, name: str) -> Optional[LLMProvider]:
        """Lấy provider theo tên"""
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        """Danh sách providers khả dụng"""
        return list(self._providers.keys())


def get_registry() -> LLMRegistry:
    """Factory function"""
    return LLMRegistry()