"""SQLite database module for AutomatedPastor.

Provides database initialization, connection management, and schema creation
for all application tables.
"""
import sqlite3

# Module-level storage for in-memory database connections (for testing)
_memory_db_cache = {}


def get_db(db_path=None):
    """Get a database connection.

    Args:
        db_path: Path to SQLite database file, or ':memory:' for in-memory database.
                 If None, uses Flask's g and current_app.config['DATABASE'].

    Returns:
        sqlite3.Connection: Database connection with row factory set.
    """
    if db_path is None:
        # Use Flask's application context
        from flask import g, current_app
        if 'db' not in g:
            db_path = current_app.config.get('DATABASE', ':memory:')
            # For in-memory databases, use a cached connection so all requests share the same DB
            if db_path == ':memory:':
                app_id = id(current_app._get_current_object())
                if app_id not in _memory_db_cache:
                    conn = sqlite3.connect(':memory:', check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    _memory_db_cache[app_id] = conn
                g.db = _memory_db_cache[app_id]
            else:
                g.db = sqlite3.connect(db_path)
                g.db.row_factory = sqlite3.Row
        return g.db

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def clear_memory_db_cache():
    """Clear the in-memory database cache (for testing)."""
    global _memory_db_cache
    for conn in _memory_db_cache.values():
        try:
            conn.close()
        except Exception:
            pass
    _memory_db_cache = {}


def close_db(conn):
    """Close a database connection.

    Args:
        conn: sqlite3.Connection to close.
    """
    conn.close()


def init_db(conn):
    """Initialize the database with all required tables.

    Creates all 12 tables required for the application:
    - sermons
    - illustrations
    - scriptures_used
    - themes
    - custom_reviewers
    - sermon_reviewers
    - reference_materials
    - sermon_series
    - chat_sessions
    - chat_messages
    - share_links
    - review_comments

    Args:
        conn: sqlite3.Connection to initialize.
    """
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")

    cursor = conn.cursor()

    # Create sermon_series table first (referenced by sermons)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sermon_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            theme TEXT,
            planned_weeks INTEGER,
            narrative_arc TEXT,
            recurring_imagery TEXT,
            series_illustration TEXT,
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sermons table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            scripture TEXT NOT NULL,
            theme TEXT,
            main_point TEXT,
            liturgical_season TEXT,
            special_occasion TEXT,
            manuscript TEXT,
            outline TEXT,
            word_count INTEGER,
            estimated_minutes REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            preached_on DATE,
            research_data TEXT,
            review_feedback TEXT,
            series_id INTEGER REFERENCES sermon_series(id),
            series_week INTEGER,
            confirmed_preached BOOLEAN DEFAULT FALSE,
            post_sermon_notes TEXT,
            service_times TEXT
        )
    """)

    # Create illustrations table (cascade delete when sermon deleted)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS illustrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            type TEXT,
            content TEXT,
            source TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create scriptures_used table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scriptures_used (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            reference TEXT,
            translation TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create themes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            theme TEXT,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create custom_reviewers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_reviewers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            focus_area TEXT,
            style_notes TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create sermon_reviewers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sermon_reviewers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            reviewer_name TEXT,
            is_custom BOOLEAN DEFAULT FALSE,
            feedback TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create reference_materials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reference_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            type TEXT,
            title TEXT,
            content TEXT,
            file_path TEXT,
            url TEXT,
            usage_mode TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create chat_sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create chat_messages table (cascade delete when session deleted)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            sender TEXT,
            message TEXT,
            mentioned_panelists TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    """)

    # Create share_links table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS share_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            share_token TEXT UNIQUE,
            password_hash TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create review_comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            reviewer_name TEXT,
            comment_text TEXT,
            highlight_start INTEGER,
            highlight_end INTEGER,
            suggestion TEXT,
            resolved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
