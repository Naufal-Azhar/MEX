"""OpenAI-compatible chat completion provider (works with most hosted APIs)."""

from __future__ import annotations

import time

import httpx

from app.llm.base import ChatMessage, LLMError, LLMProvider

RETRY_STATUS = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3


class OpenAICompatibleProvider(LLMProvider):
    name = "api"

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 90.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def complete(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 800,
    ) -> str:
        if not self.is_configured():
            raise LLMError("LLM_API_KEY is not set.")
        payload = {
            "model": self.model,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = httpx.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=self.timeout,
                )
                if response.status_code in RETRY_STATUS and attempt < MAX_ATTEMPTS - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                response.raise_for_status()
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise LLMError("Unexpected LLM response shape.") from exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code in RETRY_STATUS and attempt < MAX_ATTEMPTS - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise LLMError(f"LLM request failed: {exc}") from exc
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                if attempt < MAX_ATTEMPTS - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise LLMError(f"LLM request failed: {exc}") from exc
        raise LLMError(f"LLM request failed after retries: {last_error}")
