"""Theme/scripture usage tracking functionality module.

Provides tracking of themes and scripture passages used in sermons
to help maintain variety and identify coverage gaps.
"""

import re
from datetime import datetime


def _parse_scripture_passage(passage):
    """Parse a scripture passage to extract book name.

    Args:
        passage: Scripture reference like "John 3:16" or "1 Corinthians 13"

    Returns:
        tuple: (book, chapter) or (None, None) if invalid
    """
    # Pattern for scripture: Book Name Chapter:Verse or Book Name Chapter
    pattern = r'^(\d?\s?[A-Za-z]+)\s+(\d+)'
    match = re.match(pattern, passage.strip())

    if match:
        book = match.group(1).strip()
        chapter = int(match.group(2))
        return book, chapter

    return None, None


def track_scripture_usage(conn, sermon_id, passage, is_primary=False):
    """Track scripture passage usage in a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        passage: Scripture passage reference.
        is_primary: Whether this is the primary passage.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Parse passage
    book, chapter = _parse_scripture_passage(passage)

    if book is None:
        return {'success': False, 'warning': 'Invalid passage format'}

    # Get sermon preached_date
    cursor.execute('SELECT preached_date FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    if row is None:
        return {'success': False, 'error': 'Sermon not found'}

    used_date = (row['preached_date'] if hasattr(row, 'keys') else row[0]) or datetime.now().strftime('%Y-%m-%d')

    # Insert usage record
    cursor.execute(
        '''INSERT INTO scripture_usage (sermon_id, passage, book, chapter, is_primary, used_date)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (sermon_id, passage, book, chapter, 1 if is_primary else 0, used_date)
    )
    conn.commit()

    return {'success': True}


def track_theme_usage(conn, sermon_id, theme, is_primary=False):
    """Track theme usage in a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        theme: Theme name.
        is_primary: Whether this is the primary theme.

    Returns:
        dict: Result with success status.
    """
    cursor = conn.cursor()

    # Normalize theme
    normalized_theme = theme.strip().lower()

    # Get sermon preached_date
    cursor.execute('SELECT preached_date FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    if row is None:
        return {'success': False, 'error': 'Sermon not found'}

    used_date = (row['preached_date'] if hasattr(row, 'keys') else row[0]) or datetime.now().strftime('%Y-%m-%d')

    # Insert usage record
    cursor.execute(
        '''INSERT INTO theme_usage (sermon_id, theme, is_primary, used_date)
           VALUES (?, ?, ?, ?)''',
        (sermon_id, normalized_theme, 1 if is_primary else 0, used_date)
    )
    conn.commit()

    return {'success': True}


def get_scripture_frequency(conn, book=None):
    """Get frequency of scripture book usage.

    Args:
        conn: Database connection.
        book: Optional book to filter by.

    Returns:
        list: List of dicts with book and count, ordered by frequency.
    """
    cursor = conn.cursor()

    if book:
        cursor.execute(
            '''SELECT book, COUNT(*) as count
               FROM scripture_usage
               WHERE book = ?
               GROUP BY book
               ORDER BY count DESC''',
            (book,)
        )
    else:
        cursor.execute(
            '''SELECT book, COUNT(*) as count
               FROM scripture_usage
               GROUP BY book
               ORDER BY count DESC'''
        )

    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'book': row['book'] if hasattr(row, 'keys') else row[0],
            'count': row['count'] if hasattr(row, 'keys') else row[1]
        })

    return result


def get_theme_frequency(conn):
    """Get frequency of theme usage.

    Args:
        conn: Database connection.

    Returns:
        list: List of dicts with theme, count, and last_used.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT theme, COUNT(*) as count, MAX(used_date) as last_used
           FROM theme_usage
           GROUP BY theme
           ORDER BY count DESC'''
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'theme': row['theme'] if hasattr(row, 'keys') else row[0],
            'count': row['count'] if hasattr(row, 'keys') else row[1],
            'last_used': row['last_used'] if hasattr(row, 'keys') else row[2]
        })

    return result


def get_uncovered_books(conn, testament=None):
    """Get Bible books never preached from.

    Args:
        conn: Database connection.
        testament: Optional testament filter ('OT' or 'NT').

    Returns:
        list: List of uncovered book dicts.
    """
    cursor = conn.cursor()

    # Get all used books
    cursor.execute('SELECT DISTINCT book FROM scripture_usage')
    used_rows = cursor.fetchall()
    used_books = set(row['book'] if hasattr(row, 'keys') else row[0] for row in used_rows)

    # Get all Bible books
    if testament:
        cursor.execute(
            '''SELECT name, testament, book_order
               FROM bible_books
               WHERE testament = ?
               ORDER BY book_order''',
            (testament,)
        )
    else:
        cursor.execute(
            '''SELECT name, testament, book_order
               FROM bible_books
               ORDER BY book_order'''
        )

    rows = cursor.fetchall()

    result = []
    for row in rows:
        name = row['name'] if hasattr(row, 'keys') else row[0]
        if name not in used_books:
            result.append({
                'name': name,
                'testament': row['testament'] if hasattr(row, 'keys') else row[1],
                'book_order': row['book_order'] if hasattr(row, 'keys') else row[2]
            })

    return result


def get_theme_gaps(conn, months=12, current_date=None):
    """Get themes not covered within time window.

    Args:
        conn: Database connection.
        months: Months to look back.
        current_date: Reference date (defaults to today).

    Returns:
        list: List of theme dicts not covered recently.
    """
    cursor = conn.cursor()

    if current_date:
        ref_date = datetime.strptime(current_date, '%Y-%m-%d')
    else:
        ref_date = datetime.now()

    # Calculate cutoff
    cutoff = ref_date.replace(year=ref_date.year - (months // 12),
                              month=((ref_date.month - (months % 12) - 1) % 12) + 1)
    cutoff_str = cutoff.strftime('%Y-%m-%d')

    # Get themes covered recently
    cursor.execute(
        '''SELECT DISTINCT theme FROM theme_usage
           WHERE used_date >= ?''',
        (cutoff_str,)
    )
    recent_rows = cursor.fetchall()
    recent_themes = set(row['theme'] if hasattr(row, 'keys') else row[0] for row in recent_rows)

    # Get all standard themes
    cursor.execute('SELECT name, category FROM standard_themes')
    rows = cursor.fetchall()

    result = []
    for row in rows:
        name = row['name'] if hasattr(row, 'keys') else row[0]
        if name not in recent_themes:
            result.append({
                'name': name,
                'category': row['category'] if hasattr(row, 'keys') else row[1]
            })

    return result


def get_usage_report(conn, start_date, end_date):
    """Generate usage report for date range.

    Args:
        conn: Database connection.
        start_date: Start date string.
        end_date: End date string.

    Returns:
        dict: Report with scripture and theme usage stats.
    """
    cursor = conn.cursor()

    # Get sermons in range
    cursor.execute(
        '''SELECT COUNT(*) as count FROM sermons
           WHERE preached_date >= ? AND preached_date <= ?''',
        (start_date, end_date)
    )
    row = cursor.fetchone()
    sermon_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Get scripture usage
    cursor.execute(
        '''SELECT book, passage, COUNT(*) as count
           FROM scripture_usage
           WHERE used_date >= ? AND used_date <= ?
           GROUP BY book
           ORDER BY count DESC''',
        (start_date, end_date)
    )
    scripture_rows = cursor.fetchall()
    scriptures = []
    for row in scripture_rows:
        scriptures.append({
            'book': row['book'] if hasattr(row, 'keys') else row[0],
            'count': row['count'] if hasattr(row, 'keys') else row[2]
        })

    # Get total scripture count
    cursor.execute(
        '''SELECT COUNT(*) as count FROM scripture_usage
           WHERE used_date >= ? AND used_date <= ?''',
        (start_date, end_date)
    )
    row = cursor.fetchone()
    scripture_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Get theme usage
    cursor.execute(
        '''SELECT theme, COUNT(*) as count
           FROM theme_usage
           WHERE used_date >= ? AND used_date <= ?
           GROUP BY theme
           ORDER BY count DESC''',
        (start_date, end_date)
    )
    theme_rows = cursor.fetchall()
    themes = []
    for row in theme_rows:
        themes.append({
            'theme': row['theme'] if hasattr(row, 'keys') else row[0],
            'count': row['count'] if hasattr(row, 'keys') else row[1]
        })

    # Get total theme count
    cursor.execute(
        '''SELECT COUNT(*) as count FROM theme_usage
           WHERE used_date >= ? AND used_date <= ?''',
        (start_date, end_date)
    )
    row = cursor.fetchone()
    theme_count = row['count'] if hasattr(row, 'keys') else row[0]

    return {
        'sermon_count': sermon_count,
        'scriptures': scriptures,
        'scripture_count': scripture_count,
        'themes': themes,
        'theme_count': theme_count,
        'start_date': start_date,
        'end_date': end_date
    }


def suggest_underused_scriptures(conn, limit=10):
    """Suggest underused scripture books.

    Args:
        conn: Database connection.
        limit: Maximum suggestions to return.

    Returns:
        list: List of underused book suggestions.
    """
    cursor = conn.cursor()

    # Get usage counts per book
    cursor.execute(
        '''SELECT b.name as book, b.testament, COALESCE(s.count, 0) as usage_count
           FROM bible_books b
           LEFT JOIN (
               SELECT book, COUNT(*) as count
               FROM scripture_usage
               GROUP BY book
           ) s ON b.name = s.book
           ORDER BY usage_count ASC, b.book_order ASC
           LIMIT ?''',
        (limit,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'book': row['book'] if hasattr(row, 'keys') else row[0],
            'testament': row['testament'] if hasattr(row, 'keys') else row[1],
            'usage_count': row['usage_count'] if hasattr(row, 'keys') else row[2]
        })

    return result


def suggest_underused_themes(conn, limit=10, current_date=None):
    """Suggest underused themes.

    Args:
        conn: Database connection.
        limit: Maximum suggestions to return.
        current_date: Reference date for days calculation.

    Returns:
        list: List of underused theme suggestions.
    """
    cursor = conn.cursor()

    if current_date:
        ref_date = datetime.strptime(current_date, '%Y-%m-%d')
    else:
        ref_date = datetime.now()

    # Get usage info per theme
    cursor.execute(
        '''SELECT st.name as theme, st.category,
                  COALESCE(t.count, 0) as usage_count,
                  t.last_used
           FROM standard_themes st
           LEFT JOIN (
               SELECT theme, COUNT(*) as count, MAX(used_date) as last_used
               FROM theme_usage
               GROUP BY theme
           ) t ON st.name = t.theme
           ORDER BY usage_count ASC, last_used ASC NULLS FIRST
           LIMIT ?''',
        (limit,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        theme = row['theme'] if hasattr(row, 'keys') else row[0]
        last_used = row['last_used'] if hasattr(row, 'keys') else row[3]

        days_since = None
        if last_used:
            last_date = datetime.strptime(last_used, '%Y-%m-%d')
            days_since = (ref_date - last_date).days

        result.append({
            'theme': theme,
            'category': row['category'] if hasattr(row, 'keys') else row[1],
            'usage_count': row['usage_count'] if hasattr(row, 'keys') else row[2],
            'last_used': last_used,
            'days_since_use': days_since
        })

    return result
