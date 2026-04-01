"""
Pydantic schemas for knowledge base endpoints.
"""
from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime
import uuid


class KBDocumentUploadResponse(BaseModel):
    """KB document upload response"""
    id: uuid.UUID
    title: str
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    chunk_count: int
    created_at: datetime
    created_by_id: Optional[uuid.UUID] = None
    is_deleted: bool = False

    model_config = {
        "from_attributes": True
    }


class KBDocumentUploadRequest(BaseModel):
    """JSON upload payload used by tests and non-browser clients."""
    content: str = Field(..., min_length=1, description="Document content")
    file_name: str = Field(..., min_length=1, description="Original file name")
    title: Optional[str] = Field(None, description="Document title")


class KBDocumentResponse(BaseModel):
    """KB document response"""
    id: uuid.UUID
    title: str
    file_name: str
    file_type: str
    content: Optional[str] = None
    file_size: Optional[int] = None
    chunk_count: int
    is_active: bool
    created_at: datetime
    uploader_id: Optional[uuid.UUID] = None
    created_by_id: Optional[uuid.UUID] = None

    @computed_field
    @property
    def is_deleted(self) -> bool:
        return not self.is_active

    model_config = {
        "from_attributes": True
    }


class KBDocumentListResponse(BaseModel):
    """List of KB documents"""
    documents: List[KBDocumentResponse]
    total: int


class KBSearchRequest(BaseModel):
    """KB search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    top_k: Optional[int] = Field(None, ge=1, le=10, description="Number of results")


class KBSearchResult(BaseModel):
    """Individual search result"""
    content: str
    metadata: dict
    relevance_score: Optional[float] = None

    @computed_field
    @property
    def score(self) -> Optional[float]:
        return self.relevance_score


class KBSearchResponse(BaseModel):
    """KB search response"""
    query: str
    results: List[KBSearchResult]
    count: int
