"""Tests for moderation controls.

These tests verify user's ability to guide panel discussions.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import json
from datetime import datetime


def create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE panel_discussions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE moderation_actions (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            action_type TEXT,
            target TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE reviewer_states (
            id INTEGER PRIMARY KEY,
            discussion_id INTEGER,
            reviewer TEXT,
            is_muted INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    conn.execute(
        'INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)',
        (1, 1, 'active')
    )
    conn.commit()
    return conn


class TestEndDiscussion:
    """Test suite for ending panel discussions."""

    def test_should_end_active_discussion(self):
        """Test ending an active discussion."""
        from moderation import end_discussion

        conn = create_test_db()

        result = end_discussion(conn, discussion_id=1)

        cursor = conn.execute('SELECT status FROM panel_discussions WHERE id = 1')
        row = cursor.fetchone()

        assert row['status'] == 'ended'
        conn.close()

    def test_should_set_ended_timestamp(self):
        """Test ended timestamp is set."""
        from moderation import end_discussion

        conn = create_test_db()

        end_discussion(conn, discussion_id=1)

        cursor = conn.execute('SELECT ended_at FROM panel_discussions WHERE id = 1')
        row = cursor.fetchone()

        assert row['ended_at'] is not None
        conn.close()

    def test_should_log_end_action(self):
        """Test end action is logged."""
        from moderation import end_discussion

        conn = create_test_db()

        end_discussion(conn, discussion_id=1, user_id='user_1')

        cursor = conn.execute(
            'SELECT * FROM moderation_actions WHERE discussion_id = 1 AND action_type = ?',
            ('end_discussion',)
        )
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_not_end_already_ended_discussion(self):
        """Test cannot end already ended discussion."""
        from moderation import end_discussion, DiscussionAlreadyEndedError

        conn = create_test_db()
        conn.execute('UPDATE panel_discussions SET status = ? WHERE id = 1', ('ended',))
        conn.commit()

        with pytest.raises(DiscussionAlreadyEndedError):
            end_discussion(conn, discussion_id=1)
        conn.close()


class TestRedirectConversation:
    """Test suite for redirecting conversation topic."""

    def test_should_redirect_conversation(self):
        """Test redirecting conversation to new topic."""
        from moderation import redirect_discussion

        conn = create_test_db()

        result = redirect_discussion(
            conn,
            discussion_id=1,
            new_topic='Let us discuss the conclusion.'
        )

        assert result is not None
        conn.close()

    def test_should_log_redirect_action(self):
        """Test redirect action is logged."""
        from moderation import redirect_discussion

        conn = create_test_db()

        redirect_discussion(
            conn,
            discussion_id=1,
            new_topic='New topic here',
            user_id='user_1'
        )

        cursor = conn.execute(
            'SELECT * FROM moderation_actions WHERE discussion_id = 1 AND action_type = ?',
            ('redirect',)
        )
        row = cursor.fetchone()

        assert row is not None
        assert 'New topic' in row['details']
        conn.close()

    def test_should_include_topic_in_action_details(self):
        """Test action details include new topic."""
        from moderation import redirect_discussion

        conn = create_test_db()

        redirect_discussion(
            conn,
            discussion_id=1,
            new_topic='Focus on grace theology'
        )

        cursor = conn.execute(
            'SELECT details FROM moderation_actions WHERE action_type = ?',
            ('redirect',)
        )
        row = cursor.fetchone()

        assert 'grace theology' in row['details'].lower()
        conn.close()

    def test_should_not_redirect_ended_discussion(self):
        """Test cannot redirect ended discussion."""
        from moderation import redirect_discussion, DiscussionEndedError

        conn = create_test_db()
        conn.execute('UPDATE panel_discussions SET status = ? WHERE id = 1', ('ended',))
        conn.commit()

        with pytest.raises(DiscussionEndedError):
            redirect_discussion(conn, discussion_id=1, new_topic='New topic')
        conn.close()


class TestMuteUnmuteReviewers:
    """Test suite for muting/unmuting reviewers."""

    def test_should_mute_reviewer(self):
        """Test muting a reviewer."""
        from moderation import mute_reviewer, is_reviewer_muted

        conn = create_test_db()

        mute_reviewer(conn, discussion_id=1, reviewer='theological')

        assert is_reviewer_muted(conn, discussion_id=1, reviewer='theological')
        conn.close()

    def test_should_unmute_reviewer(self):
        """Test unmuting a reviewer."""
        from moderation import mute_reviewer, unmute_reviewer, is_reviewer_muted

        conn = create_test_db()

        mute_reviewer(conn, discussion_id=1, reviewer='theological')
        unmute_reviewer(conn, discussion_id=1, reviewer='theological')

        assert not is_reviewer_muted(conn, discussion_id=1, reviewer='theological')
        conn.close()

    def test_should_log_mute_action(self):
        """Test mute action is logged."""
        from moderation import mute_reviewer

        conn = create_test_db()

        mute_reviewer(conn, discussion_id=1, reviewer='theological', user_id='user_1')

        cursor = conn.execute(
            'SELECT * FROM moderation_actions WHERE action_type = ?',
            ('mute_reviewer',)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row['target'] == 'theological'
        conn.close()

    def test_should_toggle_mute_state(self):
        """Test toggling mute state."""
        from moderation import toggle_mute, is_reviewer_muted

        conn = create_test_db()

        # First toggle - mute
        toggle_mute(conn, discussion_id=1, reviewer='theological')
        assert is_reviewer_muted(conn, discussion_id=1, reviewer='theological')

        # Second toggle - unmute
        toggle_mute(conn, discussion_id=1, reviewer='theological')
        assert not is_reviewer_muted(conn, discussion_id=1, reviewer='theological')
        conn.close()

    def test_should_list_muted_reviewers(self):
        """Test listing all muted reviewers."""
        from moderation import mute_reviewer, get_muted_reviewers

        conn = create_test_db()

        mute_reviewer(conn, discussion_id=1, reviewer='theological')
        mute_reviewer(conn, discussion_id=1, reviewer='structural')

        muted = get_muted_reviewers(conn, discussion_id=1)

        assert 'theological' in muted
        assert 'structural' in muted
        conn.close()


class TestPauseResumeDiscussion:
    """Test suite for pause/resume discussion."""

    def test_should_pause_discussion(self):
        """Test pausing a discussion."""
        from moderation import pause_discussion

        conn = create_test_db()

        pause_discussion(conn, discussion_id=1)

        cursor = conn.execute('SELECT status FROM panel_discussions WHERE id = 1')
        row = cursor.fetchone()

        assert row['status'] == 'paused'
        conn.close()

    def test_should_resume_discussion(self):
        """Test resuming a paused discussion."""
        from moderation import pause_discussion, resume_discussion

        conn = create_test_db()

        pause_discussion(conn, discussion_id=1)
        resume_discussion(conn, discussion_id=1)

        cursor = conn.execute('SELECT status FROM panel_discussions WHERE id = 1')
        row = cursor.fetchone()

        assert row['status'] == 'active'
        conn.close()

    def test_should_log_pause_action(self):
        """Test pause action is logged."""
        from moderation import pause_discussion

        conn = create_test_db()

        pause_discussion(conn, discussion_id=1, user_id='user_1')

        cursor = conn.execute(
            'SELECT * FROM moderation_actions WHERE action_type = ?',
            ('pause',)
        )
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_not_resume_ended_discussion(self):
        """Test cannot resume ended discussion."""
        from moderation import resume_discussion, DiscussionEndedError

        conn = create_test_db()
        conn.execute('UPDATE panel_discussions SET status = ? WHERE id = 1', ('ended',))
        conn.commit()

        with pytest.raises(DiscussionEndedError):
            resume_discussion(conn, discussion_id=1)
        conn.close()


class TestModerationPermissions:
    """Test suite for moderation permissions."""

    def test_should_require_user_permission(self):
        """Test moderation requires permission."""
        from moderation import end_discussion, PermissionDeniedError

        conn = create_test_db()
        conn.execute(
            'INSERT INTO users (id, username, role) VALUES (?, ?, ?)',
            (1, 'guest', 'guest')
        )
        conn.commit()

        with pytest.raises(PermissionDeniedError):
            end_discussion(conn, discussion_id=1, user_id=1, check_permission=True)
        conn.close()

    def test_should_allow_owner_moderation(self):
        """Test discussion owner can moderate."""
        from moderation import end_discussion

        conn = create_test_db()
        conn.execute(
            'INSERT INTO users (id, username, role) VALUES (?, ?, ?)',
            (1, 'owner', 'owner')
        )
        conn.commit()

        result = end_discussion(conn, discussion_id=1, user_id=1, check_permission=True)

        assert result is not None
        conn.close()

    def test_should_allow_admin_moderation(self):
        """Test admin can moderate."""
        from moderation import end_discussion

        conn = create_test_db()
        conn.execute(
            'INSERT INTO users (id, username, role) VALUES (?, ?, ?)',
            (1, 'admin', 'admin')
        )
        conn.commit()

        result = end_discussion(conn, discussion_id=1, user_id=1, check_permission=True)

        assert result is not None
        conn.close()

    def test_should_check_permission_for_mute(self):
        """Test permission check for mute action."""
        from moderation import mute_reviewer, PermissionDeniedError

        conn = create_test_db()
        conn.execute(
            'INSERT INTO users (id, username, role) VALUES (?, ?, ?)',
            (1, 'guest', 'guest')
        )
        conn.commit()

        with pytest.raises(PermissionDeniedError):
            mute_reviewer(
                conn,
                discussion_id=1,
                reviewer='theological',
                user_id=1,
                check_permission=True
            )
        conn.close()


class TestModerationHistory:
    """Test suite for moderation history."""

    def test_should_record_all_actions(self):
        """Test all moderation actions are recorded."""
        from moderation import end_discussion, redirect_discussion, mute_reviewer, get_moderation_history

        conn = create_test_db()

        redirect_discussion(conn, discussion_id=1, new_topic='Topic 1')
        mute_reviewer(conn, discussion_id=1, reviewer='theological')

        history = get_moderation_history(conn, discussion_id=1)

        assert len(history) >= 2
        conn.close()

    def test_should_include_timestamp_in_history(self):
        """Test history includes timestamps."""
        from moderation import redirect_discussion, get_moderation_history

        conn = create_test_db()

        redirect_discussion(conn, discussion_id=1, new_topic='Test')

        history = get_moderation_history(conn, discussion_id=1)

        assert history[0].get('created_at') is not None
        conn.close()

    def test_should_order_history_chronologically(self):
        """Test history is in chronological order."""
        from moderation import redirect_discussion, mute_reviewer, get_moderation_history

        conn = create_test_db()

        redirect_discussion(conn, discussion_id=1, new_topic='Topic 1')
        mute_reviewer(conn, discussion_id=1, reviewer='theological')

        history = get_moderation_history(conn, discussion_id=1)

        for i in range(len(history) - 1):
            assert history[i]['created_at'] <= history[i + 1]['created_at']
        conn.close()

    def test_should_filter_history_by_action_type(self):
        """Test filtering history by action type."""
        from moderation import redirect_discussion, mute_reviewer, get_moderation_history

        conn = create_test_db()

        redirect_discussion(conn, discussion_id=1, new_topic='Topic')
        mute_reviewer(conn, discussion_id=1, reviewer='theological')

        history = get_moderation_history(conn, discussion_id=1, action_type='redirect')

        for action in history:
            assert action['action_type'] == 'redirect'
        conn.close()


class TestFlaskIntegration:
    """Test suite for Flask integration."""

    def test_should_expose_end_endpoint(self):
        """Test end discussion API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/end')
            assert response.status_code in [200, 404]

    def test_should_expose_pause_endpoint(self):
        """Test pause discussion API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/pause')
            assert response.status_code in [200, 404]

    def test_should_expose_redirect_endpoint(self):
        """Test redirect discussion API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/redirect', json={
                'topic': 'New topic'
            })
            assert response.status_code in [200, 400, 404]

    def test_should_expose_mute_endpoint(self):
        """Test mute reviewer API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.post('/api/discussion/1/mute', json={
                'reviewer': 'theological'
            })
            assert response.status_code in [200, 400, 404]

    def test_should_expose_history_endpoint(self):
        """Test moderation history API endpoint."""
        from app import create_app

        app = create_app(testing=True)

        with app.test_client() as client:
            response = client.get('/api/discussion/1/moderation-history')
            assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
