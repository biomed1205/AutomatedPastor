"""Post-sermon notes functionality module.

Provides ability for pastors to add notes after preaching,
including reflections on what worked, congregation response,
and improvements for next time.
"""

from datetime import datetime


# Valid note types
VALID_NOTE_TYPES = ['what_worked', 'improve', 'congregation_response', 'general']


def add_post_note(conn, sermon_id, note_type, content):
    """Add a post-sermon note.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        note_type: Type of note (what_worked, improve, congregation_response, general).
        content: Note content.

    Returns:
        dict: Result with success status and note_id.
    """
    # Validate note type
    if note_type not in VALID_NOTE_TYPES:
        return {
            'success': False,
            'error': f'Invalid note type. Must be one of: {", ".join(VALID_NOTE_TYPES)}'
        }

    # Validate content
    if not content or not content.strip():
        return {
            'success': False,
            'error': 'Note content cannot be empty'
        }

    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id, status, preached_date FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    if row is None:
        return {
            'success': False,
            'error': 'Sermon not found'
        }

    status = row['status'] if hasattr(row, 'keys') else row[1]
    preached_date = row['preached_date'] if hasattr(row, 'keys') else row[2]

    # Check if sermon is preached
    result = {'success': True}
    if status != 'preached' or preached_date is None:
        result['warning'] = 'Sermon has not been preached yet'

    # Insert note
    created_at = datetime.now().isoformat()
    cursor.execute(
        '''INSERT INTO post_sermon_notes (sermon_id, note_type, content, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?)''',
        (sermon_id, note_type, content, created_at, created_at)
    )
    conn.commit()

    result['note_id'] = cursor.lastrowid
    result['created_at'] = created_at
    return result


def get_post_notes(conn, sermon_id):
    """Get all post notes for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of note dictionaries ordered by creation time.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, note_type, content, section_name, created_at, updated_at
           FROM post_sermon_notes
           WHERE sermon_id = ?
           ORDER BY id ASC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'note_type': row['note_type'] if hasattr(row, 'keys') else row[2],
            'content': row['content'] if hasattr(row, 'keys') else row[3],
            'section_name': row['section_name'] if hasattr(row, 'keys') else row[4],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5],
            'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def update_post_note(conn, note_id, content):
    """Update a post-sermon note.

    Args:
        conn: Database connection.
        note_id: ID of the note.
        content: New content.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check note exists
    cursor.execute('SELECT id FROM post_sermon_notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    if row is None:
        return {
            'success': False,
            'error': 'Note not found'
        }

    # Update note
    updated_at = datetime.now().isoformat()
    cursor.execute(
        'UPDATE post_sermon_notes SET content = ?, updated_at = ? WHERE id = ?',
        (content, updated_at, note_id)
    )
    conn.commit()

    return {
        'success': True,
        'note_id': note_id,
        'updated_at': updated_at
    }


def delete_post_note(conn, note_id):
    """Delete a post-sermon note.

    Args:
        conn: Database connection.
        note_id: ID of the note.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check note exists
    cursor.execute('SELECT id FROM post_sermon_notes WHERE id = ?', (note_id,))
    row = cursor.fetchone()
    if row is None:
        return {
            'success': False,
            'error': 'Note not found'
        }

    # Delete note
    cursor.execute('DELETE FROM post_sermon_notes WHERE id = ?', (note_id,))
    conn.commit()

    return {
        'success': True,
        'note_id': note_id
    }


def get_notes_by_type(conn, sermon_id, note_type):
    """Get notes filtered by type.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        note_type: Type of notes to retrieve.

    Returns:
        list: List of note dictionaries of the specified type.
    """
    # Validate note type
    if note_type not in VALID_NOTE_TYPES:
        return []

    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, note_type, content, section_name, created_at, updated_at
           FROM post_sermon_notes
           WHERE sermon_id = ? AND note_type = ?
           ORDER BY id ASC''',
        (sermon_id, note_type)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'note_type': row['note_type'] if hasattr(row, 'keys') else row[2],
            'content': row['content'] if hasattr(row, 'keys') else row[3],
            'section_name': row['section_name'] if hasattr(row, 'keys') else row[4],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5],
            'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def add_section_note(conn, sermon_id, section_name, content):
    """Add a note linked to a sermon section.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        section_name: Name of the section.
        content: Note content.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check section exists
    cursor.execute(
        'SELECT id FROM sermon_sections WHERE sermon_id = ? AND section_name = ?',
        (sermon_id, section_name)
    )
    row = cursor.fetchone()
    if row is None:
        return {
            'success': False,
            'error': 'Section not found'
        }

    # Insert note with section
    created_at = datetime.now().isoformat()
    cursor.execute(
        '''INSERT INTO post_sermon_notes (sermon_id, note_type, content, section_name, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (sermon_id, 'general', content, section_name, created_at, created_at)
    )
    conn.commit()

    return {
        'success': True,
        'note_id': cursor.lastrowid,
        'section_name': section_name,
        'created_at': created_at
    }


def get_section_notes(conn, sermon_id):
    """Get all notes organized by section.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Dictionary with section names as keys and lists of notes as values.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, note_type, content, section_name, created_at, updated_at
           FROM post_sermon_notes
           WHERE sermon_id = ? AND section_name IS NOT NULL
           ORDER BY section_name, id ASC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = {}
    for row in rows:
        section = row['section_name'] if hasattr(row, 'keys') else row[4]
        if section not in result:
            result[section] = []

        result[section].append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'note_type': row['note_type'] if hasattr(row, 'keys') else row[2],
            'content': row['content'] if hasattr(row, 'keys') else row[3],
            'section_name': section,
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5],
            'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def export_post_notes(conn, sermon_id):
    """Export all notes for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Export bundle with notes organized by type and section, or None if sermon not found.
    """
    cursor = conn.cursor()

    # Get sermon
    cursor.execute(
        'SELECT id, title, preached_date FROM sermons WHERE id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None

    sermon_title = row['title'] if hasattr(row, 'keys') else row[1]
    preached_date = row['preached_date'] if hasattr(row, 'keys') else row[2]

    # Get all notes
    notes = get_post_notes(conn, sermon_id)

    # Organize by type
    by_type = {}
    for note in notes:
        note_type = note['note_type']
        if note_type not in by_type:
            by_type[note_type] = []
        by_type[note_type].append(note)

    # Organize by section
    by_section = get_section_notes(conn, sermon_id)

    return {
        'sermon_id': sermon_id,
        'sermon_title': sermon_title,
        'preached_date': preached_date,
        'notes': notes,
        'by_type': by_type,
        'by_section': by_section,
        'exported_at': datetime.now().isoformat()
    }
