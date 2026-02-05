from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "OpenVoice Orchestrator"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    
    # Simple defaults for dev
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5435  # Match docker-compose
    POSTGRES_DB: str = "openvoice"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    TEMPORAL_HOST: str = "localhost:7233"
    
    # API Keys (optional)
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEEPGRAM_API_KEY: Optional[str] = None
    
    # Telephony
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    SERVER_HOST: str = "localhost:8001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
