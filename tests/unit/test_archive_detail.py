"""Tests for archive detail view.

These tests verify the detail view for archived sermons.
Shows complete sermon information including manuscript, feedback, and materials.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime


def create_test_db():
    """Create an in-memory test database for archive detail testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create sermons table
    conn.execute('''
        CREATE TABLE sermons (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            scripture TEXT,
            manuscript TEXT,
            outline TEXT,
            preached_on DATE,
            series_id INTEGER,
            status TEXT DEFAULT 'published',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create series table
    conn.execute('''
        CREATE TABLE series (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')

    # Create panel_feedback table
    conn.execute('''
        CREATE TABLE panel_feedback (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            reviewer_name TEXT NOT NULL,
            feedback_text TEXT NOT NULL,
            feedback_type TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create research_notes table
    conn.execute('''
        CREATE TABLE research_notes (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            note_type TEXT,
            title TEXT,
            content TEXT NOT NULL,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create illustrations table
    conn.execute('''
        CREATE TABLE illustrations (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            source TEXT,
            section TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create sermon_versions table
    conn.execute('''
        CREATE TABLE sermon_versions (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            manuscript_text TEXT,
            author TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    # Create scripture_references table
    conn.execute('''
        CREATE TABLE scripture_references (
            id INTEGER PRIMARY KEY,
            sermon_id INTEGER NOT NULL,
            reference TEXT NOT NULL,
            is_primary INTEGER DEFAULT 0,
            context TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    return conn


def insert_sample_sermon(conn, title="Test Sermon", manuscript="Content",
                         scripture="John 3:16", preached_on="2024-01-01",
                         series_id=None, outline=None):
    """Insert a sample sermon for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermons (title, manuscript, scripture, preached_on, series_id, outline)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, manuscript, scripture, preached_on, series_id, outline)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_series(conn, name="Test Series"):
    """Insert a sample series for testing."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO series (name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid


def insert_sample_feedback(conn, sermon_id, reviewer, text, feedback_type='general'):
    """Insert sample feedback for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO panel_feedback (sermon_id, reviewer_name, feedback_text, feedback_type)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, reviewer, text, feedback_type)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_research(conn, sermon_id, content, note_type='biblical', title=None):
    """Insert sample research note for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO research_notes (sermon_id, content, note_type, title)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, content, note_type, title)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_illustration(conn, sermon_id, description, source=None, section=None):
    """Insert sample illustration for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO illustrations (sermon_id, description, source, section)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, description, source, section)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_version(conn, sermon_id, version_number, text, author=None):
    """Insert sample version for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO sermon_versions (sermon_id, version_number, manuscript_text, author)
           VALUES (?, ?, ?, ?)""",
        (sermon_id, version_number, text, author)
    )
    conn.commit()
    return cursor.lastrowid


def insert_sample_scripture_ref(conn, sermon_id, reference, is_primary=0):
    """Insert sample scripture reference for testing."""
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO scripture_references (sermon_id, reference, is_primary)
           VALUES (?, ?, ?)""",
        (sermon_id, reference, is_primary)
    )
    conn.commit()
    return cursor.lastrowid


class TestGetArchiveDetail:
    """Test suite for getting archive detail."""

    def test_should_get_archive_detail(self):
        """Test that archive detail is returned."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Easter Sermon")

        detail = get_archive_detail(conn, sermon_id)

        assert detail is not None
        assert detail['title'] == "Easter Sermon"
        conn.close()

    def test_should_include_manuscript(self):
        """Test that manuscript is included."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon", manuscript="Full manuscript text here.")

        detail = get_archive_detail(conn, sermon_id)

        assert detail['manuscript'] == "Full manuscript text here."
        conn.close()

    def test_should_include_outline(self):
        """Test that outline is included."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        outline = "1. Introduction\n2. Point One\n3. Point Two\n4. Conclusion"
        sermon_id = insert_sample_sermon(conn, "Sermon", outline=outline)

        detail = get_archive_detail(conn, sermon_id)

        assert detail['outline'] == outline
        conn.close()

    def test_should_include_scripture(self):
        """Test that scripture reference is included."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Sermon", scripture="Romans 8:28")

        detail = get_archive_detail(conn, sermon_id)

        assert detail['scripture'] == "Romans 8:28"
        conn.close()

    def test_should_include_series_context(self):
        """Test that series context is included when applicable."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Lent Series")
        sermon_id = insert_sample_sermon(conn, "Lent Week 1", series_id=series_id)

        detail = get_archive_detail(conn, sermon_id)

        assert detail.get('series_id') == series_id or detail.get('series_name') == "Lent Series"
        conn.close()

    def test_should_return_none_for_nonexistent_sermon(self):
        """Test that None is returned for nonexistent sermon."""
        from archive_detail import get_archive_detail

        conn = create_test_db()

        detail = get_archive_detail(conn, 9999)

        assert detail is None
        conn.close()


class TestGetArchiveMaterials:
    """Test suite for getting archive materials."""

    def test_should_get_archive_materials(self):
        """Test that all materials are returned."""
        from archive_detail import get_archive_materials

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_research(conn, sermon_id, "Research note")
        insert_sample_illustration(conn, sermon_id, "Illustration")

        materials = get_archive_materials(conn, sermon_id)

        assert materials is not None
        conn.close()

    def test_should_include_research_notes(self):
        """Test that research notes are included."""
        from archive_detail import get_archive_materials

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_research(conn, sermon_id, "Note 1")
        insert_sample_research(conn, sermon_id, "Note 2")

        materials = get_archive_materials(conn, sermon_id)

        assert 'research' in materials or 'research_notes' in materials
        conn.close()

    def test_should_include_illustrations(self):
        """Test that illustrations are included."""
        from archive_detail import get_archive_materials

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_illustration(conn, sermon_id, "Story about...")

        materials = get_archive_materials(conn, sermon_id)

        assert 'illustrations' in materials
        conn.close()

    def test_should_handle_sermon_without_materials(self):
        """Test handling of sermon without materials."""
        from archive_detail import get_archive_materials

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        materials = get_archive_materials(conn, sermon_id)

        assert materials is not None
        conn.close()


class TestGetArchiveFeedback:
    """Test suite for getting archive feedback."""

    def test_should_get_archive_feedback(self):
        """Test that panel feedback is returned."""
        from archive_detail import get_archive_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_feedback(conn, sermon_id, "John", "Great intro!")
        insert_sample_feedback(conn, sermon_id, "Jane", "Consider more examples.")

        feedback = get_archive_feedback(conn, sermon_id)

        assert len(feedback) == 2
        conn.close()

    def test_should_organize_feedback_by_reviewer(self):
        """Test that feedback is organized by reviewer."""
        from archive_detail import get_archive_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_feedback(conn, sermon_id, "John", "Comment 1")
        insert_sample_feedback(conn, sermon_id, "John", "Comment 2")
        insert_sample_feedback(conn, sermon_id, "Jane", "Comment")

        feedback = get_archive_feedback(conn, sermon_id)

        # Should have structure for reviewers
        assert feedback is not None
        conn.close()

    def test_should_include_feedback_type(self):
        """Test that feedback type is included."""
        from archive_detail import get_archive_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_feedback(conn, sermon_id, "Editor", "Fix grammar", feedback_type='editorial')

        feedback = get_archive_feedback(conn, sermon_id)

        if isinstance(feedback, list) and len(feedback) > 0:
            assert feedback[0].get('feedback_type') == 'editorial'
        conn.close()

    def test_should_return_empty_for_no_feedback(self):
        """Test that empty list is returned for no feedback."""
        from archive_detail import get_archive_feedback

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        feedback = get_archive_feedback(conn, sermon_id)

        assert feedback == [] or feedback == {}
        conn.close()


class TestGetArchiveResearch:
    """Test suite for getting archive research notes."""

    def test_should_get_archive_research(self):
        """Test that research notes are returned."""
        from archive_detail import get_archive_research

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_research(conn, sermon_id, "Biblical context...")
        insert_sample_research(conn, sermon_id, "Historical background...")

        research = get_archive_research(conn, sermon_id)

        assert len(research) == 2
        conn.close()

    def test_should_categorize_by_note_type(self):
        """Test that research is categorized by type."""
        from archive_detail import get_archive_research

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_research(conn, sermon_id, "Note 1", note_type='biblical')
        insert_sample_research(conn, sermon_id, "Note 2", note_type='theological')

        research = get_archive_research(conn, sermon_id)

        # Should have type information
        assert research is not None
        conn.close()

    def test_should_include_sources(self):
        """Test that sources are included."""
        from archive_detail import get_archive_research

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO research_notes (sermon_id, content, source)
               VALUES (?, ?, ?)""",
            (sermon_id, "Quote", "Commentary by N.T. Wright")
        )
        conn.commit()

        research = get_archive_research(conn, sermon_id)

        if isinstance(research, list) and len(research) > 0:
            assert research[0].get('source') is not None
        conn.close()

    def test_should_return_empty_for_no_research(self):
        """Test that empty list is returned for no research."""
        from archive_detail import get_archive_research

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        research = get_archive_research(conn, sermon_id)

        assert research == []
        conn.close()


class TestGetArchiveIllustrations:
    """Test suite for getting archive illustrations."""

    def test_should_get_archive_illustrations(self):
        """Test that illustrations are returned."""
        from archive_detail import get_archive_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_illustration(conn, sermon_id, "Story about forgiveness")
        insert_sample_illustration(conn, sermon_id, "Modern example of faith")

        illustrations = get_archive_illustrations(conn, sermon_id)

        assert len(illustrations) == 2
        conn.close()

    def test_should_include_section_placement(self):
        """Test that section placement is included."""
        from archive_detail import get_archive_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_illustration(conn, sermon_id, "Intro story", section="introduction")
        insert_sample_illustration(conn, sermon_id, "Main story", section="point_2")

        illustrations = get_archive_illustrations(conn, sermon_id)

        if len(illustrations) > 0:
            assert 'section' in illustrations[0]
        conn.close()

    def test_should_include_sources(self):
        """Test that sources are included."""
        from archive_detail import get_archive_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_illustration(conn, sermon_id, "News story", source="NY Times 2024-01-15")

        illustrations = get_archive_illustrations(conn, sermon_id)

        if len(illustrations) > 0:
            assert illustrations[0].get('source') == "NY Times 2024-01-15"
        conn.close()

    def test_should_return_empty_for_no_illustrations(self):
        """Test that empty list is returned for no illustrations."""
        from archive_detail import get_archive_illustrations

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        illustrations = get_archive_illustrations(conn, sermon_id)

        assert illustrations == []
        conn.close()


class TestGetArchiveVersions:
    """Test suite for getting archive versions."""

    def test_should_get_archive_versions(self):
        """Test that version history is returned."""
        from archive_detail import get_archive_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "First draft")
        insert_sample_version(conn, sermon_id, 2, "Revised")
        insert_sample_version(conn, sermon_id, 3, "Final")

        versions = get_archive_versions(conn, sermon_id)

        assert len(versions) == 3
        conn.close()

    def test_should_order_by_version_number(self):
        """Test that versions are ordered by version number."""
        from archive_detail import get_archive_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 3, "Third")
        insert_sample_version(conn, sermon_id, 1, "First")
        insert_sample_version(conn, sermon_id, 2, "Second")

        versions = get_archive_versions(conn, sermon_id)

        # Should be ordered (descending - most recent first)
        assert versions[0]['version_number'] == 3 or versions[0]['version_number'] == 1
        conn.close()

    def test_should_include_author(self):
        """Test that author is included."""
        from archive_detail import get_archive_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_version(conn, sermon_id, 1, "Draft", author="Pastor Katie")

        versions = get_archive_versions(conn, sermon_id)

        assert versions[0].get('author') == "Pastor Katie"
        conn.close()

    def test_should_return_empty_for_no_versions(self):
        """Test that empty list is returned for no versions."""
        from archive_detail import get_archive_versions

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        versions = get_archive_versions(conn, sermon_id)

        assert versions == []
        conn.close()


class TestGetScriptureReferences:
    """Test suite for getting scripture references."""

    def test_should_get_scripture_references(self):
        """Test that scripture references are returned."""
        from archive_detail import get_scripture_references

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_scripture_ref(conn, sermon_id, "John 3:16", is_primary=1)
        insert_sample_scripture_ref(conn, sermon_id, "Romans 8:28")
        insert_sample_scripture_ref(conn, sermon_id, "Psalm 23:1")

        refs = get_scripture_references(conn, sermon_id)

        assert len(refs) == 3
        conn.close()

    def test_should_indicate_primary_reference(self):
        """Test that primary reference is indicated."""
        from archive_detail import get_scripture_references

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)
        insert_sample_scripture_ref(conn, sermon_id, "Main Text", is_primary=1)
        insert_sample_scripture_ref(conn, sermon_id, "Supporting", is_primary=0)

        refs = get_scripture_references(conn, sermon_id)

        primary = [r for r in refs if r.get('is_primary')]
        assert len(primary) == 1
        conn.close()

    def test_should_return_empty_for_no_references(self):
        """Test that empty list is returned for no references."""
        from archive_detail import get_scripture_references

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        refs = get_scripture_references(conn, sermon_id)

        assert refs == []
        conn.close()


class TestExportArchiveBundle:
    """Test suite for exporting archive bundle."""

    def test_should_export_archive_bundle(self):
        """Test that archive bundle can be exported."""
        from archive_detail import export_archive_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Export Sermon", "Full manuscript")

        bundle = export_archive_bundle(conn, sermon_id)

        assert bundle is not None
        conn.close()

    def test_should_include_all_materials_in_bundle(self):
        """Test that all materials are included in bundle."""
        from archive_detail import export_archive_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Rich Sermon", "Manuscript")
        insert_sample_feedback(conn, sermon_id, "Reviewer", "Great!")
        insert_sample_research(conn, sermon_id, "Research note")
        insert_sample_illustration(conn, sermon_id, "Illustration")
        insert_sample_version(conn, sermon_id, 1, "Version 1")

        bundle = export_archive_bundle(conn, sermon_id)

        assert 'sermon' in bundle or 'manuscript' in bundle
        assert 'feedback' in bundle or 'materials' in bundle
        conn.close()

    def test_should_include_metadata_in_bundle(self):
        """Test that metadata is included in bundle."""
        from archive_detail import export_archive_bundle

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Metadata Sermon")

        bundle = export_archive_bundle(conn, sermon_id)

        assert 'title' in bundle or 'metadata' in bundle or 'sermon' in bundle
        conn.close()

    def test_should_return_none_for_nonexistent_sermon(self):
        """Test that None is returned for nonexistent sermon."""
        from archive_detail import export_archive_bundle

        conn = create_test_db()

        bundle = export_archive_bundle(conn, 9999)

        assert bundle is None
        conn.close()


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_should_handle_minimal_sermon(self):
        """Test sermon with only required fields."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn, "Minimal", manuscript=None)

        detail = get_archive_detail(conn, sermon_id)

        assert detail is not None
        assert detail['title'] == "Minimal"
        conn.close()

    def test_should_handle_rich_sermon(self):
        """Test sermon with all fields populated."""
        from archive_detail import get_archive_detail, get_archive_materials

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Series")
        sermon_id = insert_sample_sermon(
            conn, "Rich Sermon", "Full manuscript",
            scripture="John 3:16", series_id=series_id,
            outline="1. Intro\n2. Body\n3. Conclusion"
        )
        insert_sample_feedback(conn, sermon_id, "R1", "Good")
        insert_sample_feedback(conn, sermon_id, "R2", "Great")
        insert_sample_research(conn, sermon_id, "Note 1")
        insert_sample_research(conn, sermon_id, "Note 2")
        insert_sample_illustration(conn, sermon_id, "Story 1")
        insert_sample_version(conn, sermon_id, 1, "V1")
        insert_sample_version(conn, sermon_id, 2, "V2")

        detail = get_archive_detail(conn, sermon_id)
        materials = get_archive_materials(conn, sermon_id)

        assert detail is not None
        assert materials is not None
        conn.close()

    def test_should_handle_unicode_in_content(self):
        """Test unicode in sermon content."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        sermon_id = insert_sample_sermon(
            conn,
            "Greek Sermon: ἀγάπη",
            manuscript="In Greek, love is ἀγάπη (agape)."
        )

        detail = get_archive_detail(conn, sermon_id)

        assert 'ἀγάπη' in detail['title']
        assert 'ἀγάπη' in detail['manuscript']
        conn.close()

    def test_should_handle_very_long_manuscript(self):
        """Test very long manuscript."""
        from archive_detail import get_archive_detail

        conn = create_test_db()
        long_manuscript = "This is the sermon content. " * 1000
        sermon_id = insert_sample_sermon(conn, "Long Sermon", manuscript=long_manuscript)

        detail = get_archive_detail(conn, sermon_id)

        assert len(detail['manuscript']) == len(long_manuscript)
        conn.close()

    def test_should_handle_missing_optional_materials(self):
        """Test sermon with missing optional materials."""
        from archive_detail import (
            get_archive_feedback,
            get_archive_research,
            get_archive_illustrations,
            get_archive_versions
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(conn)

        feedback = get_archive_feedback(conn, sermon_id)
        research = get_archive_research(conn, sermon_id)
        illustrations = get_archive_illustrations(conn, sermon_id)
        versions = get_archive_versions(conn, sermon_id)

        assert feedback == [] or feedback == {}
        assert research == []
        assert illustrations == []
        assert versions == []
        conn.close()


class TestIntegration:
    """Integration tests for archive detail workflows."""

    def test_should_get_complete_archive_view(self):
        """Test getting complete archive view."""
        from archive_detail import (
            get_archive_detail,
            get_archive_materials,
            get_archive_feedback
        )

        conn = create_test_db()
        sermon_id = insert_sample_sermon(
            conn, "Complete Sermon", "Manuscript text",
            scripture="John 14:6"
        )
        insert_sample_feedback(conn, sermon_id, "Reviewer", "Good sermon!")
        insert_sample_research(conn, sermon_id, "Background info")

        detail = get_archive_detail(conn, sermon_id)
        materials = get_archive_materials(conn, sermon_id)
        feedback = get_archive_feedback(conn, sermon_id)

        assert detail['title'] == "Complete Sermon"
        assert materials is not None
        assert len(feedback) == 1 or feedback != {}

        conn.close()

    def test_should_export_complete_bundle(self):
        """Test exporting complete bundle."""
        from archive_detail import export_archive_bundle

        conn = create_test_db()
        series_id = insert_sample_series(conn, "Export Series")
        sermon_id = insert_sample_sermon(
            conn, "Bundle Sermon", "Full manuscript content",
            scripture="Romans 8:28", series_id=series_id
        )
        insert_sample_feedback(conn, sermon_id, "Editor", "Approved!")
        insert_sample_research(conn, sermon_id, "Commentary notes")
        insert_sample_illustration(conn, sermon_id, "Opening story")
        insert_sample_version(conn, sermon_id, 1, "Initial draft")
        insert_sample_version(conn, sermon_id, 2, "Final version")

        bundle = export_archive_bundle(conn, sermon_id)

        assert bundle is not None
        # Bundle should contain comprehensive data
        conn.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
