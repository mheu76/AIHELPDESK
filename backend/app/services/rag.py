"""
RAG (Retrieval-Augmented Generation) service for knowledge base management.
"""
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    chromadb = None
    Settings = None
import uuid
import re

from app.models.kb_document import KBDocument
from app.models.user import User
from app.core.config import settings
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.utils.document_parser import DocumentParser

logger = get_logger(__name__)


class RAGService:
    """Service for managing knowledge base documents and vector search"""

    def __init__(self, db: AsyncSession):
        self.db = db
        if chromadb:
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=Settings(anonymized_telemetry=False)
            )
        else:
            self.chroma_client = None
        self.collection_name = settings.CHROMA_COLLECTION

    def _get_collection(self):
        """Get or create ChromaDB collection"""
        try:
            collection = self.chroma_client.get_collection(name=self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "IT Knowledge Base documents"}
            )
            logger.info(f"Created ChromaDB collection: {self.collection_name}")
        return collection

    async def upload_document(
        self,
        file_name: str,
        file_content: Optional[Union[str, bytes]] = None,
        file_type: Optional[str] = None,
        title: Optional[str] = None,
        user: Optional[User] = None,
        *,
        content: Optional[str] = None,
        created_by_id: Optional[uuid.UUID] = None
    ) -> KBDocument:
        """
        Upload and process a document into the knowledge base.

        Args:
            file_name: Original file name
            file_content: File content as bytes or text
            file_type: File type (pdf, docx, txt, md)
            title: Optional document title (defaults to file_name)
            user: User uploading the document

        Returns:
            Created KBDocument

        Raises:
            BadRequestError: If file is empty or invalid
        """
        file_content = file_content if file_content is not None else content

        # Parse document content if bytes
        if isinstance(file_content, bytes):
            # Validate file format
            if not DocumentParser.is_supported(file_name):
                raise BadRequestError(
                    message=f"Unsupported file format. Supported: {', '.join(DocumentParser.SUPPORTED_FORMATS)}",
                    error_code="UNSUPPORTED_FILE_TYPE"
                )

            try:
                parsed_text = DocumentParser.parse(file_name, file_content)
            except ValueError as e:
                raise BadRequestError(
                    message=str(e),
                    error_code="UNSUPPORTED_FILE_TYPE"
                )
            except ImportError as e:
                raise BadRequestError(
                    message=f"Required library not installed: {str(e)}",
                    error_code="PARSER_LIBRARY_MISSING"
                )
            except Exception as e:
                raise BadRequestError(
                    message=f"Failed to parse document: {str(e)}",
                    error_code="PARSING_FAILED"
                )

            file_content = parsed_text

        if file_content is None or not file_content.strip():
            raise BadRequestError(
                message="File content is empty or could not be extracted",
                error_code="EMPTY_FILE"
            )

        if file_type is None:
            file_type = DocumentParser.get_file_type(file_name)

        uploader_id = user.id if user else created_by_id

        # Use file_name as title if not provided
        if not title:
            title = file_name

        # Chunk the document
        chunks = self._chunk_text(file_content)
        if not chunks:
            raise BadRequestError(
                message="Failed to chunk document",
                error_code="CHUNKING_FAILED"
            )

        logger.info(f"Chunked document '{title}' into {len(chunks)} chunks")

        doc_id = str(uuid.uuid4())
        chroma_ids = []
        if self.chroma_client is not None:
            collection = self._get_collection()
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chroma_ids.append(chunk_id)
                collection.add(
                    documents=[chunk],
                    ids=[chunk_id],
                    metadatas=[{
                        "document_id": doc_id,
                        "id": doc_id,
                        "title": title,
                        "chunk_index": i,
                        "file_type": file_type,
                        "file_name": file_name
                    }]
                )
            logger.info(f"Stored {len(chroma_ids)} chunks in ChromaDB")

        # Create database record
        kb_doc = KBDocument(
            id=uuid.UUID(doc_id),
            title=title,
            file_name=file_name,
            file_type=file_type,
            content=file_content,
            file_size=len(file_content.encode('utf-8')),
            chunk_count=len(chunks),
            chroma_ids=chroma_ids or None,
            uploaded_by=uploader_id,
            is_active=True
        )

        self.db.add(kb_doc)
        await self.db.commit()
        await self.db.refresh(kb_doc)

        logger.info(f"Created KB document: {kb_doc.id}")
        return kb_doc

    async def search_knowledge_base(
        self,
        query: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant documents.

        Args:
            query: Search query
            top_k: Number of results to return (defaults to settings.RAG_TOP_K)

        Returns:
            List of relevant document chunks with metadata
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        if self.chroma_client is not None:
            collection = self._get_collection()

            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k
                )

                documents = []
                if results["documents"] and results["documents"][0]:
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else None
                        documents.append({
                            "content": doc,
                            "metadata": metadata,
                            "relevance_score": 1 - distance if distance is not None else None
                        })

                if documents:
                    logger.info(f"Found {len(documents)} relevant documents for query")
                    return documents
            except Exception as e:
                logger.error(f"Error searching ChromaDB: {str(e)}")

        query_terms = [term for term in re.split(r"\s+", query.strip()) if term]
        like_clauses = []
        for term in query_terms or [query]:
            like_query = f"%{term}%"
            like_clauses.extend([
                KBDocument.title.ilike(like_query),
                KBDocument.content.ilike(like_query)
            ])
        result = await self.db.execute(
            select(KBDocument)
            .where(
                KBDocument.is_active == True,
                or_(*like_clauses)
            )
            .order_by(desc(KBDocument.created_at))
            .limit(top_k)
        )
        documents = []
        for doc in result.scalars().all():
            documents.append({
                "content": doc.content or "",
                "metadata": {
                    "id": str(doc.id),
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "file_type": doc.file_type,
                    "file_name": doc.file_name
                },
                "relevance_score": 1.0
            })
        return documents

    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> List[KBDocument]:
        """
        List knowledge base documents.

        Args:
            limit: Number of documents to return
            offset: Pagination offset
            active_only: Only return active documents

        Returns:
            List of KB documents
        """
        query = select(KBDocument).order_by(desc(KBDocument.created_at))

        if active_only:
            query = query.where(KBDocument.is_active == True)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_document(self, doc_id: uuid.UUID) -> KBDocument:
        """
        Get a knowledge base document by ID.

        Args:
            doc_id: Document ID

        Returns:
            KB document

        Raises:
            NotFoundError: If document not found
        """
        result = await self.db.execute(
            select(KBDocument).where(KBDocument.id == doc_id)
        )
        doc = result.scalar_one_or_none()

        if not doc:
            raise NotFoundError(
                message="Document not found",
                error_code="DOCUMENT_NOT_FOUND"
            )

        return doc

    async def delete_document(self, doc_id: uuid.UUID) -> None:
        """
        Delete a knowledge base document.

        Args:
            doc_id: Document ID

        Raises:
            NotFoundError: If document not found
        """
        doc = await self.get_document(doc_id)

        # Delete from ChromaDB
        if doc.chroma_ids and self.chroma_client is not None:
            collection = self._get_collection()
            try:
                collection.delete(ids=doc.chroma_ids)
                logger.info(f"Deleted {len(doc.chroma_ids)} chunks from ChromaDB")
            except Exception as e:
                logger.warning(f"Error deleting from ChromaDB: {str(e)}")

        # Soft delete in database
        doc.is_active = False
        await self.db.commit()

        logger.info(f"Deleted KB document: {doc_id}")

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end),
                    text.rfind('\n', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - chunk_overlap

        return chunks
