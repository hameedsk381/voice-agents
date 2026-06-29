"""
LLM selection for high-stakes reasoning tasks.

`get_reasoning_llm()` returns the strongest configured provider for compliance
auditing and outcome classification. Selection (settings.REASONING_LLM_PROVIDER):

- "auto"  : Claude when ANTHROPIC_API_KEY is set, otherwise Groq llama-3.3-70b.
- "anthropic" / "openai" / "groq" : forced provider.

Optionally override the model with settings.REASONING_LLM_MODEL.
"""

from loguru import logger

from app.core.config import settings
from .base import LLMProvider

_DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "groq": "llama-3.3-70b-versatile",
}


def _resolve_provider() -> str:
    provider = (settings.REASONING_LLM_PROVIDER or "auto").lower()
    if provider != "auto":
        return provider
    # Auto: prefer Claude when available, else fall back to the reliably-configured Groq.
    if settings.ANTHROPIC_API_KEY:
        return "anthropic"
    return "groq"


def get_reasoning_llm() -> LLMProvider:
    provider = _resolve_provider()
    model = settings.REASONING_LLM_MODEL or _DEFAULT_MODELS.get(provider)

    if provider == "anthropic":
        from .anthropic_provider import AnthropicLLM
        return AnthropicLLM(model=model, temperature=0.2)
    if provider == "openai":
        from .openai_provider import OpenAILLM
        return OpenAILLM(model=model, temperature=0.2)
    if provider == "groq":
        from .groq_provider import GroqLLM
        return GroqLLM(model=model, temperature=0.2)

    logger.warning(f"Unknown REASONING_LLM_PROVIDER '{provider}', defaulting to Groq 70B.")
    from .groq_provider import GroqLLM
    return GroqLLM(model=_DEFAULT_MODELS["groq"], temperature=0.2)
