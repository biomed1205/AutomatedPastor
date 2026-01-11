"""Version history tracking module.

Provides version history system for sermon drafts with revision tracking,
comparison, and restoration capabilities.
"""

import difflib


def create_version(conn, sermon_id, text, author=None):
    """Create a new version for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        text: Full manuscript text for this version.
        author: Optional author name.

    Returns:
        int: ID of the created version, or None if invalid.
    """
    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        return None

    # Get next version number
    cursor.execute(
        'SELECT COALESCE(MAX(version_number), 0) + 1 as next_num FROM sermon_versions WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    next_version = row['next_num'] if hasattr(row, 'keys') else row[0]

    # Insert version
    cursor.execute(
        '''INSERT INTO sermon_versions (sermon_id, version_number, manuscript_text, author)
           VALUES (?, ?, ?, ?)''',
        (sermon_id, next_version, text, author)
    )
    conn.commit()
    return cursor.lastrowid


def get_version(conn, version_id):
    """Get a specific version by ID.

    Args:
        conn: Database connection.
        version_id: ID of the version.

    Returns:
        dict: Version details, or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, version_number, manuscript_text, author, change_summary, created_at
           FROM sermon_versions WHERE id = ?''',
        (version_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
        'version_number': row['version_number'] if hasattr(row, 'keys') else row[2],
        'manuscript_text': row['manuscript_text'] if hasattr(row, 'keys') else row[3],
        'author': row['author'] if hasattr(row, 'keys') else row[4],
        'change_summary': row['change_summary'] if hasattr(row, 'keys') else row[5],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[6]
    }


def list_versions(conn, sermon_id):
    """List all versions for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of version dictionaries, newest first.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, version_number, manuscript_text, author, change_summary, created_at
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
            'change_summary': row['change_summary'] if hasattr(row, 'keys') else row[5],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[6]
        })

    return result


def get_latest_version(conn, sermon_id):
    """Get the most recent version for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Latest version details, or None if no versions exist.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, version_number, manuscript_text, author, change_summary, created_at
           FROM sermon_versions
           WHERE sermon_id = ?
           ORDER BY version_number DESC
           LIMIT 1''',
        (sermon_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
        'version_number': row['version_number'] if hasattr(row, 'keys') else row[2],
        'manuscript_text': row['manuscript_text'] if hasattr(row, 'keys') else row[3],
        'author': row['author'] if hasattr(row, 'keys') else row[4],
        'change_summary': row['change_summary'] if hasattr(row, 'keys') else row[5],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[6]
    }


def compare_versions(conn, version_id_1, version_id_2):
    """Compare two versions and return diff.

    Args:
        conn: Database connection.
        version_id_1: ID of the first version.
        version_id_2: ID of the second version.

    Returns:
        dict: Diff structure with additions, deletions, and unified diff.
    """
    v1 = get_version(conn, version_id_1)
    v2 = get_version(conn, version_id_2)

    if v1 is None or v2 is None:
        return None

    text1 = v1['manuscript_text'].splitlines(keepends=True)
    text2 = v2['manuscript_text'].splitlines(keepends=True)

    # Generate unified diff
    diff_lines = list(difflib.unified_diff(
        text1, text2,
        fromfile=f'Version {v1["version_number"]}',
        tofile=f'Version {v2["version_number"]}'
    ))

    # Count additions and deletions
    additions = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
    deletions = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))

    return {
        'version_1': v1['version_number'],
        'version_2': v2['version_number'],
        'diff': ''.join(diff_lines),
        'diff_lines': diff_lines,
        'additions': additions,
        'deletions': deletions,
        'has_changes': len(diff_lines) > 0
    }


def restore_version(conn, sermon_id, version_id):
    """Restore a previous version as a new version.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        version_id: ID of the version to restore.

    Returns:
        bool: True if restored, False if invalid.
    """
    # Get the version to restore
    version = get_version(conn, version_id)

    if version is None:
        return False

    # Verify version belongs to the specified sermon
    if version['sermon_id'] != sermon_id:
        return False

    # Create new version with the restored content
    new_version_id = create_version(
        conn,
        sermon_id,
        version['manuscript_text'],
        author=f"Restored from v{version['version_number']}"
    )

    return new_version_id is not None


def delete_version(conn, version_id):
    """Delete a version.

    Args:
        conn: Database connection.
        version_id: ID of the version to delete.

    Returns:
        bool: True if deleted, False if not found.
    """
    cursor = conn.cursor()

    # Check version exists
    cursor.execute('SELECT id FROM sermon_versions WHERE id = ?', (version_id,))
    row = cursor.fetchone()
    if row is None:
        return False

    # Delete the version
    cursor.execute('DELETE FROM sermon_versions WHERE id = ?', (version_id,))
    conn.commit()
    return True


def get_version_count(conn, sermon_id):
    """Get the count of versions for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        int: Number of versions.
    """
    cursor = conn.cursor()

    cursor.execute(
        'SELECT COUNT(*) as count FROM sermon_versions WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    return row['count'] if hasattr(row, 'keys') else row[0]
