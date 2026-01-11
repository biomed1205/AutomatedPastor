"""Sermon series database schema and operations.

Provides CRUD operations for managing sermon series and their associations.
"""


def create_series(conn, name, description=None, theme=None, start_date=None,
                  end_date=None, status='planning'):
    """Create a new sermon series.

    Args:
        conn: Database connection.
        name: Series name (required).
        description: Optional description.
        theme: Optional theme.
        start_date: Optional start date.
        end_date: Optional end date.
        status: Series status (default 'planning').

    Returns:
        int: ID of the created series.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO series (name, description, theme, start_date, end_date, status)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (name, description, theme, start_date, end_date, status)
    )
    conn.commit()
    return cursor.lastrowid


def get_series(conn, series_id):
    """Get a series by ID.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        dict: Series data, or None if not found.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, name, description, theme, start_date, end_date, status,
                  created_at, updated_at
           FROM series WHERE id = ?''',
        (series_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'name': row['name'] if hasattr(row, 'keys') else row[1],
        'description': row['description'] if hasattr(row, 'keys') else row[2],
        'theme': row['theme'] if hasattr(row, 'keys') else row[3],
        'start_date': row['start_date'] if hasattr(row, 'keys') else row[4],
        'end_date': row['end_date'] if hasattr(row, 'keys') else row[5],
        'status': row['status'] if hasattr(row, 'keys') else row[6],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[7],
        'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[8]
    }


def list_series(conn, status=None):
    """List all series, optionally filtered by status.

    Args:
        conn: Database connection.
        status: Optional status filter.

    Returns:
        list: List of series dictionaries.
    """
    cursor = conn.cursor()

    if status:
        cursor.execute(
            '''SELECT id, name, description, theme, start_date, end_date, status,
                      created_at, updated_at
               FROM series WHERE status = ?
               ORDER BY created_at DESC''',
            (status,)
        )
    else:
        cursor.execute(
            '''SELECT id, name, description, theme, start_date, end_date, status,
                      created_at, updated_at
               FROM series
               ORDER BY created_at DESC'''
        )

    rows = cursor.fetchall()
    result = []

    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'name': row['name'] if hasattr(row, 'keys') else row[1],
            'description': row['description'] if hasattr(row, 'keys') else row[2],
            'theme': row['theme'] if hasattr(row, 'keys') else row[3],
            'start_date': row['start_date'] if hasattr(row, 'keys') else row[4],
            'end_date': row['end_date'] if hasattr(row, 'keys') else row[5],
            'status': row['status'] if hasattr(row, 'keys') else row[6],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[7],
            'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[8]
        })

    return result


def update_series(conn, series_id, **kwargs):
    """Update a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        **kwargs: Fields to update (name, description, theme, start_date,
                  end_date, status).

    Returns:
        bool: True if updated, False if series not found.
    """
    if not kwargs:
        return False

    # Check if series exists
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        return False

    # Build update query
    allowed_fields = ['name', 'description', 'theme', 'start_date', 'end_date', 'status']
    fields_to_update = []
    values = []

    for field in allowed_fields:
        if field in kwargs:
            fields_to_update.append(f'{field} = ?')
            values.append(kwargs[field])

    if not fields_to_update:
        return False

    # Add updated_at
    fields_to_update.append('updated_at = CURRENT_TIMESTAMP')
    values.append(series_id)

    query = f'UPDATE series SET {", ".join(fields_to_update)} WHERE id = ?'  # nosec B608 - fields from whitelist
    cursor.execute(query, values)
    conn.commit()
    return True


def delete_series(conn, series_id):
    """Delete a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        bool: True if deleted, False if not found.
    """
    cursor = conn.cursor()

    # Check if series exists
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        return False

    # Delete associations first
    cursor.execute('DELETE FROM series_sermons WHERE series_id = ?', (series_id,))

    # Delete series
    cursor.execute('DELETE FROM series WHERE id = ?', (series_id,))
    conn.commit()
    return True


def add_sermon_to_series(conn, series_id, sermon_id, order=None):
    """Add a sermon to a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        sermon_id: ID of the sermon.
        order: Optional order position (auto-increments if not specified).

    Returns:
        bool: True if added, False if series not found or duplicate.
    """
    cursor = conn.cursor()

    # Check if series exists
    cursor.execute('SELECT id FROM series WHERE id = ?', (series_id,))
    if cursor.fetchone() is None:
        return False

    # Check for duplicate
    cursor.execute(
        'SELECT id FROM series_sermons WHERE series_id = ? AND sermon_id = ?',
        (series_id, sermon_id)
    )
    if cursor.fetchone() is not None:
        return False

    # Determine order
    if order is None:
        cursor.execute(
            'SELECT COALESCE(MAX(order_in_series), 0) + 1 as next_order FROM series_sermons WHERE series_id = ?',
            (series_id,)
        )
        row = cursor.fetchone()
        order = row['next_order'] if hasattr(row, 'keys') else row[0]

    # Insert association
    cursor.execute(
        'INSERT INTO series_sermons (series_id, sermon_id, order_in_series) VALUES (?, ?, ?)',
        (series_id, sermon_id, order)
    )
    conn.commit()
    return True


def remove_sermon_from_series(conn, series_id, sermon_id):
    """Remove a sermon from a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        sermon_id: ID of the sermon.

    Returns:
        bool: True if removed, False if association not found.
    """
    cursor = conn.cursor()

    # Check if association exists
    cursor.execute(
        'SELECT id FROM series_sermons WHERE series_id = ? AND sermon_id = ?',
        (series_id, sermon_id)
    )
    if cursor.fetchone() is None:
        return False

    # Delete association
    cursor.execute(
        'DELETE FROM series_sermons WHERE series_id = ? AND sermon_id = ?',
        (series_id, sermon_id)
    )
    conn.commit()
    return True


def get_sermons_in_series(conn, series_id):
    """Get all sermons in a series, ordered by position.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of sermon dictionaries with order info.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.manuscript, s.created_at,
                  ss.order_in_series
           FROM sermons s
           JOIN series_sermons ss ON s.id = ss.sermon_id
           WHERE ss.series_id = ?
           ORDER BY ss.order_in_series''',
        (series_id,)
    )
    rows = cursor.fetchall()
    result = []

    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'manuscript': row['manuscript'] if hasattr(row, 'keys') else row[3],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[4],
            'order_in_series': row['order_in_series'] if hasattr(row, 'keys') else row[5]
        })

    return result


def get_series_for_sermon(conn, sermon_id):
    """Get all series containing a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of series dictionaries.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT ser.id, ser.name, ser.description, ser.theme, ser.start_date,
                  ser.end_date, ser.status, ser.created_at, ser.updated_at
           FROM series ser
           JOIN series_sermons ss ON ser.id = ss.series_id
           WHERE ss.sermon_id = ?''',
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
            'start_date': row['start_date'] if hasattr(row, 'keys') else row[4],
            'end_date': row['end_date'] if hasattr(row, 'keys') else row[5],
            'status': row['status'] if hasattr(row, 'keys') else row[6],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[7],
            'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[8]
        })

    return result
