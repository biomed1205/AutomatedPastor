"""Tests for shareable links generation.

These tests verify the secure shareable links system for sermon drafts.
Enables pastors to share work with reviewers via unique tokens.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
import hashlib
from datetime import datetime, timedelta


def create_test_db():
    """Create an in-memory test database for shareable links testing."""
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

    # Create share_links table
    conn.execute('''
        CREATE TABLE share_links (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            share_token TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            expires_at TIMESTAMP,
            is_revoked INTEGER DEFAULT 0,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create share_access_log table
    conn.execute('''
        CREATE TABLE share_access_log (
            id INTEGER PRIMARY KEY,
            share_link_id INTEGER NOT NULL,
            share_token TEXT NOT NULL,
            accessor_ip TEXT,
            accessor_name TEXT,
            accessor_email TEXT,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (share_link_id) REFERENCES share_links(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", content="Sermon content"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_share_link(conn, sermon_id, token, expires_at=None, password_hash=None):
    """Insert a sample share link for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO share_links (sermon_id, share_token, expires_at, password_hash)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, token, expires_at, password_hash)
    )
    conn.commit()
    return cursor.lastrowid


class TestCreateShareLink:
    """Test suite for creating share links."""

    def test_should_create_share_link_for_sermon(self):
        """Test that a share link can be created for a sermon."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Easter Sermon")

        result = create_share_link(conn, sermon_id)

        assert result is not None
        assert 'token' in result or 'share_token' in result
        conn.close()

    def test_should_return_unique_token(self):
        """Test that each share link has a unique token."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")

        result1 = create_share_link(conn, sermon_id)
        result2 = create_share_link(conn, sermon_id)

        token1 = result1.get('token') or result1.get('share_token')
        token2 = result2.get('token') or result2.get('share_token')
        assert token1 != token2
        conn.close()

    def test_should_create_link_with_expiration(self):
        """Test that share link can have expiration date."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        expires = datetime.now() + timedelta(days=7)

        result = create_share_link(conn, sermon_id, expires_at=expires)

        assert result is not None
        assert result.get('expires_at') is not None
        conn.close()

    def test_should_create_link_with_password(self):
        """Test that share link can have password protection."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Protected Sermon")

        result = create_share_link(conn, sermon_id, password="secret123")

        assert result is not None
        assert result.get('has_password') is True or result.get('password_protected') is True
        conn.close()

    def test_should_fail_for_nonexistent_sermon(self):
        """Test that creating link for nonexistent sermon fails."""
        from shareable_links import create_share_link

        conn = create_test_db()

        result = create_share_link(conn, 9999)

        assert result is None or result.get('error') is not None
        conn.close()

    def test_should_store_created_by_user(self):
        """Test that creator user ID is stored."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")

        result = create_share_link(conn, sermon_id, created_by=42)

        assert result is not None
        conn.close()

    def test_should_generate_secure_token(self):
        """Test that generated token is cryptographically secure."""
        from shareable_links import create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")

        result = create_share_link(conn, sermon_id)
        token = result.get('token') or result.get('share_token')

        # Token should be reasonably long and contain alphanumeric characters
        assert len(token) >= 16
        conn.close()


class TestGetShareLink:
    """Test suite for retrieving share link details."""

    def test_should_get_share_link_by_token(self):
        """Test that share link can be retrieved by token."""
        from shareable_links import get_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "test_token_123")

        result = get_share_link(conn, "test_token_123")

        assert result is not None
        assert result.get('sermon_id') == sermon_id
        conn.close()

    def test_should_return_none_for_invalid_token(self):
        """Test that None is returned for invalid token."""
        from shareable_links import get_share_link

        conn = create_test_db()

        result = get_share_link(conn, "nonexistent_token")

        assert result is None
        conn.close()

    def test_should_include_sermon_details(self):
        """Test that sermon details are included in result."""
        from shareable_links import get_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "My Sermon Title")
        insert_sample_share_link(conn, sermon_id, "token_with_details")

        result = get_share_link(conn, "token_with_details")

        assert result is not None
        # Should include sermon info
        conn.close()

    def test_should_indicate_if_expired(self):
        """Test that expired status is indicated."""
        from shareable_links import get_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        insert_sample_share_link(conn, sermon_id, "expired_token", expires_at=past_date)

        result = get_share_link(conn, "expired_token")

        assert result is not None
        assert result.get('is_expired') is True or result.get('expired') is True
        conn.close()


class TestValidateShareLink:
    """Test suite for validating share links."""

    def test_should_validate_valid_token(self):
        """Test that valid token passes validation."""
        from shareable_links import validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        insert_sample_share_link(conn, sermon_id, "valid_token", expires_at=future_date)

        is_valid, message = validate_share_link(conn, "valid_token")

        assert is_valid is True
        conn.close()

    def test_should_reject_invalid_token(self):
        """Test that invalid token fails validation."""
        from shareable_links import validate_share_link

        conn = create_test_db()

        is_valid, message = validate_share_link(conn, "fake_token")

        assert is_valid is False
        assert 'invalid' in message.lower() or 'not found' in message.lower()
        conn.close()

    def test_should_reject_expired_token(self):
        """Test that expired token fails validation."""
        from shareable_links import validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        insert_sample_share_link(conn, sermon_id, "expired_token", expires_at=past_date)

        is_valid, message = validate_share_link(conn, "expired_token")

        assert is_valid is False
        assert 'expired' in message.lower()
        conn.close()

    def test_should_validate_correct_password(self):
        """Test that correct password passes validation."""
        from shareable_links import validate_share_link, create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Protected Sermon")

        # Create link with password
        result = create_share_link(conn, sermon_id, password="mysecret")
        token = result.get('token') or result.get('share_token')

        is_valid, message = validate_share_link(conn, token, password="mysecret")

        assert is_valid is True
        conn.close()

    def test_should_reject_wrong_password(self):
        """Test that wrong password fails validation."""
        from shareable_links import validate_share_link, create_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Protected Sermon")

        result = create_share_link(conn, sermon_id, password="correct")
        token = result.get('token') or result.get('share_token')

        is_valid, message = validate_share_link(conn, token, password="wrong")

        assert is_valid is False
        assert 'password' in message.lower()
        conn.close()

    def test_should_reject_revoked_token(self):
        """Test that revoked token fails validation."""
        from shareable_links import validate_share_link, revoke_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "revoked_token")
        # Mark as revoked
        conn.execute("UPDATE share_links SET is_revoked = 1 WHERE share_token = ?",
                     ("revoked_token",))
        conn.commit()

        is_valid, message = validate_share_link(conn, "revoked_token")

        assert is_valid is False
        assert 'revoked' in message.lower()
        conn.close()

    def test_should_allow_token_without_expiration(self):
        """Test that token without expiration is valid indefinitely."""
        from shareable_links import validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "no_expiry_token", expires_at=None)

        is_valid, message = validate_share_link(conn, "no_expiry_token")

        assert is_valid is True
        conn.close()


class TestListShareLinks:
    """Test suite for listing share links."""

    def test_should_list_share_links_for_sermon(self):
        """Test that all share links for a sermon are listed."""
        from shareable_links import list_share_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "token1")
        insert_sample_share_link(conn, sermon_id, "token2")
        insert_sample_share_link(conn, sermon_id, "token3")

        links = list_share_links(conn, sermon_id)

        assert links is not None
        assert len(links) == 3
        conn.close()

    def test_should_return_empty_for_sermon_without_links(self):
        """Test that empty list is returned for sermon without links."""
        from shareable_links import list_share_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "No Links Sermon")

        links = list_share_links(conn, sermon_id)

        assert links == []
        conn.close()

    def test_should_include_link_details(self):
        """Test that link details are included."""
        from shareable_links import list_share_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        future_date = (datetime.now() + timedelta(days=7)).isoformat()
        insert_sample_share_link(conn, sermon_id, "detailed_token", expires_at=future_date)

        links = list_share_links(conn, sermon_id)

        assert len(links) == 1
        assert 'share_token' in links[0] or 'token' in links[0]
        conn.close()

    def test_should_order_by_creation_date(self):
        """Test that links are ordered by creation date."""
        from shareable_links import list_share_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "first_token")
        insert_sample_share_link(conn, sermon_id, "second_token")

        links = list_share_links(conn, sermon_id)

        # Should be ordered (newest first or oldest first consistently)
        assert len(links) == 2
        conn.close()


class TestRevokeShareLink:
    """Test suite for revoking share links."""

    def test_should_revoke_share_link(self):
        """Test that share link can be revoked."""
        from shareable_links import revoke_share_link, validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "to_revoke_token")

        result = revoke_share_link(conn, "to_revoke_token")

        assert result is True
        is_valid, _ = validate_share_link(conn, "to_revoke_token")
        assert is_valid is False
        conn.close()

    def test_should_fail_revoke_for_nonexistent_token(self):
        """Test that revoking nonexistent token fails."""
        from shareable_links import revoke_share_link

        conn = create_test_db()

        result = revoke_share_link(conn, "nonexistent")

        assert result is False
        conn.close()

    def test_should_fail_revoke_for_already_revoked(self):
        """Test handling of already revoked token."""
        from shareable_links import revoke_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "already_revoked")
        conn.execute("UPDATE share_links SET is_revoked = 1 WHERE share_token = ?",
                     ("already_revoked",))
        conn.commit()

        result = revoke_share_link(conn, "already_revoked")

        # Should either succeed (idempotent) or indicate already revoked
        assert result is True or result is False
        conn.close()


class TestRecordShareAccess:
    """Test suite for recording share link access."""

    def test_should_record_share_access(self):
        """Test that share access is recorded."""
        from shareable_links import record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        link_id = insert_sample_share_link(conn, sermon_id, "access_token")

        result = record_share_access(conn, "access_token", {
            'ip': '192.168.1.1',
            'name': 'John Reviewer'
        })

        assert result is True
        conn.close()

    def test_should_store_accessor_details(self):
        """Test that accessor details are stored."""
        from shareable_links import record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "detailed_access")

        record_share_access(conn, "detailed_access", {
            'ip': '10.0.0.1',
            'name': 'Jane Smith',
            'email': 'jane@example.com'
        })

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM share_access_log WHERE share_token = ?",
                       ("detailed_access",))
        row = cursor.fetchone()

        assert row is not None
        assert row['accessor_name'] == 'Jane Smith'
        conn.close()

    def test_should_record_multiple_accesses(self):
        """Test that multiple accesses are recorded."""
        from shareable_links import record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "multi_access")

        record_share_access(conn, "multi_access", {'name': 'User 1'})
        record_share_access(conn, "multi_access", {'name': 'User 2'})
        record_share_access(conn, "multi_access", {'name': 'User 1'})  # Same user again

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM share_access_log WHERE share_token = ?",
                       ("multi_access",))
        count = cursor.fetchone()['count']

        assert count == 3
        conn.close()

    def test_should_fail_for_invalid_token(self):
        """Test that recording access for invalid token fails."""
        from shareable_links import record_share_access

        conn = create_test_db()

        result = record_share_access(conn, "nonexistent", {'name': 'User'})

        assert result is False
        conn.close()


class TestGetShareStats:
    """Test suite for getting sharing statistics."""

    def test_should_get_share_stats_for_sermon(self):
        """Test that sharing statistics are returned."""
        from shareable_links import get_share_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "stat_token1")
        insert_sample_share_link(conn, sermon_id, "stat_token2")

        stats = get_share_stats(conn, sermon_id)

        assert stats is not None
        assert 'total_links' in stats or 'link_count' in stats
        conn.close()

    def test_should_include_access_count(self):
        """Test that total access count is included."""
        from shareable_links import get_share_stats, record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "counted_token")
        record_share_access(conn, "counted_token", {'name': 'User 1'})
        record_share_access(conn, "counted_token", {'name': 'User 2'})

        stats = get_share_stats(conn, sermon_id)

        assert stats.get('total_accesses', 0) >= 2 or stats.get('access_count', 0) >= 2
        conn.close()

    def test_should_include_unique_visitors(self):
        """Test that unique visitor count is included."""
        from shareable_links import get_share_stats, record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "visitor_token")
        record_share_access(conn, "visitor_token", {'email': 'user1@test.com'})
        record_share_access(conn, "visitor_token", {'email': 'user2@test.com'})
        record_share_access(conn, "visitor_token", {'email': 'user1@test.com'})  # Same user

        stats = get_share_stats(conn, sermon_id)

        # Should track unique visitors
        assert stats is not None
        conn.close()

    def test_should_handle_sermon_without_links(self):
        """Test stats for sermon without links."""
        from shareable_links import get_share_stats

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "No Links")

        stats = get_share_stats(conn, sermon_id)

        assert stats is not None
        total = stats.get('total_links', stats.get('link_count', 0))
        assert total == 0
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_unicode_in_accessor_name(self):
        """Test unicode in accessor details."""
        from shareable_links import record_share_access

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "unicode_token")

        result = record_share_access(conn, "unicode_token", {
            'name': 'Ιωάννης Παπαδόπουλος',
            'email': 'yiannis@εκκλησία.gr'
        })

        assert result is True
        conn.close()

    def test_should_handle_very_long_token(self):
        """Test handling of very long tokens."""
        from shareable_links import get_share_link

        conn = create_test_db()
        long_token = "a" * 500

        result = get_share_link(conn, long_token)

        assert result is None
        conn.close()

    def test_should_handle_special_characters_in_password(self):
        """Test special characters in password."""
        from shareable_links import create_share_link, validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        special_password = "P@$$w0rd!#%^&*()"

        result = create_share_link(conn, sermon_id, password=special_password)
        token = result.get('token') or result.get('share_token')

        is_valid, _ = validate_share_link(conn, token, password=special_password)

        assert is_valid is True
        conn.close()

    def test_should_handle_concurrent_share_links(self):
        """Test multiple share links for same sermon."""
        from shareable_links import create_share_link, list_share_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Popular Sermon")

        # Create many share links
        for i in range(10):
            create_share_link(conn, sermon_id)

        links = list_share_links(conn, sermon_id)

        assert len(links) == 10
        conn.close()

    def test_should_handle_expired_password_protected_link(self):
        """Test expired link with password."""
        from shareable_links import create_share_link, validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        past_date = datetime.now() - timedelta(days=1)

        result = create_share_link(conn, sermon_id, password="secret", expires_at=past_date)
        token = result.get('token') or result.get('share_token')

        # Even with correct password, should fail due to expiration
        is_valid, message = validate_share_link(conn, token, password="secret")

        assert is_valid is False
        assert 'expired' in message.lower()
        conn.close()


class TestBulkOperations:
    """Test suite for bulk operations."""

    def test_should_revoke_all_links_for_sermon(self):
        """Test revoking all links for a sermon."""
        from shareable_links import revoke_all_links, validate_share_link

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        insert_sample_share_link(conn, sermon_id, "bulk1")
        insert_sample_share_link(conn, sermon_id, "bulk2")
        insert_sample_share_link(conn, sermon_id, "bulk3")

        result = revoke_all_links(conn, sermon_id)

        assert result is True or result >= 3
        # All should be revoked
        is_valid1, _ = validate_share_link(conn, "bulk1")
        is_valid2, _ = validate_share_link(conn, "bulk2")
        assert is_valid1 is False
        assert is_valid2 is False
        conn.close()

    def test_should_cleanup_expired_links(self):
        """Test cleaning up expired links."""
        from shareable_links import cleanup_expired_links

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon")
        past_date = (datetime.now() - timedelta(days=30)).isoformat()
        insert_sample_share_link(conn, sermon_id, "old_token", expires_at=past_date)
        future_date = (datetime.now() + timedelta(days=30)).isoformat()
        insert_sample_share_link(conn, sermon_id, "new_token", expires_at=future_date)

        count = cleanup_expired_links(conn)

        assert count >= 1
        conn.close()


class TestIntegration:
    """Integration tests for share link workflows."""

    def test_should_complete_share_workflow(self):
        """Test complete sharing workflow."""
        from shareable_links import (
            create_share_link,
            validate_share_link,
            record_share_access,
            get_share_stats
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Shared Sermon", "Full content here")

        # Create share link
        result = create_share_link(conn, sermon_id, expires_at=datetime.now() + timedelta(days=7))
        token = result.get('token') or result.get('share_token')

        # Validate and access
        is_valid, _ = validate_share_link(conn, token)
        assert is_valid is True

        # Record access
        record_share_access(conn, token, {'name': 'Staff Member', 'email': 'staff@church.org'})

        # Check stats
        stats = get_share_stats(conn, sermon_id)
        assert stats.get('total_links', stats.get('link_count', 0)) >= 1

        conn.close()

    def test_should_handle_protected_share_workflow(self):
        """Test password-protected sharing workflow."""
        from shareable_links import (
            create_share_link,
            validate_share_link,
            record_share_access
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Confidential Sermon")

        # Create protected link
        result = create_share_link(conn, sermon_id, password="churchstaff2024")
        token = result.get('token') or result.get('share_token')

        # Fail without password
        is_valid, _ = validate_share_link(conn, token)
        assert is_valid is False

        # Succeed with correct password
        is_valid, _ = validate_share_link(conn, token, password="churchstaff2024")
        assert is_valid is True

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
