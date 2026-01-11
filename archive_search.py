"""Archive search and filter functionality module.

Provides comprehensive search and filtering capabilities for the sermon archive
including full-text search, date filters, scripture filters, and saved searches.
"""

import json
from datetime import datetime


def search_sermons(conn, query, **filters):
    """Search sermons with optional filters.

    Args:
        conn: Database connection.
        query: Search query string.
        **filters: Optional filters including:
            - start_date: Filter by start date.
            - end_date: Filter by end date.
            - scripture_book: Filter by scripture book.
            - status: Filter by status.
            - series_id: Filter by series ID.
            - sort_by: Sort field (date, title, scripture).
            - sort_order: Sort order (asc, desc).

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    # Handle empty query - return all sermons with filters applied
    if not query or not query.strip():
        return _get_filtered_sermons(conn, filters)

    # Use FTS for search
    try:
        # Search using FTS5
        cursor.execute(
            '''SELECT sermon_id FROM sermons_fts
               WHERE sermons_fts MATCH ?''',
            (query,)
        )
        fts_results = cursor.fetchall()
        sermon_ids = [row['sermon_id'] if hasattr(row, 'keys') else row[0]
                      for row in fts_results]
    except Exception:
        # Fallback to LIKE search if FTS fails
        sermon_ids = _fallback_search(conn, query)

    if not sermon_ids:
        return []

    # Build query with filters - placeholders are safe (just '?' repeated)
    placeholders = ','.join('?' * len(sermon_ids))
    query_sql = f'''SELECT id, title, scripture, scripture_book, content,
                           status, preached_date, series_id
                    FROM sermons
                    WHERE id IN ({placeholders})'''  # nosec B608
    params = list(sermon_ids)

    # Apply filters
    query_sql, params = _apply_filters(query_sql, params, filters)

    # Add sorting
    sort_by = filters.get('sort_by', 'date')
    sort_order = filters.get('sort_order')

    if sort_by == 'date':
        sort_col = 'preached_date'
        default_order = 'desc'
    elif sort_by == 'title':
        sort_col = 'title'
        default_order = 'asc'
    elif sort_by == 'scripture':
        sort_col = 'scripture'
        default_order = 'asc'
    else:
        sort_col = 'preached_date'
        default_order = 'desc'

    if sort_order is None:
        sort_order = default_order

    sort_dir = 'DESC' if sort_order == 'desc' else 'ASC'
    query_sql += f' ORDER BY {sort_col} {sort_dir}'

    cursor.execute(query_sql, params)
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def _get_filtered_sermons(conn, filters):
    """Get all sermons with filters applied."""
    cursor = conn.cursor()

    query_sql = '''SELECT id, title, scripture, scripture_book, content,
                          status, preached_date, series_id
                   FROM sermons WHERE 1=1'''
    params = []

    # Apply same filters as search_sermons
    query_sql, params = _apply_filters(query_sql, params, filters)
    query_sql += ' ORDER BY preached_date DESC'

    cursor.execute(query_sql, params)
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def _apply_filters(query_sql, params, filters):
    """Apply filter conditions to query."""
    if filters.get('start_date'):
        query_sql += ' AND preached_date >= ?'
        params.append(filters['start_date'])

    if filters.get('end_date'):
        query_sql += ' AND preached_date <= ?'
        params.append(filters['end_date'])

    if filters.get('scripture_book'):
        query_sql += ' AND LOWER(scripture_book) = LOWER(?)'
        params.append(filters['scripture_book'])

    if filters.get('status'):
        query_sql += ' AND status = ?'
        params.append(filters['status'])

    if filters.get('series_id'):
        query_sql += ' AND series_id = ?'
        params.append(filters['series_id'])

    return query_sql, params


def _fallback_search(conn, query):
    """Fallback LIKE search when FTS fails."""
    cursor = conn.cursor()
    pattern = f'%{query}%'

    cursor.execute(
        '''SELECT id FROM sermons
           WHERE title LIKE ? COLLATE NOCASE
              OR scripture LIKE ? COLLATE NOCASE
              OR content LIKE ? COLLATE NOCASE''',
        (pattern, pattern, pattern)
    )
    rows = cursor.fetchall()

    return [row['id'] if hasattr(row, 'keys') else row[0] for row in rows]


def _rows_to_dicts(rows):
    """Convert rows to list of dictionaries."""
    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': row['title'] if hasattr(row, 'keys') else row[1],
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'scripture_book': row['scripture_book'] if hasattr(row, 'keys') else row[3],
            'content': row['content'] if hasattr(row, 'keys') else row[4],
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'preached_date': row['preached_date'] if hasattr(row, 'keys') else row[6],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[7]
        })
    return result


def filter_by_date_range(conn, start_date=None, end_date=None):
    """Filter sermons by date range.

    Args:
        conn: Database connection.
        start_date: Optional start date (YYYY-MM-DD).
        end_date: Optional end date (YYYY-MM-DD).

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    # Validate date format if provided
    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return []

    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return []

    query_sql = '''SELECT id, title, scripture, scripture_book, content,
                          status, preached_date, series_id
                   FROM sermons WHERE 1=1'''
    params = []

    if start_date:
        query_sql += ' AND preached_date >= ?'
        params.append(start_date)

    if end_date:
        query_sql += ' AND preached_date <= ?'
        params.append(end_date)

    query_sql += ' ORDER BY preached_date DESC'

    cursor.execute(query_sql, params)
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def filter_by_scripture_book(conn, book):
    """Filter sermons by scripture book.

    Args:
        conn: Database connection.
        book: Scripture book name.

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, title, scripture, scripture_book, content,
                  status, preached_date, series_id
           FROM sermons
           WHERE LOWER(scripture_book) = LOWER(?)
           ORDER BY preached_date DESC''',
        (book,)
    )
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def filter_by_series(conn, series_id):
    """Filter sermons by series ID.

    Args:
        conn: Database connection.
        series_id: ID of the series.

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, title, scripture, scripture_book, content,
                  status, preached_date, series_id
           FROM sermons
           WHERE series_id = ?
           ORDER BY preached_date DESC''',
        (series_id,)
    )
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def filter_by_status(conn, status):
    """Filter sermons by status.

    Args:
        conn: Database connection.
        status: Sermon status.

    Returns:
        list: List of matching sermon dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, title, scripture, scripture_book, content,
                  status, preached_date, series_id
           FROM sermons
           WHERE status = ?
           ORDER BY preached_date DESC''',
        (status,)
    )
    rows = cursor.fetchall()

    return _rows_to_dicts(rows)


def search_with_highlighting(conn, query):
    """Search with highlighted matching text.

    Args:
        conn: Database connection.
        query: Search query string.

    Returns:
        list: List of results with highlighted snippets.
    """
    cursor = conn.cursor()

    if not query or not query.strip():
        return []

    try:
        # Use FTS5 highlight function
        cursor.execute(
            '''SELECT sermon_id,
                      highlight(sermons_fts, 0, '<mark>', '</mark>') as title_highlight,
                      highlight(sermons_fts, 2, '<mark>', '</mark>') as content_highlight,
                      snippet(sermons_fts, 2, '<mark>', '</mark>', '...', 20) as snippet
               FROM sermons_fts
               WHERE sermons_fts MATCH ?''',
            (query,)
        )
        fts_rows = cursor.fetchall()

        if not fts_rows:
            return []

        results = []
        for row in fts_rows:
            sermon_id = row['sermon_id'] if hasattr(row, 'keys') else row[0]
            title_highlight = row['title_highlight'] if hasattr(row, 'keys') else row[1]
            content_highlight = row['content_highlight'] if hasattr(row, 'keys') else row[2]
            snippet = row['snippet'] if hasattr(row, 'keys') else row[3]

            # Get full sermon data
            cursor.execute(
                '''SELECT id, title, scripture, scripture_book, content,
                          status, preached_date, series_id
                   FROM sermons WHERE id = ?''',
                (sermon_id,)
            )
            sermon_row = cursor.fetchone()

            if sermon_row:
                result = {
                    'id': sermon_row['id'] if hasattr(sermon_row, 'keys') else sermon_row[0],
                    'title': sermon_row['title'] if hasattr(sermon_row, 'keys') else sermon_row[1],
                    'scripture': sermon_row['scripture'] if hasattr(sermon_row, 'keys') else sermon_row[2],
                    'scripture_book': sermon_row['scripture_book'] if hasattr(sermon_row, 'keys') else sermon_row[3],
                    'content': sermon_row['content'] if hasattr(sermon_row, 'keys') else sermon_row[4],
                    'status': sermon_row['status'] if hasattr(sermon_row, 'keys') else sermon_row[5],
                    'preached_date': sermon_row['preached_date'] if hasattr(sermon_row, 'keys') else sermon_row[6],
                    'series_id': sermon_row['series_id'] if hasattr(sermon_row, 'keys') else sermon_row[7],
                    'highlight': title_highlight,
                    'snippet': snippet or content_highlight
                }
                results.append(result)

        return results

    except Exception:
        # Fallback to simple search
        return _fallback_highlighted_search(conn, query)


def _fallback_highlighted_search(conn, query):
    """Fallback search with simple highlighting."""
    cursor = conn.cursor()
    pattern = f'%{query}%'

    cursor.execute(
        '''SELECT id, title, scripture, scripture_book, content,
                  status, preached_date, series_id
           FROM sermons
           WHERE title LIKE ? COLLATE NOCASE
              OR content LIKE ? COLLATE NOCASE''',
        (pattern, pattern)
    )
    rows = cursor.fetchall()

    results = []
    for row in rows:
        title = row['title'] if hasattr(row, 'keys') else row[1]
        content = row['content'] if hasattr(row, 'keys') else row[4]

        # Create simple snippet around query
        snippet = _create_snippet(content, query)

        results.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'title': title,
            'scripture': row['scripture'] if hasattr(row, 'keys') else row[2],
            'scripture_book': row['scripture_book'] if hasattr(row, 'keys') else row[3],
            'content': content,
            'status': row['status'] if hasattr(row, 'keys') else row[5],
            'preached_date': row['preached_date'] if hasattr(row, 'keys') else row[6],
            'series_id': row['series_id'] if hasattr(row, 'keys') else row[7],
            'highlight': title,
            'snippet': snippet
        })

    return results


def _create_snippet(content, query):
    """Create a snippet around the query term."""
    if not content:
        return ""

    lower_content = content.lower()
    lower_query = query.lower()

    pos = lower_content.find(lower_query)
    if pos == -1:
        return content[:100] + '...' if len(content) > 100 else content

    start = max(0, pos - 50)
    end = min(len(content), pos + len(query) + 50)

    snippet = content[start:end]
    if start > 0:
        snippet = '...' + snippet
    if end < len(content):
        snippet = snippet + '...'

    return snippet


def get_search_suggestions(conn, partial_query, limit=10):
    """Get search suggestions based on partial query.

    Args:
        conn: Database connection.
        partial_query: Partial search query.
        limit: Maximum number of suggestions.

    Returns:
        list: List of suggestion strings.
    """
    cursor = conn.cursor()

    if not partial_query or not partial_query.strip():
        return []

    pattern = f'%{partial_query}%'
    suggestions = set()

    # Get matching titles
    cursor.execute(
        '''SELECT DISTINCT title FROM sermons
           WHERE title LIKE ? COLLATE NOCASE
           LIMIT ?''',
        (pattern, limit)
    )
    for row in cursor.fetchall():
        title = row['title'] if hasattr(row, 'keys') else row[0]
        suggestions.add(title)

    # Get matching scriptures
    cursor.execute(
        '''SELECT DISTINCT scripture FROM sermons
           WHERE scripture LIKE ? COLLATE NOCASE
           LIMIT ?''',
        (pattern, limit)
    )
    for row in cursor.fetchall():
        scripture = row['scripture'] if hasattr(row, 'keys') else row[0]
        if scripture:
            suggestions.add(scripture)

    # Convert to list and limit
    result = list(suggestions)[:limit]
    return result


def save_search_filter(conn, filter_name, filter_params, update_existing=False):
    """Save a search filter.

    Args:
        conn: Database connection.
        filter_name: Name for the saved filter.
        filter_params: Dictionary of filter parameters.
        update_existing: Whether to update if name exists.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Check if name exists
    cursor.execute(
        'SELECT id FROM saved_searches WHERE filter_name = ?',
        (filter_name,)
    )
    existing = cursor.fetchone()

    if existing and not update_existing:
        return {
            'success': False,
            'error': 'Filter name already exists'
        }

    params_json = json.dumps(filter_params)

    if existing and update_existing:
        # Update existing
        existing_id = existing['id'] if hasattr(existing, 'keys') else existing[0]
        cursor.execute(
            'UPDATE saved_searches SET filter_params = ? WHERE id = ?',
            (params_json, existing_id)
        )
        conn.commit()
        return {
            'success': True,
            'filter_id': existing_id,
            'updated': True
        }

    # Insert new
    cursor.execute(
        '''INSERT INTO saved_searches (filter_name, filter_params, created_at)
           VALUES (?, ?, ?)''',
        (filter_name, params_json, datetime.now().isoformat())
    )
    conn.commit()

    return {
        'success': True,
        'filter_id': cursor.lastrowid
    }


def load_saved_filter(conn, filter_name):
    """Load a saved search filter.

    Args:
        conn: Database connection.
        filter_name: Name of the saved filter.

    Returns:
        dict: Filter parameters, or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        'SELECT filter_params FROM saved_searches WHERE filter_name = ?',
        (filter_name,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    params_json = row['filter_params'] if hasattr(row, 'keys') else row[0]
    return json.loads(params_json)
