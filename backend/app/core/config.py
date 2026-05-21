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
    
    # Simple defaults for dev
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5435  # Match docker-compose
    POSTGRES_DB: str = "voise"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    MIN_PASSWORD_LENGTH: int = 8
    
    TEMPORAL_HOST: str = "localhost:7233"
    
    # API Keys (optional)
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    STT_PROVIDER: Literal["mock", "deepgram"] = "mock"
    DEFAULT_STT_CONFIDENCE: float = 0.85
    DEFAULT_STT_CONFIDENCE_FLOOR: float = 0.5
    ULTRAVOX_API_KEY: Optional[str] = None
    ULTRAVOX_BASE_URL: str = "https://api.ultravox.ai/api"
    ULTRAVOX_MODEL: str = "fixie-ai/ultravox-70B"
    ULTRAVOX_VOICE: str = "Mark"
    # Voice runtime: ultravox (recommended) uses Ultravox for STT/LLM/TTS via client SDK or proxy.
    VOICE_RUNTIME: Literal["ultravox", "custom"] = "ultravox"
    USE_ULTRAVOX_RUNTIME: bool = True
    # Browser apps should use ultravox-client (WebRTC). Server WebSocket proxy is for custom integrations only.
    USE_ULTRAVOX_WEBSOCKET_PROXY: bool = False
    ULTRAVOX_INPUT_SAMPLE_RATE: int = 48000
    ULTRAVOX_OUTPUT_SAMPLE_RATE: int = 48000
    ULTRAVOX_CLIENT_BUFFER_MS: int = 60
    ULTRAVOX_CALLBACKS_ENABLED: bool = True
    ULTRAVOX_CALLBACK_SECRET: Optional[str] = None
    # Override full URL; default derived from SERVER_HOST at runtime
    ULTRAVOX_CALL_ENDED_WEBHOOK_URL: Optional[str] = None

    # Telephony
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SERVER_HOST: str = "localhost:8001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()


def public_api_base() -> str:
    host = (settings.SERVER_HOST or "localhost:8001").strip()
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    if "localhost" in host or host.startswith("127.0.0.1"):
        return f"http://{host.rstrip('/')}"
    return f"https://{host.rstrip('/')}"


def ultravox_call_ended_webhook_url() -> Optional[str]:
    if settings.ULTRAVOX_CALL_ENDED_WEBHOOK_URL:
        return settings.ULTRAVOX_CALL_ENDED_WEBHOOK_URL
    if not settings.ULTRAVOX_CALLBACKS_ENABLED:
        return None
    return f"{public_api_base()}{settings.API_V1_STR}/ultravox/webhooks/call-ended"
