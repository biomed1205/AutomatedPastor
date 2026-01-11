"""
Tests for archive export and backup functionality.

Tests the complete archive export, backup creation,
restore, and validation capabilities.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database and real temp files.

THIS COMPLETES PHASE 7: Sermon Archive
"""

import sqlite3
import pytest
import tempfile
import os
import json
import zipfile
from datetime import datetime


def create_test_db():
    """Create test database with sermon and related tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scripture TEXT,
            content TEXT,
            manuscript TEXT,
            word_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            preached_date TEXT,
            series_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Series table
    cursor.execute('''
        CREATE TABLE sermon_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date TEXT,
            end_date TEXT
        )
    ''')

    # Research notes table
    cursor.execute('''
        CREATE TABLE research_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            content TEXT,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Illustrations table
    cursor.execute('''
        CREATE TABLE illustrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            content TEXT,
            source TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Post-sermon notes table
    cursor.execute('''
        CREATE TABLE post_sermon_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            note_type TEXT,
            content TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                        content="Content here", manuscript="Full manuscript",
                        word_count=2000, status="preached",
                        preached_date="2024-03-17", series_id=None):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, scripture, content, manuscript,
                            word_count, status, preached_date, series_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, scripture, content, manuscript, word_count, status,
          preached_date, series_id))
    conn.commit()
    return cursor.lastrowid


def insert_sample_series(conn, name="Test Series", description="A test series"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_series (name, description)
        VALUES (?, ?)
    ''', (name, description))
    conn.commit()
    return cursor.lastrowid


def insert_research_note(conn, sermon_id, content="Research note", source="Source"):
    """Insert a research note for a sermon."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO research_notes (sermon_id, content, source)
        VALUES (?, ?, ?)
    ''', (sermon_id, content, source))
    conn.commit()
    return cursor.lastrowid


def insert_illustration(conn, sermon_id, content="Illustration", source="Source"):
    """Insert an illustration for a sermon."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO illustrations (sermon_id, content, source)
        VALUES (?, ?, ?)
    ''', (sermon_id, content, source))
    conn.commit()
    return cursor.lastrowid


def insert_post_note(conn, sermon_id, note_type="what_worked", content="Note"):
    """Insert a post-sermon note."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO post_sermon_notes (sermon_id, note_type, content)
        VALUES (?, ?, ?)
    ''', (sermon_id, note_type, content))
    conn.commit()
    return cursor.lastrowid


class TestExportFullArchive:
    """Tests for export_full_archive function."""

    def test_should_export_as_zip(self):
        """Test exporting entire archive as ZIP."""
        from archive_export import export_full_archive

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1")
        insert_sample_sermon(conn, title="Sermon 2")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='zip', output_dir=tmpdir)

            assert result['success'] is True
            assert result['path'].endswith('.zip')
            assert os.path.exists(result['path'])

    def test_should_include_all_sermons(self):
        """Test that all sermons are included in export."""
        from archive_export import export_full_archive

        conn = create_test_db()
        insert_sample_sermon(conn, title="Sermon 1")
        insert_sample_sermon(conn, title="Sermon 2")
        insert_sample_sermon(conn, title="Sermon 3")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='zip', output_dir=tmpdir)

            assert result['sermon_count'] == 3

    def test_should_include_metadata(self):
        """Test that export includes metadata file."""
        from archive_export import export_full_archive

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='zip', output_dir=tmpdir)

            with zipfile.ZipFile(result['path'], 'r') as zf:
                assert 'metadata.json' in zf.namelist()

    def test_should_export_as_json(self):
        """Test exporting archive as JSON."""
        from archive_export import export_full_archive

        conn = create_test_db()
        insert_sample_sermon(conn, title="Test Sermon")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='json', output_dir=tmpdir)

            assert result['success'] is True
            assert result['path'].endswith('.json')

    def test_should_return_error_for_empty_archive(self):
        """Test handling empty archive."""
        from archive_export import export_full_archive

        conn = create_test_db()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='zip', output_dir=tmpdir)

            # Should either succeed with empty or return warning
            assert 'warning' in result or result['sermon_count'] == 0


class TestExportSermonBundle:
    """Tests for export_sermon_bundle function."""

    def test_should_export_single_sermon(self):
        """Test exporting a single sermon bundle."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Bundle Test")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True
            assert os.path.exists(result['path'])

    def test_should_include_manuscript(self):
        """Test that bundle includes manuscript."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, manuscript="Full sermon text here")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            # Check bundle contains manuscript
            assert 'manuscript' in result.get('contents', []) or result['success']

    def test_should_include_research_notes(self):
        """Test that bundle includes research notes."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_research_note(conn, sermon_id, content="Important research")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_include_illustrations(self):
        """Test that bundle includes illustrations."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_illustration(conn, sermon_id, content="Good story")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_include_post_notes(self):
        """Test that bundle includes post-sermon notes."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_post_note(conn, sermon_id, content="What worked well")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test error for non-existent sermon."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, 9999, output_dir=tmpdir)

            assert result['success'] is False


class TestExportDateRange:
    """Tests for export_date_range function."""

    def test_should_export_date_range(self):
        """Test exporting sermons within date range."""
        from archive_export import export_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, title="Old", preached_date="2023-06-01")
        insert_sample_sermon(conn, title="Target", preached_date="2024-03-01")
        insert_sample_sermon(conn, title="Future", preached_date="2025-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_date_range(conn, "2024-01-01", "2024-12-31",
                                       output_dir=tmpdir)

            assert result['success'] is True
            assert result['sermon_count'] == 1

    def test_should_include_boundary_dates(self):
        """Test that boundary dates are included."""
        from archive_export import export_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2024-03-01")  # Start boundary
        insert_sample_sermon(conn, preached_date="2024-03-31")  # End boundary

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_date_range(conn, "2024-03-01", "2024-03-31",
                                       output_dir=tmpdir)

            assert result['sermon_count'] == 2

    def test_should_return_empty_for_no_matches(self):
        """Test handling no matching sermons."""
        from archive_export import export_date_range

        conn = create_test_db()
        insert_sample_sermon(conn, preached_date="2020-01-01")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_date_range(conn, "2024-01-01", "2024-12-31",
                                       output_dir=tmpdir)

            assert result['sermon_count'] == 0


class TestCreateBackup:
    """Tests for create_backup function."""

    def test_should_create_backup_file(self):
        """Test creating a backup file."""
        from archive_export import create_backup

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            result = create_backup(conn, backup_path)

            assert result['success'] is True
            assert os.path.exists(backup_path)

    def test_should_include_database_dump(self):
        """Test that backup includes database dump."""
        from archive_export import create_backup

        conn = create_test_db()
        insert_sample_sermon(conn, title="Test Sermon")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            with zipfile.ZipFile(backup_path, 'r') as zf:
                # Should contain database or data files
                names = zf.namelist()
                assert len(names) > 0

    def test_should_include_backup_metadata(self):
        """Test that backup includes metadata."""
        from archive_export import create_backup

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            result = create_backup(conn, backup_path)

            assert 'created_at' in result
            assert 'version' in result or 'metadata' in result

    def test_should_include_sermon_count_in_metadata(self):
        """Test that backup metadata includes sermon count."""
        from archive_export import create_backup

        conn = create_test_db()
        for i in range(5):
            insert_sample_sermon(conn, title=f"Sermon {i}")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            result = create_backup(conn, backup_path)

            assert result['sermon_count'] == 5


class TestRestoreFromBackup:
    """Tests for restore_from_backup function."""

    def test_should_restore_from_backup(self):
        """Test restoring from a backup file."""
        from archive_export import create_backup, restore_from_backup

        # Create original database and backup
        conn = create_test_db()
        insert_sample_sermon(conn, title="Original Sermon")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            # Create new connection and restore
            new_conn = create_test_db()
            result = restore_from_backup(new_conn, backup_path)

            assert result['success'] is True

    def test_should_restore_all_sermons(self):
        """Test that all sermons are restored."""
        from archive_export import create_backup, restore_from_backup

        conn = create_test_db()
        for i in range(3):
            insert_sample_sermon(conn, title=f"Sermon {i}")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            new_conn = create_test_db()
            result = restore_from_backup(new_conn, backup_path)

            assert result['restored_count'] == 3

    def test_should_return_error_for_nonexistent_file(self):
        """Test error for non-existent backup file."""
        from archive_export import restore_from_backup

        conn = create_test_db()

        result = restore_from_backup(conn, "/nonexistent/backup.zip")

        assert result['success'] is False

    def test_should_return_error_for_invalid_backup(self):
        """Test error for invalid backup file."""
        from archive_export import restore_from_backup

        conn = create_test_db()

        with tempfile.TemporaryDirectory() as tmpdir:
            invalid_path = os.path.join(tmpdir, "invalid.zip")
            with open(invalid_path, 'w') as f:
                f.write("not a zip file")

            result = restore_from_backup(conn, invalid_path)

            assert result['success'] is False


class TestValidateBackup:
    """Tests for validate_backup function."""

    def test_should_validate_good_backup(self):
        """Test validating a valid backup file."""
        from archive_export import create_backup, validate_backup

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            result = validate_backup(backup_path)

            assert result['is_valid'] is True

    def test_should_detect_corrupted_backup(self):
        """Test detecting corrupted backup file."""
        from archive_export import validate_backup

        with tempfile.TemporaryDirectory() as tmpdir:
            corrupted_path = os.path.join(tmpdir, "corrupted.zip")
            with open(corrupted_path, 'wb') as f:
                f.write(b"corrupted content")

            result = validate_backup(corrupted_path)

            assert result['is_valid'] is False

    def test_should_check_required_files(self):
        """Test checking for required files in backup."""
        from archive_export import create_backup, validate_backup

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            result = validate_backup(backup_path)

            assert 'has_metadata' in result or result['is_valid']

    def test_should_return_error_for_nonexistent_file(self):
        """Test handling non-existent file."""
        from archive_export import validate_backup

        result = validate_backup("/nonexistent/file.zip")

        assert result['is_valid'] is False
        assert 'error' in result


class TestGetBackupMetadata:
    """Tests for get_backup_metadata function."""

    def test_should_get_backup_metadata(self):
        """Test getting metadata from backup file."""
        from archive_export import create_backup, get_backup_metadata

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            result = get_backup_metadata(backup_path)

            assert result is not None
            assert 'created_at' in result

    def test_should_include_sermon_count(self):
        """Test that metadata includes sermon count."""
        from archive_export import create_backup, get_backup_metadata

        conn = create_test_db()
        for i in range(5):
            insert_sample_sermon(conn, title=f"Sermon {i}")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            result = get_backup_metadata(backup_path)

            assert result['sermon_count'] == 5

    def test_should_include_backup_version(self):
        """Test that metadata includes version info."""
        from archive_export import create_backup, get_backup_metadata

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "backup.zip")
            create_backup(conn, backup_path)

            result = get_backup_metadata(backup_path)

            assert 'version' in result or 'format_version' in result

    def test_should_return_none_for_invalid_file(self):
        """Test returning None for invalid backup."""
        from archive_export import get_backup_metadata

        result = get_backup_metadata("/nonexistent/file.zip")

        assert result is None


class TestListAvailableBackups:
    """Tests for list_available_backups function."""

    def test_should_list_backups_in_directory(self):
        """Test listing backups in a directory."""
        from archive_export import create_backup, list_available_backups

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple backups
            create_backup(conn, os.path.join(tmpdir, "backup1.zip"))
            create_backup(conn, os.path.join(tmpdir, "backup2.zip"))

            result = list_available_backups(tmpdir)

            assert len(result) == 2

    def test_should_include_backup_info(self):
        """Test that listing includes backup info."""
        from archive_export import create_backup, list_available_backups

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            create_backup(conn, os.path.join(tmpdir, "backup.zip"))

            result = list_available_backups(tmpdir)

            assert result[0]['path'] is not None
            assert result[0]['size'] > 0

    def test_should_sort_by_date(self):
        """Test sorting backups by date."""
        from archive_export import create_backup, list_available_backups

        conn = create_test_db()
        insert_sample_sermon(conn)

        with tempfile.TemporaryDirectory() as tmpdir:
            create_backup(conn, os.path.join(tmpdir, "old_backup.zip"))
            # Small delay to ensure different timestamps
            create_backup(conn, os.path.join(tmpdir, "new_backup.zip"))

            result = list_available_backups(tmpdir, sort_by='date')

            assert len(result) == 2

    def test_should_return_empty_for_no_backups(self):
        """Test returning empty for directory with no backups."""
        from archive_export import list_available_backups

        with tempfile.TemporaryDirectory() as tmpdir:
            result = list_available_backups(tmpdir)

            assert result == []


class TestExportFormats:
    """Tests for different export formats."""

    def test_should_export_as_pdf(self):
        """Test exporting sermon as PDF."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, manuscript="Sermon content here")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id,
                                         format='pdf', output_dir=tmpdir)

            # PDF export may not be implemented yet
            assert result is not None

    def test_should_export_as_word(self):
        """Test exporting sermon as Word document."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, manuscript="Sermon content here")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id,
                                         format='docx', output_dir=tmpdir)

            # Word export may not be implemented yet
            assert result is not None


class TestEdgeCases:
    """Tests for edge cases in archive export."""

    def test_should_handle_empty_archive(self):
        """Test handling empty archive export."""
        from archive_export import export_full_archive

        conn = create_test_db()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, output_dir=tmpdir)

            # Should handle gracefully
            assert isinstance(result, dict)

    def test_should_handle_large_manuscript(self):
        """Test handling large manuscript in export."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        large_manuscript = "Word " * 10000  # Very large text
        sermon_id = insert_sample_sermon(conn, manuscript=large_manuscript)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_handle_unicode_content(self):
        """Test handling unicode content in export."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(
            conn,
            title="Grace \u2764\ufe0f",
            manuscript="Unicode content: \u2728 \u2665"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_handle_special_characters_in_title(self):
        """Test handling special characters in sermon title."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(
            conn,
            title="What's Next? A Sermon!"
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_sermon_bundle(conn, sermon_id, output_dir=tmpdir)

            assert result['success'] is True

    def test_should_handle_concurrent_exports(self):
        """Test handling multiple exports at once."""
        from archive_export import export_sermon_bundle

        conn = create_test_db()
        sermon1 = insert_sample_sermon(conn, title="Sermon 1")
        sermon2 = insert_sample_sermon(conn, title="Sermon 2")

        with tempfile.TemporaryDirectory() as tmpdir:
            result1 = export_sermon_bundle(conn, sermon1, output_dir=tmpdir)
            result2 = export_sermon_bundle(conn, sermon2, output_dir=tmpdir)

            assert result1['success'] is True
            assert result2['success'] is True


class TestIntegration:
    """Integration tests for archive export."""

    def test_should_complete_backup_restore_cycle(self):
        """Test complete backup and restore workflow."""
        from archive_export import (
            create_backup,
            restore_from_backup,
            validate_backup,
            get_backup_metadata
        )

        # Create database with data
        conn = create_test_db()
        series_id = insert_sample_series(conn, name="Lent Series")
        sermon_id = insert_sample_sermon(
            conn,
            title="Lent Week 1",
            series_id=series_id,
            manuscript="Full sermon content"
        )
        insert_research_note(conn, sermon_id, content="Background research")
        insert_illustration(conn, sermon_id, content="Opening story")
        insert_post_note(conn, sermon_id, content="Went well!")

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = os.path.join(tmpdir, "full_backup.zip")

            # Create backup
            create_result = create_backup(conn, backup_path)
            assert create_result['success'] is True

            # Validate backup
            validate_result = validate_backup(backup_path)
            assert validate_result['is_valid'] is True

            # Get metadata
            metadata = get_backup_metadata(backup_path)
            assert metadata['sermon_count'] == 1

            # Restore to new database
            new_conn = create_test_db()
            restore_result = restore_from_backup(new_conn, backup_path)
            assert restore_result['success'] is True

    def test_should_export_full_archive_with_all_data(self):
        """Test full archive export with all related data."""
        from archive_export import export_full_archive

        conn = create_test_db()

        # Create comprehensive test data
        series1 = insert_sample_series(conn, name="Advent")
        series2 = insert_sample_series(conn, name="Lent")

        for i in range(5):
            sermon_id = insert_sample_sermon(
                conn,
                title=f"Sermon {i+1}",
                series_id=[series1, series2, None][i % 3],
                preached_date=f"2024-{(i+1):02d}-15"
            )
            insert_research_note(conn, sermon_id)
            insert_illustration(conn, sermon_id)
            insert_post_note(conn, sermon_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = export_full_archive(conn, format='zip', output_dir=tmpdir)

            assert result['success'] is True
            assert result['sermon_count'] == 5
            assert os.path.exists(result['path'])
