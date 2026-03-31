"""
Knowledge Base document model.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class KBDocument(Base):
    """
    Knowledge Base document model for storing uploaded documents metadata.
    Actual document content is stored in ChromaDB as vector embeddings.
    """
    __tablename__ = "kb_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, md
    file_size = Column(Integer, nullable=True)  # bytes
    chunk_count = Column(Integer, default=0, nullable=False)  # Number of chunks in ChromaDB
    chroma_ids = Column(ARRAY(Text), nullable=True)  # ChromaDB document IDs
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self) -> str:
        return f"<KBDocument(id={self.id}, title={self.title}, chunks={self.chunk_count})>"
