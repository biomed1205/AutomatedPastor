"""Sermon archive list view module.

Provides archive list view that organizes sermons by year and month.
Enables browsing complete history with pagination and search.
"""

import math


def get_archive_by_year(conn, year):
    """Get sermons for a specific year.

    Args:
        conn: Database connection.
        year: Year to filter by.

    Returns:
        list: List of sermon dictionaries ordered by date descending.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.preached_on, s.series_id, s.status,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE strftime('%Y', s.preached_on) = ?
             AND s.status = 'published'
             AND s.preached_on IS NOT NULL
           ORDER BY s.preached_on DESC''',
        (str(year),)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[3],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[6]
        })

    return result


def get_archive_by_month(conn, year, month):
    """Get sermons for a specific month.

    Args:
        conn: Database connection.
        year: Year to filter by.
        month: Month to filter by (1-12 or '01'-'12').

    Returns:
        list: List of sermon dictionaries ordered by date descending.
    """
    cursor = conn.cursor()

    # Handle month as int or string
    month_str = str(month).zfill(2)

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.preached_on, s.series_id, s.status,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE strftime('%Y', s.preached_on) = ?
             AND strftime('%m', s.preached_on) = ?
             AND s.status = 'published'
             AND s.preached_on IS NOT NULL
           ORDER BY s.preached_on DESC''',
        (str(year), month_str)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[3],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[6]
        })

    return result


def list_archive_years(conn):
    """List all years with sermons.

    Args:
        conn: Database connection.

    Returns:
        list: List of years with sermons, most recent first.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT DISTINCT strftime('%Y', preached_on) as year
           FROM sermons
           WHERE preached_on IS NOT NULL AND status = 'published'
           ORDER BY year DESC'''
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        year_str = row['year'] if hasattr(row, 'keys') else row[0]
        if year_str:
            result.append(int(year_str))

    return result


def list_archive_months(conn, year):
    """List months with sermons for a year.

    Args:
        conn: Database connection.
        year: Year to filter by.

    Returns:
        list: List of month dictionaries with counts.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT strftime('%m', preached_on) as month,
                  COUNT(*) as count
           FROM sermons
           WHERE strftime('%Y', preached_on) = ?
             AND preached_on IS NOT NULL
             AND status = 'published'
           GROUP BY month
           ORDER BY month DESC''',
        (str(year),)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        month_str = row['month'] if hasattr(row, 'keys') else row[0]
        count = row['count'] if hasattr(row, 'keys') else row[1]
        if month_str:
            result.append({
                'month': int(month_str),
                'month_str': month_str,
                'count': count,
                'sermon_count': count
            })

    return result


def get_archive_summary(conn):
    """Get archive overview summary.

    Args:
        conn: Database connection.

    Returns:
        dict: Summary with total count and year range.
    """
    cursor = conn.cursor()

    # Count total sermons
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons
           WHERE preached_on IS NOT NULL AND status = 'published' '''
    )
    row = cursor.fetchone()
    total = row['count'] if hasattr(row, 'keys') else row[0]

    # Get year range
    cursor.execute(
        '''SELECT MIN(strftime('%Y', preached_on)) as earliest,
                  MAX(strftime('%Y', preached_on)) as latest
           FROM sermons
           WHERE preached_on IS NOT NULL AND status = 'published' '''
    )
    row = cursor.fetchone()
    earliest = row['earliest'] if hasattr(row, 'keys') else row[0]
    latest = row['latest'] if hasattr(row, 'keys') else row[1]

    return {
        'total_sermons': total,
        'total': total,
        'earliest_year': int(earliest) if earliest else None,
        'first_year': int(earliest) if earliest else None,
        'latest_year': int(latest) if latest else None,
        'last_year': int(latest) if latest else None,
        'year_range': f"{earliest}-{latest}" if earliest and latest else None
    }


def get_archive_page(conn, page, per_page):
    """Get paginated sermon archive.

    Args:
        conn: Database connection.
        page: Page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        dict: Page with sermons and pagination metadata.
    """
    cursor = conn.cursor()

    # Get total count
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons
           WHERE preached_on IS NOT NULL AND status = 'published' '''
    )
    row = cursor.fetchone()
    total = row['count'] if hasattr(row, 'keys') else row[0]

    # Calculate pagination
    offset = (page - 1) * per_page
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0

    # Get sermons for page
    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.preached_on, s.series_id, s.status,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE s.preached_on IS NOT NULL AND s.status = 'published'
           ORDER BY s.preached_on DESC
           LIMIT ? OFFSET ?''',
        (per_page, offset)
    )
    rows = cursor.fetchall()

    sermons = []
    for row in rows:
        sermons.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[3],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[6]
        })

    return {
        'sermons': sermons,
        'items': sermons,
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_count': total,
        'pages': total_pages,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }


def search_archive(conn, query):
    """Search archive by title or scripture.

    Args:
        conn: Database connection.
        query: Search query string.

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    search_pattern = f'%{query}%'

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.preached_on, s.series_id, s.status,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE (s.title LIKE ? COLLATE NOCASE OR s.scripture LIKE ? COLLATE NOCASE)
             AND s.preached_on IS NOT NULL
             AND s.status = 'published'
           ORDER BY s.preached_on DESC''',
        (search_pattern, search_pattern)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[3],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[6]
        })

    return result


def get_recent_sermons(conn, limit):
    """Get most recent sermons.

    Args:
        conn: Database connection.
        limit: Maximum number of sermons to return.

    Returns:
        list: List of recent sermon dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT s.id, s.title, s.scripture, s.preached_on, s.series_id, s.status,
                  sr.name as series_name
           FROM sermons s
           LEFT JOIN series sr ON s.series_id = sr.id
           WHERE s.preached_on IS NOT NULL AND s.status = 'published'
           ORDER BY s.preached_on DESC
           LIMIT ?''',
        (limit,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'preached_on': row['preached_on'] if hasattr(row, 'keys') else row[3],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'series_name': row['series_name'] if hasattr(row, 'keys') else row[6]
        })

    return result
