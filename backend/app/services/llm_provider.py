import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 60


class LLMProviderError(Exception):
    """Raised when an LLM provider call fails."""


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, Any]


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Return a single completion response."""

    @abstractmethod
    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        """Yield completion text chunks via streaming."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def default_model(self) -> str: ...


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return "gemma3:4b"

    def complete(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        resolved_model = model or self.default_model
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
            message = data.get("message", {})
            return LLMResponse(
                content=message.get("content", ""),
                model=resolved_model,
                provider="ollama",
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                },
            )
        except httpx.HTTPError as error:
            raise LLMProviderError(f"Ollama request failed: {error}") from error

    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        resolved_model = model or self.default_model
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as error:
            raise LLMProviderError(f"Ollama stream failed: {error}") from error


class GroqProvider(LLMProvider):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return "llama-3.3-70b-versatile"

    def complete(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        resolved_model = model or self.default_model
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})
            return LLMResponse(
                content=message.get("content", ""),
                model=resolved_model,
                provider="groq",
                usage={
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                },
            )
        except httpx.HTTPError as error:
            raise LLMProviderError(f"Groq request failed: {error}") from error

    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        resolved_model = model or self.default_model
        payload = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            with httpx.Client(timeout=LLM_TIMEOUT_SECONDS) as client:
                with client.stream(
                    "POST",
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.HTTPError as error:
            raise LLMProviderError(f"Groq stream failed: {error}") from error


class NoOpLLMProvider(LLMProvider):
    """Fallback when no LLM provider is configured."""

    @property
    def provider_name(self) -> str:
        return "none"

    @property
    def default_model(self) -> str:
        return "none"

    def complete(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        return LLMResponse(
            content="",
            model="none",
            provider="none",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> Iterator[str]:
        return iter(())


def create_llm_provider(
    provider_type: str = "ollama",
    ollama_base_url: str = "http://localhost:11434",
    groq_api_key: str | None = None,
) -> LLMProvider:
    if provider_type == "groq" and groq_api_key:
        return GroqProvider(api_key=groq_api_key)
    if provider_type == "ollama":
        return OllamaProvider(base_url=ollama_base_url)
    return NoOpLLMProvider()
