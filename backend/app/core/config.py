from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    CYRUS_ENV: str = "local"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    CYRUS_COLLECTION: str = "cyrus_messages"

    # Provider selection: openai | grok | deepseek
    CYRUS_PROVIDER: str = "openai"

    # API keys for supported providers
    OPENAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None

    # Model logical names (provider resolves to actual names)
    CYRUS_CHAT_MODEL: str = "gpt-4o-mini"
    CYRUS_EMBED_MODEL: str = "text-embedding-3-small"

    # Vector dimension for the embed model (text-embedding-3-small = 1536)
    CYRUS_EMBED_DIM: int = 1536

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
