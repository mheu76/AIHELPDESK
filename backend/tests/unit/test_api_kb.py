"""
Unit tests for Knowledge Base API endpoints.
Tests document upload, list, search, and delete operations.
"""
import pytest
import json
from httpx import AsyncClient

from app.models.user import UserRole


class TestKBAPIEndpoints:
    """Tests for knowledge base API endpoints"""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(
        self,
        test_client: AsyncClient,
        admin_headers: dict,
        admin_user
    ):
        """Should upload document successfully (admin only)"""
        content = "How to reset your password..."
        
        response = await test_client.post(
            "/api/v1/kb/upload",
            headers=admin_headers,
            json={
                "content": content,
                "file_name": "password.txt",
                "title": "Password Reset Guide"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["id"] is not None
        assert data["title"] == "Password Reset Guide"
        assert data["file_type"] == "txt"
    
    @pytest.mark.asyncio
    async def test_upload_document_unauthorized(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Should reject upload from non-admin user"""
        response = await test_client.post(
            "/api/v1/kb/upload",
            headers=auth_headers,  # Regular user, not admin
            json={
                "content": "Content",
                "file_name": "doc.txt",
                "title": "Document"
            }
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_upload_document_unauthenticated(
        self,
        test_client: AsyncClient
    ):
        """Should reject upload without authentication"""
        response = await test_client.post(
            "/api/v1/kb/upload",
            json={
                "content": "Content",
                "file_name": "doc.txt",
                "title": "Document"
            }
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_documents(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_kb_document
    ):
        """Should list all knowledge base documents"""
        response = await test_client.get(
            "/api/v1/kb/documents",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert len(data["documents"]) > 0
        
        # Check if our test document is in the list
        doc_titles = [doc["title"] for doc in data["documents"]]
        assert test_kb_document.title in doc_titles
    
    @pytest.mark.asyncio
    async def test_list_documents_unauthenticated(
        self,
        test_client: AsyncClient
    ):
        """Should require authentication to list documents"""
        response = await test_client.get("/api/v1/kb/documents")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_document_detail(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_kb_document
    ):
        """Should retrieve specific document details"""
        response = await test_client.get(
            f"/api/v1/kb/documents/{test_kb_document.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_kb_document.id)
        assert data["title"] == test_kb_document.title
        assert data["content"] is not None
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_document(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Should return 404 for non-existent document"""
        import uuid
        fake_id = uuid.uuid4()
        
        response = await test_client.get(
            f"/api/v1/kb/documents/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_search_documents_query(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_kb_document
    ):
        """Should search documents by query"""
        response = await test_client.post(
            "/api/v1/kb/search",
            headers=auth_headers,
            json={
                "query": "password reset",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_search_documents_empty_query(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Should require non-empty search query"""
        response = await test_client.post(
            "/api/v1/kb/search",
            headers=auth_headers,
            json={
                "query": "",
                "top_k": 5
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        test_client: AsyncClient,
        admin_headers: dict,
        test_kb_document
    ):
        """Should delete document (soft delete)"""
        response = await test_client.delete(
            f"/api/v1/kb/documents/{test_kb_document.id}",
            headers=admin_headers
        )
        
        assert response.status_code == 204
        
        # Verify document is marked as deleted
        # Should not appear in list anymore
        list_response = await test_client.get(
            "/api/v1/kb/documents",
            headers=admin_headers
        )
        
        doc_ids = [str(doc["id"]) for doc in list_response.json()["documents"]]
        assert str(test_kb_document.id) not in doc_ids
    
    @pytest.mark.asyncio
    async def test_delete_document_unauthorized(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_kb_document
    ):
        """Should prevent non-admin from deleting documents"""
        response = await test_client.delete(
            f"/api/v1/kb/documents/{test_kb_document.id}",
            headers=auth_headers  # Regular user
        )
        
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(
        self,
        test_client: AsyncClient,
        admin_headers: dict
    ):
        """Should return 404 when deleting non-existent document"""
        import uuid
        fake_id = uuid.uuid4()
        
        response = await test_client.delete(
            f"/api/v1/kb/documents/{fake_id}",
            headers=admin_headers
        )
        
        assert response.status_code == 404


class TestKBAPIPagination:
    """Tests for document listing pagination"""
    
    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        test_client: AsyncClient,
        admin_headers: dict,
        admin_user,
        test_db
    ):
        """Should support pagination in document list"""
        from app.services.rag import RAGService
        
        # Upload multiple documents
        rag_service = RAGService(test_db)
        for i in range(15):
            await rag_service.upload_document(
                content=f"Document {i} content",
                file_name=f"doc{i}.txt",
                title=f"Document {i}",
                created_by_id=admin_user.id
            )
        
        # Get first page
        response = await test_client.get(
            "/api/v1/kb/documents?page=1&per_page=10",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) <= 10
        
        # Get second page
        response2 = await test_client.get(
            "/api/v1/kb/documents?page=2&per_page=10",
            headers=admin_headers
        )
        
        assert response2.status_code == 200


class TestKBAPIErrorHandling:
    """Tests for KB API error handling"""
    
    @pytest.mark.asyncio
    async def test_upload_empty_content_validation(
        self,
        test_client: AsyncClient,
        admin_headers: dict
    ):
        """Should validate non-empty content"""
        response = await test_client.post(
            "/api/v1/kb/upload",
            headers=admin_headers,
            json={
                "content": "",
                "file_name": "empty.txt",
                "title": "Empty"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_upload_missing_required_fields(
        self,
        test_client: AsyncClient,
        admin_headers: dict
    ):
        """Should validate required fields"""
        response = await test_client.post(
            "/api/v1/kb/upload",
            headers=admin_headers,
            json={
                "content": "Content only"
                # Missing file_name and title
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_search_missing_query_field(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Should validate required search fields"""
        response = await test_client.post(
            "/api/v1/kb/search",
            headers=auth_headers,
            json={
                "top_k": 5
                # Missing query
            }
        )
        
        assert response.status_code == 422


class TestKBAPIResponseFormat:
    """Tests for KB API response format consistency"""
    
    @pytest.mark.asyncio
    async def test_upload_response_format(
        self,
        test_client: AsyncClient,
        admin_headers: dict
    ):
        """Should return consistent response format for upload"""
        response = await test_client.post(
            "/api/v1/kb/upload",
            headers=admin_headers,
            json={
                "content": "Test content",
                "file_name": "test.txt",
                "title": "Test Document"
            }
        )
        
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert "title" in data
        assert "file_name" in data
        assert "file_type" in data
        assert "created_at" in data
        assert "created_by_id" in data
        assert "is_deleted" in data
    
    @pytest.mark.asyncio
    async def test_search_response_format(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_kb_document
    ):
        """Should return consistent response format for search"""
        response = await test_client.post(
            "/api/v1/kb/search",
            headers=auth_headers,
            json={
                "query": "password",
                "top_k": 5
            }
        )
        
        data = response.json()
        
        # Verify response structure
        assert "results" in data
        assert isinstance(data["results"], list)
        
        if len(data["results"]) > 0:
            result = data["results"][0]
            assert "content" in result
            assert "metadata" in result
            assert "score" in result or "relevance" in result
