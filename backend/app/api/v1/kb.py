"""
Knowledge Base management endpoints.
"""
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
from pydantic import ValidationError

from app.api.v1.deps import get_db
from app.api.v1.auth import get_current_user
from app.services.rag import RAGService
from app.schemas.kb import (
    KBDocumentUploadRequest,
    KBDocumentUploadResponse,
    KBDocumentListResponse,
    KBDocumentResponse,
    KBSearchRequest,
    KBSearchResponse,
    KBSearchResult
)
from app.models.user import User, UserRole
from app.core.exceptions import ForbiddenError, BadRequestError

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin or IT staff"""
    if current_user.role not in [UserRole.ADMIN, UserRole.IT_STAFF]:
        raise ForbiddenError(
            message="Admin or IT staff access required",
        )
    return current_user


@router.post(
    "/upload",
    response_model=KBDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to knowledge base"
)
async def upload_document(
    http_request: Request,
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, TXT, MD)"),
    title: Optional[str] = Form(None, description="Document title"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to the knowledge base.

    Requires admin or IT staff role.

    Supports: PDF, DOCX, TXT, MD files
    - Maximum file size: 10MB
    - File will be parsed, chunked, and stored in ChromaDB for RAG

    Form data:
    - **file**: Document file to upload
    - **title**: Optional document title (defaults to filename)
    """
    rag_service = RAGService(db)
    if file is not None:
        # Validate file size (10MB limit)
        max_file_size = 10 * 1024 * 1024
        content = await file.read()

        if len(content) == 0:
            raise BadRequestError(
                message="File is empty",
                error_code="EMPTY_FILE"
            )

        if len(content) > max_file_size:
            raise BadRequestError(
                message=f"File size exceeds maximum limit of {max_file_size // (1024*1024)}MB",
                error_code="FILE_TOO_LARGE"
            )

        kb_doc = await rag_service.upload_document(
            file_name=file.filename,
            file_content=content,
            title=title,
            user=current_user
        )
    else:
        try:
            payload = await http_request.json()
        except Exception:
            payload = None

        try:
            upload_request = KBDocumentUploadRequest.model_validate(payload or {})
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc

        kb_doc = await rag_service.upload_document(
            file_name=upload_request.file_name,
            content=upload_request.content,
            title=upload_request.title,
            created_by_id=current_user.id
        )

    return KBDocumentUploadResponse.model_validate(kb_doc)


@router.get(
    "/documents",
    response_model=KBDocumentListResponse,
    summary="List knowledge base documents"
)
async def list_documents(
    limit: Optional[int] = Query(None, ge=1, le=100, description="Number of documents"),
    offset: Optional[int] = Query(None, ge=0, description="Pagination offset"),
    page: Optional[int] = Query(None, ge=1, description="1-based page number"),
    per_page: Optional[int] = Query(None, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all knowledge base documents.

    Available to all authenticated users.
    """
    if per_page is not None:
        limit = per_page
    if page is not None:
        effective_limit = limit or 50
        offset = (page - 1) * effective_limit
    limit = limit or 50
    offset = offset or 0

    rag_service = RAGService(db)
    documents = await rag_service.list_documents(limit=limit, offset=offset)

    # Get total count (simplified - in production, add proper count query)
    total = len(documents)

    doc_responses = [
        KBDocumentResponse(
            id=doc.id,
            title=doc.title,
            file_name=doc.file_name,
            file_type=doc.file_type,
            content=doc.content,
            file_size=doc.file_size,
            chunk_count=doc.chunk_count,
            is_active=doc.is_active,
            created_at=doc.created_at,
            uploader_id=doc.uploaded_by,
            created_by_id=doc.uploaded_by
        )
        for doc in documents
    ]

    return KBDocumentListResponse(documents=doc_responses, total=total)


@router.get(
    "/documents/{doc_id}",
    response_model=KBDocumentResponse,
    summary="Get document details"
)
async def get_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific document.

    Available to all authenticated users.
    """
    rag_service = RAGService(db)
    doc = await rag_service.get_document(doc_id)

    return KBDocumentResponse(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_type=doc.file_type,
        content=doc.content,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        is_active=doc.is_active,
        created_at=doc.created_at,
        uploader_id=doc.uploaded_by,
        created_by_id=doc.uploaded_by
    )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document"
)
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document from the knowledge base.

    Requires admin or IT staff role.

    This performs a soft delete - the document is marked as inactive.
    """
    rag_service = RAGService(db)
    await rag_service.delete_document(doc_id)
    return None


@router.post(
    "/search",
    response_model=KBSearchResponse,
    summary="Search knowledge base"
)
async def search_kb(
    request: KBSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search the knowledge base for relevant documents.

    Available to all authenticated users.

    - **query**: Search query
    - **top_k**: Number of results (default: 3)
    """
    rag_service = RAGService(db)
    results = await rag_service.search_knowledge_base(
        query=request.query,
        top_k=request.top_k
    )

    search_results = [
        KBSearchResult(
            content=r["content"],
            metadata=r["metadata"],
            relevance_score=r["relevance_score"]
        )
        for r in results
    ]

    return KBSearchResponse(
        query=request.query,
        results=search_results,
        count=len(search_results)
    )
