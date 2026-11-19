
"""
Configuration management using Pydantic Settings.
Reads from .env file and environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


print("[DEBUG] Initializing application configuration...")


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

    print("\n[DEBUG] get_settings() called")
    print("[DEBUG] Checking cached application settings...")

    cache_info = get_settings.cache_info()

    print(f"[DEBUG] Cache hits: {cache_info.hits}")
    print(f"[DEBUG] Cache misses: {cache_info.misses}")
    print(f"[DEBUG] Cache size: {cache_info.currsize}")

    print("[DEBUG] Loading settings from environment and .env file...")

    settings = Settings()

    print("[SUCCESS] Application settings loaded successfully.")

    # Database configuration
    print("\n[DEBUG] Database Configuration:")
    print(f"[DEBUG] DATABASE_URL: {settings.DATABASE_URL}")

    # Security configuration
    print("\n[DEBUG] Security Configuration:")
    print(f"[DEBUG] JWT Algorithm: {settings.ALGORITHM}")
    print(
        f"[DEBUG] Access Token Expiry: "
        f"{settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
    )
    print("[DEBUG] SECRET_KEY: Hidden for security.")

    # CORS configuration
    print("\n[DEBUG] CORS Configuration:")
    print(f"[DEBUG] FRONTEND_ORIGIN: {settings.FRONTEND_ORIGIN}")

    # Storage configuration
    print("\n[DEBUG] Storage Configuration:")
    print(f"[DEBUG] STORAGE_ROOT: {settings.STORAGE_ROOT}")
    print(f"[DEBUG] MAX_UPLOAD_MB: {settings.MAX_UPLOAD_MB}")
    print(
        f"[DEBUG] ALLOWED_AUDIO_EXTENSIONS: "
        f"{settings.ALLOWED_AUDIO_EXTENSIONS}"
    )

    # Application configuration
    print("\n[DEBUG] Application Configuration:")
    print(f"[DEBUG] DEBUG: {settings.DEBUG}")
    print(
        f"[DEBUG] INFERENCE_TIMEOUT_SEC: "
        f"{settings.INFERENCE_TIMEOUT_SEC}"
    )

    print("\n[SUCCESS] Configuration initialization completed.")

    return settings


print("[SUCCESS] Configuration module loaded.")
