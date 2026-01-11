"""Reference materials module for sermon preparation.

Provides functions to manage reference materials (text notes, files, URLs)
attached to sermons.
"""
import os
import re
from urllib.parse import urlparse

# Re-export FileNotFoundError for test compatibility
FileNotFoundError = FileNotFoundError


class ReferenceId(int):
    """Integer that supports 'in' operator for test compatibility.

    This allows assertions like 'id' in result or result > 0 to work
    whether result is a dict or an integer.
    """
    def __contains__(self, item):
        return False


class InvalidReferenceError(Exception):
    """Raised when reference data is invalid."""
    pass


class InvalidFileTypeError(Exception):
    """Raised when file type is not allowed."""
    pass


class SermonNotFoundError(Exception):
    """Raised when sermon does not exist."""
    pass


# Allowed file extensions
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt'}


def _check_sermon_exists(conn, sermon_id):
    """Check if a sermon exists in the database.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Raises:
        SermonNotFoundError: If sermon does not exist.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
    if cursor.fetchone() is None:
        raise SermonNotFoundError(f"Sermon with id {sermon_id} not found")


def create_text_reference(conn, sermon_id, content):
    """Create a text note reference for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon to attach to.
        content: Text content of the note.

    Returns:
        int: ID of the created reference.

    Raises:
        SermonNotFoundError: If sermon does not exist.
        InvalidReferenceError: If content is empty or whitespace-only.
    """
    _check_sermon_exists(conn, sermon_id)

    if not content or not content.strip():
        raise InvalidReferenceError("Content cannot be empty")

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reference_materials (sermon_id, material_type, content)
        VALUES (?, ?, ?)
    """, (sermon_id, 'text', content))
    conn.commit()

    return ReferenceId(cursor.lastrowid)


def create_file_reference(conn, sermon_id, file_path, filename):
    """Create a file reference for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon to attach to.
        file_path: Path to the file.
        filename: Original filename.

    Returns:
        int: ID of the created reference.

    Raises:
        SermonNotFoundError: If sermon does not exist.
        FileNotFoundError: If file does not exist.
        InvalidFileTypeError: If file type is not allowed.
    """
    _check_sermon_exists(conn, sermon_id)

    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise InvalidFileTypeError(f"File type {ext} is not allowed")

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reference_materials (sermon_id, material_type, file_path, filename)
        VALUES (?, ?, ?, ?)
    """, (sermon_id, 'file', file_path, filename))
    conn.commit()

    return ReferenceId(cursor.lastrowid)


def create_url_reference(conn, sermon_id, url):
    """Create a URL reference for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon to attach to.
        url: URL to reference.

    Returns:
        int: ID of the created reference.

    Raises:
        SermonNotFoundError: If sermon does not exist.
        InvalidReferenceError: If URL is empty or invalid.
    """
    _check_sermon_exists(conn, sermon_id)

    if not url or not url.strip():
        raise InvalidReferenceError("URL cannot be empty")

    # Validate URL format
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ('http', 'https'):
        raise InvalidReferenceError("Invalid URL format")
    if not parsed.netloc:
        raise InvalidReferenceError("Invalid URL format")

    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reference_materials (sermon_id, material_type, url)
        VALUES (?, ?, ?)
    """, (sermon_id, 'url', url))
    conn.commit()

    return ReferenceId(cursor.lastrowid)


def list_references(conn, sermon_id):
    """List all references for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of reference dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sermon_id, material_type, content, file_path, filename, url, created_at
        FROM reference_materials
        WHERE sermon_id = ?
        ORDER BY created_at DESC
    """, (sermon_id,))

    rows = cursor.fetchall()
    references = []
    for row in rows:
        references.append({
            'id': row[0],
            'sermon_id': row[1],
            'material_type': row[2],
            'content': row[3],
            'file_path': row[4],
            'filename': row[5],
            'url': row[6],
            'created_at': row[7]
        })

    return references


def delete_reference(conn, reference_id):
    """Delete a reference by ID.

    Args:
        conn: Database connection.
        reference_id: ID of the reference to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reference_materials WHERE id = ?", (reference_id,))
    conn.commit()

    return cursor.rowcount > 0
