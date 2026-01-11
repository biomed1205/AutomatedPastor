"""
Tests for post-sermon notes functionality.

Tests the ability for pastors to add notes after preaching,
including reflections on what worked, congregation response,
and improvements for next time.

TDD: All tests should fail with ModuleNotFoundError until implementation.
NO MOCKS: Uses real SQLite in-memory database.
"""

import sqlite3
import pytest
from datetime import datetime


def create_test_db():
    """Create test database with sermon and notes tables."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Sermons table
    cursor.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scripture TEXT,
            status TEXT DEFAULT 'draft',
            preached_date TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Post-sermon notes table
    cursor.execute('''
        CREATE TABLE post_sermon_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            note_type TEXT NOT NULL,
            content TEXT NOT NULL,
            section_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    # Sermon sections table
    cursor.execute('''
        CREATE TABLE sermon_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT,
            position INTEGER DEFAULT 0,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id)
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", scripture="John 3:16",
                        status="preached", preached_date="2024-03-17"):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermons (title, scripture, status, preached_date)
        VALUES (?, ?, ?, ?)
    ''', (title, scripture, status, preached_date))
    conn.commit()
    return cursor.lastrowid


def insert_sample_note(conn, sermon_id, note_type="general",
                      content="Sample note", section_name=None):
    """Insert a sample post-sermon note."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO post_sermon_notes (sermon_id, note_type, content, section_name)
        VALUES (?, ?, ?, ?)
    ''', (sermon_id, note_type, content, section_name))
    conn.commit()
    return cursor.lastrowid


def insert_sermon_section(conn, sermon_id, section_name, content="",
                         position=0):
    """Insert a sermon section."""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sermon_sections (sermon_id, section_name, content, position)
        VALUES (?, ?, ?, ?)
    ''', (sermon_id, section_name, content, position))
    conn.commit()
    return cursor.lastrowid


class TestAddPostNote:
    """Tests for add_post_note function."""

    def test_should_add_post_note(self):
        """Test adding a post-sermon note."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "what_worked",
                              "Opening illustration resonated well")

        assert result is not None
        assert result['success'] is True
        assert result['note_id'] is not None

    def test_should_store_note_type(self):
        """Test that note type is stored correctly."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "improve",
                              "Need to cut the second illustration")

        cursor = conn.cursor()
        cursor.execute('SELECT note_type FROM post_sermon_notes WHERE id = ?',
                      (result['note_id'],))
        row = cursor.fetchone()
        assert row['note_type'] == "improve"

    def test_should_store_content(self):
        """Test that note content is stored correctly."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        content = "Several people mentioned the Beatitudes connection helped"

        result = add_post_note(conn, sermon_id, "congregation_response", content)

        cursor = conn.cursor()
        cursor.execute('SELECT content FROM post_sermon_notes WHERE id = ?',
                      (result['note_id'],))
        row = cursor.fetchone()
        assert row['content'] == content

    def test_should_record_timestamp(self):
        """Test that timestamp is recorded when adding note."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "general", "Test note")

        assert 'created_at' in result
        assert result['created_at'] is not None

    def test_should_reject_invalid_note_type(self):
        """Test rejecting invalid note type."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "invalid_type", "Content")

        assert result['success'] is False
        assert 'error' in result

    def test_should_return_error_for_nonexistent_sermon(self):
        """Test error handling for non-existent sermon."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()

        result = add_post_note(conn, 9999, "what_worked", "Content")

        assert result['success'] is False

    def test_should_allow_notes_for_all_valid_types(self):
        """Test all valid note types are accepted."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        valid_types = ["what_worked", "improve", "congregation_response", "general"]
        for note_type in valid_types:
            result = add_post_note(conn, sermon_id, note_type, f"Note for {note_type}")
            assert result['success'] is True, f"Failed for type: {note_type}"


class TestGetPostNotes:
    """Tests for get_post_notes function."""

    def test_should_get_all_post_notes(self):
        """Test getting all post notes for a sermon."""
        from post_sermon_notes import get_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Note 1")
        insert_sample_note(conn, sermon_id, "improve", "Note 2")

        result = get_post_notes(conn, sermon_id)

        assert len(result) == 2

    def test_should_include_note_details(self):
        """Test that note details are included."""
        from post_sermon_notes import get_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Good opening")

        result = get_post_notes(conn, sermon_id)

        assert result[0]['note_type'] == "what_worked"
        assert result[0]['content'] == "Good opening"

    def test_should_order_by_creation_time(self):
        """Test notes ordered by creation time."""
        from post_sermon_notes import get_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "First note")
        insert_sample_note(conn, sermon_id, "improve", "Second note")

        result = get_post_notes(conn, sermon_id)

        # First created should come first
        assert result[0]['content'] == "First note"

    def test_should_return_empty_for_no_notes(self):
        """Test returning empty when no notes exist."""
        from post_sermon_notes import get_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = get_post_notes(conn, sermon_id)

        assert result == []

    def test_should_return_empty_for_nonexistent_sermon(self):
        """Test returning empty for non-existent sermon."""
        from post_sermon_notes import get_post_notes

        conn = create_test_db()

        result = get_post_notes(conn, 9999)

        assert result == []


class TestUpdatePostNote:
    """Tests for update_post_note function."""

    def test_should_update_note_content(self):
        """Test updating note content."""
        from post_sermon_notes import update_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        note_id = insert_sample_note(conn, sermon_id, "what_worked",
                                    "Original content")

        result = update_post_note(conn, note_id, "Updated content")

        assert result['success'] is True

        cursor = conn.cursor()
        cursor.execute('SELECT content FROM post_sermon_notes WHERE id = ?',
                      (note_id,))
        row = cursor.fetchone()
        assert row['content'] == "Updated content"

    def test_should_update_timestamp(self):
        """Test that updated_at is changed on update."""
        from post_sermon_notes import update_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        note_id = insert_sample_note(conn, sermon_id)

        result = update_post_note(conn, note_id, "New content")

        assert 'updated_at' in result

    def test_should_return_error_for_nonexistent_note(self):
        """Test error for non-existent note."""
        from post_sermon_notes import update_post_note

        conn = create_test_db()

        result = update_post_note(conn, 9999, "Content")

        assert result['success'] is False

    def test_should_preserve_note_type_on_update(self):
        """Test that note type is preserved when updating."""
        from post_sermon_notes import update_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        note_id = insert_sample_note(conn, sermon_id, "improve", "Original")

        update_post_note(conn, note_id, "Updated")

        cursor = conn.cursor()
        cursor.execute('SELECT note_type FROM post_sermon_notes WHERE id = ?',
                      (note_id,))
        row = cursor.fetchone()
        assert row['note_type'] == "improve"


class TestDeletePostNote:
    """Tests for delete_post_note function."""

    def test_should_delete_note(self):
        """Test deleting a note."""
        from post_sermon_notes import delete_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        note_id = insert_sample_note(conn, sermon_id)

        result = delete_post_note(conn, note_id)

        assert result['success'] is True

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM post_sermon_notes WHERE id = ?',
                      (note_id,))
        assert cursor.fetchone() is None

    def test_should_return_error_for_nonexistent_note(self):
        """Test error when deleting non-existent note."""
        from post_sermon_notes import delete_post_note

        conn = create_test_db()

        result = delete_post_note(conn, 9999)

        assert result['success'] is False

    def test_should_not_affect_other_notes(self):
        """Test that deleting one note doesn't affect others."""
        from post_sermon_notes import delete_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        note1 = insert_sample_note(conn, sermon_id, content="Note 1")
        note2 = insert_sample_note(conn, sermon_id, content="Note 2")

        delete_post_note(conn, note1)

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM post_sermon_notes WHERE id = ?', (note2,))
        assert cursor.fetchone() is not None


class TestGetNotesByType:
    """Tests for get_notes_by_type function."""

    def test_should_get_notes_by_type(self):
        """Test getting notes filtered by type."""
        from post_sermon_notes import get_notes_by_type

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Note 1")
        insert_sample_note(conn, sermon_id, "improve", "Note 2")
        insert_sample_note(conn, sermon_id, "what_worked", "Note 3")

        result = get_notes_by_type(conn, sermon_id, "what_worked")

        assert len(result) == 2
        assert all(n['note_type'] == "what_worked" for n in result)

    def test_should_return_empty_for_no_matching_type(self):
        """Test returning empty when no notes of type exist."""
        from post_sermon_notes import get_notes_by_type

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Note")

        result = get_notes_by_type(conn, sermon_id, "improve")

        assert result == []

    def test_should_include_content_in_results(self):
        """Test that content is included in results."""
        from post_sermon_notes import get_notes_by_type

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "congregation_response",
                          "People were engaged during the story")

        result = get_notes_by_type(conn, sermon_id, "congregation_response")

        assert result[0]['content'] == "People were engaged during the story"

    def test_should_return_error_for_invalid_type(self):
        """Test handling invalid note type."""
        from post_sermon_notes import get_notes_by_type

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = get_notes_by_type(conn, sermon_id, "invalid_type")

        # Should return empty or error
        assert result == [] or (isinstance(result, dict) and 'error' in result)


class TestAddSectionNote:
    """Tests for add_section_note function."""

    def test_should_add_note_to_section(self):
        """Test adding a note linked to a sermon section."""
        from post_sermon_notes import add_section_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "introduction")

        result = add_section_note(conn, sermon_id, "introduction",
                                 "Opening story landed well")

        assert result['success'] is True
        assert result['section_name'] == "introduction"

    def test_should_store_section_name(self):
        """Test that section name is stored with note."""
        from post_sermon_notes import add_section_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "point_one")

        result = add_section_note(conn, sermon_id, "point_one",
                                 "This point needed more development")

        cursor = conn.cursor()
        cursor.execute('SELECT section_name FROM post_sermon_notes WHERE id = ?',
                      (result['note_id'],))
        row = cursor.fetchone()
        assert row['section_name'] == "point_one"

    def test_should_default_to_general_type(self):
        """Test that section notes default to general type."""
        from post_sermon_notes import add_section_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "conclusion")

        result = add_section_note(conn, sermon_id, "conclusion", "Strong ending")

        cursor = conn.cursor()
        cursor.execute('SELECT note_type FROM post_sermon_notes WHERE id = ?',
                      (result['note_id'],))
        row = cursor.fetchone()
        assert row['note_type'] == "general"

    def test_should_return_error_for_nonexistent_section(self):
        """Test error for non-existent section."""
        from post_sermon_notes import add_section_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_section_note(conn, sermon_id, "nonexistent_section",
                                 "Content")

        assert result['success'] is False


class TestGetSectionNotes:
    """Tests for get_section_notes function."""

    def test_should_get_notes_by_section(self):
        """Test getting all notes organized by section."""
        from post_sermon_notes import get_section_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "introduction")
        insert_sermon_section(conn, sermon_id, "conclusion")
        insert_sample_note(conn, sermon_id, section_name="introduction",
                          content="Good opening")
        insert_sample_note(conn, sermon_id, section_name="conclusion",
                          content="Strong close")

        result = get_section_notes(conn, sermon_id)

        assert "introduction" in result
        assert "conclusion" in result

    def test_should_group_multiple_notes_per_section(self):
        """Test grouping multiple notes per section."""
        from post_sermon_notes import get_section_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "point_one")
        insert_sample_note(conn, sermon_id, section_name="point_one",
                          content="Note 1")
        insert_sample_note(conn, sermon_id, section_name="point_one",
                          content="Note 2")

        result = get_section_notes(conn, sermon_id)

        assert len(result["point_one"]) == 2

    def test_should_return_empty_for_no_section_notes(self):
        """Test returning empty when no section notes exist."""
        from post_sermon_notes import get_section_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        # Add note without section
        insert_sample_note(conn, sermon_id, content="General note")

        result = get_section_notes(conn, sermon_id)

        assert result == {} or len(result) == 0

    def test_should_include_note_details(self):
        """Test that note details are included in section results."""
        from post_sermon_notes import get_section_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "introduction")
        insert_sample_note(conn, sermon_id, "what_worked",
                          "Great hook", section_name="introduction")

        result = get_section_notes(conn, sermon_id)

        note = result["introduction"][0]
        assert note['content'] == "Great hook"
        assert note['note_type'] == "what_worked"


class TestExportPostNotes:
    """Tests for export_post_notes function."""

    def test_should_export_all_notes(self):
        """Test exporting all notes for a sermon."""
        from post_sermon_notes import export_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Test Sermon",
                                        status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Note 1")
        insert_sample_note(conn, sermon_id, "improve", "Note 2")

        result = export_post_notes(conn, sermon_id)

        assert result is not None
        assert result['sermon_title'] == "Test Sermon"
        assert len(result['notes']) == 2

    def test_should_organize_export_by_type(self):
        """Test that export organizes notes by type."""
        from post_sermon_notes import export_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sample_note(conn, sermon_id, "what_worked", "Note 1")
        insert_sample_note(conn, sermon_id, "improve", "Note 2")

        result = export_post_notes(conn, sermon_id)

        assert 'by_type' in result
        assert 'what_worked' in result['by_type']
        assert 'improve' in result['by_type']

    def test_should_include_section_notes_in_export(self):
        """Test that section notes are included in export."""
        from post_sermon_notes import export_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        insert_sermon_section(conn, sermon_id, "introduction")
        insert_sample_note(conn, sermon_id, section_name="introduction",
                          content="Section note")

        result = export_post_notes(conn, sermon_id)

        assert 'by_section' in result
        assert 'introduction' in result['by_section']

    def test_should_include_preaching_date_in_export(self):
        """Test that preaching date is included in export."""
        from post_sermon_notes import export_post_notes

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, preached_date="2024-03-17",
                                        status="preached")

        result = export_post_notes(conn, sermon_id)

        assert result['preached_date'] == "2024-03-17"

    def test_should_return_none_for_nonexistent_sermon(self):
        """Test returning None for non-existent sermon."""
        from post_sermon_notes import export_post_notes

        conn = create_test_db()

        result = export_post_notes(conn, 9999)

        assert result is None


class TestEdgeCases:
    """Tests for edge cases in post-sermon notes."""

    def test_should_warn_when_adding_note_before_preaching(self):
        """Test warning when adding note to unpreached sermon."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="approved",
                                        preached_date=None)

        result = add_post_note(conn, sermon_id, "what_worked", "Note")

        # Should either warn or reject
        assert 'warning' in result or result['success'] is False

    def test_should_reject_empty_note_content(self):
        """Test rejecting empty note content."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "what_worked", "")

        assert result['success'] is False

    def test_should_handle_very_long_note(self):
        """Test handling very long note content."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        long_content = "A" * 10000

        result = add_post_note(conn, sermon_id, "general", long_content)

        assert result['success'] is True

    def test_should_handle_unicode_in_notes(self):
        """Test handling unicode characters in notes."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")
        unicode_content = "Great sermon! \u2728 People were moved \u2764\ufe0f"

        result = add_post_note(conn, sermon_id, "congregation_response",
                              unicode_content)

        assert result['success'] is True

    def test_should_handle_whitespace_only_content(self):
        """Test rejecting whitespace-only note content."""
        from post_sermon_notes import add_post_note

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        result = add_post_note(conn, sermon_id, "what_worked", "   \n\t  ")

        assert result['success'] is False

    def test_should_allow_multiple_notes_same_type_same_sermon(self):
        """Test allowing multiple notes of same type."""
        from post_sermon_notes import add_post_note, get_notes_by_type

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        add_post_note(conn, sermon_id, "improve", "First improvement note")
        add_post_note(conn, sermon_id, "improve", "Second improvement note")

        notes = get_notes_by_type(conn, sermon_id, "improve")
        assert len(notes) == 2


class TestIntegration:
    """Integration tests for post-sermon notes workflow."""

    def test_should_complete_full_notes_workflow(self):
        """Test complete workflow of adding and managing notes."""
        from post_sermon_notes import (
            add_post_note,
            get_post_notes,
            update_post_note,
            delete_post_note,
            export_post_notes
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, title="Sunday Sermon",
                                        status="preached",
                                        preached_date="2024-03-17")

        # Add notes of different types
        result1 = add_post_note(conn, sermon_id, "what_worked",
                               "Opening story was powerful")
        result2 = add_post_note(conn, sermon_id, "improve",
                               "Second point ran too long")
        result3 = add_post_note(conn, sermon_id, "congregation_response",
                               "Several people mentioned feeling challenged")

        assert all(r['success'] for r in [result1, result2, result3])

        # Get all notes
        notes = get_post_notes(conn, sermon_id)
        assert len(notes) == 3

        # Update a note
        update_result = update_post_note(conn, result2['note_id'],
                                        "Second point needs trimming next time")
        assert update_result['success'] is True

        # Delete a note
        delete_result = delete_post_note(conn, result1['note_id'])
        assert delete_result['success'] is True

        # Export remaining notes
        export = export_post_notes(conn, sermon_id)
        assert export['sermon_title'] == "Sunday Sermon"
        assert len(export['notes']) == 2

    def test_should_handle_notes_with_sections(self):
        """Test workflow with section-specific notes."""
        from post_sermon_notes import (
            add_section_note,
            get_section_notes,
            export_post_notes
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, status="preached")

        # Create sections
        insert_sermon_section(conn, sermon_id, "introduction", position=1)
        insert_sermon_section(conn, sermon_id, "point_one", position=2)
        insert_sermon_section(conn, sermon_id, "point_two", position=3)
        insert_sermon_section(conn, sermon_id, "conclusion", position=4)

        # Add section notes
        add_section_note(conn, sermon_id, "introduction",
                        "Hook was effective")
        add_section_note(conn, sermon_id, "point_one",
                        "Illustration landed well")
        add_section_note(conn, sermon_id, "point_two",
                        "Needed more scripture support")
        add_section_note(conn, sermon_id, "conclusion",
                        "Call to action was clear")

        # Get section notes
        section_notes = get_section_notes(conn, sermon_id)
        assert len(section_notes) >= 4

        # Export with sections
        export = export_post_notes(conn, sermon_id)
        assert 'by_section' in export
        assert 'introduction' in export['by_section']
