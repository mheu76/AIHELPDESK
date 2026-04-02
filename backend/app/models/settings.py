"""
System settings model for persistent configuration
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped

from app.db.base import Base


class SystemSettings(Base):
    """
    System-wide settings stored in database.

    This table should only have one row (singleton pattern).
    Settings are cached in-memory and reloaded on updates.
    """

    __tablename__ = "system_settings"

    # Use a fixed ID to enforce singleton
    id: Mapped[int] = Column(Integer, primary_key=True, default=1)

    # LLM Configuration
    llm_provider: Mapped[str] = Column(String(50), nullable=False, default="claude")
    llm_model: Mapped[str] = Column(String(100), nullable=False, default="claude-sonnet-4-20250514")
    llm_temperature: Mapped[float] = Column(Float, nullable=False, default=0.7)
    max_tokens: Mapped[int] = Column(Integer, nullable=False, default=1024)

    # RAG Configuration
    rag_enabled: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    rag_top_k: Mapped[int] = Column(Integer, nullable=False, default=3)

    # Metadata
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<SystemSettings("
            f"llm_provider='{self.llm_provider}', "
            f"llm_model='{self.llm_model}', "
            f"temperature={self.llm_temperature})>"
        )
