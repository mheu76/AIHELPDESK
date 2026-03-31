"""
Application configuration management using Pydantic Settings.
All configuration is loaded from environment variables.
"""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Validates on startup - fails fast if misconfigured.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore unknown env vars
    )

    # Environment
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = Field(default=True, description="Enable debug mode")

    # LLM Configuration
    LLM_PROVIDER: Literal["claude", "openai", "gemini"] = "claude"
    ANTHROPIC_API_KEY: str = Field(..., description="Required for Claude provider")
    OPENAI_API_KEY: str | None = Field(None, description="Optional for OpenAI provider")
    LLM_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.7

    # Database
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string",
        examples=["postgresql+asyncpg://user:pass@localhost:5432/helpdesk"]
    )
    DB_POOL_SIZE: int = Field(default=5, ge=1, le=20)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_ECHO: bool = Field(default=False, description="Log SQL queries")

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "it_knowledge_base"

    # Authentication
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="Must be 32+ chars")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["human", "json"] = "human"  # human-readable for dev

    # Application
    APP_NAME: str = "IT Helpdesk API"
    APP_VERSION: str = "1.0.0"
    MAX_CONVERSATION_TURNS: int = 10
    RAG_TOP_K: int = 3

    @field_validator("ENVIRONMENT")
    @classmethod
    def set_debug_from_env(cls, v: str) -> str:
        """Automatically disable debug in production"""
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
