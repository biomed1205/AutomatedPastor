"""Review status dashboard module.

Provides review tracking dashboard for sermon drafts with reviewer activity
tracking, feedback aggregation, and progress reports.
"""

from datetime import datetime


def track_reviewer_view(conn, sermon_id, share_token, reviewer_name):
    """Track when a reviewer views a shared sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        share_token: Share token used for access.
        reviewer_name: Name of the reviewer.

    Returns:
        bool: True if tracked successfully.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    # Check if activity already exists
    cursor.execute(
        '''SELECT id, first_viewed_at FROM review_activity
           WHERE sermon_id = ? AND reviewer_name = ?''',
        (sermon_id, reviewer_name)
    )
    row = cursor.fetchone()

    if row is not None:
        # Update last_viewed_at
        cursor.execute(
            '''UPDATE review_activity SET last_viewed_at = ?, share_token = ?
               WHERE sermon_id = ? AND reviewer_name = ?''',
            (now, share_token, sermon_id, reviewer_name)
        )
    else:
        # Create new activity
        cursor.execute(
            '''INSERT INTO review_activity
               (sermon_id, reviewer_name, share_token, first_viewed_at, last_viewed_at, status)
               VALUES (?, ?, ?, ?, ?, 'pending')''',
            (sermon_id, reviewer_name, share_token, now, now)
        )

    conn.commit()
    return True


def track_reviewer_feedback(conn, sermon_id, reviewer_name):
    """Track when a reviewer provides feedback.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        reviewer_name: Name of the reviewer.

    Returns:
        bool: True if tracked successfully.
    """
    cursor = conn.cursor()

    # Count comments from this reviewer
    cursor.execute(
        '''SELECT COUNT(*) as count FROM review_comments
           WHERE sermon_id = ? AND reviewer_name = ?''',
        (sermon_id, reviewer_name)
    )
    row = cursor.fetchone()
    comment_count = row['count'] if hasattr(row, 'keys') else row[0]

    # Check if activity exists
    cursor.execute(
        'SELECT id FROM review_activity WHERE sermon_id = ? AND reviewer_name = ?',
        (sermon_id, reviewer_name)
    )
    activity = cursor.fetchone()

    if activity is not None:
        # Update existing activity
        cursor.execute(
            '''UPDATE review_activity
               SET status = 'completed', comments_count = ?
               WHERE sermon_id = ? AND reviewer_name = ?''',
            (comment_count, sermon_id, reviewer_name)
        )
    else:
        # Create new activity
        now = datetime.now().isoformat()
        cursor.execute(
            '''INSERT INTO review_activity
               (sermon_id, reviewer_name, status, comments_count, first_viewed_at)
               VALUES (?, ?, 'completed', ?, ?)''',
            (sermon_id, reviewer_name, comment_count, now)
        )

    conn.commit()
    return True


def get_review_status(conn, sermon_id):
    """Get overall review status for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Status summary with reviewer counts and completion stats.
    """
    cursor = conn.cursor()

    # Count total reviewers
    cursor.execute(
        'SELECT COUNT(*) as count FROM review_activity WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    total_reviewers = row['count'] if hasattr(row, 'keys') else row[0]

    # Count completed reviewers
    cursor.execute(
        '''SELECT COUNT(*) as count FROM review_activity
           WHERE sermon_id = ? AND status = 'completed' ''',
        (sermon_id,)
    )
    row = cursor.fetchone()
    completed = row['count'] if hasattr(row, 'keys') else row[0]

    # Count pending reviewers
    cursor.execute(
        '''SELECT COUNT(*) as count FROM review_activity
           WHERE sermon_id = ? AND status = 'pending' ''',
        (sermon_id,)
    )
    row = cursor.fetchone()
    pending = row['count'] if hasattr(row, 'keys') else row[0]

    # Sum total comments
    cursor.execute(
        'SELECT COALESCE(SUM(comments_count), 0) as total FROM review_activity WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    total_comments = row['total'] if hasattr(row, 'keys') else row[0]

    return {
        'sermon_id': sermon_id,
        'total_reviewers': total_reviewers,
        'reviewers_count': total_reviewers,
        'completed': completed,
        'completed_count': completed,
        'pending': pending,
        'pending_count': pending,
        'total_comments': total_comments,
        'comments_count': total_comments
    }


def list_reviewer_activity(conn, sermon_id):
    """List all reviewer activity for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of reviewer activity dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, reviewer_name, share_token, first_viewed_at,
                  last_viewed_at, comments_count, status, created_at
           FROM review_activity
           WHERE sermon_id = ?
           ORDER BY created_at DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[2],
            'share_token': row['share_token'] if hasattr(row, 'keys') else row[3],
            'first_viewed_at': row['first_viewed_at'] if hasattr(row, 'keys') else row[4],
            'last_viewed_at': row['last_viewed_at'] if hasattr(row, 'keys') else row[5],
            'comments_count': row['comments_count'] if hasattr(row, 'keys') else row[6],
            'status': row['status'] if hasattr(row, 'keys') else row[7],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[8]
        })

    return result


def get_pending_reviewers(conn, sermon_id):
    """Get reviewers who haven't completed their review.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of pending reviewer dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, reviewer_name, share_token, first_viewed_at,
                  last_viewed_at, comments_count, status, created_at
           FROM review_activity
           WHERE sermon_id = ? AND status = 'pending'
           ORDER BY first_viewed_at''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[2],
            'share_token': row['share_token'] if hasattr(row, 'keys') else row[3],
            'first_viewed_at': row['first_viewed_at'] if hasattr(row, 'keys') else row[4],
            'last_viewed_at': row['last_viewed_at'] if hasattr(row, 'keys') else row[5],
            'comments_count': row['comments_count'] if hasattr(row, 'keys') else row[6],
            'status': row['status'] if hasattr(row, 'keys') else row[7],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[8]
        })

    return result


def get_completed_reviewers(conn, sermon_id):
    """Get reviewers who have completed their review.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of completed reviewer dictionaries.
    """
    cursor = conn.cursor()

    cursor.execute(
        '''SELECT id, sermon_id, reviewer_name, share_token, first_viewed_at,
                  last_viewed_at, comments_count, status, created_at
           FROM review_activity
           WHERE sermon_id = ? AND status = 'completed'
           ORDER BY first_viewed_at''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[2],
            'share_token': row['share_token'] if hasattr(row, 'keys') else row[3],
            'first_viewed_at': row['first_viewed_at'] if hasattr(row, 'keys') else row[4],
            'last_viewed_at': row['last_viewed_at'] if hasattr(row, 'keys') else row[5],
            'comments_count': row['comments_count'] if hasattr(row, 'keys') else row[6],
            'status': row['status'] if hasattr(row, 'keys') else row[7],
            'created_at': row['created_at'] if hasattr(row, 'keys') else row[8]
        })

    return result


def calculate_review_progress(conn, sermon_id):
    """Calculate review progress percentage.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        int: Progress percentage (0-100).
    """
    cursor = conn.cursor()

    # Count total reviewers
    cursor.execute(
        'SELECT COUNT(*) as count FROM review_activity WHERE sermon_id = ?',
        (sermon_id,)
    )
    row = cursor.fetchone()
    total = row['count'] if hasattr(row, 'keys') else row[0]

    if total == 0:
        return 0

    # Count completed
    cursor.execute(
        '''SELECT COUNT(*) as count FROM review_activity
           WHERE sermon_id = ? AND status = 'completed' ''',
        (sermon_id,)
    )
    row = cursor.fetchone()
    completed = row['count'] if hasattr(row, 'keys') else row[0]

    return int((completed / total) * 100)


def get_feedback_summary(conn, sermon_id):
    """Get aggregated feedback summary by reviewer.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Summary with reviewers list and aggregate stats.
    """
    cursor = conn.cursor()

    # Get reviewer activity
    cursor.execute(
        '''SELECT reviewer_name, status, comments_count, first_viewed_at
           FROM review_activity WHERE sermon_id = ?
           ORDER BY comments_count DESC''',
        (sermon_id,)
    )
    rows = cursor.fetchall()

    reviewers = []
    total_comments = 0
    for row in rows:
        comments = row['comments_count'] if hasattr(row, 'keys') else row[2]
        total_comments += comments or 0
        reviewers.append({
            'reviewer_name': row['reviewer_name'] if hasattr(row, 'keys') else row[0],
            'status': row['status'] if hasattr(row, 'keys') else row[1],
            'comments_count': comments or 0,
            'first_viewed_at': row['first_viewed_at'] if hasattr(row, 'keys') else row[3]
        })

    return {
        'sermon_id': sermon_id,
        'reviewers': reviewers,
        'total_reviewers': len(reviewers),
        'total_comments': total_comments,
        'avg_comments': total_comments / len(reviewers) if reviewers else 0
    }


def export_review_report(conn, sermon_id):
    """Export complete review report data.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Complete report with sermon info, reviewers, and statistics.
    """
    cursor = conn.cursor()

    # Get sermon info
    cursor.execute(
        'SELECT id, title, content, status, created_at FROM sermons WHERE id = ?',
        (sermon_id,)
    )
    sermon_row = cursor.fetchone()

    sermon_info = {}
    if sermon_row:
        sermon_info = {
            'id': sermon_row['id'] if hasattr(sermon_row, 'keys') else sermon_row[0],
            'title': sermon_row['title'] if hasattr(sermon_row, 'keys') else sermon_row[1],
            'status': sermon_row['status'] if hasattr(sermon_row, 'keys') else sermon_row[3],
            'created_at': sermon_row['created_at'] if hasattr(sermon_row, 'keys') else sermon_row[4]
        }

    # Get review status
    status = get_review_status(conn, sermon_id)

    # Get all activity
    activity = list_reviewer_activity(conn, sermon_id)

    # Get progress
    progress = calculate_review_progress(conn, sermon_id)

    # Get feedback summary
    feedback = get_feedback_summary(conn, sermon_id)

    return {
        'sermon': sermon_info,
        'title': sermon_info.get('title', ''),
        'status': status,
        'reviewers': activity,
        'activity': activity,
        'progress': progress,
        'completion': progress,
        'feedback_summary': feedback,
        'generated_at': datetime.now().isoformat()
    }
