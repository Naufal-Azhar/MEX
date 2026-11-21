"""Provider-agnostic LLM interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import Settings, load_settings


class LLMError(RuntimeError):
    pass


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMProvider(ABC):
    name: str = "base"
    model: str = ""

    @abstractmethod
    def is_configured(self) -> bool:
        ...

    @abstractmethod
    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 800,
    ) -> str:
        ...


def get_provider(settings: Settings | None = None) -> LLMProvider | None:
    """Return the configured provider, or None when LLM use is disabled."""
    settings = settings or load_settings()
    if not settings.provider_enabled:
        return None
    if settings.llm_provider == "api":
        from app.llm.api_provider import OpenAICompatibleProvider

        return OpenAICompatibleProvider(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key,
            model=settings.llm_api_model,
        )
    if settings.llm_provider == "ollama":
        from app.llm.local_provider import OllamaProvider

        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)
    raise LLMError(f"Unknown LLM provider: {settings.llm_provider}")
