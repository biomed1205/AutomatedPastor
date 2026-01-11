"""Tests for SQLite database schema.

These tests verify the database schema can be created correctly and all tables
function as expected with proper constraints, foreign keys, and CRUD operations.
Tests are written first (TDD) - implementation does not exist yet.
All tests use REAL SQLite in-memory database - NO MOCKS.
"""
import pytest
import sqlite3
from datetime import datetime, date


class TestDatabaseCreation:
    """Test suite for database initialization and schema creation."""

    def test_should_create_database_when_init_called(self):
        """Test that database module can create all tables."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        # Verify connection is valid
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert len(tables) >= 12  # At least 12 tables should exist
        conn.close()

    def test_should_create_all_required_tables_when_init_called(self):
        """Test that all 12 required tables are created."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            'sermons',
            'illustrations',
            'scriptures_used',
            'themes',
            'custom_reviewers',
            'sermon_reviewers',
            'reference_materials',
            'sermon_series',
            'chat_sessions',
            'chat_messages',
            'share_links',
            'review_comments'
        ]

        for table in required_tables:
            assert table in tables, f"Table '{table}' should exist"

        conn.close()

    def test_should_enable_foreign_keys_when_init_called(self):
        """Test that foreign key constraints are enabled."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys")
        result = cursor.fetchone()

        assert result[0] == 1, "Foreign keys should be enabled"
        conn.close()


class TestSermonsTable:
    """Test suite for sermons table."""

    def test_should_create_sermon_when_valid_data_provided(self):
        """Test inserting a sermon with required fields."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture, theme, main_point)
            VALUES (?, ?, ?, ?)
        """, ('Test Sermon', 'John 3:16', 'Love', 'God loves us'))
        conn.commit()

        cursor.execute("SELECT * FROM sermons WHERE title = ?", ('Test Sermon',))
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_reject_sermon_when_title_missing(self):
        """Test that title is required (NOT NULL)."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO sermons (scripture, theme)
                VALUES (?, ?)
            """, ('John 3:16', 'Love'))
            conn.commit()

        conn.close()

    def test_should_reject_sermon_when_scripture_missing(self):
        """Test that scripture is required (NOT NULL)."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO sermons (title, theme)
                VALUES (?, ?)
            """, ('Test Sermon', 'Love'))
            conn.commit()

        conn.close()

    def test_should_set_created_at_default_when_sermon_inserted(self):
        """Test that created_at gets default timestamp."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture)
            VALUES (?, ?)
        """, ('Test Sermon', 'John 3:16'))
        conn.commit()

        cursor.execute("SELECT created_at FROM sermons WHERE title = ?", ('Test Sermon',))
        row = cursor.fetchone()

        assert row[0] is not None, "created_at should have default value"
        conn.close()

    def test_should_update_sermon_when_valid_changes_made(self):
        """Test updating an existing sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture, manuscript)
            VALUES (?, ?, ?)
        """, ('Original Title', 'John 3:16', 'Original content'))
        conn.commit()

        cursor.execute("""
            UPDATE sermons SET title = ?, manuscript = ? WHERE scripture = ?
        """, ('Updated Title', 'Updated content', 'John 3:16'))
        conn.commit()

        cursor.execute("SELECT title, manuscript FROM sermons WHERE scripture = ?", ('John 3:16',))
        row = cursor.fetchone()

        assert row[0] == 'Updated Title'
        assert row[1] == 'Updated content'
        conn.close()

    def test_should_delete_sermon_when_id_specified(self):
        """Test deleting a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sermons (title, scripture) VALUES (?, ?)
        """, ('To Delete', 'John 3:16'))
        conn.commit()

        cursor.execute("DELETE FROM sermons WHERE title = ?", ('To Delete',))
        conn.commit()

        cursor.execute("SELECT * FROM sermons WHERE title = ?", ('To Delete',))
        row = cursor.fetchone()

        assert row is None
        conn.close()

    def test_should_link_sermon_to_series_when_series_id_provided(self):
        """Test that sermons can be linked to sermon_series."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        # Create series first
        cursor.execute("""
            INSERT INTO sermon_series (title, description)
            VALUES (?, ?)
        """, ('Rooted', 'A series on spiritual foundations'))
        conn.commit()
        series_id = cursor.lastrowid

        # Create sermon linked to series
        cursor.execute("""
            INSERT INTO sermons (title, scripture, series_id, series_week)
            VALUES (?, ?, ?, ?)
        """, ('Week 1: Connected', 'John 15:1-8', series_id, 1))
        conn.commit()

        cursor.execute("""
            SELECT s.title, ss.title as series_title, s.series_week
            FROM sermons s
            JOIN sermon_series ss ON s.series_id = ss.id
            WHERE s.title = ?
        """, ('Week 1: Connected',))
        row = cursor.fetchone()

        assert row[1] == 'Rooted'
        assert row[2] == 1
        conn.close()


class TestIllustrationsTable:
    """Test suite for illustrations table."""

    def test_should_create_illustration_when_linked_to_sermon(self):
        """Test inserting an illustration linked to a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        # Create sermon first
        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO illustrations (sermon_id, type, content, source)
            VALUES (?, ?, ?, ?)
        """, (sermon_id, 'story', 'A story about grace', 'Personal experience'))
        conn.commit()

        cursor.execute("SELECT * FROM illustrations WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row is not None
        conn.close()

    def test_should_reject_illustration_when_sermon_id_invalid(self):
        """Test foreign key constraint on sermon_id."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO illustrations (sermon_id, type, content)
                VALUES (?, ?, ?)
            """, (9999, 'story', 'Invalid sermon reference'))
            conn.commit()

        conn.close()

    def test_should_set_used_at_default_when_illustration_inserted(self):
        """Test that used_at gets default timestamp."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO illustrations (sermon_id, type, content)
            VALUES (?, ?, ?)
        """, (sermon_id, 'quote', 'A wise quote'))
        conn.commit()

        cursor.execute("SELECT used_at FROM illustrations WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row[0] is not None
        conn.close()

    def test_should_cascade_delete_illustrations_when_sermon_deleted(self):
        """Test that illustrations are deleted when parent sermon is deleted."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO illustrations (sermon_id, type, content)
            VALUES (?, ?, ?)
        """, (sermon_id, 'story', 'Test illustration'))
        conn.commit()

        cursor.execute("DELETE FROM sermons WHERE id = ?", (sermon_id,))
        conn.commit()

        cursor.execute("SELECT * FROM illustrations WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row is None, "Illustrations should be cascade deleted"
        conn.close()


class TestScripturesUsedTable:
    """Test suite for scriptures_used table."""

    def test_should_create_scripture_reference_when_valid_data(self):
        """Test inserting a scripture reference."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO scriptures_used (sermon_id, reference, translation)
            VALUES (?, ?, ?)
        """, (sermon_id, 'John 3:16-17', 'NRSV'))
        conn.commit()

        cursor.execute("SELECT reference, translation FROM scriptures_used WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'John 3:16-17'
        assert row[1] == 'NRSV'
        conn.close()

    def test_should_reject_scripture_when_sermon_id_invalid(self):
        """Test foreign key constraint on sermon_id."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO scriptures_used (sermon_id, reference)
                VALUES (?, ?)
            """, (9999, 'John 3:16'))
            conn.commit()

        conn.close()

    def test_should_allow_multiple_scriptures_per_sermon(self):
        """Test that a sermon can have multiple scripture references."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        scriptures = [
            ('John 3:16', 'NRSV'),
            ('Romans 8:28', 'NIV'),
            ('Psalm 23:1', 'KJV')
        ]

        for ref, trans in scriptures:
            cursor.execute("""
                INSERT INTO scriptures_used (sermon_id, reference, translation)
                VALUES (?, ?, ?)
            """, (sermon_id, ref, trans))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM scriptures_used WHERE sermon_id = ?",
                      (sermon_id,))
        count = cursor.fetchone()[0]

        assert count == 3
        conn.close()


class TestThemesTable:
    """Test suite for themes table."""

    def test_should_create_theme_when_linked_to_sermon(self):
        """Test inserting a theme linked to a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO themes (sermon_id, theme)
            VALUES (?, ?)
        """, (sermon_id, 'Grace'))
        conn.commit()

        cursor.execute("SELECT theme FROM themes WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'Grace'
        conn.close()

    def test_should_track_theme_usage_over_time(self):
        """Test that themes have timestamps for tracking frequency."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("INSERT INTO themes (sermon_id, theme) VALUES (?, ?)",
                      (sermon_id, 'Love'))
        conn.commit()

        cursor.execute("SELECT used_at FROM themes WHERE sermon_id = ?", (sermon_id,))
        row = cursor.fetchone()

        assert row[0] is not None
        conn.close()


class TestCustomReviewersTable:
    """Test suite for custom_reviewers table."""

    def test_should_create_custom_reviewer_when_valid_data(self):
        """Test inserting a custom reviewer."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO custom_reviewers (name, focus_area, style_notes)
            VALUES (?, ?, ?)
        """, ('Fred Craddock', 'Inductive preaching', 'Master storyteller'))
        conn.commit()

        cursor.execute("SELECT name, focus_area FROM custom_reviewers WHERE name = ?",
                      ('Fred Craddock',))
        row = cursor.fetchone()

        assert row[0] == 'Fred Craddock'
        assert row[1] == 'Inductive preaching'
        conn.close()

    def test_should_reject_reviewer_when_name_missing(self):
        """Test that name is required (NOT NULL)."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO custom_reviewers (focus_area, style_notes)
                VALUES (?, ?)
            """, ('Preaching', 'Notes'))
            conn.commit()

        conn.close()

    def test_should_set_is_default_false_when_not_specified(self):
        """Test that is_default defaults to FALSE."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO custom_reviewers (name, focus_area)
            VALUES (?, ?)
        """, ('Test Reviewer', 'General'))
        conn.commit()

        cursor.execute("SELECT is_default FROM custom_reviewers WHERE name = ?",
                      ('Test Reviewer',))
        row = cursor.fetchone()

        assert row[0] == 0 or row[0] is False
        conn.close()

    def test_should_allow_setting_reviewer_as_default(self):
        """Test that a reviewer can be marked as default."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO custom_reviewers (name, focus_area, is_default)
            VALUES (?, ?, ?)
        """, ('Default Reviewer', 'General', True))
        conn.commit()

        cursor.execute("SELECT is_default FROM custom_reviewers WHERE name = ?",
                      ('Default Reviewer',))
        row = cursor.fetchone()

        assert row[0] == 1 or row[0] is True
        conn.close()


class TestSermonReviewersTable:
    """Test suite for sermon_reviewers table."""

    def test_should_link_reviewer_to_sermon(self):
        """Test linking a reviewer to a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO sermon_reviewers (sermon_id, reviewer_name, feedback)
            VALUES (?, ?, ?)
        """, (sermon_id, 'Adam Hamilton', 'Great practical application!'))
        conn.commit()

        cursor.execute("SELECT reviewer_name, feedback FROM sermon_reviewers WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'Adam Hamilton'
        assert row[1] == 'Great practical application!'
        conn.close()

    def test_should_track_if_reviewer_is_custom(self):
        """Test that is_custom flag works correctly."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        # Built-in reviewer
        cursor.execute("""
            INSERT INTO sermon_reviewers (sermon_id, reviewer_name, is_custom)
            VALUES (?, ?, ?)
        """, (sermon_id, 'Will Willimon', False))

        # Custom reviewer
        cursor.execute("""
            INSERT INTO sermon_reviewers (sermon_id, reviewer_name, is_custom)
            VALUES (?, ?, ?)
        """, (sermon_id, 'Fred Craddock', True))
        conn.commit()

        cursor.execute("""
            SELECT reviewer_name, is_custom FROM sermon_reviewers
            WHERE sermon_id = ? ORDER BY reviewer_name
        """, (sermon_id,))
        rows = cursor.fetchall()

        assert len(rows) == 2
        # Fred Craddock should be custom
        fred = [r for r in rows if r[0] == 'Fred Craddock'][0]
        assert fred[1] == 1 or fred[1] is True
        conn.close()


class TestReferenceMaterialsTable:
    """Test suite for reference_materials table."""

    def test_should_create_text_note_reference(self):
        """Test creating a text notes reference material."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO reference_materials (sermon_id, type, title, content, usage_mode)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 'text_notes', 'My Notes', 'Some research notes...', 'source'))
        conn.commit()

        cursor.execute("SELECT type, title, content, usage_mode FROM reference_materials WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'text_notes'
        assert row[1] == 'My Notes'
        assert row[3] == 'source'
        conn.close()

    def test_should_create_file_reference(self):
        """Test creating a file-based reference material."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO reference_materials (sermon_id, type, title, file_path, usage_mode)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 'file', 'Commentary PDF', '/uploads/commentary.pdf', 'background'))
        conn.commit()

        cursor.execute("SELECT type, file_path, usage_mode FROM reference_materials WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'file'
        assert row[1] == '/uploads/commentary.pdf'
        assert row[2] == 'background'
        conn.close()

    def test_should_create_url_reference(self):
        """Test creating a URL-based reference material."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO reference_materials (sermon_id, type, title, url, usage_mode)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 'url', 'Working Preacher', 'https://workingpreacher.org/john-3', 'constraint'))
        conn.commit()

        cursor.execute("SELECT type, url, usage_mode FROM reference_materials WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'url'
        assert row[1] == 'https://workingpreacher.org/john-3'
        assert row[2] == 'constraint'
        conn.close()


class TestSermonSeriesTable:
    """Test suite for sermon_series table."""

    def test_should_create_series_when_valid_data(self):
        """Test creating a sermon series."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sermon_series (title, description, theme, planned_weeks)
            VALUES (?, ?, ?, ?)
        """, ('Rooted', 'Spiritual foundations', 'Growth', 6))
        conn.commit()

        cursor.execute("SELECT title, planned_weeks FROM sermon_series WHERE title = ?",
                      ('Rooted',))
        row = cursor.fetchone()

        assert row[0] == 'Rooted'
        assert row[1] == 6
        conn.close()

    def test_should_reject_series_when_title_missing(self):
        """Test that title is required (NOT NULL)."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO sermon_series (description, theme)
                VALUES (?, ?)
            """, ('A description', 'A theme'))
            conn.commit()

        conn.close()

    def test_should_store_narrative_arc_as_json(self):
        """Test that narrative_arc can store JSON data."""
        from database import init_db
        import json

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        arc = json.dumps(['Introduction', 'Development', 'Climax', 'Resolution'])

        cursor.execute("""
            INSERT INTO sermon_series (title, narrative_arc)
            VALUES (?, ?)
        """, ('Test Series', arc))
        conn.commit()

        cursor.execute("SELECT narrative_arc FROM sermon_series WHERE title = ?",
                      ('Test Series',))
        row = cursor.fetchone()

        retrieved_arc = json.loads(row[0])
        assert len(retrieved_arc) == 4
        assert 'Climax' in retrieved_arc
        conn.close()


class TestChatSessionsTable:
    """Test suite for chat_sessions table."""

    def test_should_create_chat_session(self):
        """Test creating a chat session."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chat_sessions (title)
            VALUES (?)
        """, ('Brainstorm: John 15',))
        conn.commit()

        cursor.execute("SELECT title FROM chat_sessions WHERE title = ?",
                      ('Brainstorm: John 15',))
        row = cursor.fetchone()

        assert row[0] == 'Brainstorm: John 15'
        conn.close()

    def test_should_link_chat_session_to_sermon(self):
        """Test linking a chat session to a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 15:1-8'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO chat_sessions (sermon_id, title)
            VALUES (?, ?)
        """, (sermon_id, 'Discussion about vine imagery'))
        conn.commit()

        cursor.execute("""
            SELECT cs.title, s.scripture
            FROM chat_sessions cs
            JOIN sermons s ON cs.sermon_id = s.id
            WHERE cs.sermon_id = ?
        """, (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'Discussion about vine imagery'
        assert row[1] == 'John 15:1-8'
        conn.close()

    def test_should_set_created_at_default_for_session(self):
        """Test that created_at gets default timestamp."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)",
                      ('Test Session',))
        conn.commit()

        cursor.execute("SELECT created_at FROM chat_sessions WHERE title = ?",
                      ('Test Session',))
        row = cursor.fetchone()

        assert row[0] is not None
        conn.close()


class TestChatMessagesTable:
    """Test suite for chat_messages table."""

    def test_should_create_message_in_session(self):
        """Test creating a message in a chat session."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)",
                      ('Test Session',))
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES (?, ?, ?)
        """, (session_id, 'Katie', 'What do you think about this passage?'))
        conn.commit()

        cursor.execute("SELECT sender, message FROM chat_messages WHERE session_id = ?",
                      (session_id,))
        row = cursor.fetchone()

        assert row[0] == 'Katie'
        assert row[1] == 'What do you think about this passage?'
        conn.close()

    def test_should_reject_message_when_session_id_invalid(self):
        """Test foreign key constraint on session_id."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO chat_messages (session_id, sender, message)
                VALUES (?, ?, ?)
            """, (9999, 'Katie', 'Invalid session'))
            conn.commit()

        conn.close()

    def test_should_store_mentioned_panelists_as_json(self):
        """Test that mentioned_panelists can store JSON array."""
        from database import init_db
        import json

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)",
                      ('Test Session',))
        session_id = cursor.lastrowid

        mentions = json.dumps(['Adam Hamilton', 'Barbara Brown Taylor'])

        cursor.execute("""
            INSERT INTO chat_messages (session_id, sender, message, mentioned_panelists)
            VALUES (?, ?, ?, ?)
        """, (session_id, 'Katie', '@Adam @Barbara thoughts?', mentions))
        conn.commit()

        cursor.execute("SELECT mentioned_panelists FROM chat_messages WHERE session_id = ?",
                      (session_id,))
        row = cursor.fetchone()

        retrieved_mentions = json.loads(row[0])
        assert 'Adam Hamilton' in retrieved_mentions
        assert 'Barbara Brown Taylor' in retrieved_mentions
        conn.close()

    def test_should_cascade_delete_messages_when_session_deleted(self):
        """Test that messages are deleted when session is deleted."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO chat_sessions (title) VALUES (?)",
                      ('Test Session',))
        session_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO chat_messages (session_id, sender, message)
            VALUES (?, ?, ?)
        """, (session_id, 'Katie', 'Test message'))
        conn.commit()

        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()

        cursor.execute("SELECT * FROM chat_messages WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        assert row is None, "Messages should be cascade deleted"
        conn.close()


class TestShareLinksTable:
    """Test suite for share_links table."""

    def test_should_create_share_link_for_sermon(self):
        """Test creating a share link for a sermon."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO share_links (sermon_id, share_token)
            VALUES (?, ?)
        """, (sermon_id, 'abc123xyz'))
        conn.commit()

        cursor.execute("SELECT share_token FROM share_links WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'abc123xyz'
        conn.close()

    def test_should_enforce_unique_share_token(self):
        """Test that share_token must be unique."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Sermon 1', 'John 3:16'))
        sermon1_id = cursor.lastrowid

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Sermon 2', 'John 3:17'))
        sermon2_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO share_links (sermon_id, share_token)
            VALUES (?, ?)
        """, (sermon1_id, 'unique_token'))
        conn.commit()

        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO share_links (sermon_id, share_token)
                VALUES (?, ?)
            """, (sermon2_id, 'unique_token'))  # Same token - should fail
            conn.commit()

        conn.close()

    def test_should_store_password_hash_for_protected_link(self):
        """Test that password-protected links store hash."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        # Simulated bcrypt hash
        fake_hash = '$2b$12$fakehashvalue'

        cursor.execute("""
            INSERT INTO share_links (sermon_id, share_token, password_hash)
            VALUES (?, ?, ?)
        """, (sermon_id, 'protected_link', fake_hash))
        conn.commit()

        cursor.execute("SELECT password_hash FROM share_links WHERE share_token = ?",
                      ('protected_link',))
        row = cursor.fetchone()

        assert row[0] == fake_hash
        conn.close()

    def test_should_store_expiration_timestamp(self):
        """Test that expiration can be set for links."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO share_links (sermon_id, share_token, expires_at)
            VALUES (?, ?, datetime('now', '+7 days'))
        """, (sermon_id, 'expiring_link'))
        conn.commit()

        cursor.execute("SELECT expires_at FROM share_links WHERE share_token = ?",
                      ('expiring_link',))
        row = cursor.fetchone()

        assert row[0] is not None
        conn.close()


class TestReviewCommentsTable:
    """Test suite for review_comments table."""

    def test_should_create_review_comment_on_sermon(self):
        """Test creating a review comment."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO review_comments (sermon_id, reviewer_name, comment_text)
            VALUES (?, ?, ?)
        """, (sermon_id, 'Associate Pastor', 'Great opening hook!'))
        conn.commit()

        cursor.execute("SELECT reviewer_name, comment_text FROM review_comments WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'Associate Pastor'
        assert row[1] == 'Great opening hook!'
        conn.close()

    def test_should_store_highlight_positions(self):
        """Test that highlight positions are stored for inline comments."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO review_comments (sermon_id, reviewer_name, comment_text,
                                         highlight_start, highlight_end)
            VALUES (?, ?, ?, ?, ?)
        """, (sermon_id, 'Reviewer', 'Consider rewording this', 150, 200))
        conn.commit()

        cursor.execute("""
            SELECT highlight_start, highlight_end FROM review_comments WHERE sermon_id = ?
        """, (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 150
        assert row[1] == 200
        conn.close()

    def test_should_store_suggestion_for_replacement(self):
        """Test that suggestions for text replacement are stored."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO review_comments (sermon_id, reviewer_name, comment_text, suggestion)
            VALUES (?, ?, ?, ?)
        """, (sermon_id, 'Editor', 'This phrase could be clearer', 'Try saying it this way instead'))
        conn.commit()

        cursor.execute("SELECT suggestion FROM review_comments WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 'Try saying it this way instead'
        conn.close()

    def test_should_track_resolved_status(self):
        """Test that comments can be marked as resolved."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO review_comments (sermon_id, reviewer_name, comment_text, resolved)
            VALUES (?, ?, ?, ?)
        """, (sermon_id, 'Reviewer', 'Check this fact', False))
        conn.commit()

        # Initially not resolved
        cursor.execute("SELECT resolved FROM review_comments WHERE sermon_id = ?",
                      (sermon_id,))
        assert cursor.fetchone()[0] == 0 or cursor.fetchone() is False

        # Mark as resolved
        cursor.execute("UPDATE review_comments SET resolved = ? WHERE sermon_id = ?",
                      (True, sermon_id))
        conn.commit()

        cursor.execute("SELECT resolved FROM review_comments WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 1 or row[0] is True
        conn.close()

    def test_should_default_resolved_to_false(self):
        """Test that resolved defaults to FALSE."""
        from database import init_db

        conn = sqlite3.connect(':memory:')
        init_db(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO sermons (title, scripture) VALUES (?, ?)",
                      ('Test Sermon', 'John 3:16'))
        sermon_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO review_comments (sermon_id, reviewer_name, comment_text)
            VALUES (?, ?, ?)
        """, (sermon_id, 'Reviewer', 'A comment'))
        conn.commit()

        cursor.execute("SELECT resolved FROM review_comments WHERE sermon_id = ?",
                      (sermon_id,))
        row = cursor.fetchone()

        assert row[0] == 0 or row[0] is False
        conn.close()


class TestDatabaseHelperFunctions:
    """Test suite for database helper functions."""

    def test_should_get_connection_when_get_db_called(self):
        """Test that get_db returns a valid connection."""
        from database import get_db, init_db

        # Test with in-memory database path
        conn = get_db(':memory:')
        assert conn is not None

        # Should be able to execute queries
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

        conn.close()

    def test_should_close_connection_when_close_db_called(self):
        """Test that close_db properly closes the connection."""
        from database import get_db, close_db

        conn = get_db(':memory:')
        close_db(conn)

        # Connection should be closed - attempting to use it should fail
        with pytest.raises(Exception):
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
