"""Reviewer comment system module.

Provides inline commenting system for shared sermon drafts with position
markers, threaded replies, and suggestion handling.
"""


def add_comment(conn, sermon_id, reviewer_name, text, start_pos=None, end_pos=None, suggestion=None):
    """Add a comment to a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        reviewer_name: Name of the reviewer.
        text: Comment text.
        start_pos: Optional start position of highlight.
        end_pos: Optional end position of highlight.
        suggestion: Optional suggested replacement text.

    Returns:
        int: ID of the created comment, or None if invalid.
    """
    # Validate required fields
    if not reviewer_name or not reviewer_name.strip():
        return None
    if not text or not text.strip():
        return None

    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if cursor.fetchone() is None:
        return None

    # Insert comment
    cursor.execute(
        '''INSERT INTO review_comments
           (sermon_id, reviewer_name, comment_text, highlight_start, highlight_end, suggestion)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (sermon_id, reviewer_name, text, start_pos, end_pos, suggestion)
    )
    conn.commit()
    return cursor.lastrowid


def get_comment(conn, comment_id):
    """Get a single comment by ID.

    Args:
        conn: Database connection.
        comment_id: ID of the comment.

    Returns:
        dict: Comment details, or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, parent_id, reviewer_name, comment_text,
                  highlight_start, highlight_end, suggestion, resolved, created_at, updated_at
           FROM review_comments WHERE id = ?''',
        (comment_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
        'parent_id': row['parent_id'] if hasattr(row, 'keys') else row[2],
        'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[3],
        'comment_text': row['comment_text'] if hasattr(row, 'keys') else row[4],
        'highlight_start': row['highlight_start'] if hasattr(row, 'keys') else row[5],
        'highlight_end': row['highlight_end'] if hasattr(row, 'keys') else row[6],
        'suggestion': row['suggestion'] if hasattr(row, 'keys') else row[7],
        'resolved': row['resolved'] if hasattr(row, 'keys') else row[8],
        'created_at': row['created_at'] if hasattr(row, 'keys') else row[9],
        'updated_at': row['updated_at'] if hasattr(row, 'keys') else row[10]
    }


def list_comments(conn, sermon_id, status=None):
    """List comments for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        status: Optional filter - 'open' or 'resolved'.

    Returns:
        list: List of comment dictionaries ordered by position.
    """
    cursor = conn.cursor()

    query = '''SELECT id, sermon_id, parent_id, reviewer_name, comment_text,
                      highlight_start, highlight_end, suggestion, resolved, created_at
               FROM review_comments
               WHERE sermon_id = ? AND parent_id IS NULL'''
    params = [sermon_id]

    if status == 'open':
        query += ' AND resolved = 0'
    elif status == 'resolved':
        query += ' AND resolved = 1'

    query += ' ORDER BY highlight_start, created_at'

    cursor.execute(query, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'parent_id': row['parent_id'] if hasattr(row, 'keys') else row[2],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[3],
            'comment_text': row['comment_text'] if hasattr(row, 'keys') else row[4],
            'highlight_start': row['highlight_start'] if hasattr(row, 'keys') else row[5],
            'highlight_end': row['highlight_end'] if hasattr(row, 'keys') else row[6],
            'suggestion': row['suggestion'] if hasattr(row, 'keys') else row[7],
            'resolved': row['resolved'] if hasattr(row, 'keys') else row[8],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[9]
        })

    return result


def update_comment(conn, comment_id, text):
    """Update comment text.

    Args:
        conn: Database connection.
        comment_id: ID of the comment.
        text: New comment text.

    Returns:
        bool: True if updated, False if not found or invalid.
    """
    if not text or not text.strip():
        return False

    cursor = conn.cursor()

    # Check comment exists
    cursor.execute('SELECT id FROM review_comments WHERE id = ?', (comment_id,))
    if cursor.fetchone() is None:
        return False

    cursor.execute(
        '''UPDATE review_comments
           SET comment_text = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?''',
        (text, comment_id)
    )
    conn.commit()
    return True


def resolve_comment(conn, comment_id):
    """Mark a comment as resolved.

    Args:
        conn: Database connection.
        comment_id: ID of the comment.

    Returns:
        bool: True if resolved, False if not found.
    """
    cursor = conn.cursor()

    # Check comment exists
    cursor.execute('SELECT id FROM review_comments WHERE id = ?', (comment_id,))
    if cursor.fetchone() is None:
        return False

    cursor.execute(
        'UPDATE review_comments SET resolved = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (comment_id,)
    )
    conn.commit()
    return True


def delete_comment(conn, comment_id):
    """Delete a comment and its replies.

    Args:
        conn: Database connection.
        comment_id: ID of the comment.

    Returns:
        bool: True if deleted, False if not found.
    """
    cursor = conn.cursor()

    # Check comment exists
    cursor.execute('SELECT id FROM review_comments WHERE id = ?', (comment_id,))
    if cursor.fetchone() is None:
        return False

    # Delete replies first (cascade)
    cursor.execute('DELETE FROM review_comments WHERE parent_id = ?', (comment_id,))

    # Delete the comment
    cursor.execute('DELETE FROM review_comments WHERE id = ?', (comment_id,))
    conn.commit()
    return True


def add_reply(conn, parent_comment_id, reviewer_name, text):
    """Add a reply to a comment.

    Args:
        conn: Database connection.
        parent_comment_id: ID of the parent comment.
        reviewer_name: Name of the reviewer.
        text: Reply text.

    Returns:
        int: ID of the created reply, or None if invalid.
    """
    if not reviewer_name or not reviewer_name.strip():
        return None
    if not text or not text.strip():
        return None

    cursor = conn.cursor()

    # Get parent comment's sermon_id
    cursor.execute('SELECT sermon_id FROM review_comments WHERE id = ?', (parent_comment_id,))
    row = cursor.fetchone()
    if row is None:
        return None

    sermon_id = row['sermon_id'] if hasattr(row, 'keys') else row[0]

    # Insert reply
    cursor.execute(
        '''INSERT INTO review_comments
           (sermon_id, parent_id, reviewer_name, comment_text)
           VALUES (?, ?, ?, ?)''',
        (sermon_id, parent_comment_id, reviewer_name, text)
    )
    conn.commit()
    return cursor.lastrowid


def get_replies(conn, parent_comment_id):
    """Get replies to a comment.

    Args:
        conn: Database connection.
        parent_comment_id: ID of the parent comment.

    Returns:
        list: List of reply dictionaries ordered by creation time.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, parent_id, reviewer_name, comment_text,
                  highlight_start, highlight_end, suggestion, resolved, created_at
           FROM review_comments
           WHERE parent_id = ?
           ORDER BY created_at''',
        (parent_comment_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'parent_id': row['parent_id'] if hasattr(row, 'keys') else row[2],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[3],
            'comment_text': row['comment_text'] if hasattr(row, 'keys') else row[4],
            'highlight_start': row['highlight_start'] if hasattr(row, 'keys') else row[5],
            'highlight_end': row['highlight_end'] if hasattr(row, 'keys') else row[6],
            'suggestion': row['suggestion'] if hasattr(row, 'keys') else row[7],
            'resolved': row['resolved'] if hasattr(row, 'keys') else row[8],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[9]
        })

    return result


def accept_suggestion(conn, comment_id):
    """Accept a suggestion and resolve the comment.

    Args:
        conn: Database connection.
        comment_id: ID of the comment with suggestion.

    Returns:
        dict: Result with suggestion text and success, or None if no suggestion.
    """
    cursor = conn.cursor()

    # Get comment with suggestion
    cursor.execute(
        'SELECT id, sermon_id, suggestion, highlight_start, highlight_end FROM review_comments WHERE id = ?',
        (comment_id,)
    )
    row = cursor.fetchone()

    if row is None:
        return None

    suggestion = row['suggestion'] if hasattr(row, 'keys') else row[2]
    if not suggestion:
        return None

    # Mark as resolved
    cursor.execute(
        'UPDATE review_comments SET resolved = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (comment_id,)
    )
    conn.commit()

    return {
        'success': True,
        'suggestion': suggestion,
        'comment_id': comment_id
    }


def get_comment_summary(conn, sermon_id):
    """Get a summary of comments for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Summary with total, open, and resolved counts.
    """
    cursor = conn.cursor()

    # Get total count
    cursor.execute(
        'SELECT COUNT(*) as count FROM review_comments WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    total = row['count'] if hasattr(row, 'keys') else row[0]

    # Get open count
    cursor.execute(
        'SELECT COUNT(*) as count FROM review_comments WHERE sermon_id = ? AND resolved = 0',
        (sermon_id,)
    )
    row = cursor.fetchone()
    open_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Get resolved count
    cursor.execute(
        'SELECT COUNT(*) as count FROM review_comments WHERE sermon_id = ? AND resolved = 1',
        (sermon_id,)
    )
    row = cursor.fetchone()
    resolved_count = row['count'] if hasattr(row, 'keys') else row[0]

    return {
        'sermon_id': sermon_id,
        'total': total,
        'total_comments': total,
        'open': open_count,
        'open_count': open_count,
        'resolved': resolved_count,
        'resolved_count': resolved_count
    }
