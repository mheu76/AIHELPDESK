"""
Document parsing utilities for extracting text from various file formats.
Supports: PDF, DOCX, TXT, MD
"""
import io
from typing import Optional
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    import markdown
except ImportError:
    markdown = None


class DocumentParser:
    """
    Parse documents and extract text content.
    """

    SUPPORTED_FORMATS = {".pdf", ".docx", ".txt", ".md"}

    @staticmethod
    def is_supported(file_name: str) -> bool:
        """
        Check if file format is supported.

        Args:
            file_name: Name of the file

        Returns:
            True if supported, False otherwise
        """
        suffix = Path(file_name).suffix.lower()
        return suffix in DocumentParser.SUPPORTED_FORMATS

    @staticmethod
    def get_file_type(file_name: str) -> str:
        """
        Get file type from filename.

        Args:
            file_name: Name of the file

        Returns:
            File extension without dot (e.g., 'pdf', 'docx')
        """
        return Path(file_name).suffix.lower().lstrip(".")

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            content: PDF file content as bytes

        Returns:
            Extracted text

        Raises:
            ImportError: If pypdf is not installed
            Exception: If parsing fails
        """
        if PdfReader is None:
            raise ImportError("pypdf is not installed. Install with: pip install pypdf")

        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")

    @staticmethod
    def parse_docx(content: bytes) -> str:
        """
        Extract text from DOCX file.

        Args:
            content: DOCX file content as bytes

        Returns:
            Extracted text

        Raises:
            ImportError: If python-docx is not installed
            Exception: If parsing fails
        """
        if DocxDocument is None:
            raise ImportError("python-docx is not installed. Install with: pip install python-docx")

        try:
            docx_file = io.BytesIO(content)
            doc = DocxDocument(docx_file)

            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n\n".join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to parse DOCX: {str(e)}")

    @staticmethod
    def parse_txt(content: bytes, encoding: str = "utf-8") -> str:
        """
        Extract text from TXT file.

        Args:
            content: TXT file content as bytes
            encoding: Text encoding (default: utf-8)

        Returns:
            Extracted text

        Raises:
            Exception: If parsing fails
        """
        try:
            # Try UTF-8 first
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to CP949 (Korean) or latin-1
                for fallback_encoding in ["cp949", "euc-kr", "latin-1"]:
                    try:
                        return content.decode(fallback_encoding)
                    except UnicodeDecodeError:
                        continue
                raise UnicodeDecodeError(
                    encoding, content, 0, len(content),
                    "Unable to decode text with any supported encoding"
                )
        except Exception as e:
            raise Exception(f"Failed to parse TXT: {str(e)}")

    @staticmethod
    def parse_markdown(content: bytes, encoding: str = "utf-8") -> str:
        """
        Extract text from Markdown file.

        Args:
            content: Markdown file content as bytes
            encoding: Text encoding (default: utf-8)

        Returns:
            Extracted text (plain text, HTML stripped if markdown library available)

        Raises:
            Exception: If parsing fails
        """
        try:
            # Decode markdown content
            try:
                md_text = content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to CP949 (Korean) or latin-1
                for fallback_encoding in ["cp949", "euc-kr", "latin-1"]:
                    try:
                        md_text = content.decode(fallback_encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise UnicodeDecodeError(
                        encoding, content, 0, len(content),
                        "Unable to decode markdown with any supported encoding"
                    )

            # If markdown library is available, convert to HTML then strip tags
            # Otherwise, return raw markdown text
            if markdown is not None:
                html = markdown.markdown(md_text)
                # Simple HTML tag stripping
                import re
                text = re.sub(r'<[^>]+>', '', html)
                # Clean up extra whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                return text.strip()
            else:
                return md_text

        except Exception as e:
            raise Exception(f"Failed to parse Markdown: {str(e)}")

    @staticmethod
    def parse(file_name: str, content: bytes) -> str:
        """
        Parse document and extract text based on file type.

        Args:
            file_name: Name of the file (used to determine type)
            content: File content as bytes

        Returns:
            Extracted text

        Raises:
            ValueError: If file format is not supported
            Exception: If parsing fails
        """
        if not DocumentParser.is_supported(file_name):
            suffix = Path(file_name).suffix.lower()
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {', '.join(DocumentParser.SUPPORTED_FORMATS)}"
            )

        file_type = DocumentParser.get_file_type(file_name)

        if file_type == "pdf":
            return DocumentParser.parse_pdf(content)
        elif file_type == "docx":
            return DocumentParser.parse_docx(content)
        elif file_type == "txt":
            return DocumentParser.parse_txt(content)
        elif file_type == "md":
            return DocumentParser.parse_markdown(content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
