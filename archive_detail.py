"""Archive detail view module.

Provides detail view for archived sermons showing complete information
including manuscript, feedback, and all related materials.
"""

from datetime import datetime


def get_archive_detail(conn, sermon_id):
    """Get full sermon detail.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Full sermon details, or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.manuscript, s.outline,
                  s.preached_on, s.series_id, s.status, s.created_at,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE s.id = ?''',
        (sermon_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'title': row['title'] if hasattr(row, 'keys') else row[1],
        'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
        'manuscript': row['manuscript'] if hasattr(row, 'keys') else row[3],
        'outline': row['outline'] if hasattr(row, 'keys') else row[4],
        'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[5],
        'series_id': row['series_id'] if hasattr(row, 'keys') else row[6],
        'status': row['status'] if hasattr(row, 'keys') else row[7],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[8],
        'series_name': row['series_name'] if hasattr(row, 'keys') else row[9]
    }


def get_archive_materials(conn, sermon_id):
    """Get all related materials for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Dictionary containing research notes and illustrations.
    """
    research = get_archive_research(conn, sermon_id)
    illustrations = get_archive_illustrations(conn, sermon_id)

    return {
        'research': research,
        'research_notes': research,
        'illustrations': illustrations,
        'total_materials': len(research) + len(illustrations)
    }


def get_archive_feedback(conn, sermon_id):
    """Get panel feedback for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of feedback dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, reviewer_name, feedback_text, feedback_type, created_at
           FROM panel_feedback
           WHERE sermon_id = ?
           ORDER BY created_at DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[2],
            'feedback_text': row['feedback_text'] if hasattr(row, 'keys') else row[3],
            'feedback_type': row['feedback_type'] if hasattr(row, 'keys') else row[4],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5]
        })

    return result


def get_archive_research(conn, sermon_id):
    """Get research notes for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of research note dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, note_type, title, content, source, created_at
           FROM research_notes
           WHERE sermon_id = ?
           ORDER BY created_at DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'note_type': row['note_type'] if hasattr(row, 'keys') else row[2],
            'title': row['title'] if hasattr(row, 'keys') else row[3],
            'content': row['content'] if hasattr(row, 'keys') else row[4],
            'source': row['source'] if hasattr(row, 'keys') else row[5],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def get_archive_illustrations(conn, sermon_id):
    """Get illustrations for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of illustration dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, description, source, section, created_at
           FROM illustrations
           WHERE sermon_id = ?
           ORDER BY created_at DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'description': row['description'] if hasattr(row, 'keys') else row[2],
            'source': row['source'] if hasattr(row, 'keys') else row[3],
            'section': row['section'] if hasattr(row, 'keys') else row[4],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5]
        })

    return result


def get_archive_versions(conn, sermon_id):
    """Get version history for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of version dictionaries ordered by version number descending.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, version_number, manuscript_text, author, created_at
           FROM sermon_versions
           WHERE sermon_id = ?
           ORDER BY version_number DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'version_number': row['version_number'] if hasattr(row, 'keys') else row[2],
            'manuscript_text': row['manuscript_text'] if hasattr(row, 'keys') else row[3],
            'author': row['author'] if hasattr(row, 'keys') else row[4],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[5]
        })

    return result


def get_scripture_references(conn, sermon_id):
    """Get all scripture references for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of scripture reference dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, reference, is_primary, context
           FROM scripture_references
           WHERE sermon_id = ?
           ORDER BY is_primary DESC, id''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'reference': row['reference'] if hasattr(row, 'keys') else row[2],
            'is_primary': bool(row['is_primary'] if hasattr(row, 'keys') else row[3]),
            'context': row['context'] if hasattr(row, 'keys') else row[4]
        })

    return result


def export_archive_bundle(conn, sermon_id):
    """Export complete archive bundle for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Complete bundle with all materials, or None if sermon not found.
    """
    # Get sermon detail
    sermon = get_archive_detail(conn, sermon_id)
    if sermon is None:
        return None

    # Get all related materials
    materials = get_archive_materials(conn, sermon_id)
    feedback = get_archive_feedback(conn, sermon_id)
    versions = get_archive_versions(conn, sermon_id)
    scripture_refs = get_scripture_references(conn, sermon_id)

    return {
        'sermon': sermon,
        'title': sermon['title'],
        'manuscript': sermon.get('manuscript'),
        'scripture': sermon.get('scripture'),
        'outline': sermon.get('outline'),
        'metadata': {
            'id': sermon['id'],
            'title': sermon['title'],
            'preached_on': sermon.get('preached_on'),
            'series_id': sermon.get('series_id'),
            'series_name': sermon.get('series_name'),
            'status': sermon.get('status'),
            'created_at': sermon.get('created_at')
        },
        'materials': materials,
        'feedback': feedback,
        'versions': versions,
        'scripture_references': scripture_refs,
        'exported_at': datetime.now().isoformat()
    }
