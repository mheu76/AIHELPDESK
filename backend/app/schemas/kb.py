"""
Pydantic schemas for knowledge base endpoints.
"""
from pydantic import BaseModel, Field
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

    model_config = {
        "from_attributes": True
    }


class KBDocumentResponse(BaseModel):
    """KB document response"""
    id: uuid.UUID
    title: str
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    chunk_count: int
    is_active: bool
    created_at: datetime
    uploader_id: Optional[uuid.UUID] = None

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


class KBSearchResponse(BaseModel):
    """KB search response"""
    query: str
    results: List[KBSearchResult]
    count: int
