from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "Voise AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    COOKIE_SECURE: bool = False
    ENVIRONMENT: str = "dev"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if value is None:
            return value
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                return json.loads(raw)
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return value

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5435
    POSTGRES_DB: str = "voise"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    MIN_PASSWORD_LENGTH: int = 8

    TEMPORAL_HOST: str = "localhost:7233"

    # API Keys (optional — used by custom runtime)
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    STT_PROVIDER: Literal["mock", "deepgram", "sarvam", "google", "groq"] = "mock"
    DEFAULT_STT_CONFIDENCE: float = 0.85
    DEFAULT_STT_CONFIDENCE_FLOOR: float = 0.5

    # Voice runtime — "custom" uses the turn processor (Groq + pluggable STT/TTS).
    VOICE_RUNTIME: Literal["custom", "livekit"] = "custom"

    # TTS provider: qwen, deepgram, sarvam
    TTS_PROVIDER: Literal["qwen", "deepgram", "sarvam", "google", "groq"] = "sarvam"

    # --- Sarvam AI API (STT / TTS) ---
    SARVAM_API_KEY: Optional[str] = None

    # --- LiveKit voice runtime (Google full pipeline) ---
    LIVEKIT_URL: Optional[str] = None
    LIVEKIT_API_KEY: Optional[str] = None
    LIVEKIT_API_SECRET: Optional[str] = None
    LIVEKIT_AGENT_NAME: str = "voise-livekit-agent"
    LIVEKIT_STT_MODEL: str = "latest_long"
    LIVEKIT_STT_LANGUAGE: str = "hi-IN"
    LIVEKIT_LLM_MODEL: str = "gemini-2.5-flash"
    LIVEKIT_TTS_VOICE: str = "hi-IN-Wavenet-A"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Telephony — multi-provider
    TELEPHONY_PROVIDER: str = "twilio"  # twilio | vonage | plivo | telnyx
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    VONAGE_API_KEY: Optional[str] = None
    VONAGE_API_SECRET: Optional[str] = None
    VONAGE_APPLICATION_ID: Optional[str] = None
    VONAGE_PRIVATE_KEY: Optional[str] = None
    PLIVO_AUTH_ID: Optional[str] = None
    PLIVO_AUTH_TOKEN: Optional[str] = None
    TELNYX_API_KEY: Optional[str] = None
    SERVER_HOST: str = "localhost:8001"

    # WhatsApp
    TWILIO_WHATSAPP_SENDER: str = "whatsapp:+919999999999"
    TWILIO_STATUS_CALLBACK_URL: Optional[str] = None
    WHATSAPP_RATE_LIMIT_PER_HOUR: int = 0
    WHATSAPP_OPTIN_REQUIRED: bool = True
    WHATSAPP_TEMPLATE_NAMESPACE: Optional[str] = None

    # Email (workflow automation)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # Observability
    LOG_FORMAT: str = "text"
    METRICS_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()


def public_api_base() -> str:
    host = (settings.SERVER_HOST or "localhost:8001").strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    if "localhost" in host or host.startswith("127.0.0.1"):
        return f"http://{host.rstrip('/')}"
    return f"https://{host.rstrip('/')}"
