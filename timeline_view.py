"""Visual timeline view for sermon series.

Provides functions for displaying schedule and tracking sermon series progress.
"""


def get_timeline_data(conn, series_id):
    """Get timeline data for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        dict: Timeline data with series info and sermon slots, or None if not found.
    """
    cursor = conn.cursor()

    # Get series info
    cursor.execute(
        '''SELECT id, name, description, theme, start_date, end_date, status
           FROM series WHERE id = ?''',
        (series_id,)
    )
    series_row = cursor.fetchone()

    if series_row is None:
        return None

    # Get sermon slots
    cursor.execute(
        '''SELECT id, slot_number, title, scripture, planned_date, actual_date, status
           FROM sermon_slots
           WHERE series_id = ?
           ORDER BY slot_number''',
        (series_id,)
    )
    slot_rows = cursor.fetchall()

    sermons = []
    for row in slot_rows:
        sermons.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'slot_number': row['slot_number'] if hasattr(row, 'keys') else row[1],
            'title': row['title'] if hasattr(row, 'keys') else row[2],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[3],
            'planned_date': row['planned_date'] if hasattr(row, 'keys') else row[4],
            'actual_date': row['actual_date'] if hasattr(row, 'keys') else row[5],
            'status': row['status'] if hasattr(row, 'keys') else row[6]
        })

    return {
        'series_id': series_row['id'] if hasattr(series_row, 'keys') else series_row[0],
        'series_name': series_row['name'] if hasattr(series_row, 'keys') else series_row[1],
        'name': series_row['name'] if hasattr(series_row, 'keys') else series_row[1],
        'description': series_row['description'] if hasattr(series_row, 'keys') else series_row[2],
        'theme': series_row['theme'] if hasattr(series_row, 'keys') else series_row[3],
        'start_date': series_row['start_date'] if hasattr(series_row, 'keys') else series_row[4],
        'end_date': series_row['end_date'] if hasattr(series_row, 'keys') else series_row[5],
        'status': series_row['status'] if hasattr(series_row, 'keys') else series_row[6],
        'sermons': sermons
    }


def get_upcoming_sermons(conn, series_id, limit=5):
    """Get upcoming (not completed) sermons for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        limit: Maximum number of sermons to return.

    Returns:
        list: List of upcoming sermon dictionaries ordered by planned date.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, slot_number, title, scripture, planned_date, actual_date, status
           FROM sermon_slots
           WHERE series_id = ? AND status != 'completed'
           ORDER BY planned_date
           LIMIT ?''',
        (series_id, limit)
    )
    rows = cursor.fetchall()

    sermons = []
    for row in rows:
        sermons.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'slot_number': row['slot_number'] if hasattr(row, 'keys') else row[1],
            'title': row['title'] if hasattr(row, 'keys') else row[2],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[3],
            'planned_date': row['planned_date'] if hasattr(row, 'keys') else row[4],
            'actual_date': row['actual_date'] if hasattr(row, 'keys') else row[5],
            'status': row['status'] if hasattr(row, 'keys') else row[6]
        })

    return sermons


def get_completed_sermons(conn, series_id):
    """Get completed sermons for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of completed sermon dictionaries ordered by actual date.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, slot_number, title, scripture, planned_date, actual_date, status
           FROM sermon_slots
           WHERE series_id = ? AND status = 'completed'
           ORDER BY actual_date''',
        (series_id,)
    )
    rows = cursor.fetchall()

    sermons = []
    for row in rows:
        sermons.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'slot_number': row['slot_number'] if hasattr(row, 'keys') else row[1],
            'title': row['title'] if hasattr(row, 'keys') else row[2],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[3],
            'planned_date': row['planned_date'] if hasattr(row, 'keys') else row[4],
            'actual_date': row['actual_date'] if hasattr(row, 'keys') else row[5],
            'status': row['status'] if hasattr(row, 'keys') else row[6]
        })

    return sermons


def calculate_series_progress(conn, series_id):
    """Calculate series progress as percentage.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        int: Progress percentage (0-100).
    """
    cursor = conn.cursor()

    # Get total count
    cursor.execute(
        'SELECT COUNT(*) as total FROM sermon_slots WHERE series_id = ?',
        (series_id,)
    )
    total = cursor.fetchone()
    total_count = total['total'] if hasattr(total, 'keys') else total[0]

    if total_count == 0:
        return 0

    # Get completed count
    cursor.execute(
        '''SELECT COUNT(*) as completed FROM sermon_slots
           WHERE series_id = ? AND status = 'completed' ''',
        (series_id,)
    )
    completed = cursor.fetchone()
    completed_count = completed['completed'] if hasattr(completed, 'keys') else completed[0]

    return int((completed_count / total_count) * 100)


def get_timeline_for_date_range(conn, start, end):
    """Get all timeline items within a date range.

    Args:
        conn: Database connection.
        start: Start date (ISO format string).
        end: End date (ISO format string).

    Returns:
        list: List of sermon slot dictionaries within the range.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT ss.id, ss.series_id, ss.slot_number, ss.title, ss.scripture,
                  ss.planned_date, ss.actual_date, ss.status, s.name as series_name
           FROM sermon_slots ss
           JOIN series s ON ss.series_id = s.id
           WHERE ss.planned_date >= ? AND ss.planned_date <= ?
           ORDER BY ss.planned_date''',
        (start, end)
    )
    rows = cursor.fetchall()

    items = []
    for row in rows:
        items.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[1],
            'slot_number': row['slot_number'] if hasattr(row, 'keys') else row[2],
            'title': row['title'] if hasattr(row, 'keys') else row[3],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[4],
            'planned_date': row['planned_date'] if hasattr(row, 'keys') else row[5],
            'actual_date': row['actual_date'] if hasattr(row, 'keys') else row[6],
            'status': row['status'] if hasattr(row, 'keys') else row[7],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[8]
        })

    return items


def mark_sermon_complete(conn, sermon_id, actual_date):
    """Mark a sermon slot as complete.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon slot.
        actual_date: Actual date the sermon was delivered (ISO format).

    Returns:
        bool: True if marked complete, False if sermon not found.
    """
    cursor = conn.cursor()

    # Check if sermon exists
    cursor.execute('SELECT id FROM sermon_slots WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        return False

    # Mark as complete
    cursor.execute(
        '''UPDATE sermon_slots
           SET status = 'completed', actual_date = ?
           WHERE id = ?''',
        (actual_date, sermon_id)
    )
    conn.commit()
    return True


def get_series_milestones(conn, series_id):
    """Get milestones for a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of milestone dictionaries ordered by date.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''SELECT id, name, milestone_date, description, completed
           FROM series_milestones
           WHERE series_id = ?
           ORDER BY milestone_date''',
        (series_id,)
    )
    rows = cursor.fetchall()

    milestones = []
    for row in rows:
        milestones.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'name': row['name'] if hasattr(row, 'keys') else row[1],
            'milestone_date': row['milestone_date'] if hasattr(row, 'keys') else row[2],
            'description': row['description'] if hasattr(row, 'keys') else row[3],
            'completed': bool(row['completed'] if hasattr(row, 'keys') else row[4])
        })

    return milestones


def add_milestone(conn, series_id, name, milestone_date, description=None):
    """Add a milestone to a series.

    Args:
        conn: Database connection.
        series_id: ID of the series.
        name: Milestone name.
        milestone_date: Date for the milestone (ISO format).
        description: Optional description.

    Returns:
        int: ID of the created milestone.
    """
    cursor = conn.cursor()
    cursor.execute(
        '''INSERT INTO series_milestones (series_id, name, milestone_date, description)
           VALUES (?, ?, ?, ?)''',
        (series_id, name, milestone_date, description)
    )
    conn.commit()
    return cursor.lastrowid
