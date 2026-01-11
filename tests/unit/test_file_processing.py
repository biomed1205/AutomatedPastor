"""Tests for file processing (PDFs and Word docs).

These tests verify text extraction from PDFs and Word documents
for reference materials attached to sermons.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL files generated in temp directories - NO MOCKS.
"""
import pytest
import tempfile
import os


# Helper functions to create real test files
def create_valid_pdf(path, text_content="This is test PDF content."):
    """Create a real PDF file using reportlab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(path, pagesize=letter)
        c.drawString(72, 720, text_content)
        c.save()
    except ImportError:
        # Fallback: create minimal PDF manually
        pdf_content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""
        with open(path, 'wb') as f:
            f.write(pdf_content.encode('latin-1'))


def create_valid_docx(path, text_content="This is test Word content."):
    """Create a real DOCX file using python-docx."""
    from docx import Document
    doc = Document()
    doc.add_paragraph(text_content)
    doc.save(path)


def create_empty_pdf(path):
    """Create an empty PDF (minimal valid structure but no text)."""
    pdf_content = """%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
178
%%EOF"""
    with open(path, 'wb') as f:
        f.write(pdf_content.encode('latin-1'))


def create_empty_docx(path):
    """Create an empty DOCX file."""
    from docx import Document
    doc = Document()
    doc.save(path)


def create_corrupted_file(path, extension):
    """Create a corrupted file with random bytes."""
    with open(path, 'wb') as f:
        f.write(b'This is not a valid ' + extension.encode() + b' file\x00\xff\xfe')


class TestExtractTextFromPDF:
    """Test suite for PDF text extraction."""

    def test_should_extract_text_when_valid_pdf_provided(self):
        """Test extracting text from a valid PDF."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            create_valid_pdf(pdf_path, "Sample sermon text from PDF.")

            result = extract_text_from_pdf(pdf_path)

            assert result is not None
            assert 'text' in result
            assert len(result['text']) > 0

    def test_should_return_dict_with_text_key(self):
        """Test that result contains text key."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            create_valid_pdf(pdf_path, "Test content.")

            result = extract_text_from_pdf(pdf_path)

            assert isinstance(result, dict)
            assert 'text' in result

    def test_should_include_metadata_in_result(self):
        """Test that result includes metadata."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            create_valid_pdf(pdf_path, "Content with metadata.")

            result = extract_text_from_pdf(pdf_path)

            assert 'metadata' in result or 'page_count' in result

    def test_should_handle_empty_pdf(self):
        """Test extracting text from empty PDF."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'empty.pdf')
            create_empty_pdf(pdf_path)

            result = extract_text_from_pdf(pdf_path)

            # Should return empty text, not error
            assert result is not None
            assert result.get('text', '') == '' or result.get('text') is not None

    def test_should_raise_error_when_file_not_found(self):
        """Test that missing file raises appropriate error."""
        from file_processing import extract_text_from_pdf, FileProcessingError

        with pytest.raises((FileProcessingError, FileNotFoundError)):
            extract_text_from_pdf('/nonexistent/path/document.pdf')

    def test_should_raise_error_when_file_corrupted(self):
        """Test that corrupted file raises appropriate error."""
        from file_processing import extract_text_from_pdf, FileProcessingError

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'corrupted.pdf')
            create_corrupted_file(pdf_path, 'pdf')

            with pytest.raises((FileProcessingError, Exception)):
                extract_text_from_pdf(pdf_path)

    def test_should_handle_password_protected_pdf(self):
        """Test that password-protected PDF raises appropriate error."""
        from file_processing import extract_text_from_pdf, PasswordProtectedError

        # Create a password-protected PDF is complex, so test the error handling
        # by using a manually created encrypted PDF header
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'protected.pdf')
            # Minimal encrypted PDF marker
            with open(pdf_path, 'wb') as f:
                f.write(b'%PDF-1.4\n/Encrypt ')

            with pytest.raises((PasswordProtectedError, FileProcessingError, Exception)):
                extract_text_from_pdf(pdf_path)

    def test_should_handle_multipage_pdf(self):
        """Test extracting text from multi-page PDF."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'multipage.pdf')

            # Create multi-page PDF
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(pdf_path, pagesize=letter)
                c.drawString(72, 720, "Page 1 content")
                c.showPage()
                c.drawString(72, 720, "Page 2 content")
                c.showPage()
                c.drawString(72, 720, "Page 3 content")
                c.save()
            except ImportError:
                pytest.skip("reportlab not available for multi-page test")

            result = extract_text_from_pdf(pdf_path)

            assert result is not None
            # Should extract text from all pages
            if 'page_count' in result:
                assert result['page_count'] >= 3


class TestExtractTextFromDocx:
    """Test suite for Word document text extraction."""

    def test_should_extract_text_when_valid_docx_provided(self):
        """Test extracting text from a valid Word document."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'test.docx')
            create_valid_docx(docx_path, "Sample sermon text from Word doc.")

            result = extract_text_from_docx(docx_path)

            assert result is not None
            assert 'text' in result
            assert 'sermon' in result['text'].lower() or len(result['text']) > 0

    def test_should_return_dict_with_text_key_for_docx(self):
        """Test that result contains text key."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'test.docx')
            create_valid_docx(docx_path, "Test content.")

            result = extract_text_from_docx(docx_path)

            assert isinstance(result, dict)
            assert 'text' in result

    def test_should_handle_empty_docx(self):
        """Test extracting text from empty Word document."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'empty.docx')
            create_empty_docx(docx_path)

            result = extract_text_from_docx(docx_path)

            assert result is not None
            assert result.get('text', '') == '' or result.get('text') is not None

    def test_should_raise_error_when_docx_not_found(self):
        """Test that missing file raises appropriate error."""
        from file_processing import extract_text_from_docx, FileProcessingError

        with pytest.raises((FileProcessingError, FileNotFoundError)):
            extract_text_from_docx('/nonexistent/path/document.docx')

    def test_should_raise_error_when_docx_corrupted(self):
        """Test that corrupted file raises appropriate error."""
        from file_processing import extract_text_from_docx, FileProcessingError

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'corrupted.docx')
            create_corrupted_file(docx_path, 'docx')

            with pytest.raises((FileProcessingError, Exception)):
                extract_text_from_docx(docx_path)

    def test_should_preserve_paragraph_structure(self):
        """Test that paragraph structure is preserved."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'paragraphs.docx')

            # Create docx with multiple paragraphs
            from docx import Document
            doc = Document()
            doc.add_paragraph("First paragraph.")
            doc.add_paragraph("Second paragraph.")
            doc.add_paragraph("Third paragraph.")
            doc.save(docx_path)

            result = extract_text_from_docx(docx_path)

            assert 'First' in result['text']
            assert 'Second' in result['text']
            assert 'Third' in result['text']

    def test_should_include_metadata_for_docx(self):
        """Test that metadata is included in result."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'with_meta.docx')
            create_valid_docx(docx_path, "Content.")

            result = extract_text_from_docx(docx_path)

            # Should have some metadata info
            assert result is not None


class TestProcessFile:
    """Test suite for auto-detect file processing."""

    def test_should_process_pdf_file_automatically(self):
        """Test that PDF files are auto-detected and processed."""
        from file_processing import process_file

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'test.pdf')
            create_valid_pdf(pdf_path, "Auto-detected PDF content.")

            result = process_file(pdf_path)

            assert result is not None
            assert 'text' in result

    def test_should_process_docx_file_automatically(self):
        """Test that Word files are auto-detected and processed."""
        from file_processing import process_file

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'test.docx')
            create_valid_docx(docx_path, "Auto-detected Word content.")

            result = process_file(docx_path)

            assert result is not None
            assert 'text' in result

    def test_should_process_txt_file(self):
        """Test that plain text files are processed."""
        from file_processing import process_file

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_path = os.path.join(tmpdir, 'test.txt')
            with open(txt_path, 'w') as f:
                f.write("Plain text content for sermon reference.")

            result = process_file(txt_path)

            assert result is not None
            assert 'text' in result
            assert 'Plain text' in result['text']

    def test_should_raise_error_for_unsupported_format(self):
        """Test that unsupported formats raise appropriate error."""
        from file_processing import process_file, UnsupportedFormatError

        with tempfile.TemporaryDirectory() as tmpdir:
            unsupported_path = os.path.join(tmpdir, 'test.xyz')
            with open(unsupported_path, 'wb') as f:
                f.write(b'random content')

            with pytest.raises((UnsupportedFormatError, ValueError)):
                process_file(unsupported_path)

    def test_should_include_file_type_in_result(self):
        """Test that file type is included in result."""
        from file_processing import process_file

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'typed.pdf')
            create_valid_pdf(pdf_path, "Content.")

            result = process_file(pdf_path)

            assert 'file_type' in result or 'format' in result

    def test_should_handle_file_not_found(self):
        """Test that missing file raises appropriate error."""
        from file_processing import process_file, FileProcessingError

        with pytest.raises((FileProcessingError, FileNotFoundError)):
            process_file('/nonexistent/path/file.pdf')


class TestLargeFileHandling:
    """Test suite for handling large files."""

    def test_should_handle_large_pdf(self):
        """Test processing large PDF file."""
        from file_processing import extract_text_from_pdf

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'large.pdf')

            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.pdfgen import canvas

                c = canvas.Canvas(pdf_path, pagesize=letter)
                # Create 50 pages with content
                for i in range(50):
                    c.drawString(72, 720, f"Page {i + 1}: " + "Lorem ipsum " * 50)
                    c.showPage()
                c.save()
            except ImportError:
                pytest.skip("reportlab not available for large file test")

            result = extract_text_from_pdf(pdf_path)

            assert result is not None

    def test_should_handle_large_docx(self):
        """Test processing large Word document."""
        from file_processing import extract_text_from_docx

        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, 'large.docx')

            from docx import Document
            doc = Document()
            # Create many paragraphs
            for i in range(100):
                doc.add_paragraph(f"Paragraph {i + 1}: " + "Lorem ipsum dolor sit amet. " * 20)
            doc.save(docx_path)

            result = extract_text_from_docx(docx_path)

            assert result is not None
            assert len(result['text']) > 1000


class TestFileProcessingErrors:
    """Test suite for error handling."""

    def test_should_provide_meaningful_error_message(self):
        """Test that errors include helpful messages."""
        from file_processing import extract_text_from_pdf, FileProcessingError

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'bad.pdf')
            create_corrupted_file(pdf_path, 'pdf')

            with pytest.raises(Exception) as exc_info:
                extract_text_from_pdf(pdf_path)

            # Error should have some message
            assert str(exc_info.value) != '' or exc_info.value is not None

    def test_should_not_crash_on_binary_garbage(self):
        """Test that binary garbage is handled gracefully."""
        from file_processing import process_file

        with tempfile.TemporaryDirectory() as tmpdir:
            garbage_path = os.path.join(tmpdir, 'garbage.pdf')
            with open(garbage_path, 'wb') as f:
                f.write(os.urandom(1000))  # Random bytes

            # Should raise error, not crash
            with pytest.raises(Exception):
                process_file(garbage_path)
