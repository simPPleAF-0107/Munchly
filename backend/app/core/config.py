from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Munchly"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://munchly:munchly_dev@localhost:5432/munchly"
    JWT_SECRET: str = "supersecretkey_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str | None = None
    GOOGLE_CLIENT_ID: str | None = None
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    AI_PROVIDER: str = "gemini"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
