"""
Configuration management using Pydantic Settings.
Reads from .env file and environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = "sqlite:///./birdclef.db"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    
    # Storage
    STORAGE_ROOT: str = "storage"
    MAX_UPLOAD_MB: int = 100
    ALLOWED_AUDIO_EXTENSIONS: list = ["wav", "ogg", "mp3", "flac"]
    
    # App
    DEBUG: bool = True
    INFERENCE_TIMEOUT_SEC: int = 900  # 15 minutes max for inference
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get settings singleton."""
    return Settings()
