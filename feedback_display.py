"""Feedback display module for UI presentation.

Provides functions for retrieving, formatting, and displaying
panel reviewer feedback to users.
"""
import html
from datetime import datetime


class SermonNotFoundError(Exception):
    """Raised when the requested sermon is not found."""
    pass


class InvalidSermonIdError(Exception):
    """Raised when the sermon ID is invalid."""
    pass


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass


# Valid sermon sections in order
SECTION_ORDER = ['Introduction', 'Point 1', 'Point 2', 'Point 3', 'Conclusion']


def get_feedback_for_sermon(conn, sermon_id, reviewer=None, section=None,
                            min_rating=None, sort_by=None, require_sermon=False):
    """Get feedback for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        reviewer: Optional reviewer type filter.
        section: Optional section filter.
        min_rating: Optional minimum rating filter.
        sort_by: Sort order ('rating', 'section', or default date desc).
        require_sermon: If True, raise SermonNotFoundError for missing sermon.

    Returns:
        list: List of feedback dicts.

    Raises:
        DatabaseError: If conn is None or invalid.
        InvalidSermonIdError: If sermon_id is not an integer.
        SermonNotFoundError: If require_sermon and sermon doesn't exist.
    """
    if conn is None:
        raise DatabaseError("Database connection is required")

    if not isinstance(sermon_id, int):
        raise InvalidSermonIdError(f"Invalid sermon ID: {sermon_id}")

    cursor = conn.cursor()

    if require_sermon:
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if not cursor.fetchone():
            raise SermonNotFoundError(f"Sermon not found: {sermon_id}")

    # Build query with filters
    query = """
        SELECT id, reviewer, reviewer_name, focus_area, sermon_id,
               section, comment, rating, created_at
        FROM panel_feedback
        WHERE sermon_id = ?
    """
    params = [sermon_id]

    if reviewer:
        query += " AND reviewer = ?"
        params.append(reviewer)

    if section:
        query += " AND section = ?"
        params.append(section)

    if min_rating:
        query += " AND rating >= ?"
        params.append(min_rating)

    # Sort order
    if sort_by == 'rating':
        query += " ORDER BY rating DESC"
    elif sort_by == 'section':
        query += " ORDER BY CASE section " + " ".join(
            f"WHEN '{s}' THEN {i}" for i, s in enumerate(SECTION_ORDER)
        ) + " ELSE 99 END"
    else:
        query += " ORDER BY created_at DESC"

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) if hasattr(row, 'keys') else _row_to_dict(row) for row in rows]
    except Exception:
        # Table may not exist yet
        return []


def _row_to_dict(row):
    """Convert a row tuple to dict."""
    keys = ['id', 'reviewer', 'reviewer_name', 'focus_area', 'sermon_id',
            'section', 'comment', 'rating', 'created_at']
    return dict(zip(keys, row))


def group_feedback_by_reviewer(conn, sermon_id):
    """Group feedback by reviewer type.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Feedback grouped by reviewer type.
    """
    feedback = get_feedback_for_sermon(conn, sermon_id)
    grouped = {}
    for fb in feedback:
        reviewer = fb.get('reviewer', 'unknown')
        if reviewer not in grouped:
            grouped[reviewer] = []
        grouped[reviewer].append(fb)
    return grouped


def get_feedback_with_section_links(conn, sermon_id):
    """Get feedback with section anchor links.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: Feedback with anchor_id for section linking.
    """
    feedback = get_feedback_for_sermon(conn, sermon_id)
    for fb in feedback:
        section = fb.get('section')
        if section:
            fb['anchor_id'] = section.lower().replace(' ', '-')
    return feedback


def get_feedback_display_data(conn, sermon_id):
    """Get feedback display data for UI.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Display data including has_feedback flag.
    """
    feedback = get_feedback_for_sermon(conn, sermon_id)
    return {
        'feedback': feedback,
        'has_feedback': len(feedback) > 0,
        'count': len(feedback)
    }


def prepare_template_context(conn, sermon_id):
    """Prepare template context for feedback display.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Template context with feedback and sermon info.
    """
    feedback = get_feedback_for_sermon(conn, sermon_id)
    grouped = group_feedback_by_reviewer(conn, sermon_id)

    # Get sermon info - handle different column names
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, title, content, word_count FROM sermons WHERE id = ?", (sermon_id,))
    except Exception:
        cursor.execute("SELECT id, title, manuscript, word_count FROM sermons WHERE id = ?", (sermon_id,))
    row = cursor.fetchone()

    sermon = {}
    if row:
        if hasattr(row, 'keys'):
            sermon = dict(row)
        else:
            sermon = {'id': row[0], 'title': row[1], 'content': row[2], 'word_count': row[3]}

    return {
        'feedback_list': feedback,
        'grouped_feedback': grouped,
        'sermon': sermon,
        'sermon_title': sermon.get('title', ''),
        'reviewer_count': len(grouped),
        'reviewers': list(grouped.keys()),
        'has_feedback': len(feedback) > 0
    }


def format_feedback_for_display(feedback):
    """Format feedback for display.

    Args:
        feedback: Feedback dict.

    Returns:
        dict: Formatted feedback with display fields.
    """
    result = dict(feedback)

    # Format rating as stars
    rating = feedback.get('rating', 0)
    if rating:
        result['rating_display'] = '*' * rating
        result['stars'] = rating

    # Format timestamp
    created_at = feedback.get('created_at', '')
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                result['formatted_date'] = dt.strftime('%B %d, %Y')
                result['display_time'] = dt.strftime('%I:%M %p')
        except ValueError:
            result['formatted_date'] = str(created_at)
            result['display_time'] = str(created_at)

    # Escape HTML in comments
    comment = feedback.get('comment', '')
    if comment:
        result['comment'] = html.escape(comment)
        # Preserve markdown by not escaping asterisks for strong/emphasis
        if '**' in comment:
            escaped = html.escape(comment)
            result['comment'] = escaped
            result['comment_html'] = escaped.replace('**', '<strong>').replace('**', '</strong>')

    return result
