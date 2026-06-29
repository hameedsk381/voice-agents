"""
Production preflight checks.

Run at startup. In ENVIRONMENT=prod, hard errors abort boot so a
misconfigured container fails fast and loud instead of silently serving
broken behaviour (placeholder API keys, default secrets, localhost
webhook hosts that telephony callbacks can never reach, etc.).

Outside prod the same checks run but only log warnings.
"""

from typing import List, Tuple

from app.core.config import settings

# Substrings that mark a value as an unfilled placeholder rather than a real secret.
_PLACEHOLDER_MARKERS = (
    "your-",
    "placeholder",
    "change-in-production",
    "changeme",
    "xxxxx",
    "rzp_test_xxxx",
)


def _is_placeholder(value: str | None) -> bool:
    if not value:
        return True
    low = value.strip().lower()
    return any(marker in low for marker in _PLACEHOLDER_MARKERS)


def collect_issues() -> Tuple[List[str], List[str]]:
    """Return (errors, warnings) for the current settings.

    Errors abort boot in prod; warnings are always advisory.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # ── Secrets that must never run with a default/placeholder value ──
    if _is_placeholder(settings.SECRET_KEY) or settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        errors.append("SECRET_KEY is unset or a placeholder - set a strong random value.")

    # ── Voice runtime (Ultravox is the sole production runtime) ──
    if settings.VOICE_RUNTIME == "ultravox" and _is_placeholder(settings.ULTRAVOX_API_KEY):
        errors.append("ULTRAVOX_API_KEY is missing/placeholder but VOICE_RUNTIME=ultravox.")
    if settings.ULTRAVOX_CALLBACKS_ENABLED and _is_placeholder(settings.ULTRAVOX_CALLBACK_SECRET):
        warnings.append("ULTRAVOX_CALLBACK_SECRET unset - call.ended webhooks cannot be signature-verified.")

    # ── Reasoning LLM (compliance audit / outcome classification) ──
    provider = settings.REASONING_LLM_PROVIDER
    has_anthropic = not _is_placeholder(settings.ANTHROPIC_API_KEY)
    has_groq = not _is_placeholder(settings.GROQ_API_KEY)
    has_openai = not _is_placeholder(settings.OPENAI_API_KEY)
    if provider == "anthropic" and not has_anthropic:
        errors.append("REASONING_LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is unset.")
    elif provider == "openai" and not has_openai:
        errors.append("REASONING_LLM_PROVIDER=openai but OPENAI_API_KEY is unset.")
    elif provider == "groq" and not has_groq:
        errors.append("REASONING_LLM_PROVIDER=groq but GROQ_API_KEY is unset.")
    elif provider == "auto" and not (has_anthropic or has_groq or has_openai):
        errors.append("REASONING_LLM_PROVIDER=auto but no Anthropic/Groq/OpenAI key is set.")

    # ── Public host: telephony + payment webhooks must be reachable ──
    host = (settings.SERVER_HOST or "").lower()
    if "localhost" in host or host.startswith("127.0.0.1") or not host:
        errors.append("SERVER_HOST is localhost/empty - Twilio, Ultravox and Razorpay webhooks cannot reach it.")

    # ── Cookies must be Secure over HTTPS in prod ──
    if not settings.COOKIE_SECURE:
        warnings.append("COOKIE_SECURE is False - set True so auth cookies are HTTPS-only in production.")

    # ── Telephony: partial Twilio config is a silent outbound failure ──
    twilio_fields = [settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_PHONE_NUMBER]
    twilio_set = [bool(f) and not _is_placeholder(f) for f in twilio_fields]
    if any(twilio_set) and not all(twilio_set):
        errors.append("Twilio is partially configured - set ACCOUNT_SID, AUTH_TOKEN and PHONE_NUMBER together (or none).")

    # ── India compliance posture ──
    if not settings.DLT_ENFORCEMENT:
        warnings.append("DLT_ENFORCEMENT is False - outbound from non-DLT-registered numbers is allowed (illegal for live Indian commercial calls).")
    if not settings.AI_DISCLOSURE_REQUIRED:
        warnings.append("AI_DISCLOSURE_REQUIRED is False - calls will not announce the AI disclosure (TCCCPR risk).")

    # ── Simulated tools must stay off in prod ──
    if settings.ALLOW_SIMULATED_TOOLS:
        warnings.append("ALLOW_SIMULATED_TOOLS is True - fake KYC/translation tools are live; disable outside demos.")

    return errors, warnings


def run_preflight() -> None:
    """Log warnings; in prod, raise on any hard error so boot aborts."""
    from loguru import logger

    errors, warnings = collect_issues()
    is_prod = settings.ENVIRONMENT == "prod"

    for w in warnings:
        logger.warning(f"[preflight] {w}")

    if errors:
        for e in errors:
            (logger.critical if is_prod else logger.warning)(f"[preflight] {e}")
        if is_prod:
            raise RuntimeError(
                "Production preflight failed:\n  - " + "\n  - ".join(errors)
            )
