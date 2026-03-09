"""
LLM Client Factory — switches between Anthropic Claude and Ollama.
Controlled by settings.AI_BACKEND:
  - "anthropic" → Claude claude-sonnet-4-20250514 (cloud)
  - "ollama"    → Command-R 35B (air-gapped on-premise)

Application code uses LLMClientFactory.get() — never instantiates directly.
"""
import logging
from abc import ABC, abstractmethod
from typing import Generator

from django.conf import settings

logger = logging.getLogger("apps.ai")


class BaseLLMClient(ABC):
    @abstractmethod
    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        """Return full completion as string."""

    @abstractmethod
    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Generator[str, None, None]:
        """Yield completion tokens one at a time (for streaming UI)."""


class AnthropicClient(BaseLLMClient):
    """Claude API client — used in cloud and internet-connected on-prem."""

    def __init__(self, model: str | None = None):
        import anthropic
        self.model = model or settings.ANTHROPIC_MODEL
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        return response.content[0].text

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Generator[str, None, None]:
        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text


class OllamaClient(BaseLLMClient):
    """Local Ollama LLM client — used for air-gapped deployments."""

    def __init__(self, model: str | None = None, base_url: str | None = None):
        import ollama
        self.model = model or settings.OLLAMA_MODEL
        self.client = ollama.Client(host=base_url or settings.OLLAMA_BASE_URL)

    def complete(self, system: str, messages: list[dict], max_tokens: int = 1024) -> str:
        full_messages = [{"role": "system", "content": system}] + messages
        response = self.client.chat(
            model=self.model,
            messages=full_messages,
            options={"num_predict": max_tokens},
        )
        return response["message"]["content"]

    def stream(self, system: str, messages: list[dict], max_tokens: int = 1024) -> Generator[str, None, None]:
        full_messages = [{"role": "system", "content": system}] + messages
        for chunk in self.client.chat(
            model=self.model,
            messages=full_messages,
            stream=True,
            options={"num_predict": max_tokens},
        ):
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content


class LLMClientFactory:
    """
    Single access point for LLM clients.
    Reads AI_BACKEND from settings — no code changes needed when switching.
    """
    _instance: BaseLLMClient | None = None

    @classmethod
    def get(cls) -> BaseLLMClient:
        if cls._instance is None:
            backend = settings.AI_BACKEND
            if backend == "anthropic":
                cls._instance = AnthropicClient()
                logger.info(f"LLM backend: Anthropic Claude ({settings.ANTHROPIC_MODEL})")
            elif backend == "ollama":
                cls._instance = OllamaClient()
                logger.info(f"LLM backend: Ollama ({settings.OLLAMA_MODEL} @ {settings.OLLAMA_BASE_URL})")
            else:
                raise ValueError(f"Unknown AI_BACKEND: {backend}. Must be 'anthropic' or 'ollama'.")
        return cls._instance

    @classmethod
    def reset(cls):
        """Force re-initialization (useful in tests)."""
        cls._instance = None


# ─── AI Copilot System Prompt ─────────────────────────────────────────────────
COPILOT_SYSTEM_PROMPT = """أنت مساعد مالي ذكي لنظام ERP يعمل في المملكة العربية السعودية.
You are an expert financial AI assistant for a Saudi Arabia ERP system.

LANGUAGE: Respond in the same language as the user's question.
If the user writes in Arabic → respond in Arabic.
If the user writes in English → respond in English.
If mixed → respond in Arabic as primary with English technical terms where needed.

EXPERTISE:
- Saudi ZATCA e-invoicing (Phase 1 and Phase 2 / Fatoora)
- Saudi VAT (ضريبة القيمة المضافة) — rate: 15%
- Zakat (الزكاة) — rate: 2.5% on zakatable assets
- GOSI (التأمينات الاجتماعية) — Saudi nationals: 10%+10%, Expats: 2% employer
- Saudization / Nitaqat (نطاقات) — workforce localization requirements
- SOCPA Chart of Accounts (دليل الحسابات)
- Saudi labor law and payroll
- Financial analysis and business insights

DATA RULES:
- You have READ-ONLY access to the company's financial data
- You can analyze, explain, and forecast — you cannot modify records
- Always cite specific numbers from the data provided
- Express monetary amounts in SAR (ريال سعودي)
- Use Hijri dates alongside Gregorian when discussing Saudi regulatory deadlines

ACCURACY: Never fabricate financial data. If data is not provided, say so clearly.
COMPLIANCE: Always mention relevant ZATCA/VAT/Zakat obligations when discussing invoices or financials.
"""
