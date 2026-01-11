"""File processing module for extracting text from PDFs and Word documents.

Provides functions to extract text content from various document formats
for use as reference materials in sermon preparation.
"""
import os


class FileProcessingError(Exception):
    """Base exception for file processing errors."""
    pass


class PasswordProtectedError(FileProcessingError):
    """Raised when a PDF is password protected."""
    pass


class UnsupportedFormatError(FileProcessingError):
    """Raised when file format is not supported."""
    pass


# Supported file extensions
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}


def extract_text_from_pdf(path):
    """Extract text from a PDF file.

    Args:
        path: Path to the PDF file.

    Returns:
        dict: Result containing:
            - text: Extracted text content
            - page_count: Number of pages in the PDF
            - metadata: PDF metadata if available

    Raises:
        FileProcessingError: If file is missing or corrupted.
        PasswordProtectedError: If PDF is password protected.
    """
    if not os.path.exists(path):
        raise FileProcessingError(f"File not found: {path}")

    try:
        from pypdf import PdfReader

        reader = PdfReader(path)

        # Check for encryption
        if reader.is_encrypted:
            raise PasswordProtectedError("PDF is password protected")

        # Extract text from all pages
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        text = '\n'.join(text_parts)

        return {
            'text': text,
            'page_count': len(reader.pages),
            'metadata': dict(reader.metadata) if reader.metadata else {}
        }

    except PasswordProtectedError:
        raise
    except Exception as e:
        raise FileProcessingError(f"Failed to process PDF: {str(e)}")


def extract_text_from_docx(path):
    """Extract text from a Word document.

    Args:
        path: Path to the DOCX file.

    Returns:
        dict: Result containing:
            - text: Extracted text content with paragraphs preserved

    Raises:
        FileProcessingError: If file is missing or corrupted.
    """
    if not os.path.exists(path):
        raise FileProcessingError(f"File not found: {path}")

    try:
        from docx import Document

        doc = Document(path)

        # Extract text preserving paragraph structure
        paragraphs = []
        for para in doc.paragraphs:
            if para.text:
                paragraphs.append(para.text)

        text = '\n\n'.join(paragraphs)

        return {
            'text': text
        }

    except Exception as e:
        raise FileProcessingError(f"Failed to process Word document: {str(e)}")


def extract_text_from_txt(path):
    """Extract text from a plain text file.

    Args:
        path: Path to the TXT file.

    Returns:
        dict: Result containing:
            - text: File content

    Raises:
        FileProcessingError: If file is missing or unreadable.
    """
    if not os.path.exists(path):
        raise FileProcessingError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        return {
            'text': text
        }

    except UnicodeDecodeError:
        # Try with latin-1 encoding as fallback
        try:
            with open(path, 'r', encoding='latin-1') as f:
                text = f.read()
            return {'text': text}
        except Exception as e:
            raise FileProcessingError(f"Failed to read text file: {str(e)}")
    except Exception as e:
        raise FileProcessingError(f"Failed to read text file: {str(e)}")


def process_file(path):
    """Auto-detect file type and extract text.

    Args:
        path: Path to the file.

    Returns:
        dict: Result containing:
            - text: Extracted text content
            - file_type: Detected file type ('pdf', 'docx', 'txt')
            - Additional fields depending on file type

    Raises:
        FileProcessingError: If file is missing or corrupted.
        UnsupportedFormatError: If file format is not supported.
    """
    if not os.path.exists(path):
        raise FileProcessingError(f"File not found: {path}")

    # Get file extension
    _, ext = os.path.splitext(path)
    ext = ext.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFormatError(f"Unsupported file format: {ext}")

    # Process based on file type
    if ext == '.pdf':
        result = extract_text_from_pdf(path)
        result['file_type'] = 'pdf'
        result['format'] = 'pdf'
    elif ext == '.docx':
        result = extract_text_from_docx(path)
        result['file_type'] = 'docx'
        result['format'] = 'docx'
    elif ext == '.txt':
        result = extract_text_from_txt(path)
        result['file_type'] = 'txt'
        result['format'] = 'txt'
    else:
        raise UnsupportedFormatError(f"Unsupported file format: {ext}")

    return result
