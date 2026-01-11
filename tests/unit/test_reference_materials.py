"""Tests for reference material input.

These tests verify the reference material system that allows users
to attach notes, files, and URLs to sermons.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL SQLite :memory: and tempfile - NO MOCKS.
"""
import pytest
import sqlite3
import tempfile
import os


class TestCreateTextReference:
    """Test suite for creating text note references."""

    def test_should_create_text_reference_when_valid_sermon_exists(self):
        """Test creating a text note reference for a sermon."""
        from reference_materials import create_text_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Create a sermon first
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        # Create text reference
        result = create_text_reference(
            conn,
            sermon_id=sermon_id,
            content='This is a note about the sermon theme.'
        )

        assert result is not None
        assert 'id' in result or result > 0
        conn.close()

    def test_should_store_text_content_in_database(self):
        """Test that text content is stored correctly."""
        from reference_materials import create_text_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        content = 'Important theological point about grace.'
        create_text_reference(conn, sermon_id=sermon_id, content=content)

        cursor.execute(
            "SELECT content, material_type FROM reference_materials WHERE sermon_id = ?",
            (sermon_id,)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == content
        assert row[1] == 'text'
        conn.close()

    def test_should_reject_empty_text_content(self):
        """Test that empty text content is rejected."""
        from reference_materials import create_text_reference, InvalidReferenceError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with pytest.raises(InvalidReferenceError):
            create_text_reference(conn, sermon_id=sermon_id, content='')

        conn.close()

    def test_should_reject_whitespace_only_content(self):
        """Test that whitespace-only content is rejected."""
        from reference_materials import create_text_reference, InvalidReferenceError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with pytest.raises(InvalidReferenceError):
            create_text_reference(conn, sermon_id=sermon_id, content='   \n\t  ')

        conn.close()


class TestCreateFileReference:
    """Test suite for creating file references."""

    def test_should_create_file_reference_when_valid_pdf_uploaded(self):
        """Test creating a file reference with PDF."""
        from reference_materials import create_file_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        # Create a real temp file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 fake pdf content')
            temp_path = f.name

        try:
            result = create_file_reference(
                conn,
                sermon_id=sermon_id,
                file_path=temp_path,
                filename='sermon_notes.pdf'
            )

            assert result is not None
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_create_file_reference_when_valid_docx_uploaded(self):
        """Test creating a file reference with Word document."""
        from reference_materials import create_file_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(b'PK fake docx content')
            temp_path = f.name

        try:
            result = create_file_reference(
                conn,
                sermon_id=sermon_id,
                file_path=temp_path,
                filename='notes.docx'
            )

            assert result is not None
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_create_file_reference_when_valid_txt_uploaded(self):
        """Test creating a file reference with text file."""
        from reference_materials import create_file_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Plain text sermon notes')
            temp_path = f.name

        try:
            result = create_file_reference(
                conn,
                sermon_id=sermon_id,
                file_path=temp_path,
                filename='notes.txt'
            )

            assert result is not None
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_store_filename_in_database(self):
        """Test that filename is stored correctly."""
        from reference_materials import create_file_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 content')
            temp_path = f.name

        try:
            create_file_reference(
                conn,
                sermon_id=sermon_id,
                file_path=temp_path,
                filename='important_research.pdf'
            )

            cursor.execute(
                "SELECT filename, material_type FROM reference_materials WHERE sermon_id = ?",
                (sermon_id,)
            )
            row = cursor.fetchone()

            assert row is not None
            assert row[0] == 'important_research.pdf'
            assert row[1] == 'file'
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_reject_invalid_file_type(self):
        """Test that invalid file types are rejected."""
        from reference_materials import create_file_reference, InvalidFileTypeError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'malicious content')
            temp_path = f.name

        try:
            with pytest.raises(InvalidFileTypeError):
                create_file_reference(
                    conn,
                    sermon_id=sermon_id,
                    file_path=temp_path,
                    filename='program.exe'
                )
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_reject_jpg_file_type(self):
        """Test that image files are rejected."""
        from reference_materials import create_file_reference, InvalidFileTypeError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'\xff\xd8\xff fake jpg')
            temp_path = f.name

        try:
            with pytest.raises(InvalidFileTypeError):
                create_file_reference(
                    conn,
                    sermon_id=sermon_id,
                    file_path=temp_path,
                    filename='image.jpg'
                )
        finally:
            os.unlink(temp_path)
            conn.close()

    def test_should_reject_missing_file(self):
        """Test that missing files are rejected."""
        from reference_materials import create_file_reference, FileNotFoundError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with pytest.raises((FileNotFoundError, Exception)):
            create_file_reference(
                conn,
                sermon_id=sermon_id,
                file_path='/nonexistent/path/file.pdf',
                filename='missing.pdf'
            )

        conn.close()


class TestCreateURLReference:
    """Test suite for creating URL references."""

    def test_should_create_url_reference_when_valid_url_provided(self):
        """Test creating a URL reference."""
        from reference_materials import create_url_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        result = create_url_reference(
            conn,
            sermon_id=sermon_id,
            url='https://www.biblegateway.com/passage/?search=John+3%3A16'
        )

        assert result is not None
        conn.close()

    def test_should_store_url_in_database(self):
        """Test that URL is stored correctly."""
        from reference_materials import create_url_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        url = 'https://example.com/theology/article'
        create_url_reference(conn, sermon_id=sermon_id, url=url)

        cursor.execute(
            "SELECT url, material_type FROM reference_materials WHERE sermon_id = ?",
            (sermon_id,)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == url
        assert row[1] == 'url'
        conn.close()

    def test_should_reject_empty_url(self):
        """Test that empty URLs are rejected."""
        from reference_materials import create_url_reference, InvalidReferenceError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with pytest.raises(InvalidReferenceError):
            create_url_reference(conn, sermon_id=sermon_id, url='')

        conn.close()

    def test_should_reject_invalid_url_format(self):
        """Test that invalid URL formats are rejected."""
        from reference_materials import create_url_reference, InvalidReferenceError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        with pytest.raises(InvalidReferenceError):
            create_url_reference(conn, sermon_id=sermon_id, url='not-a-valid-url')

        conn.close()

    def test_should_accept_http_url(self):
        """Test that HTTP URLs are accepted."""
        from reference_materials import create_url_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        result = create_url_reference(
            conn,
            sermon_id=sermon_id,
            url='http://example.com/resource'
        )

        assert result is not None
        conn.close()


class TestListReferences:
    """Test suite for listing references."""

    def test_should_list_all_references_for_sermon(self):
        """Test listing all references for a sermon."""
        from reference_materials import (
            create_text_reference, create_url_reference, list_references
        )
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        # Create multiple references
        create_text_reference(conn, sermon_id=sermon_id, content='Note 1')
        create_text_reference(conn, sermon_id=sermon_id, content='Note 2')
        create_url_reference(conn, sermon_id=sermon_id, url='https://example.com')

        references = list_references(conn, sermon_id=sermon_id)

        assert len(references) == 3
        conn.close()

    def test_should_return_empty_list_when_no_references(self):
        """Test that empty list is returned when no references exist."""
        from reference_materials import list_references
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        references = list_references(conn, sermon_id=sermon_id)

        assert references == []
        conn.close()

    def test_should_only_return_references_for_specified_sermon(self):
        """Test that only references for the specified sermon are returned."""
        from reference_materials import create_text_reference, list_references
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        # Create two sermons
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Sermon 1', 'John 3:16')
        )
        conn.commit()
        sermon1_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Sermon 2', 'Romans 8:28')
        )
        conn.commit()
        sermon2_id = cursor.lastrowid

        # Add references to both
        create_text_reference(conn, sermon_id=sermon1_id, content='Note for sermon 1')
        create_text_reference(conn, sermon_id=sermon2_id, content='Note for sermon 2')
        create_text_reference(conn, sermon_id=sermon2_id, content='Another note for sermon 2')

        # List only sermon 1's references
        references = list_references(conn, sermon_id=sermon1_id)

        assert len(references) == 1
        conn.close()

    def test_should_include_reference_type_in_listing(self):
        """Test that reference type is included in listing."""
        from reference_materials import (
            create_text_reference, create_url_reference, list_references
        )
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        create_text_reference(conn, sermon_id=sermon_id, content='A note')
        create_url_reference(conn, sermon_id=sermon_id, url='https://example.com')

        references = list_references(conn, sermon_id=sermon_id)

        types = [r['material_type'] for r in references]
        assert 'text' in types
        assert 'url' in types
        conn.close()


class TestDeleteReference:
    """Test suite for deleting references."""

    def test_should_delete_reference_when_valid_id_provided(self):
        """Test deleting a reference by ID."""
        from reference_materials import create_text_reference, delete_reference, list_references
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        ref_id = create_text_reference(conn, sermon_id=sermon_id, content='To be deleted')

        # Delete the reference
        result = delete_reference(conn, reference_id=ref_id)

        assert result is True

        # Verify it's gone
        references = list_references(conn, sermon_id=sermon_id)
        assert len(references) == 0
        conn.close()

    def test_should_return_false_when_reference_not_found(self):
        """Test deleting nonexistent reference returns False."""
        from reference_materials import delete_reference
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        result = delete_reference(conn, reference_id=99999)

        assert result is False
        conn.close()

    def test_should_not_delete_other_references(self):
        """Test that deleting one reference doesn't affect others."""
        from reference_materials import create_text_reference, delete_reference, list_references
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
            ('Test Sermon', 'John 3:16')
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        ref1_id = create_text_reference(conn, sermon_id=sermon_id, content='Keep this')
        ref2_id = create_text_reference(conn, sermon_id=sermon_id, content='Delete this')

        delete_reference(conn, reference_id=ref2_id)

        references = list_references(conn, sermon_id=sermon_id)
        assert len(references) == 1
        assert references[0]['content'] == 'Keep this'
        conn.close()


class TestSermonNotFound:
    """Test suite for handling missing sermons."""

    def test_should_raise_error_when_creating_reference_for_missing_sermon(self):
        """Test that creating reference for nonexistent sermon fails."""
        from reference_materials import create_text_reference, SermonNotFoundError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        with pytest.raises(SermonNotFoundError):
            create_text_reference(conn, sermon_id=99999, content='Orphan note')

        conn.close()

    def test_should_raise_error_when_creating_url_for_missing_sermon(self):
        """Test that creating URL reference for nonexistent sermon fails."""
        from reference_materials import create_url_reference, SermonNotFoundError
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        with pytest.raises(SermonNotFoundError):
            create_url_reference(conn, sermon_id=99999, url='https://example.com')

        conn.close()

    def test_should_return_empty_list_when_listing_references_for_missing_sermon(self):
        """Test listing references for nonexistent sermon returns empty."""
        from reference_materials import list_references
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Should not raise, just return empty
        references = list_references(conn, sermon_id=99999)

        assert references == []
        conn.close()


class TestFlaskRoutes:
    """Test suite for Flask reference material routes."""

    def test_should_return_200_when_listing_references(self):
        """Test that listing references route returns 200."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.get(f'/sermon/{sermon_id}/references')

            assert response.status_code == 200

    def test_should_return_201_when_creating_text_reference(self):
        """Test that creating text reference returns 201."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.post(
                f'/sermon/{sermon_id}/references',
                json={'type': 'text', 'content': 'My note'}
            )

            assert response.status_code == 201

    def test_should_return_404_when_sermon_not_found(self):
        """Test that routes return 404 for missing sermon."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)

        with app.test_client() as client:
            response = client.get('/sermon/99999/references')

            assert response.status_code == 404

    def test_should_return_400_when_invalid_reference_data(self):
        """Test that invalid data returns 400."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.post(
                f'/sermon/{sermon_id}/references',
                json={'type': 'text', 'content': ''}  # Empty content
            )

            assert response.status_code == 400

    def test_should_return_204_when_deleting_reference(self):
        """Test that deleting reference returns 204."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO reference_materials (sermon_id, material_type, content) VALUES (?, ?, ?)",
                (sermon_id, 'text', 'A note')
            )
            conn.commit()
            ref_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.delete(f'/sermon/{sermon_id}/references/{ref_id}')

            assert response.status_code == 204

    def test_should_return_404_when_deleting_nonexistent_reference(self):
        """Test that deleting missing reference returns 404."""
        from app import create_app
        from database import init_db, get_db

        app = create_app({'TESTING': True, 'DATABASE': ':memory:'})

        with app.app_context():
            conn = get_db()
            init_db(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                ('Test Sermon', 'John 3:16')
            )
            conn.commit()
            sermon_id = cursor.lastrowid

        with app.test_client() as client:
            response = client.delete(f'/sermon/{sermon_id}/references/99999')

            assert response.status_code == 404
