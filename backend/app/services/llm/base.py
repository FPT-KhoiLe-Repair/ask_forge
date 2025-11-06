# backend/app/services/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any


class LLMProvider(ABC):
    """Base interface cho tất cả LLM providers"""

    @abstractmethod
    async def generate(
            self,
            prompt: str,
            **kwargs
    ) -> str:
        """Generate text (non-streaming)"""
        pass

    @abstractmethod
    async def generate_stream(
            self,
            prompt: str,
            **kwargs
    ) -> AsyncIterator[str]:
        """Generate text (streaming)"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier"""
        pass

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """Có hỗ trợ streaming không"""
        pass