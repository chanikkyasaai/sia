# app/core/config.py
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ValidationError

from dotenv import load_dotenv
load_dotenv()

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "SIA Backend"
    ENV: str = "local"

    # Database
    DATABASE_URL: Optional[str] = None  # Make optional with default None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = None  # model deployment name
    
    AZURE_OPENAI_ENDPOINT_mini: Optional[str] = None
    AZURE_OPENAI_API_KEY_mini: Optional[str] = None
    AZURE_OPENAI_DEPLOYMENT_mini: Optional[str] = None

    # Azure Speech (optional fallback STT/TTS)
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: Optional[str] = None

    # Soniox (primary STT, if you use it)
    SONIOX_API_KEY: Optional[str] = None

    # Murf (TTS for fancy voice)
    MURF_API_KEY: Optional[str] = None
    
    # Twilio (For SMS)
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError("Configuration validation error: Check your .env file.") from e
