"""
Knowledge Base management endpoints.
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.api.v1.deps import get_db
from app.api.v1.auth import get_current_user
from app.services.rag import RAGService
from app.schemas.kb import (
    KBDocumentUploadResponse,
    KBDocumentListResponse,
    KBDocumentResponse,
    KBSearchRequest,
    KBSearchResponse,
    KBSearchResult
)
from app.models.user import User, UserRole
from app.core.exceptions import UnauthorizedError, BadRequestError

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin or IT staff"""
    if current_user.role not in [UserRole.ADMIN, UserRole.IT_STAFF]:
        raise UnauthorizedError(
            message="Admin or IT staff access required",
            error_code="INSUFFICIENT_PERMISSIONS"
        )
    return current_user


@router.post(
    "/upload",
    response_model=KBDocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to knowledge base"
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (txt, md, pdf, docx)"),
    title: str = Form(None, description="Document title (optional)"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document to the knowledge base.

    Requires admin or IT staff role.

    - **file**: Document file (supported: txt, md, pdf, docx)
    - **title**: Optional document title (defaults to filename)

    The document will be chunked and stored in ChromaDB for RAG.
    """
    # Validate file type
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    supported_types = ['txt', 'md', 'pdf', 'docx']

    if file_ext not in supported_types:
        raise BadRequestError(
            message=f"Unsupported file type. Supported: {', '.join(supported_types)}",
            error_code="UNSUPPORTED_FILE_TYPE"
        )

    # Read file content
    content = await file.read()

    # For now, only handle text files
    # TODO: Add PDF and DOCX parsing
    if file_ext not in ['txt', 'md']:
        raise BadRequestError(
            message="PDF and DOCX parsing not implemented yet. Please use TXT or MD files.",
            error_code="FILE_TYPE_NOT_IMPLEMENTED"
        )

    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        raise BadRequestError(
            message="Failed to decode file. Please ensure it's UTF-8 encoded.",
            error_code="DECODE_ERROR"
        )

    # Upload to RAG service
    rag_service = RAGService(db)
    kb_doc = await rag_service.upload_document(
        file_name=file.filename,
        file_content=text_content,
        file_type=file_ext,
        title=title,
        user=current_user
    )

    return KBDocumentUploadResponse.model_validate(kb_doc)


@router.get(
    "/documents",
    response_model=KBDocumentListResponse,
    summary="List knowledge base documents"
)
async def list_documents(
    limit: int = Query(50, ge=1, le=100, description="Number of documents"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all knowledge base documents.

    Requires admin or IT staff role.
    """
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
            file_size=doc.file_size,
            chunk_count=doc.chunk_count,
            is_active=doc.is_active,
            created_at=doc.created_at,
            uploader_id=doc.uploaded_by
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
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific document.

    Requires admin or IT staff role.
    """
    rag_service = RAGService(db)
    doc = await rag_service.get_document(doc_id)

    return KBDocumentResponse(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        chunk_count=doc.chunk_count,
        is_active=doc.is_active,
        created_at=doc.created_at,
        uploader_id=doc.uploaded_by
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
