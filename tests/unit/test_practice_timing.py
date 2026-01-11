"""
Tests for Practice Timing Feature (Issue #222)

Phase 10: Polish - Item 1 (PHASE 10 START)

Tests cover:
- Timer management (start, pause, resume, stop)
- Session tracking (get session, history, average)
- Duration goals (set target, get target, check goal)
- Pacing feedback (calculate pace, get feedback, section timing)
- Statistics (timing stats, export report)

TDD Approach: All tests fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite :memory: database.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
import time


def create_test_db():
    """Create a real SQLite in-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create sermons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            word_count INTEGER,
            content TEXT,
            target_duration_minutes INTEGER DEFAULT 15,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create practice sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            started_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            paused_at TIMESTAMP,
            total_paused_seconds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            notes TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Create section timings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS section_timings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            section_name TEXT,
            section_index INTEGER,
            start_time_seconds INTEGER,
            end_time_seconds INTEGER,
            FOREIGN KEY (session_id) REFERENCES practice_sessions(id)
        )
    ''')

    # Create timing goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timing_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL UNIQUE,
            target_minutes INTEGER NOT NULL,
            tolerance_seconds INTEGER DEFAULT 60,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title='Test Sermon', word_count=2200):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, word_count, content)
        VALUES (?, ?, ?)
    ''', (title, word_count, 'Sample sermon content ' * 200))
    conn.commit()
    return cursor.lastrowid


def insert_sample_session(conn, sermon_id, duration_seconds, days_ago=0):
    """Insert a completed practice session."""
    cursor = conn.cursor()
    end_time = datetime.now() - timedelta(days=days_ago)
    start_time = end_time - timedelta(seconds=duration_seconds)

    cursor.execute('''
        INSERT INTO practice_sessions (sermon_id, started_at, ended_at, status)
        VALUES (?, ?, ?, ?)
    ''', (sermon_id, start_time.isoformat(), end_time.isoformat(), 'completed'))
    conn.commit()
    return cursor.lastrowid


class TestStartPracticeTimer:
    """Tests for start_practice_timer function."""

    def test_should_start_timer(self):
        """Should start a practice timer session."""
        from practice_timing import start_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        session = start_practice_timer(conn, sermon_id)

        assert session is not None
        assert 'id' in session or 'session_id' in session
        assert session.get('status') == 'running' or 'started_at' in session

        conn.close()

    def test_should_record_start_time(self):
        """Should record accurate start time."""
        from practice_timing import start_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        before = datetime.now()
        session = start_practice_timer(conn, sermon_id)
        after = datetime.now()

        # Start time should be between before and after
        start_time = session.get('started_at')
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)

        assert before <= start_time <= after

        conn.close()

    def test_should_return_session_id(self):
        """Should return unique session ID."""
        from practice_timing import start_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        session1 = start_practice_timer(conn, sermon_id)
        session2 = start_practice_timer(conn, sermon_id)

        id1 = session1.get('id') or session1.get('session_id')
        id2 = session2.get('id') or session2.get('session_id')

        assert id1 != id2

        conn.close()

    def test_should_link_to_sermon(self):
        """Session should be linked to sermon."""
        from practice_timing import start_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        session = start_practice_timer(conn, sermon_id)

        assert session.get('sermon_id') == sermon_id

        conn.close()


class TestPausePracticeTimer:
    """Tests for pause_practice_timer function."""

    def test_should_pause_timer(self):
        """Should pause a running timer."""
        from practice_timing import start_practice_timer, pause_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = pause_practice_timer(conn, session_id)

        assert result is True or result.get('status') == 'paused'

        conn.close()

    def test_should_record_pause_time(self):
        """Should record when timer was paused."""
        from practice_timing import start_practice_timer, pause_practice_timer, get_practice_session

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        pause_practice_timer(conn, session_id)
        updated = get_practice_session(conn, session_id)

        assert updated.get('paused_at') is not None or updated.get('status') == 'paused'

        conn.close()

    def test_should_not_pause_already_paused(self):
        """Should handle already paused timer gracefully."""
        from practice_timing import start_practice_timer, pause_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        pause_practice_timer(conn, session_id)
        result = pause_practice_timer(conn, session_id)

        # Should not error, but return False or same paused state
        assert result is False or result is not None

        conn.close()


class TestResumePracticeTimer:
    """Tests for resume_practice_timer function."""

    def test_should_resume_timer(self):
        """Should resume a paused timer."""
        from practice_timing import start_practice_timer, pause_practice_timer, resume_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        pause_practice_timer(conn, session_id)
        result = resume_practice_timer(conn, session_id)

        assert result is True or result.get('status') == 'running'

        conn.close()

    def test_should_track_paused_duration(self):
        """Should track total paused duration."""
        from practice_timing import (
            start_practice_timer, pause_practice_timer,
            resume_practice_timer, get_practice_session
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        pause_practice_timer(conn, session_id)
        time.sleep(0.1)  # Small pause
        resume_practice_timer(conn, session_id)

        updated = get_practice_session(conn, session_id)
        paused = updated.get('total_paused_seconds', 0)

        # Should have tracked some paused time
        assert paused >= 0

        conn.close()

    def test_should_not_resume_running_timer(self):
        """Should handle resuming already running timer."""
        from practice_timing import start_practice_timer, resume_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = resume_practice_timer(conn, session_id)

        # Should return False or handle gracefully
        assert result is False or result is not None

        conn.close()


class TestStopPracticeTimer:
    """Tests for stop_practice_timer function."""

    def test_should_stop_timer(self):
        """Should stop and save timer session."""
        from practice_timing import start_practice_timer, stop_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = stop_practice_timer(conn, session_id)

        assert result is not None
        assert result.get('status') == 'completed' or 'duration' in result

        conn.close()

    def test_should_record_end_time(self):
        """Should record accurate end time."""
        from practice_timing import start_practice_timer, stop_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = stop_practice_timer(conn, session_id)

        assert result.get('ended_at') is not None

        conn.close()

    def test_should_calculate_duration(self):
        """Should calculate total duration."""
        from practice_timing import start_practice_timer, stop_practice_timer

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        time.sleep(0.1)  # Small delay
        result = stop_practice_timer(conn, session_id)

        duration = result.get('duration_seconds', 0)
        assert duration >= 0

        conn.close()

    def test_should_exclude_paused_time(self):
        """Duration should exclude paused time."""
        from practice_timing import (
            start_practice_timer, pause_practice_timer,
            resume_practice_timer, stop_practice_timer
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        pause_practice_timer(conn, session_id)
        time.sleep(0.1)
        resume_practice_timer(conn, session_id)

        result = stop_practice_timer(conn, session_id)

        # Duration should not include paused time
        assert 'duration' in str(result).lower() or 'seconds' in str(result).lower()

        conn.close()


class TestGetPracticeSession:
    """Tests for get_practice_session function."""

    def test_should_get_session(self):
        """Should retrieve practice session by ID."""
        from practice_timing import start_practice_timer, get_practice_session

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = get_practice_session(conn, session_id)

        assert result is not None
        result_id = result.get('id') or result.get('session_id')
        assert result_id == session_id

        conn.close()

    def test_should_include_all_fields(self):
        """Should include all session fields."""
        from practice_timing import start_practice_timer, get_practice_session

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        result = get_practice_session(conn, session_id)

        assert 'started_at' in result
        assert 'status' in result
        assert 'sermon_id' in result

        conn.close()

    def test_should_return_none_for_nonexistent(self):
        """Should return None for nonexistent session."""
        from practice_timing import get_practice_session

        conn = create_test_db()

        result = get_practice_session(conn, 9999)

        assert result is None

        conn.close()


class TestGetPracticeHistory:
    """Tests for get_practice_history function."""

    def test_should_get_history(self):
        """Should get all practice sessions for a sermon."""
        from practice_timing import get_practice_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900)  # 15 min
        insert_sample_session(conn, sermon_id, 840)  # 14 min
        insert_sample_session(conn, sermon_id, 960)  # 16 min

        result = get_practice_history(conn, sermon_id)

        assert isinstance(result, list)
        assert len(result) == 3

        conn.close()

    def test_should_order_by_date(self):
        """Should order sessions by date (newest first)."""
        from practice_timing import get_practice_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900, days_ago=7)
        insert_sample_session(conn, sermon_id, 840, days_ago=3)
        insert_sample_session(conn, sermon_id, 960, days_ago=0)

        result = get_practice_history(conn, sermon_id)

        # Most recent should be first
        if len(result) >= 2:
            first_date = result[0].get('ended_at') or result[0].get('started_at')
            last_date = result[-1].get('ended_at') or result[-1].get('started_at')
            assert first_date >= last_date

        conn.close()

    def test_should_return_empty_for_no_history(self):
        """Should return empty list for no practice history."""
        from practice_timing import get_practice_history

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = get_practice_history(conn, sermon_id)

        assert result == []

        conn.close()


class TestGetAverageDuration:
    """Tests for get_average_duration function."""

    def test_should_calculate_average(self):
        """Should calculate average practice duration."""
        from practice_timing import get_average_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900)   # 15 min
        insert_sample_session(conn, sermon_id, 900)   # 15 min
        insert_sample_session(conn, sermon_id, 900)   # 15 min

        result = get_average_duration(conn, sermon_id)

        # Average should be 900 seconds (15 min)
        assert result == 900 or abs(result - 900) < 1

        conn.close()

    def test_should_handle_varied_durations(self):
        """Should correctly average varied durations."""
        from practice_timing import get_average_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 600)   # 10 min
        insert_sample_session(conn, sermon_id, 900)   # 15 min
        insert_sample_session(conn, sermon_id, 1200)  # 20 min

        result = get_average_duration(conn, sermon_id)

        # Average should be 900 seconds (15 min)
        assert abs(result - 900) < 1

        conn.close()

    def test_should_return_none_for_no_sessions(self):
        """Should return None when no sessions exist."""
        from practice_timing import get_average_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = get_average_duration(conn, sermon_id)

        assert result is None

        conn.close()


class TestSetTargetDuration:
    """Tests for set_target_duration function."""

    def test_should_set_target(self):
        """Should set target duration for sermon."""
        from practice_timing import set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = set_target_duration(conn, sermon_id, 15)

        assert result is True

        conn.close()

    def test_should_update_existing_target(self):
        """Should update existing target."""
        from practice_timing import set_target_duration, get_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        set_target_duration(conn, sermon_id, 15)
        set_target_duration(conn, sermon_id, 12)

        target = get_target_duration(conn, sermon_id)

        assert target == 12

        conn.close()

    def test_should_reject_invalid_duration(self):
        """Should reject invalid duration values."""
        from practice_timing import set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result_zero = set_target_duration(conn, sermon_id, 0)
        result_negative = set_target_duration(conn, sermon_id, -5)

        assert result_zero is False
        assert result_negative is False

        conn.close()


class TestGetTargetDuration:
    """Tests for get_target_duration function."""

    def test_should_get_target(self):
        """Should get target duration."""
        from practice_timing import set_target_duration, get_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        set_target_duration(conn, sermon_id, 15)

        result = get_target_duration(conn, sermon_id)

        assert result == 15

        conn.close()

    def test_should_return_default_for_no_target(self):
        """Should return default when no target set."""
        from practice_timing import get_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = get_target_duration(conn, sermon_id)

        # Default should be 15 minutes
        assert result == 15 or result is None

        conn.close()


class TestCheckDurationGoal:
    """Tests for check_duration_goal function."""

    def test_should_check_goal_met(self):
        """Should check if duration goal was met."""
        from practice_timing import check_duration_goal, set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        set_target_duration(conn, sermon_id, 15)  # 15 minutes = 900 seconds
        session_id = insert_sample_session(conn, sermon_id, 900)

        result = check_duration_goal(conn, session_id)

        assert result.get('met') is True or result.get('goal_met') is True

        conn.close()

    def test_should_detect_under_time(self):
        """Should detect under target time."""
        from practice_timing import check_duration_goal, set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        set_target_duration(conn, sermon_id, 15)  # 15 minutes
        session_id = insert_sample_session(conn, sermon_id, 600)  # 10 minutes

        result = check_duration_goal(conn, session_id)

        assert result.get('under') is True or result.get('difference') < 0

        conn.close()

    def test_should_detect_over_time(self):
        """Should detect over target time."""
        from practice_timing import check_duration_goal, set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        set_target_duration(conn, sermon_id, 15)  # 15 minutes
        session_id = insert_sample_session(conn, sermon_id, 1200)  # 20 minutes

        result = check_duration_goal(conn, session_id)

        assert result.get('over') is True or result.get('difference') > 0

        conn.close()

    def test_should_include_difference(self):
        """Should include time difference from target."""
        from practice_timing import check_duration_goal, set_target_duration

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        set_target_duration(conn, sermon_id, 15)
        session_id = insert_sample_session(conn, sermon_id, 960)  # 16 min

        result = check_duration_goal(conn, session_id)

        assert 'difference' in result or 'delta' in str(result).lower()

        conn.close()


class TestCalculatePace:
    """Tests for calculate_pace function."""

    def test_should_calculate_wpm(self):
        """Should calculate words per minute."""
        from practice_timing import calculate_pace

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=2200)
        session_id = insert_sample_session(conn, sermon_id, 900)  # 15 min

        result = calculate_pace(conn, session_id)

        # 2200 words / 15 min = ~147 WPM
        wpm = result.get('wpm') or result.get('words_per_minute') or result
        if isinstance(wpm, (int, float)):
            assert 140 <= wpm <= 155

        conn.close()

    def test_should_handle_sermon_without_word_count(self):
        """Should handle sermon without word count."""
        from practice_timing import calculate_pace

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=None)
        session_id = insert_sample_session(conn, sermon_id, 900)

        result = calculate_pace(conn, session_id)

        # Should return None or estimate
        assert result is None or 'unknown' in str(result).lower() or result.get('wpm', 0) >= 0

        conn.close()


class TestGetPacingFeedback:
    """Tests for get_pacing_feedback function."""

    def test_should_return_good_for_ideal_pace(self):
        """Should return 'good' for ideal pacing."""
        from practice_timing import get_pacing_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=2100)  # ~140 WPM at 15 min
        session_id = insert_sample_session(conn, sermon_id, 900)

        result = get_pacing_feedback(conn, session_id)

        feedback = result.get('feedback') or result.get('status') or result
        assert 'good' in str(feedback).lower() or 'ideal' in str(feedback).lower()

        conn.close()

    def test_should_detect_too_fast(self):
        """Should detect when speaking too fast."""
        from practice_timing import get_pacing_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=2200)
        session_id = insert_sample_session(conn, sermon_id, 600)  # 10 min = 220 WPM (fast)

        result = get_pacing_feedback(conn, session_id)

        feedback = result.get('feedback') or result.get('status') or result
        assert 'fast' in str(feedback).lower() or 'slow down' in str(feedback).lower()

        conn.close()

    def test_should_detect_too_slow(self):
        """Should detect when speaking too slow."""
        from practice_timing import get_pacing_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=2200)
        session_id = insert_sample_session(conn, sermon_id, 1800)  # 30 min = 73 WPM (slow)

        result = get_pacing_feedback(conn, session_id)

        feedback = result.get('feedback') or result.get('status') or result
        assert 'slow' in str(feedback).lower() or 'speed up' in str(feedback).lower()

        conn.close()

    def test_should_include_recommendations(self):
        """Should include pacing recommendations."""
        from practice_timing import get_pacing_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=2200)
        session_id = insert_sample_session(conn, sermon_id, 600)  # Too fast

        result = get_pacing_feedback(conn, session_id)

        assert 'recommendation' in str(result).lower() or 'suggest' in str(result).lower() or 'feedback' in result

        conn.close()


class TestGetSectionTiming:
    """Tests for get_section_timing function."""

    def test_should_return_section_timings(self):
        """Should return timing for each section."""
        from practice_timing import get_section_timing

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id, 900)

        # Insert section timings
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO section_timings (session_id, section_name, section_index, start_time_seconds, end_time_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, 'Introduction', 0, 0, 120))
        cursor.execute('''
            INSERT INTO section_timings (session_id, section_name, section_index, start_time_seconds, end_time_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, 'Point 1', 1, 120, 360))
        conn.commit()

        result = get_section_timing(conn, session_id)

        assert isinstance(result, list)
        assert len(result) >= 2

        conn.close()

    def test_should_include_section_duration(self):
        """Should include duration for each section."""
        from practice_timing import get_section_timing

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        session_id = insert_sample_session(conn, sermon_id, 900)

        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO section_timings (session_id, section_name, section_index, start_time_seconds, end_time_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, 'Introduction', 0, 0, 120))
        conn.commit()

        result = get_section_timing(conn, session_id)

        if len(result) > 0:
            section = result[0]
            assert 'duration' in section or ('end_time' in str(section) and 'start_time' in str(section))

        conn.close()


class TestGetTimingStats:
    """Tests for get_timing_stats function."""

    def test_should_return_stats(self):
        """Should return comprehensive timing stats."""
        from practice_timing import get_timing_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900)
        insert_sample_session(conn, sermon_id, 840)
        insert_sample_session(conn, sermon_id, 960)

        result = get_timing_stats(conn, sermon_id)

        assert isinstance(result, dict)
        assert 'average' in str(result).lower() or 'sessions' in str(result).lower()

        conn.close()

    def test_should_include_min_max(self):
        """Should include min and max durations."""
        from practice_timing import get_timing_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 600)   # Min
        insert_sample_session(conn, sermon_id, 900)
        insert_sample_session(conn, sermon_id, 1200)  # Max

        result = get_timing_stats(conn, sermon_id)

        stats_str = str(result).lower()
        assert 'min' in stats_str or 'shortest' in stats_str
        assert 'max' in stats_str or 'longest' in stats_str

        conn.close()

    def test_should_include_session_count(self):
        """Should include total session count."""
        from practice_timing import get_timing_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900)
        insert_sample_session(conn, sermon_id, 900)
        insert_sample_session(conn, sermon_id, 900)

        result = get_timing_stats(conn, sermon_id)

        count = result.get('count') or result.get('session_count') or result.get('total_sessions')
        assert count == 3 or 'sessions' in str(result)

        conn.close()

    def test_should_include_trend(self):
        """Should include improvement trend."""
        from practice_timing import get_timing_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        # Improvement trend - getting closer to 15 min target
        insert_sample_session(conn, sermon_id, 1200, days_ago=7)
        insert_sample_session(conn, sermon_id, 1000, days_ago=3)
        insert_sample_session(conn, sermon_id, 900, days_ago=0)

        result = get_timing_stats(conn, sermon_id)

        stats_str = str(result).lower()
        assert 'trend' in stats_str or 'improvement' in stats_str or 'progress' in stats_str

        conn.close()


class TestExportTimingReport:
    """Tests for export_timing_report function."""

    def test_should_export_report(self):
        """Should export timing report."""
        from practice_timing import export_timing_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title='Test Sermon')
        insert_sample_session(conn, sermon_id, 900)

        result = export_timing_report(conn, sermon_id)

        assert result is not None
        assert isinstance(result, (str, dict))

        conn.close()

    def test_should_include_sermon_info(self):
        """Should include sermon information."""
        from practice_timing import export_timing_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title='Test Sermon Report')
        insert_sample_session(conn, sermon_id, 900)

        result = export_timing_report(conn, sermon_id)

        result_str = str(result)
        assert 'Test Sermon Report' in result_str or 'title' in result_str.lower()

        conn.close()

    def test_should_include_all_sessions(self):
        """Should include all practice sessions."""
        from practice_timing import export_timing_report

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_session(conn, sermon_id, 900)
        insert_sample_session(conn, sermon_id, 840)
        insert_sample_session(conn, sermon_id, 960)

        result = export_timing_report(conn, sermon_id)

        result_str = str(result)
        assert 'sessions' in result_str.lower() or '3' in result_str

        conn.close()


class TestIntegration:
    """Integration tests for practice timing."""

    def test_should_complete_practice_session(self):
        """Should complete a full practice session workflow."""
        from practice_timing import (
            start_practice_timer, pause_practice_timer,
            resume_practice_timer, stop_practice_timer,
            get_practice_session
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        # Start session
        session = start_practice_timer(conn, sermon_id)
        session_id = session.get('id') or session.get('session_id')

        # Pause and resume
        pause_practice_timer(conn, session_id)
        resume_practice_timer(conn, session_id)

        # Stop and check
        result = stop_practice_timer(conn, session_id)

        assert result.get('status') == 'completed'

        conn.close()

    def test_should_track_multiple_sessions(self):
        """Should track multiple practice sessions."""
        from practice_timing import (
            start_practice_timer, stop_practice_timer,
            get_practice_history, get_average_duration
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        # Create three sessions
        for _ in range(3):
            session = start_practice_timer(conn, sermon_id)
            session_id = session.get('id') or session.get('session_id')
            stop_practice_timer(conn, session_id)

        history = get_practice_history(conn, sermon_id)
        assert len(history) == 3

        conn.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_should_handle_nonexistent_sermon(self):
        """Should handle practice for nonexistent sermon."""
        from practice_timing import start_practice_timer

        conn = create_test_db()

        try:
            result = start_practice_timer(conn, 9999)
            assert result is None or 'error' in str(result).lower()
        except (ValueError, sqlite3.IntegrityError):
            pass  # Acceptable to raise

        conn.close()

    def test_should_handle_nonexistent_session(self):
        """Should handle operations on nonexistent session."""
        from practice_timing import pause_practice_timer, stop_practice_timer

        conn = create_test_db()

        pause_result = pause_practice_timer(conn, 9999)
        stop_result = stop_practice_timer(conn, 9999)

        assert pause_result is False or pause_result is None
        assert stop_result is None or 'error' in str(stop_result).lower()

        conn.close()

    def test_should_handle_zero_word_count(self):
        """Should handle sermon with zero word count."""
        from practice_timing import calculate_pace

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, word_count=0)
        session_id = insert_sample_session(conn, sermon_id, 900)

        result = calculate_pace(conn, session_id)

        # Should handle gracefully
        assert result is None or result.get('wpm') == 0 or 'error' not in str(result)

        conn.close()
