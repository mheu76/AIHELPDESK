"""
Tests for KB document upload functionality.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from tests.conftest import test_user_token, admin_user_token


@pytest.mark.asyncio
async def test_upload_txt_document(client: AsyncClient, admin_user_token: str):
    """Test uploading a TXT document"""
    content = "IT Support Document\n\nPassword reset instructions..."
    files = {
        "file": ("test_doc.txt", content.encode(), "text/plain")
    }
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    response = await client.post("/api/v1/kb/upload", files=files, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "test_doc.txt"
    assert data["file_type"] == "txt"
    assert data["chunk_count"] > 0


@pytest.mark.asyncio
async def test_upload_md_document(client: AsyncClient, admin_user_token: str):
    """Test uploading a Markdown document"""
    content = "# IT FAQ\n\n## Q1. Password Reset\n\nInstructions here..."
    files = {
        "file": ("faq.md", content.encode(), "text/markdown")
    }
    data = {"title": "IT FAQ Document"}
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    response = await client.post(
        "/api/v1/kb/upload",
        files=files,
        data=data,
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "IT FAQ Document"
    assert data["file_type"] == "md"


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient, admin_user_token: str):
    """Test uploading an empty file"""
    files = {
        "file": ("empty.txt", b"", "text/plain")
    }
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    response = await client.post("/api/v1/kb/upload", files=files, headers=headers)

    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_upload_unsupported_format(client: AsyncClient, admin_user_token: str):
    """Test uploading unsupported file format"""
    files = {
        "file": ("document.xlsx", b"fake excel content", "application/vnd.ms-excel")
    }
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    response = await client.post("/api/v1/kb/upload", files=files, headers=headers)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_without_auth(client: AsyncClient):
    """Test uploading without authentication"""
    files = {
        "file": ("test.txt", b"content", "text/plain")
    }

    response = await client.post("/api/v1/kb/upload", files=files)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_as_regular_user(client: AsyncClient, test_user_token: str):
    """Test uploading as regular user (should fail)"""
    files = {
        "file": ("test.txt", b"content", "text/plain")
    }
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await client.post("/api/v1/kb/upload", files=files, headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, test_user_token: str):
    """Test listing KB documents"""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    response = await client.get("/api/v1/kb/documents", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


@pytest.mark.asyncio
async def test_delete_document(client: AsyncClient, admin_user_token: str):
    """Test deleting a KB document"""
    # First upload a document
    files = {
        "file": ("to_delete.txt", b"This will be deleted", "text/plain")
    }
    headers = {"Authorization": f"Bearer {admin_user_token}"}

    upload_response = await client.post(
        "/api/v1/kb/upload",
        files=files,
        headers=headers
    )
    assert upload_response.status_code == 201
    doc_id = upload_response.json()["id"]

    # Delete it
    delete_response = await client.delete(
        f"/api/v1/kb/documents/{doc_id}",
        headers=headers
    )

    assert delete_response.status_code == 204
