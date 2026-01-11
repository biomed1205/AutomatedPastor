"""Sermon-series link management module.

Provides UI and API functions for managing sermon-series associations.
"""


def validate_sermon_series_link(conn, sermon_id, series_id):
    """Validate a sermon-series link before creating.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        series_id: ID of the series.

    Returns:
        list: List of error messages, empty if valid.
    """
    errors = []
    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        errors.append('Sermon not found')

    # Check series exists
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        errors.append('Series not found')

    # Check for existing link
    cursor.execute(
        '''SELECT id FROM sermon_series_link
           WHERE sermon_id = ? AND series_id = ?''',
        (sermon_id, series_id)
    )
    if cursor.fetchone() is not None:
        errors.append('Link already exists')

    return errors


def link_sermon_to_series_ui(conn, sermon_id, series_id):
    """Link a sermon to a series via UI.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        series_id: ID of the series.

    Returns:
        dict: Response with success status and link_id or error.
    """
    # Validate first
    errors = validate_sermon_series_link(conn, sermon_id, series_id)

    if errors:
        if 'already exists' in errors[0].lower():
            return {'success': False, 'already_linked': True, 'message': errors[0]}
        return {'success': False, 'error': errors[0], 'message': errors[0]}

    cursor = conn.cursor()

    # Get next position
    cursor.execute(
        '''SELECT COALESCE(MAX(position), 0) + 1 as next_pos
           FROM sermon_series_link WHERE series_id = ?''',
        (series_id,)
    )
    row = cursor.fetchone()
    next_pos = row['next_pos'] if hasattr(row, 'keys') else row[0]

    # Create link
    cursor.execute(
        '''INSERT INTO sermon_series_link (sermon_id, series_id, position)
           VALUES (?, ?, ?)''',
        (sermon_id, series_id, next_pos)
    )
    link_id = cursor.lastrowid

    # Update series sermon count
    cursor.execute(
        'UPDATE series SET sermon_count = sermon_count + 1 WHERE id = ?',
        (series_id,)
    )

    conn.commit()
    return {'success': True, 'link_id': link_id, 'id': link_id, 'position': next_pos}


def unlink_sermon_from_series_ui(conn, sermon_id, series_id):
    """Unlink a sermon from a series via UI.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        series_id: ID of the series.

    Returns:
        dict: Response with success status or error.
    """
    cursor = conn.cursor()

    # Check if link exists
    cursor.execute(
        '''SELECT id FROM sermon_series_link
           WHERE sermon_id = ? AND series_id = ?''',
        (sermon_id, series_id)
    )
    if cursor.fetchone() is None:
        return {'success': False, 'error': 'Link not found', 'message': 'Link not found'}

    # Delete link
    cursor.execute(
        '''DELETE FROM sermon_series_link
           WHERE sermon_id = ? AND series_id = ?''',
        (sermon_id, series_id)
    )

    # Update series sermon count
    cursor.execute(
        'UPDATE series SET sermon_count = sermon_count - 1 WHERE id = ? AND sermon_count > 0',
        (series_id,)
    )

    conn.commit()
    return {'success': True}


def get_linkable_series(conn, sermon_id):
    """Get series available for linking to a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of available series dictionaries.
    """
    cursor = conn.cursor()

    # Get all series not already linked to this sermon
    cursor.execute(
        '''SELECT s.id, s.name, s.description, s.theme, s.status
           FROM series s
           WHERE s.id NOT IN (
               SELECT series_id FROM sermon_series_link WHERE sermon_id = ?
           )
           ORDER BY s.name''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'name': row['name'] if hasattr(row, 'keys') else row[1],
            'description': row['description'] if hasattr(row, 'keys') else row[2],
            'theme': row['theme'] if hasattr(row, 'keys') else row[3],
            'status': row['status'] if hasattr(row, 'keys') else row[4]
        })

    return result


def reorder_sermon_in_series(conn, sermon_id, series_id, new_position):
    """Reorder a sermon within a series.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        series_id: ID of the series.
        new_position: New position for the sermon.

    Returns:
        bool: True if reordered, False if sermon not linked.
    """
    cursor = conn.cursor()

    # Check if link exists
    cursor.execute(
        '''SELECT id, position FROM sermon_series_link
           WHERE sermon_id = ? AND series_id = ?''',
        (sermon_id, series_id)
    )
    row = cursor.fetchone()
    if row is None:
        return False

    link_id = row['id'] if hasattr(row, 'keys') else row[0]

    # Handle negative position - fail
    if new_position < 0:
        return False

    # Update position
    cursor.execute(
        'UPDATE sermon_series_link SET position = ? WHERE id = ?',
        (new_position, link_id)
    )
    conn.commit()
    return True


def get_sermon_series_info(conn, sermon_id):
    """Get series context for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of series info dictionaries, or empty list if unlinked.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT s.id, s.name, s.description, s.theme, s.status, ssl.position
           FROM series s
           JOIN sermon_series_link ssl ON s.id = ssl.series_id
           WHERE ssl.sermon_id = ?
           ORDER BY ssl.linked_at''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        return []

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'name': row['name'] if hasattr(row, 'keys') else row[1],
            'series_name': row['name'] if hasattr(row, 'keys') else row[1],
            'description': row['description'] if hasattr(row, 'keys') else row[2],
            'theme': row['theme'] if hasattr(row, 'keys') else row[3],
            'status': row['status'] if hasattr(row, 'keys') else row[4],
            'position': row['position'] if hasattr(row, 'keys') else row[5]
        })

    return result


def bulk_link_sermons(conn, sermon_ids, series_id):
    """Bulk link multiple sermons to a series.

    Args:
        conn: Database connection.
        sermon_ids: List of sermon IDs.
        series_id: ID of the series.

    Returns:
        dict: Results with success_count, failed_count, and details.
    """
    if not sermon_ids:
        return {
            'success': True,
            'success_count': 0,
            'linked': 0,
            'failed_count': 0,
            'details': []
        }

    # Check if series exists
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        return {
            'success': False,
            'success_count': 0,
            'linked': 0,
            'failed_count': len(sermon_ids),
            'error': 'Series not found'
        }

    success_count = 0
    failed_count = 0
    details = []

    for sermon_id in sermon_ids:
        response = link_sermon_to_series_ui(conn, sermon_id, series_id)
        if response.get('success'):
            success_count += 1
            details.append({'sermon_id': sermon_id, 'status': 'linked'})
        else:
            failed_count += 1
            details.append({
                'sermon_id': sermon_id,
                'status': 'failed',
                'reason': response.get('error', response.get('message', 'Unknown'))
            })

    return {
        'success': success_count > 0,
        'success_count': success_count,
        'linked': success_count,
        'failed_count': failed_count,
        'details': details
    }
