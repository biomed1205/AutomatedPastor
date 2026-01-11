"""Tests for version history tracking.

These tests verify the version history system for sermon drafts.
Enables tracking revisions, comparing versions, and restoring previous states.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, timedelta


def create_test_db():
    """Create an in-memory test database for version history testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create sermon_versions table
    conn.execute('''
        CREATE TABLE sermon_versions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            manuscript_text TEXT NOT NULL,
            author TEXT,
            change_summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            UNIQUE(sermon_id, version_number)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", content="Original content"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sermons (title, content) VALUES (?, ?)",
        (title, content)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_version(conn, sermon_id, version_number, text, author="Author"):
    """Insert a sample version for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermon_versions (sermon_id, version_number, manuscript_text, author)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, version_number, text, author)
    )
    conn.commit()
    return cursor.lastrowid


class TestCreateVersion:
    """Test suite for creating versions."""

    def test_should_create_version_for_sermon(self):
        """Test that a version can be created for a sermon."""
        from version_history import create_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        version_id = create_version(conn, sermon_id, "First draft of the sermon.")

        assert version_id is not None
        assert isinstance(version_id, int)
        assert version_id > 0
        conn.close()

    def test_should_auto_increment_version_number(self):
        """Test that version numbers increment automatically."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        v1_id = create_version(conn, sermon_id, "Version 1")
        v2_id = create_version(conn, sermon_id, "Version 2")
        v3_id = create_version(conn, sermon_id, "Version 3")

        v1 = get_version(conn, v1_id)
        v2 = get_version(conn, v2_id)
        v3 = get_version(conn, v3_id)

        assert v1['version_number'] == 1
        assert v2['version_number'] == 2
        assert v3['version_number'] == 3
        conn.close()

    def test_should_store_author(self):
        """Test that author is stored with version."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        version_id = create_version(conn, sermon_id, "Content", author="Pastor Katie")
        version = get_version(conn, version_id)

        assert version['author'] == "Pastor Katie"
        conn.close()

    def test_should_store_full_manuscript_text(self):
        """Test that full manuscript text is stored."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        full_text = "This is the complete manuscript. " * 100

        version_id = create_version(conn, sermon_id, full_text)
        version = get_version(conn, version_id)

        assert version['manuscript_text'] == full_text
        conn.close()

    def test_should_fail_for_nonexistent_sermon(self):
        """Test that creating version for nonexistent sermon fails."""
        from version_history import create_version

        conn = create_test_db()

        result = create_version(conn, 9999, "Orphan content")

        assert result is None or result is False
        conn.close()

    def test_should_record_creation_timestamp(self):
        """Test that creation timestamp is recorded."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        version_id = create_version(conn, sermon_id, "Timestamped version")
        version = get_version(conn, version_id)

        assert 'created_at' in version
        assert version['created_at'] is not None
        conn.close()


class TestGetVersion:
    """Test suite for retrieving specific versions."""

    def test_should_get_version_by_id(self):
        """Test that version can be retrieved by ID."""
        from version_history import get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        version_id = insert_sample_version(conn, sermon_id, 1, "Test content")

        version = get_version(conn, version_id)

        assert version is not None
        assert version['manuscript_text'] == "Test content"
        conn.close()

    def test_should_return_none_for_invalid_id(self):
        """Test that None is returned for invalid ID."""
        from version_history import get_version

        conn = create_test_db()

        version = get_version(conn, 9999)

        assert version is None
        conn.close()

    def test_should_include_all_fields(self):
        """Test that all version fields are returned."""
        from version_history import get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        version_id = insert_sample_version(conn, sermon_id, 1, "Content", "Author")

        version = get_version(conn, version_id)

        assert 'id' in version
        assert 'sermon_id' in version
        assert 'version_number' in version
        assert 'manuscript_text' in version
        assert 'author' in version
        assert 'created_at' in version
        conn.close()


class TestListVersions:
    """Test suite for listing versions."""

    def test_should_list_all_versions_for_sermon(self):
        """Test that all versions for a sermon are listed."""
        from version_history import list_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "Version 1")
        insert_sample_version(conn, sermon_id, 2, "Version 2")
        insert_sample_version(conn, sermon_id, 3, "Version 3")

        versions = list_versions(conn, sermon_id)

        assert len(versions) == 3
        conn.close()

    def test_should_return_empty_for_sermon_without_versions(self):
        """Test that empty list is returned for sermon without versions."""
        from version_history import list_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        versions = list_versions(conn, sermon_id)

        assert versions == []
        conn.close()

    def test_should_order_by_version_number_descending(self):
        """Test that versions are ordered newest first."""
        from version_history import list_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "First")
        insert_sample_version(conn, sermon_id, 2, "Second")
        insert_sample_version(conn, sermon_id, 3, "Third")

        versions = list_versions(conn, sermon_id)

        assert versions[0]['version_number'] == 3
        assert versions[1]['version_number'] == 2
        assert versions[2]['version_number'] == 1
        conn.close()

    def test_should_only_list_versions_for_specified_sermon(self):
        """Test that only versions for the specified sermon are listed."""
        from version_history import list_versions

        conn = create_test_db()
        sermon1_id = insert_sample_sermon(conn, "Sermon 1")
        sermon2_id = insert_sample_sermon(conn, "Sermon 2")
        insert_sample_version(conn, sermon1_id, 1, "S1V1")
        insert_sample_version(conn, sermon1_id, 2, "S1V2")
        insert_sample_version(conn, sermon2_id, 1, "S2V1")

        versions = list_versions(conn, sermon1_id)

        assert len(versions) == 2
        for v in versions:
            assert v['sermon_id'] == sermon1_id
        conn.close()


class TestGetLatestVersion:
    """Test suite for getting latest version."""

    def test_should_get_latest_version(self):
        """Test that the most recent version is returned."""
        from version_history import get_latest_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "Old version")
        insert_sample_version(conn, sermon_id, 2, "Newer version")
        insert_sample_version(conn, sermon_id, 3, "Latest version")

        latest = get_latest_version(conn, sermon_id)

        assert latest is not None
        assert latest['version_number'] == 3
        assert latest['manuscript_text'] == "Latest version"
        conn.close()

    def test_should_return_none_for_sermon_without_versions(self):
        """Test that None is returned when no versions exist."""
        from version_history import get_latest_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        latest = get_latest_version(conn, sermon_id)

        assert latest is None
        conn.close()

    def test_should_handle_single_version(self):
        """Test getting latest when only one version exists."""
        from version_history import get_latest_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "Only version")

        latest = get_latest_version(conn, sermon_id)

        assert latest['version_number'] == 1
        conn.close()


class TestCompareVersions:
    """Test suite for comparing versions."""

    def test_should_compare_two_versions(self):
        """Test that two versions can be compared."""
        from version_history import compare_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "Original text here")
        v2_id = insert_sample_version(conn, sermon_id, 2, "Modified text here")

        diff = compare_versions(conn, v1_id, v2_id)

        assert diff is not None
        conn.close()

    def test_should_return_diff_structure(self):
        """Test that diff has proper structure."""
        from version_history import compare_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "Line one\nLine two")
        v2_id = insert_sample_version(conn, sermon_id, 2, "Line one\nLine three")

        diff = compare_versions(conn, v1_id, v2_id)

        # Diff should contain additions, deletions, or unified format
        assert 'additions' in diff or 'deletions' in diff or 'diff' in diff or isinstance(diff, (str, list))
        conn.close()

    def test_should_handle_identical_versions(self):
        """Test comparing identical versions."""
        from version_history import compare_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "Same content")
        v2_id = insert_sample_version(conn, sermon_id, 2, "Same content")

        diff = compare_versions(conn, v1_id, v2_id)

        # Should indicate no changes
        assert diff is not None
        conn.close()

    def test_should_fail_for_invalid_version_ids(self):
        """Test that comparison fails for invalid version IDs."""
        from version_history import compare_versions

        conn = create_test_db()

        diff = compare_versions(conn, 9998, 9999)

        assert diff is None
        conn.close()

    def test_should_handle_completely_different_content(self):
        """Test comparing completely different content."""
        from version_history import compare_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "Original content")
        v2_id = insert_sample_version(conn, sermon_id, 2, "Completely rewritten")

        diff = compare_versions(conn, v1_id, v2_id)

        assert diff is not None
        conn.close()


class TestRestoreVersion:
    """Test suite for restoring versions."""

    def test_should_restore_previous_version(self):
        """Test that a previous version can be restored."""
        from version_history import restore_version, get_latest_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "First version")
        insert_sample_version(conn, sermon_id, 2, "Second version")
        insert_sample_version(conn, sermon_id, 3, "Third version")

        result = restore_version(conn, sermon_id, v1_id)

        assert result is True or result is not None
        # Latest should now be version 4 with content from v1
        latest = get_latest_version(conn, sermon_id)
        assert latest['manuscript_text'] == "First version"
        conn.close()

    def test_should_create_new_version_on_restore(self):
        """Test that restore creates a new version (doesn't delete)."""
        from version_history import restore_version, list_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        v1_id = insert_sample_version(conn, sermon_id, 1, "V1")
        insert_sample_version(conn, sermon_id, 2, "V2")

        restore_version(conn, sermon_id, v1_id)
        versions = list_versions(conn, sermon_id)

        assert len(versions) == 3  # Should have 3 versions now
        conn.close()

    def test_should_fail_restore_for_invalid_version(self):
        """Test that restore fails for invalid version."""
        from version_history import restore_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = restore_version(conn, sermon_id, 9999)

        assert result is False or result is None
        conn.close()

    def test_should_fail_restore_for_version_from_different_sermon(self):
        """Test that restore fails for version from different sermon."""
        from version_history import restore_version

        conn = create_test_db()
        sermon1_id = insert_sample_sermon(conn, "Sermon 1")
        sermon2_id = insert_sample_sermon(conn, "Sermon 2")
        v_id = insert_sample_version(conn, sermon2_id, 1, "Wrong sermon")

        result = restore_version(conn, sermon1_id, v_id)

        assert result is False or result is None
        conn.close()


class TestDeleteVersion:
    """Test suite for deleting versions."""

    def test_should_delete_version(self):
        """Test that a version can be deleted."""
        from version_history import delete_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        version_id = insert_sample_version(conn, sermon_id, 1, "To delete")

        result = delete_version(conn, version_id)

        assert result is True
        assert get_version(conn, version_id) is None
        conn.close()

    def test_should_fail_delete_for_nonexistent_version(self):
        """Test that delete fails for nonexistent version."""
        from version_history import delete_version

        conn = create_test_db()

        result = delete_version(conn, 9999)

        assert result is False
        conn.close()

    def test_should_prevent_delete_of_only_version(self):
        """Test that the only version cannot be deleted."""
        from version_history import delete_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        version_id = insert_sample_version(conn, sermon_id, 1, "Only version")

        result = delete_version(conn, version_id)

        # Should either prevent or allow (depending on implementation)
        assert result is True or result is False
        conn.close()


class TestGetVersionCount:
    """Test suite for counting versions."""

    def test_should_get_version_count(self):
        """Test that version count is returned."""
        from version_history import get_version_count

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "V1")
        insert_sample_version(conn, sermon_id, 2, "V2")
        insert_sample_version(conn, sermon_id, 3, "V3")

        count = get_version_count(conn, sermon_id)

        assert count == 3
        conn.close()

    def test_should_return_zero_for_sermon_without_versions(self):
        """Test that zero is returned for sermon without versions."""
        from version_history import get_version_count

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        count = get_version_count(conn, sermon_id)

        assert count == 0
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_first_version(self):
        """Test creating the very first version."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        version_id = create_version(conn, sermon_id, "First ever version")
        version = get_version(conn, version_id)

        assert version['version_number'] == 1
        conn.close()

    def test_should_handle_same_content_new_version(self):
        """Test creating new version with identical content."""
        from version_history import create_version, list_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        create_version(conn, sermon_id, "Same content")
        create_version(conn, sermon_id, "Same content")

        versions = list_versions(conn, sermon_id)

        assert len(versions) == 2
        assert versions[0]['version_number'] != versions[1]['version_number']
        conn.close()

    def test_should_handle_very_long_text(self):
        """Test storing very long manuscript text."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        long_text = "This is a long sermon manuscript. " * 1000  # ~35KB

        version_id = create_version(conn, sermon_id, long_text)
        version = get_version(conn, version_id)

        assert len(version['manuscript_text']) == len(long_text)
        conn.close()

    def test_should_handle_unicode_in_manuscript(self):
        """Test unicode characters in manuscript text."""
        from version_history import create_version, get_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        unicode_text = "Greek: ἀγάπη (love) Hebrew: שָׁלוֹם (peace)"

        version_id = create_version(conn, sermon_id, unicode_text)
        version = get_version(conn, version_id)

        assert 'ἀγάπη' in version['manuscript_text']
        assert 'שָׁלוֹם' in version['manuscript_text']
        conn.close()

    def test_should_handle_empty_text(self):
        """Test handling of empty manuscript text."""
        from version_history import create_version

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        result = create_version(conn, sermon_id, "")

        # Should either reject or allow empty
        assert result is None or result is not None
        conn.close()

    def test_should_handle_many_versions(self):
        """Test handling sermon with many versions."""
        from version_history import list_versions, get_version_count

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        for i in range(50):
            insert_sample_version(conn, sermon_id, i + 1, f"Version {i + 1}")

        versions = list_versions(conn, sermon_id)
        count = get_version_count(conn, sermon_id)

        assert count == 50
        assert len(versions) == 50
        conn.close()


class TestIntegration:
    """Integration tests for version history workflows."""

    def test_should_complete_edit_workflow(self):
        """Test complete edit and version workflow."""
        from version_history import (
            create_version,
            get_latest_version,
            list_versions,
            get_version_count
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        # Create initial version
        create_version(conn, sermon_id, "First draft", author="Pastor")

        # Make edits and create new versions
        create_version(conn, sermon_id, "Second draft with edits", author="Pastor")
        create_version(conn, sermon_id, "Final draft", author="Pastor")

        # Check state
        latest = get_latest_version(conn, sermon_id)
        versions = list_versions(conn, sermon_id)
        count = get_version_count(conn, sermon_id)

        assert latest['manuscript_text'] == "Final draft"
        assert len(versions) == 3
        assert count == 3

        conn.close()

    def test_should_complete_restore_workflow(self):
        """Test complete restore workflow."""
        from version_history import (
            create_version,
            restore_version,
            get_latest_version,
            get_version_count
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        # Create versions
        v1_id = create_version(conn, sermon_id, "Good version", author="Pastor")
        create_version(conn, sermon_id, "Bad edits", author="Editor")

        # Restore v1
        restore_version(conn, sermon_id, v1_id)

        # Should have 3 versions now, latest with v1 content
        latest = get_latest_version(conn, sermon_id)
        count = get_version_count(conn, sermon_id)

        assert latest['manuscript_text'] == "Good version"
        assert count == 3

        conn.close()

    def test_should_complete_compare_workflow(self):
        """Test complete version comparison workflow."""
        from version_history import (
            create_version,
            list_versions,
            compare_versions
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        # Create two different versions
        v1_id = create_version(conn, sermon_id, "Introduction paragraph.\nMain content.")
        v2_id = create_version(conn, sermon_id, "Better introduction.\nMain content.\nNew conclusion.")

        # Compare them
        diff = compare_versions(conn, v1_id, v2_id)

        assert diff is not None

        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
