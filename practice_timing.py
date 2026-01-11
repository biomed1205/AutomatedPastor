"""Practice Timing Feature (Issue #222)

Phase 10: Polish - Item 1

Provides practice timing utilities:
- Timer management (start, pause, resume, stop)
- Session tracking (get session, history, average)
- Duration goals (set target, get target, check goal)
- Pacing feedback (calculate pace, get feedback, section timing)
- Statistics (timing stats, export report)
"""

from datetime import datetime


def start_practice_timer(conn, sermon_id):
    """Start a practice timer session.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon to practice.

    Returns:
        dict: Session info with id, sermon_id, started_at, status.
    """
    cursor = conn.cursor()

    # Check sermon exists
    cursor.execute('SELECT id FROM sermons WHERE id = ?', (sermon_id,))
    if not cursor.fetchone():
        return None

    started_at = datetime.now()
    cursor.execute('''
        INSERT INTO practice_sessions (sermon_id, started_at, status)
        VALUES (?, ?, ?)
    ''', (sermon_id, started_at.isoformat(), 'running'))
    conn.commit()

    return {
        'id': cursor.lastrowid,
        'session_id': cursor.lastrowid,
        'sermon_id': sermon_id,
        'started_at': started_at,
        'status': 'running',
    }


def pause_practice_timer(conn, session_id):
    """Pause a running practice timer.

    Args:
        conn: Database connection.
        session_id: ID of the session to pause.

    Returns:
        bool: True if paused, False if already paused or not found.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT status FROM practice_sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()

    if not row:
        return False

    status = row['status'] if hasattr(row, 'keys') else row[0]
    if status != 'running':
        return False

    paused_at = datetime.now()
    cursor.execute('''
        UPDATE practice_sessions
        SET status = ?, paused_at = ?
        WHERE id = ?
    ''', ('paused', paused_at.isoformat(), session_id))
    conn.commit()

    return True


def resume_practice_timer(conn, session_id):
    """Resume a paused practice timer.

    Args:
        conn: Database connection.
        session_id: ID of the session to resume.

    Returns:
        bool: True if resumed, False if not paused or not found.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT status, paused_at, total_paused_seconds
        FROM practice_sessions WHERE id = ?
    ''', (session_id,))
    row = cursor.fetchone()

    if not row:
        return False

    status = row['status'] if hasattr(row, 'keys') else row[0]
    if status != 'paused':
        return False

    paused_at_str = row['paused_at'] if hasattr(row, 'keys') else row[1]
    total_paused = row['total_paused_seconds'] if hasattr(row, 'keys') else row[2]
    total_paused = total_paused or 0

    if paused_at_str:
        paused_at = datetime.fromisoformat(paused_at_str)
        pause_duration = (datetime.now() - paused_at).total_seconds()
        total_paused += int(pause_duration)

    cursor.execute('''
        UPDATE practice_sessions
        SET status = ?, paused_at = NULL, total_paused_seconds = ?
        WHERE id = ?
    ''', ('running', total_paused, session_id))
    conn.commit()

    return True


def stop_practice_timer(conn, session_id):
    """Stop and save a practice timer session.

    Args:
        conn: Database connection.
        session_id: ID of the session to stop.

    Returns:
        dict: Completed session info with duration.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT started_at, paused_at, total_paused_seconds, status, sermon_id
        FROM practice_sessions WHERE id = ?
    ''', (session_id,))
    row = cursor.fetchone()

    if not row:
        return None

    started_at_str = row['started_at'] if hasattr(row, 'keys') else row[0]
    paused_at_str = row['paused_at'] if hasattr(row, 'keys') else row[1]
    total_paused = row['total_paused_seconds'] if hasattr(row, 'keys') else row[2]
    status = row['status'] if hasattr(row, 'keys') else row[3]
    sermon_id = row['sermon_id'] if hasattr(row, 'keys') else row[4]

    total_paused = total_paused or 0
    ended_at = datetime.now()

    # If paused, add remaining pause time
    if status == 'paused' and paused_at_str:
        paused_at = datetime.fromisoformat(paused_at_str)
        total_paused += int((ended_at - paused_at).total_seconds())

    started_at = datetime.fromisoformat(started_at_str)
    total_seconds = (ended_at - started_at).total_seconds()
    duration_seconds = int(total_seconds - total_paused)

    cursor.execute('''
        UPDATE practice_sessions
        SET status = ?, ended_at = ?, total_paused_seconds = ?
        WHERE id = ?
    ''', ('completed', ended_at.isoformat(), total_paused, session_id))
    conn.commit()

    return {
        'id': session_id,
        'sermon_id': sermon_id,
        'started_at': started_at_str,
        'ended_at': ended_at.isoformat(),
        'status': 'completed',
        'duration_seconds': duration_seconds,
        'total_paused_seconds': total_paused,
    }


def get_practice_session(conn, session_id):
    """Get a practice session by ID.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        dict: Session info or None if not found.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM practice_sessions WHERE id = ?', (session_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {
        'id': row['id'] if hasattr(row, 'keys') else row[0],
        'session_id': row['id'] if hasattr(row, 'keys') else row[0],
        'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
        'started_at': row['started_at'] if hasattr(row, 'keys') else row[2],
        'ended_at': row['ended_at'] if hasattr(row, 'keys') else row[3],
        'paused_at': row['paused_at'] if hasattr(row, 'keys') else row[4],
        'total_paused_seconds': row['total_paused_seconds'] if hasattr(row, 'keys') else row[5],
        'status': row['status'] if hasattr(row, 'keys') else row[6],
    }


def get_practice_history(conn, sermon_id):
    """Get all practice sessions for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        list: List of session dicts, newest first.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM practice_sessions
        WHERE sermon_id = ? AND status = 'completed'
        ORDER BY ended_at DESC
    ''', (sermon_id,))
    rows = cursor.fetchall()

    return [
        {
            'id': row['id'] if hasattr(row, 'keys') else row[0],
            'sermon_id': row['sermon_id'] if hasattr(row, 'keys') else row[1],
            'started_at': row['started_at'] if hasattr(row, 'keys') else row[2],
            'ended_at': row['ended_at'] if hasattr(row, 'keys') else row[3],
            'status': row['status'] if hasattr(row, 'keys') else row[6],
        }
        for row in rows
    ]


def get_average_duration(conn, sermon_id):
    """Calculate average practice duration for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        float: Average duration in seconds, or None if no sessions.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT started_at, ended_at, total_paused_seconds
        FROM practice_sessions
        WHERE sermon_id = ? AND status = 'completed'
    ''', (sermon_id,))
    rows = cursor.fetchall()

    if not rows:
        return None

    total_duration = 0
    for row in rows:
        started = row['started_at'] if hasattr(row, 'keys') else row[0]
        ended = row['ended_at'] if hasattr(row, 'keys') else row[1]
        paused = row['total_paused_seconds'] if hasattr(row, 'keys') else row[2]
        paused = paused or 0

        start_dt = datetime.fromisoformat(started)
        end_dt = datetime.fromisoformat(ended)
        duration = (end_dt - start_dt).total_seconds() - paused
        total_duration += duration

    return total_duration / len(rows)


def set_target_duration(conn, sermon_id, minutes):
    """Set target duration for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        minutes: Target duration in minutes.

    Returns:
        bool: True if set, False if invalid.
    """
    if minutes <= 0:
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM timing_goals WHERE sermon_id = ?', (sermon_id,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE timing_goals SET target_minutes = ?, updated_at = ?
            WHERE sermon_id = ?
        ''', (minutes, datetime.now().isoformat(), sermon_id))
    else:
        cursor.execute('''
            INSERT INTO timing_goals (sermon_id, target_minutes)
            VALUES (?, ?)
        ''', (sermon_id, minutes))

    conn.commit()
    return True


def get_target_duration(conn, sermon_id):
    """Get target duration for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        int: Target duration in minutes, or 15 as default.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT target_minutes FROM timing_goals WHERE sermon_id = ?', (sermon_id,))
    row = cursor.fetchone()

    if row:
        return row['target_minutes'] if hasattr(row, 'keys') else row[0]

    return 15  # Default 15 minutes


def check_duration_goal(conn, session_id):
    """Check if a session met the duration goal.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        dict: Goal check result with met, under, over, difference.
    """
    session = get_practice_session(conn, session_id)
    if not session:
        return {'error': 'Session not found'}

    sermon_id = session['sermon_id']
    target_minutes = get_target_duration(conn, sermon_id)
    target_seconds = target_minutes * 60

    # Calculate session duration
    started = datetime.fromisoformat(session['started_at'])
    ended_str = session.get('ended_at')

    if ended_str:
        ended = datetime.fromisoformat(ended_str)
    else:
        ended = datetime.now()

    paused = session.get('total_paused_seconds', 0) or 0
    duration_seconds = (ended - started).total_seconds() - paused

    difference = duration_seconds - target_seconds
    tolerance = 60  # 1 minute tolerance

    return {
        'met': abs(difference) <= tolerance,
        'goal_met': abs(difference) <= tolerance,
        'under': difference < -tolerance,
        'over': difference > tolerance,
        'difference': int(difference),
        'target_seconds': target_seconds,
        'actual_seconds': int(duration_seconds),
    }


def calculate_pace(conn, session_id):
    """Calculate words per minute for a session.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        dict: Pace info with wpm, or None if cannot calculate.
    """
    session = get_practice_session(conn, session_id)
    if not session:
        return None

    cursor = conn.cursor()
    cursor.execute('SELECT word_count FROM sermons WHERE id = ?', (session['sermon_id'],))
    row = cursor.fetchone()

    if not row:
        return None

    word_count = row['word_count'] if hasattr(row, 'keys') else row[0]
    if not word_count:
        return {'wpm': 0, 'unknown': True}

    # Calculate duration
    started = datetime.fromisoformat(session['started_at'])
    ended_str = session.get('ended_at')
    if ended_str:
        ended = datetime.fromisoformat(ended_str)
    else:
        ended = datetime.now()

    paused = session.get('total_paused_seconds', 0) or 0
    duration_seconds = (ended - started).total_seconds() - paused
    duration_minutes = duration_seconds / 60

    if duration_minutes <= 0:
        return {'wpm': 0}

    wpm = word_count / duration_minutes

    return {
        'wpm': int(wpm),
        'words_per_minute': int(wpm),
        'word_count': word_count,
        'duration_minutes': round(duration_minutes, 2),
    }


def get_pacing_feedback(conn, session_id):
    """Get pacing feedback for a session.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        dict: Feedback with status and recommendations.
    """
    pace = calculate_pace(conn, session_id)
    if not pace or pace.get('unknown'):
        return {'feedback': 'Unable to calculate pace', 'status': 'unknown'}

    wpm = pace.get('wpm', 0)

    # Ideal speaking pace is 120-150 WPM
    if wpm < 100:
        return {
            'feedback': 'Speaking too slow',
            'status': 'slow',
            'wpm': wpm,
            'recommendation': 'Try to speed up your delivery',
            'suggestion': 'Target 120-150 words per minute',
        }
    elif wpm > 180:
        return {
            'feedback': 'Speaking too fast',
            'status': 'fast',
            'wpm': wpm,
            'recommendation': 'Try to slow down for clarity',
            'suggestion': 'Target 120-150 words per minute',
        }
    else:
        return {
            'feedback': 'Good pacing',
            'status': 'good',
            'wpm': wpm,
            'recommendation': 'Keep up the good pace',
            'ideal': True,
        }


def get_section_timing(conn, session_id):
    """Get timing for each section of a session.

    Args:
        conn: Database connection.
        session_id: ID of the session.

    Returns:
        list: Section timing info.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM section_timings
        WHERE session_id = ?
        ORDER BY section_index
    ''', (session_id,))
    rows = cursor.fetchall()

    return [
        {
            'section_name': row['section_name'] if hasattr(row, 'keys') else row[2],
            'section_index': row['section_index'] if hasattr(row, 'keys') else row[3],
            'start_time_seconds': row['start_time_seconds'] if hasattr(row, 'keys') else row[4],
            'end_time_seconds': row['end_time_seconds'] if hasattr(row, 'keys') else row[5],
            'duration': (row['end_time_seconds'] if hasattr(row, 'keys') else row[5]) -
                        (row['start_time_seconds'] if hasattr(row, 'keys') else row[4]),
        }
        for row in rows
    ]


def get_timing_stats(conn, sermon_id):
    """Get comprehensive timing statistics for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Timing statistics.
    """
    cursor = conn.cursor()

    cursor.execute('''
        SELECT started_at, ended_at, total_paused_seconds
        FROM practice_sessions
        WHERE sermon_id = ? AND status = 'completed'
        ORDER BY ended_at
    ''', (sermon_id,))
    rows = cursor.fetchall()

    if not rows:
        return {
            'count': 0,
            'session_count': 0,
            'total_sessions': 0,
            'average': None,
            'min': None,
            'max': None,
        }

    durations = []
    for row in rows:
        started = row['started_at'] if hasattr(row, 'keys') else row[0]
        ended = row['ended_at'] if hasattr(row, 'keys') else row[1]
        paused = row['total_paused_seconds'] if hasattr(row, 'keys') else row[2]
        paused = paused or 0

        start_dt = datetime.fromisoformat(started)
        end_dt = datetime.fromisoformat(ended)
        duration = (end_dt - start_dt).total_seconds() - paused
        durations.append(duration)

    # Calculate trend (improvement if durations are getting closer to 15 min = 900s)
    target = 900
    if len(durations) >= 2:
        first_diff = abs(durations[0] - target)
        last_diff = abs(durations[-1] - target)
        trend = 'improving' if last_diff < first_diff else 'no improvement'
    else:
        trend = 'insufficient data'

    return {
        'count': len(durations),
        'session_count': len(durations),
        'total_sessions': len(durations),
        'average': sum(durations) / len(durations),
        'min': min(durations),
        'max': max(durations),
        'shortest': min(durations),
        'longest': max(durations),
        'trend': trend,
        'improvement': trend,
        'progress': trend,
    }


def export_timing_report(conn, sermon_id):
    """Export a timing report for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        dict: Comprehensive timing report.
    """
    cursor = conn.cursor()

    cursor.execute('SELECT title, word_count FROM sermons WHERE id = ?', (sermon_id,))
    row = cursor.fetchone()

    if not row:
        return {'error': 'Sermon not found'}

    title = row['title'] if hasattr(row, 'keys') else row[0]
    word_count = row['word_count'] if hasattr(row, 'keys') else row[1]

    stats = get_timing_stats(conn, sermon_id)
    history = get_practice_history(conn, sermon_id)
    target = get_target_duration(conn, sermon_id)

    return {
        'title': title,
        'sermon_id': sermon_id,
        'word_count': word_count,
        'target_minutes': target,
        'statistics': stats,
        'sessions': history,
        'session_count': len(history),
        'report_generated': datetime.now().isoformat(),
    }
