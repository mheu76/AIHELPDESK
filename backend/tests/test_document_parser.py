"""
Tests for document parser utility.
"""
import pytest

from app.utils.document_parser import DocumentParser


class TestDocumentParser:
    """Test document parser functionality"""

    def test_is_supported(self):
        """Test file format support check"""
        assert DocumentParser.is_supported("document.pdf") is True
        assert DocumentParser.is_supported("document.docx") is True
        assert DocumentParser.is_supported("document.txt") is True
        assert DocumentParser.is_supported("document.md") is True
        assert DocumentParser.is_supported("document.xlsx") is False
        assert DocumentParser.is_supported("document.pptx") is False

    def test_get_file_type(self):
        """Test file type extraction"""
        assert DocumentParser.get_file_type("document.pdf") == "pdf"
        assert DocumentParser.get_file_type("document.DOCX") == "docx"
        assert DocumentParser.get_file_type("document.TXT") == "txt"
        assert DocumentParser.get_file_type("file.name.md") == "md"

    def test_parse_txt(self):
        """Test TXT file parsing"""
        content = b"Hello World\nThis is a test."
        result = DocumentParser.parse_txt(content)
        assert result == "Hello World\nThis is a test."

    def test_parse_txt_korean(self):
        """Test TXT parsing with Korean text"""
        content = "안녕하세요\n테스트입니다.".encode("utf-8")
        result = DocumentParser.parse_txt(content)
        assert "안녕하세요" in result
        assert "테스트입니다" in result

    def test_parse_markdown(self):
        """Test Markdown file parsing"""
        content = b"# Header\n\nThis is **bold** text."
        result = DocumentParser.parse_markdown(content)
        assert "Header" in result
        assert "bold" in result or "text" in result

    def test_parse_unsupported_format(self):
        """Test parsing unsupported file format"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            DocumentParser.parse("document.xlsx", b"content")

    def test_parse_empty_content(self):
        """Test parsing empty content"""
        result = DocumentParser.parse_txt(b"")
        assert result == ""

    def test_parse_with_file_name(self):
        """Test parse method with different file types"""
        txt_content = b"Plain text content"
        result = DocumentParser.parse("test.txt", txt_content)
        assert result == "Plain text content"

        md_content = b"# Markdown content"
        result = DocumentParser.parse("test.md", md_content)
        assert "Markdown" in result
