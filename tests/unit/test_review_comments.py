"""Tests for reviewer comment system.

These tests verify the inline commenting system for shared sermon drafts.
Enables reviewers to leave comments with position markers and suggestions.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime


def create_test_db():
    """Create an in-memory test database for review comments testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create review_comments table
    conn.execute('''
        CREATE TABLE review_comments (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            parent_id INTEGER,
            reviewer_name TEXT NOT NULL,
            comment_text TEXT NOT NULL,
            highlight_start INTEGER,
            highlight_end INTEGER,
            suggestion TEXT,
            resolved INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            FOREIGN KEY (parent_id) REFERENCES review_comments(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", content="This is the sermon content for testing."):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_comment(conn, sermon_id, reviewer_name="Reviewer", text="Comment",
                          start_pos=0, end_pos=10, parent_id=None, resolved=0):
    """Insert a sample comment for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO review_comments
           (sermon_id, parent_id, reviewer_name, comment_text, highlight_start, highlight_end, resolved)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (sermon_id, parent_id, reviewer_name, text, start_pos, end_pos, resolved)
    )
    conn.commit()
    return cursor.lastrowid


class TestAddComment:
    """Test suite for adding comments."""

    def test_should_add_comment_to_sermon(self):
        """Test that a comment can be added to a sermon."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(
            conn,
            sermon_id=sermon_id,
            reviewer_name="John",
            text="Great point here!",
            start_pos=0,
            end_pos=20
        )

        assert comment_id is not None
        assert isinstance(comment_id, int)
        assert comment_id > 0
        conn.close()

    def test_should_store_position_markers(self):
        """Test that position markers are stored correctly."""
        from review_comments import add_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(
            conn, sermon_id, "Reviewer", "Comment", start_pos=50, end_pos=100
        )
        comment = get_comment(conn, comment_id)

        assert comment['highlight_start'] == 50
        assert comment['highlight_end'] == 100
        conn.close()

    def test_should_store_suggestion_text(self):
        """Test that suggestion text is stored."""
        from review_comments import add_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(
            conn, sermon_id, "Editor", "Consider this change",
            start_pos=10, end_pos=30,
            suggestion="replacement text here"
        )
        comment = get_comment(conn, comment_id)

        assert comment['suggestion'] == "replacement text here"
        conn.close()

    def test_should_fail_for_nonexistent_sermon(self):
        """Test that adding comment to nonexistent sermon fails."""
        from review_comments import add_comment

        conn = create_test_db()

        result = add_comment(
            conn, 9999, "Reviewer", "Comment", 0, 10
        )

        assert result is None or result is False
        conn.close()

    def test_should_require_reviewer_name(self):
        """Test that reviewer name is required."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_comment(
            conn, sermon_id, "", "Comment", 0, 10
        )

        assert result is None or result is False
        conn.close()

    def test_should_require_comment_text(self):
        """Test that comment text is required."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = add_comment(
            conn, sermon_id, "Reviewer", "", 0, 10
        )

        assert result is None or result is False
        conn.close()

    def test_should_allow_comment_without_position(self):
        """Test that general comment without position is allowed."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(
            conn, sermon_id, "Reviewer", "General feedback",
            start_pos=None, end_pos=None
        )

        assert comment_id is not None
        conn.close()


class TestGetComment:
    """Test suite for retrieving single comments."""

    def test_should_get_comment_by_id(self):
        """Test that comment can be retrieved by ID."""
        from review_comments import get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "John", "Test comment")

        comment = get_comment(conn, comment_id)

        assert comment is not None
        assert comment['reviewer_name'] == "John"
        assert comment['comment_text'] == "Test comment"
        conn.close()

    def test_should_return_none_for_invalid_id(self):
        """Test that None is returned for invalid ID."""
        from review_comments import get_comment

        conn = create_test_db()

        comment = get_comment(conn, 9999)

        assert comment is None
        conn.close()

    def test_should_include_all_fields(self):
        """Test that all comment fields are returned."""
        from review_comments import get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "Jane", "Detailed comment",
                                           start_pos=10, end_pos=50)

        comment = get_comment(conn, comment_id)

        assert 'id' in comment
        assert 'sermon_id' in comment
        assert 'reviewer_name' in comment
        assert 'comment_text' in comment
        assert 'highlight_start' in comment
        assert 'highlight_end' in comment
        assert 'resolved' in comment
        conn.close()


class TestListComments:
    """Test suite for listing comments."""

    def test_should_list_all_comments_for_sermon(self):
        """Test that all comments for a sermon are listed."""
        from review_comments import list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Comment 1")
        insert_sample_comment(conn, sermon_id, "User2", "Comment 2")
        insert_sample_comment(conn, sermon_id, "User3", "Comment 3")

        comments = list_comments(conn, sermon_id)

        assert len(comments) == 3
        conn.close()

    def test_should_return_empty_for_sermon_without_comments(self):
        """Test that empty list is returned for sermon without comments."""
        from review_comments import list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comments = list_comments(conn, sermon_id)

        assert comments == []
        conn.close()

    def test_should_filter_by_open_status(self):
        """Test filtering for open (unresolved) comments."""
        from review_comments import list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Open comment", resolved=0)
        insert_sample_comment(conn, sermon_id, "User2", "Resolved", resolved=1)

        comments = list_comments(conn, sermon_id, status='open')

        assert len(comments) == 1
        assert comments[0]['comment_text'] == "Open comment"
        conn.close()

    def test_should_filter_by_resolved_status(self):
        """Test filtering for resolved comments."""
        from review_comments import list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Open", resolved=0)
        insert_sample_comment(conn, sermon_id, "User2", "Done", resolved=1)
        insert_sample_comment(conn, sermon_id, "User3", "Also done", resolved=1)

        comments = list_comments(conn, sermon_id, status='resolved')

        assert len(comments) == 2
        conn.close()

    def test_should_order_by_position(self):
        """Test that comments are ordered by position."""
        from review_comments import list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User", "Third", start_pos=100, end_pos=110)
        insert_sample_comment(conn, sermon_id, "User", "First", start_pos=10, end_pos=20)
        insert_sample_comment(conn, sermon_id, "User", "Second", start_pos=50, end_pos=60)

        comments = list_comments(conn, sermon_id)

        assert comments[0]['highlight_start'] == 10
        assert comments[1]['highlight_start'] == 50
        assert comments[2]['highlight_start'] == 100
        conn.close()


class TestUpdateComment:
    """Test suite for updating comments."""

    def test_should_update_comment_text(self):
        """Test that comment text can be updated."""
        from review_comments import update_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "Original")

        result = update_comment(conn, comment_id, "Updated text")

        assert result is True
        comment = get_comment(conn, comment_id)
        assert comment['comment_text'] == "Updated text"
        conn.close()

    def test_should_fail_update_for_nonexistent_comment(self):
        """Test that update fails for nonexistent comment."""
        from review_comments import update_comment

        conn = create_test_db()

        result = update_comment(conn, 9999, "New text")

        assert result is False
        conn.close()

    def test_should_not_allow_empty_update(self):
        """Test that empty text update is rejected."""
        from review_comments import update_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "Original")

        result = update_comment(conn, comment_id, "")

        assert result is False
        conn.close()


class TestResolveComment:
    """Test suite for resolving comments."""

    def test_should_resolve_comment(self):
        """Test that comment can be marked as resolved."""
        from review_comments import resolve_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "Comment")

        result = resolve_comment(conn, comment_id)

        assert result is True
        comment = get_comment(conn, comment_id)
        assert comment['resolved'] == 1 or comment['resolved'] is True
        conn.close()

    def test_should_fail_resolve_for_nonexistent_comment(self):
        """Test that resolve fails for nonexistent comment."""
        from review_comments import resolve_comment

        conn = create_test_db()

        result = resolve_comment(conn, 9999)

        assert result is False
        conn.close()

    def test_should_allow_resolving_already_resolved(self):
        """Test that resolving already resolved comment is idempotent."""
        from review_comments import resolve_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "Done", resolved=1)

        result = resolve_comment(conn, comment_id)

        assert result is True
        conn.close()


class TestDeleteComment:
    """Test suite for deleting comments."""

    def test_should_delete_comment(self):
        """Test that comment can be deleted."""
        from review_comments import delete_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "To delete")

        result = delete_comment(conn, comment_id)

        assert result is True
        comment = get_comment(conn, comment_id)
        assert comment is None
        conn.close()

    def test_should_fail_delete_for_nonexistent_comment(self):
        """Test that delete fails for nonexistent comment."""
        from review_comments import delete_comment

        conn = create_test_db()

        result = delete_comment(conn, 9999)

        assert result is False
        conn.close()

    def test_should_cascade_delete_replies(self):
        """Test that deleting comment deletes its replies."""
        from review_comments import delete_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User", "Parent")
        reply_id = insert_sample_comment(conn, sermon_id, "User2", "Reply", parent_id=parent_id)

        delete_comment(conn, parent_id)

        # Reply should also be gone (due to cascade or explicit handling)
        reply = get_comment(conn, reply_id)
        assert reply is None
        conn.close()


class TestAddReply:
    """Test suite for adding replies to comments."""

    def test_should_add_reply_to_comment(self):
        """Test that a reply can be added to a comment."""
        from review_comments import add_reply, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User1", "Original comment")

        reply_id = add_reply(conn, parent_id, "User2", "This is a reply")

        assert reply_id is not None
        reply = get_comment(conn, reply_id)
        assert reply['parent_id'] == parent_id
        conn.close()

    def test_should_fail_reply_to_nonexistent_comment(self):
        """Test that reply to nonexistent comment fails."""
        from review_comments import add_reply

        conn = create_test_db()

        result = add_reply(conn, 9999, "User", "Reply")

        assert result is None or result is False
        conn.close()

    def test_should_inherit_sermon_id_from_parent(self):
        """Test that reply inherits sermon_id from parent."""
        from review_comments import add_reply, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User1", "Parent")

        reply_id = add_reply(conn, parent_id, "User2", "Reply")
        reply = get_comment(conn, reply_id)

        assert reply['sermon_id'] == sermon_id
        conn.close()


class TestGetReplies:
    """Test suite for getting reply threads."""

    def test_should_get_replies_for_comment(self):
        """Test that replies for a comment are returned."""
        from review_comments import get_replies

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User1", "Parent")
        insert_sample_comment(conn, sermon_id, "User2", "Reply 1", parent_id=parent_id)
        insert_sample_comment(conn, sermon_id, "User3", "Reply 2", parent_id=parent_id)

        replies = get_replies(conn, parent_id)

        assert len(replies) == 2
        conn.close()

    def test_should_return_empty_for_comment_without_replies(self):
        """Test that empty list is returned for comment without replies."""
        from review_comments import get_replies

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "No replies")

        replies = get_replies(conn, comment_id)

        assert replies == []
        conn.close()

    def test_should_order_replies_by_creation_time(self):
        """Test that replies are ordered by creation time."""
        from review_comments import get_replies

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User1", "Parent")
        insert_sample_comment(conn, sermon_id, "User2", "First reply", parent_id=parent_id)
        insert_sample_comment(conn, sermon_id, "User3", "Second reply", parent_id=parent_id)

        replies = get_replies(conn, parent_id)

        assert replies[0]['comment_text'] == "First reply"
        assert replies[1]['comment_text'] == "Second reply"
        conn.close()


class TestAcceptSuggestion:
    """Test suite for accepting suggested text."""

    def test_should_accept_suggestion(self):
        """Test that suggestion can be accepted."""
        from review_comments import accept_suggestion

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, content="Original sermon text here.")
        comment_id = insert_sample_comment(conn, sermon_id, "Editor", "Change this")
        # Add suggestion
        conn.execute("UPDATE review_comments SET suggestion = ? WHERE id = ?",
                     ("New improved text", comment_id))
        conn.commit()

        result = accept_suggestion(conn, comment_id)

        assert result is not None
        # Result should contain new content or success indicator
        conn.close()

    def test_should_fail_accept_for_comment_without_suggestion(self):
        """Test that accept fails for comment without suggestion."""
        from review_comments import accept_suggestion

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        comment_id = insert_sample_comment(conn, sermon_id, "User", "No suggestion here")

        result = accept_suggestion(conn, comment_id)

        assert result is None or result is False
        conn.close()

    def test_should_mark_comment_resolved_after_accept(self):
        """Test that comment is resolved after accepting suggestion."""
        from review_comments import accept_suggestion, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, content="Text to change.")
        comment_id = insert_sample_comment(conn, sermon_id, "Editor", "Suggestion", 0, 10)
        conn.execute("UPDATE review_comments SET suggestion = ? WHERE id = ?",
                     ("Replacement", comment_id))
        conn.commit()

        accept_suggestion(conn, comment_id)
        comment = get_comment(conn, comment_id)

        assert comment['resolved'] == 1 or comment['resolved'] is True
        conn.close()


class TestGetCommentSummary:
    """Test suite for getting comment summary."""

    def test_should_get_comment_summary(self):
        """Test that comment summary is returned."""
        from review_comments import get_comment_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Open", resolved=0)
        insert_sample_comment(conn, sermon_id, "User2", "Done", resolved=1)

        summary = get_comment_summary(conn, sermon_id)

        assert summary is not None
        assert 'total' in summary or 'total_comments' in summary
        conn.close()

    def test_should_include_open_count(self):
        """Test that open comment count is included."""
        from review_comments import get_comment_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Open 1", resolved=0)
        insert_sample_comment(conn, sermon_id, "User2", "Open 2", resolved=0)
        insert_sample_comment(conn, sermon_id, "User3", "Resolved", resolved=1)

        summary = get_comment_summary(conn, sermon_id)

        assert summary.get('open', summary.get('open_count', 0)) == 2
        conn.close()

    def test_should_include_resolved_count(self):
        """Test that resolved comment count is included."""
        from review_comments import get_comment_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_comment(conn, sermon_id, "User1", "Open", resolved=0)
        insert_sample_comment(conn, sermon_id, "User2", "Done 1", resolved=1)
        insert_sample_comment(conn, sermon_id, "User3", "Done 2", resolved=1)

        summary = get_comment_summary(conn, sermon_id)

        assert summary.get('resolved', summary.get('resolved_count', 0)) == 2
        conn.close()

    def test_should_handle_sermon_without_comments(self):
        """Test summary for sermon without comments."""
        from review_comments import get_comment_summary

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        summary = get_comment_summary(conn, sermon_id)

        assert summary is not None
        total = summary.get('total', summary.get('total_comments', 0))
        assert total == 0
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_overlapping_positions(self):
        """Test comments with overlapping position ranges."""
        from review_comments import add_comment, list_comments

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        add_comment(conn, sermon_id, "User1", "First", 10, 30)
        add_comment(conn, sermon_id, "User2", "Overlapping", 20, 40)

        comments = list_comments(conn, sermon_id)

        assert len(comments) == 2
        conn.close()

    def test_should_handle_unicode_in_comment(self):
        """Test unicode characters in comment text."""
        from review_comments import add_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(
            conn, sermon_id, "Ιωάννης", "Σχόλιο με ελληνικά: ἀγάπη",
            0, 20
        )
        comment = get_comment(conn, comment_id)

        assert 'Σχόλιο' in comment['comment_text']
        conn.close()

    def test_should_handle_very_long_comment(self):
        """Test very long comment text."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        long_text = "This is a detailed comment. " * 100

        comment_id = add_comment(conn, sermon_id, "Verbose", long_text, 0, 10)

        assert comment_id is not None
        conn.close()

    def test_should_handle_zero_length_highlight(self):
        """Test comment with zero-length highlight (cursor position)."""
        from review_comments import add_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(conn, sermon_id, "User", "Insert here", 50, 50)

        assert comment_id is not None
        conn.close()

    def test_should_handle_nested_replies(self):
        """Test multiple levels of reply nesting."""
        from review_comments import add_reply, get_replies

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        parent_id = insert_sample_comment(conn, sermon_id, "User1", "Original")
        reply1_id = insert_sample_comment(conn, sermon_id, "User2", "Reply", parent_id=parent_id)
        # Reply to the reply (nested)
        add_reply(conn, reply1_id, "User3", "Nested reply")

        replies = get_replies(conn, reply1_id)

        assert len(replies) == 1
        conn.close()

    def test_should_handle_special_characters_in_reviewer_name(self):
        """Test special characters in reviewer name."""
        from review_comments import add_comment, get_comment

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        comment_id = add_comment(conn, sermon_id, "O'Brien & Smith", "Comment", 0, 10)
        comment = get_comment(conn, comment_id)

        assert comment['reviewer_name'] == "O'Brien & Smith"
        conn.close()


class TestIntegration:
    """Integration tests for comment workflows."""

    def test_should_complete_review_workflow(self):
        """Test complete review workflow."""
        from review_comments import (
            add_comment,
            add_reply,
            resolve_comment,
            get_comment_summary
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "My Sermon", "Sermon content here.")

        # Add comments
        comment1 = add_comment(conn, sermon_id, "Reviewer", "Good intro!", 0, 20)
        comment2 = add_comment(conn, sermon_id, "Editor", "Consider rewording", 50, 80)

        # Add reply
        add_reply(conn, comment2, "Pastor", "Good suggestion, will change")

        # Resolve one comment
        resolve_comment(conn, comment1)

        # Check summary
        summary = get_comment_summary(conn, sermon_id)
        assert summary.get('total', summary.get('total_comments', 0)) == 3  # 2 comments + 1 reply
        assert summary.get('resolved', summary.get('resolved_count', 0)) == 1

        conn.close()

    def test_should_handle_suggestion_workflow(self):
        """Test suggestion accept workflow."""
        from review_comments import (
            add_comment,
            accept_suggestion,
            get_comment
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon", "Original text to modify.")

        # Add comment with suggestion
        comment_id = add_comment(
            conn, sermon_id, "Editor", "Suggest this change",
            start_pos=0, end_pos=13,
            suggestion="Better text"
        )

        # Accept suggestion
        accept_suggestion(conn, comment_id)

        # Comment should be resolved
        comment = get_comment(conn, comment_id)
        assert comment['resolved'] == 1 or comment['resolved'] is True

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
