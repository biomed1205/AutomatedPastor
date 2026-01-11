"""Illustration deduplication functionality module.

Provides tracking and deduplication of illustrations to prevent
using the same stories/examples too frequently in sermons.
"""

import json
from datetime import datetime


def _calculate_similarity(text1, text2):
    """Calculate word-based similarity between two texts.

    Uses a combination of exact matches and prefix matches
    for better semantic matching.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        float: Similarity score between 0 and 1.
    """
    # Normalize and extract meaningful words (skip small words)
    stop_words = {'a', 'an', 'the', 'of', 'and', 'or', 'to', 'in', 'on', 'at',
                  'is', 'it', 'for', 'with', 'as', 'by', 'his', 'her', 'its'}

    words1 = set(w for w in text1.lower().split() if len(w) > 2 and w not in stop_words)
    words2 = set(w for w in text2.lower().split() if len(w) > 2 and w not in stop_words)

    if not words1 or not words2:
        return 0.0

    # Count exact matches
    exact_matches = words1 & words2

    # Count prefix/stem matches (word starts with same 4+ chars)
    stem_matches = 0
    for w1 in words1:
        for w2 in words2:
            if w1 != w2 and len(w1) >= 4 and len(w2) >= 4:
                prefix = min(len(w1), len(w2), 4)
                if w1[:prefix] == w2[:prefix]:
                    stem_matches += 0.5
                    break

    total_matches = len(exact_matches) + stem_matches

    # Use overlap coefficient (matches / min) for similarity
    min_size = min(len(words1), len(words2))
    return total_matches / min_size if min_size > 0 else 0.0


def add_illustration(conn, sermon_id, text, source=None):
    """Add an illustration to a sermon with usage tracking.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        text: Illustration text.
        source: Optional source of the illustration.

    Returns:
        dict: Result with success status and illustration_id.
    """
    if not text or not text.strip():
        return {'success': False, 'error': 'Empty text'}

    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        return {'success': False, 'error': 'Sermon not found'}

    # Check for duplicate
    dup_result = check_duplicate(conn, text)
    warning = None
    gap_violation = False

    if dup_result.get('is_duplicate'):
        # Check gap setting
        min_gap = get_minimum_gap(conn)
        time_result = get_time_since_last_use(conn, text)

        if time_result.get('days') is not None:
            if time_result['days'] < min_gap:
                warning = f"Illustration used {time_result['days']} days ago"
                gap_violation = True
            else:
                warning = "Duplicate illustration"
        else:
            warning = "Duplicate illustration"

        # Use existing illustration
        illustration_id = dup_result.get('original_id') or dup_result.get('match_id')
    else:
        # Create new illustration
        cursor.execute(
            '''INSERT INTO illustrations (text, source)
               VALUES (?, ?)''',
            (text, source)
        )
        conn.commit()
        illustration_id = cursor.lastrowid

    # Get sermon preached_date for usage date
    cursor.execute('SELECT preached_date FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()
    used_date = (row['preached_date'] if hasattr(row, 'keys') else row[0]) or datetime.now().strftime('%Y-%m-%d')

    # Record usage
    cursor.execute(
        '''INSERT INTO illustration_usage (illustration_id, sermon_id, used_date)
           VALUES (?, ?, ?)''',
        (illustration_id, sermon_id, used_date)
    )
    conn.commit()

    result = {'success': True, 'illustration_id': illustration_id}
    if warning:
        result['warning'] = warning
    if gap_violation:
        result['gap_violation'] = True
        result['duplicate'] = True

    return result


def check_duplicate(conn, text):
    """Check if an illustration is a duplicate.

    Args:
        conn: Database connection.
        text: Illustration text to check.

    Returns:
        dict: Result with is_duplicate and original_id if found.
    """
    cursor = conn.cursor()

    # Check exact match (case-insensitive)
    cursor.execute('SELECT id, text FROM illustrations')
    rows = cursor.fetchall()

    text_lower = text.lower()

    for row in rows:
        row_id = row['id'] if hasattr(row, 'keys') else row[0]
        row_text = row['text'] if hasattr(row, 'keys') else row[1]

        if row_text.lower() == text_lower:
            return {
                'is_duplicate': True,
                'original_id': row_id,
                'match_id': row_id
            }

    # Check for similar illustrations
    for row in rows:
        row_id = row['id'] if hasattr(row, 'keys') else row[0]
        row_text = row['text'] if hasattr(row, 'keys') else row[1]

        similarity = _calculate_similarity(text, row_text)
        if similarity >= 0.3:
            return {
                'is_duplicate': False,
                'is_similar': True,
                'similar_found': True,
                'original_id': row_id,
                'match_id': row_id,
                'similarity': similarity
            }

    return {'is_duplicate': False}


def get_illustration_usage(conn, illustration_id):
    """Get usage history for an illustration.

    Args:
        conn: Database connection.
        illustration_id: ID of the illustration.

    Returns:
        list: List of usage records with sermon info.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT iu.used_date, s.title as sermon_title, s.id as sermon_id
           FROM illustration_usage iu
           JOIN sermons s ON iu.sermon_id = s.id
           WHERE iu.illustration_id = ?
           ORDER BY iu.used_date DESC''',
        (illustration_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'used_date': row['used_date'] if hasattr(row, 'keys') else row[0],
            'sermon_title': row['sermon_title'] if hasattr(row, 'keys') else row[1],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[2]
        })

    return result


def get_recent_illustrations(conn, days=30, from_date=None):
    """Get illustrations used within a timeframe.

    Args:
        conn: Database connection.
        days: Number of days to look back.
        from_date: Optional reference date (defaults to today).

    Returns:
        list: List of recently used illustrations.
    """
    cursor = conn.cursor()

    if from_date:
        ref_date = datetime.strptime(from_date, '%Y-%m-%d')
    else:
        ref_date = datetime.now()

    cutoff = (ref_date - __import__('datetime').timedelta(days=days)).strftime('%Y-%m-%d')

    cursor.execute(
        '''SELECT i.id, i.text, i.source, i.theme, MAX(iu.used_date) as last_used
           FROM illustrations i
           JOIN illustration_usage iu ON i.id = iu.illustration_id
           WHERE iu.used_date >= ?
           GROUP BY i.id
           ORDER BY last_used DESC''',
        (cutoff,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'text': row['text'] if hasattr(row, 'keys') else row[1],
            'source': row['source'] if hasattr(row, 'keys') else row[2],
            'theme': row['theme'] if hasattr(row, 'keys') else row[3],
            'last_used': row['last_used'] if hasattr(row, 'keys') else row[4]
        })

    return result


def find_similar_illustrations(conn, text, threshold=0.5):
    """Find illustrations similar to the given text.

    Args:
        conn: Database connection.
        text: Text to compare against.
        threshold: Minimum similarity score (0-1).

    Returns:
        list: List of similar illustrations with scores.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT id, text, source, theme FROM illustrations')
    rows = cursor.fetchall()

    result = []
    for row in rows:
        row_id = row['id'] if hasattr(row, 'keys') else row[0]
        row_text = row['text'] if hasattr(row, 'keys') else row[1]
        row_source = row['source'] if hasattr(row, 'keys') else row[2]
        row_theme = row['theme'] if hasattr(row, 'keys') else row[3]

        similarity = _calculate_similarity(text, row_text)

        if similarity >= threshold:
            result.append({
                'id': row_id,
                'text': row_text,
                'source': row_source,
                'theme': row_theme,
                'similarity': similarity,
                'score': similarity
            })

    # Sort by similarity descending
    result.sort(key=lambda x: x['similarity'], reverse=True)

    return result


def get_time_since_last_use(conn, text, current_date=None):
    """Get the number of days since an illustration was last used.

    Args:
        conn: Database connection.
        text: Illustration text.
        current_date: Optional reference date (defaults to today).

    Returns:
        dict: Result with days count or never_used flag.
    """
    cursor = conn.cursor()

    # Find the illustration by text (case-insensitive)
    cursor.execute('SELECT id, text FROM illustrations')
    rows = cursor.fetchall()

    text_lower = text.lower()
    illustration_id = None

    for row in rows:
        row_id = row['id'] if hasattr(row, 'keys') else row[0]
        row_text = row['text'] if hasattr(row, 'keys') else row[1]

        if row_text.lower() == text_lower:
            illustration_id = row_id
            break

    if illustration_id is None:
        return {'days': None, 'never_used': True}

    # Get most recent usage
    cursor.execute(
        '''SELECT MAX(used_date) as last_used
           FROM illustration_usage
           WHERE illustration_id = ?''',
        (illustration_id,)
    )
    row = cursor.fetchone()
    last_used = row['last_used'] if hasattr(row, 'keys') else row[0]

    if last_used is None:
        return {'days': None, 'never_used': True}

    if current_date:
        ref_date = datetime.strptime(current_date, '%Y-%m-%d')
    else:
        ref_date = datetime.now()

    last_date = datetime.strptime(last_used, '%Y-%m-%d')
    days = (ref_date - last_date).days

    return {'days': days, 'last_used': last_used}


def suggest_alternatives(conn, theme, exclude_days=None, current_date=None):
    """Suggest alternative illustrations for a theme.

    Args:
        conn: Database connection.
        theme: Theme to find illustrations for.
        exclude_days: Days to exclude recently used illustrations.
        current_date: Reference date for exclusion.

    Returns:
        list: List of suggested illustrations ordered by least recently used.
    """
    cursor = conn.cursor()

    # Get all illustrations with the theme
    cursor.execute(
        '''SELECT i.id, i.text, i.source, i.theme, MAX(iu.used_date) as last_used
           FROM illustrations i
           LEFT JOIN illustration_usage iu ON i.id = iu.illustration_id
           WHERE i.theme = ?
           GROUP BY i.id
           ORDER BY COALESCE(last_used, '1900-01-01') ASC''',
        (theme,)
    )
    rows = cursor.fetchall()

    if current_date:
        ref_date = datetime.strptime(current_date, '%Y-%m-%d')
    else:
        ref_date = datetime.now()

    result = []
    for row in rows:
        row_id = row['id'] if hasattr(row, 'keys') else row[0]
        row_text = row['text'] if hasattr(row, 'keys') else row[1]
        row_source = row['source'] if hasattr(row, 'keys') else row[2]
        row_theme = row['theme'] if hasattr(row, 'keys') else row[3]
        last_used = row['last_used'] if hasattr(row, 'keys') else row[4]

        # Exclude recently used if specified
        if exclude_days and last_used:
            last_date = datetime.strptime(last_used, '%Y-%m-%d')
            days_since = (ref_date - last_date).days
            if days_since < exclude_days:
                continue

        result.append({
            'id': row_id,
            'text': row_text,
            'source': row_source,
            'theme': row_theme,
            'last_used': last_used
        })

    return result


def set_minimum_gap(conn, days):
    """Set the minimum gap between illustration uses.

    Args:
        conn: Database connection.
        days: Minimum number of days between uses.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''INSERT OR REPLACE INTO illustration_settings (key, value)
           VALUES ('minimum_gap', ?)''',
        (str(days),)
    )
    conn.commit()


def get_minimum_gap(conn):
    """Get the minimum gap setting.

    Args:
        conn: Database connection.

    Returns:
        int: Minimum gap in days (default 60).
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT value FROM illustration_settings WHERE key = 'minimum_gap' '''
    )
    row = cursor.fetchone()

    if row is None:
        return 60

    return int(row['value'] if hasattr(row, 'keys') else row[0])


def export_illustration_library(conn, format=None):
    """Export the illustration library.

    Args:
        conn: Database connection.
        format: Optional format ('json' for JSON string).

    Returns:
        list or str: Library data or JSON string.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT i.id, i.text, i.source, i.theme,
                  COUNT(iu.id) as usage_count,
                  MAX(iu.used_date) as last_used
           FROM illustrations i
           LEFT JOIN illustration_usage iu ON i.id = iu.illustration_id
           GROUP BY i.id
           ORDER BY i.id'''
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'text': row['text'] if hasattr(row, 'keys') else row[1],
            'source': row['source'] if hasattr(row, 'keys') else row[2],
            'theme': row['theme'] if hasattr(row, 'keys') else row[3],
            'usage_count': row['usage_count'] if hasattr(row, 'keys') else row[4],
            'last_used': row['last_used'] if hasattr(row, 'keys') else row[5]
        })

    if format == 'json':
        return json.dumps(result)

    return result
