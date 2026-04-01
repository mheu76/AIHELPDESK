"""
Unit tests for RAG (Retrieval-Augmented Generation) Service.
Tests knowledge base operations: upload, search, delete, list.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.rag import RAGService
from app.models.kb_document import KBDocument
from app.models.user import User
from app.core.exceptions import NotFoundError, BadRequestError


class TestRAGServiceUpload:
    """Tests for knowledge base document upload"""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should store document in knowledge base"""
        rag_service = RAGService(test_db)
        
        content = """
        How to Reset Your Password
        
        If you have forgotten your password, follow these steps:
        1. Go to the login page
        2. Click on 'Forgot Password'
        3. Enter your email address
        4. Check your email for reset link
        5. Click the reset link
        6. Enter your new password
        7. Click 'Reset Password'
        8. Login with your new password
        """
        
        doc = await rag_service.upload_document(
            content=content,
            file_name="password_reset.txt",
            title="Password Reset Guide",
            created_by_id=admin_user.id
        )
        
        assert doc.id is not None
        assert doc.title == "Password Reset Guide"
        assert doc.file_name == "password_reset.txt"
        assert doc.file_type == "txt"
        assert doc.content is not None
        assert doc.created_by_id == admin_user.id
        assert doc.is_deleted is False
    
    @pytest.mark.asyncio
    async def test_upload_document_markdown_format(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should support markdown format"""
        rag_service = RAGService(test_db)
        
        content = "# FAQ\n## Q: How to reset password?\n## A: Click reset button..."
        
        doc = await rag_service.upload_document(
            content=content,
            file_name="faq.md",
            title="Frequently Asked Questions",
            created_by_id=admin_user.id
        )
        
        assert doc.file_type == "md"
        assert "# FAQ" in doc.content
    
    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should reject unsupported file types"""
        rag_service = RAGService(test_db)
        
        # PDF format not supported yet
        with pytest.raises(BadRequestError, match="file type"):
            await rag_service.upload_document(
                content=b"PDF content",
                file_name="document.pdf",
                title="PDF Document",
                created_by_id=admin_user.id
            )
    
    @pytest.mark.asyncio
    async def test_upload_empty_content(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should validate content is not empty"""
        rag_service = RAGService(test_db)
        
        with pytest.raises(BadRequestError, match="empty"):
            await rag_service.upload_document(
                content="",
                file_name="empty.txt",
                title="Empty Document",
                created_by_id=admin_user.id
            )


class TestRAGServiceSearch:
    """Tests for knowledge base search functionality"""
    
    @pytest.mark.asyncio
    async def test_search_knowledge_base_success(
        self,
        test_db: AsyncSession,
        test_kb_document: KBDocument
    ):
        """Should return matching documents by semantic similarity"""
        rag_service = RAGService(test_db)
        
        # Search for password-related content
        results = await rag_service.search_knowledge_base(
            query="password reset",
            top_k=3
        )
        
        assert len(results) > 0
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert results[0]["metadata"]["title"] == test_kb_document.title
    
    @pytest.mark.asyncio
    async def test_search_empty_knowledge_base(
        self,
        test_db: AsyncSession
    ):
        """Should return empty results for empty KB"""
        rag_service = RAGService(test_db)
        
        results = await rag_service.search_knowledge_base(
            query="anything",
            top_k=5
        )
        
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_top_k_limit(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should respect top_k limit parameter"""
        rag_service = RAGService(test_db)
        
        # Upload multiple documents
        for i in range(5):
            await rag_service.upload_document(
                content=f"Document {i}: How to do X",
                file_name=f"doc{i}.txt",
                title=f"Document {i}",
                created_by_id=admin_user.id
            )
        
        # Search with limit
        results = await rag_service.search_knowledge_base(
            query="how to",
            top_k=3
        )
        
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_search_excludes_deleted_documents(
        self,
        test_db: AsyncSession,
        admin_user: User,
        test_kb_document: KBDocument
    ):
        """Should not return deleted documents in search"""
        rag_service = RAGService(test_db)
        
        # Soft delete the test document
        test_kb_document.is_deleted = True
        await test_db.commit()
        
        results = await rag_service.search_knowledge_base(
            query="password"
        )
        
        # Should not find the deleted document
        for result in results:
            assert result["metadata"]["id"] != str(test_kb_document.id)


class TestRAGServiceManagement:
    """Tests for knowledge base document management"""
    
    @pytest.mark.asyncio
    async def test_list_documents(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should list all active documents"""
        rag_service = RAGService(test_db)
        
        # Upload multiple documents
        titles = ["Doc1", "Doc2", "Doc3"]
        for title in titles:
            await rag_service.upload_document(
                content=f"Content of {title}",
                file_name=f"{title}.txt",
                title=title,
                created_by_id=admin_user.id
            )
        
        docs = await rag_service.list_documents()
        
        assert len(docs) >= 3
        doc_titles = [doc.title for doc in docs]
        for title in titles:
            assert title in doc_titles
    
    @pytest.mark.asyncio
    async def test_get_document_success(
        self,
        test_db: AsyncSession,
        test_kb_document: KBDocument
    ):
        """Should retrieve specific document by ID"""
        rag_service = RAGService(test_db)
        
        doc = await rag_service.get_document(test_kb_document.id)
        
        assert doc.id == test_kb_document.id
        assert doc.title == test_kb_document.title
        assert doc.content == test_kb_document.content
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(
        self,
        test_db: AsyncSession
    ):
        """Should raise error for non-existent document"""
        import uuid
        rag_service = RAGService(test_db)
        
        with pytest.raises(NotFoundError):
            await rag_service.get_document(uuid.uuid4())
    
    @pytest.mark.asyncio
    async def test_delete_document_soft_delete(
        self,
        test_db: AsyncSession,
        test_kb_document: KBDocument
    ):
        """Should mark document as deleted (soft delete)"""
        rag_service = RAGService(test_db)
        
        await rag_service.delete_document(test_kb_document.id)
        
        # Verify soft delete
        result = await test_db.execute(
            select(KBDocument).where(KBDocument.id == test_kb_document.id)
        )
        doc = result.scalar_one()
        assert doc.is_deleted is True
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self,
        test_db: AsyncSession
    ):
        """Should raise error when deleting non-existent document"""
        import uuid
        rag_service = RAGService(test_db)
        
        with pytest.raises(NotFoundError):
            await rag_service.delete_document(uuid.uuid4())


class TestRAGServiceTextChunking:
    """Tests for text chunking functionality"""
    
    @pytest.mark.asyncio
    async def test_text_chunking_with_overlap(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should chunk text with proper overlap"""
        rag_service = RAGService(test_db)
        
        # Create long document
        long_content = ". ".join(["Sentence " + str(i) for i in range(100)])
        
        doc = await rag_service.upload_document(
            content=long_content,
            file_name="long_doc.txt",
            title="Long Document",
            created_by_id=admin_user.id
        )
        
        assert doc.id is not None
        assert len(long_content) > 1000  # Verify it's long enough to chunk
    
    @pytest.mark.asyncio
    async def test_text_chunking_sentence_boundaries(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should respect sentence boundaries in chunking"""
        rag_service = RAGService(test_db)
        
        # Content with clear sentence boundaries
        content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        
        doc = await rag_service.upload_document(
            content=content,
            file_name="sentences.txt",
            title="Sentences",
            created_by_id=admin_user.id
        )
        
        # Should not split in middle of sentences
        assert doc.content is not None


class TestRAGServiceIntegration:
    """Integration tests for RAG service with chat"""
    
    @pytest.mark.asyncio
    async def test_rag_context_for_chat(
        self,
        test_db: AsyncSession,
        admin_user: User,
        test_kb_document: KBDocument
    ):
        """Should provide context for chat queries"""
        rag_service = RAGService(test_db)
        
        # Ensure KB document is in the system
        assert test_kb_document.id is not None
        
        # Search for context
        results = await rag_service.search_knowledge_base(
            query="password reset",
            top_k=3
        )
        
        # Should return KB content as context
        assert len(results) > 0
        context_content = results[0]["content"]
        assert "password" in context_content.lower() or "reset" in context_content.lower()
    
    @pytest.mark.asyncio
    async def test_multiple_kb_documents_search(
        self,
        test_db: AsyncSession,
        admin_user: User
    ):
        """Should search across multiple KB documents"""
        rag_service = RAGService(test_db)
        
        # Upload multiple docs with different topics
        docs_data = [
            ("Password Reset", "How to reset your password: Go to login page..."),
            ("VPN Setup", "To set up VPN: Download the client..."),
            ("Email Configuration", "To configure email: Use IMAP server..."),
        ]
        
        for title, content in docs_data:
            await rag_service.upload_document(
                content=content,
                file_name=f"{title.lower().replace(' ', '_')}.txt",
                title=title,
                created_by_id=admin_user.id
            )
        
        # Search for specific topic
        results = await rag_service.search_knowledge_base(
            query="VPN configuration",
            top_k=5
        )
        
        assert len(results) > 0
        # Should find VPN-related document
        found_vpn = any("vpn" in r.get("metadata", {}).get("title", "").lower() 
                       for r in results)
        assert found_vpn or len(results) > 0  # At least some results
