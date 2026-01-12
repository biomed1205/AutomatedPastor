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
            identifier TEXT UNIQUE,
            focus_area TEXT,
            style_notes TEXT,
            prompt_template TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            material_type TEXT,
            type TEXT,
            title TEXT,
            content TEXT,
            file_path TEXT,
            filename TEXT,
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

    # Create panel_discussions table for The Green Room
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS panel_discussions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER,
            topic TEXT,
            mode TEXT DEFAULT 'discussion',
            status TEXT DEFAULT 'active',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create chat_messages table (supports both session and discussion)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            discussion_id INTEGER,
            sender TEXT,
            sender_type TEXT,
            message TEXT,
            content TEXT,
            reply_to_id INTEGER,
            mentioned_panelists TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (discussion_id) REFERENCES panel_discussions(id) ON DELETE CASCADE
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

    # Create practice_sessions table for practice timing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS practice_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            started_at TEXT,
            ended_at TEXT,
            paused_at TEXT,
            total_paused_seconds INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running',
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create timing_goals table for practice timing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timing_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL UNIQUE,
            target_minutes INTEGER DEFAULT 15,
            updated_at TEXT,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # Create section_timings table for practice timing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS section_timings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            section_name TEXT,
            section_index INTEGER,
            start_time_seconds INTEGER,
            end_time_seconds INTEGER,
            FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE
        )
    """)

    # Create series table for sermon series management
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            theme TEXT,
            start_date DATE,
            end_date DATE,
            status TEXT DEFAULT 'planning',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create series_sermons junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series_sermons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            series_id INTEGER NOT NULL,
            sermon_id INTEGER NOT NULL,
            order_in_series INTEGER,
            FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            UNIQUE(series_id, sermon_id)
        )
    """)

    # Create passages table for passage suggestions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT NOT NULL,
            testament TEXT,
            genre TEXT,
            themes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create passage_cache table for caching suggestions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS passage_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE NOT NULL,
            suggestions TEXT,
            expires_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create generation_log table for sermon generation tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            stage TEXT,
            agent TEXT,
            status TEXT,
            duration REAL,
            output TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE
        )
    """)

    # =========================================================================
    # Multi-AI Provider Tables (7 new tables)
    # =========================================================================

    # Create ai_providers table for managing multiple AI providers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            api_key_encrypted TEXT,
            default_model TEXT,
            is_enabled BOOLEAN DEFAULT TRUE,
            is_default BOOLEAN DEFAULT FALSE,
            color_primary TEXT,
            color_bg TEXT,
            config_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create content_sources table for tracking which AI generated what content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            content_id INTEGER NOT NULL,
            provider_id INTEGER NOT NULL,
            model_id TEXT,
            generation_params TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (provider_id) REFERENCES ai_providers(id) ON DELETE CASCADE
        )
    """)

    # Create research_items table for storing research from AI providers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            item_type TEXT,
            title TEXT,
            content TEXT,
            source_citation TEXT,
            source_url TEXT,
            relevance_score REAL,
            relevance_reasoning TEXT,
            provider_id INTEGER,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            FOREIGN KEY (provider_id) REFERENCES ai_providers(id) ON DELETE SET NULL
        )
    """)

    # Create content_versions table for version history of content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            parent_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT,
            author TEXT,
            change_summary TEXT,
            source_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES content_sources(id) ON DELETE SET NULL
        )
    """)

    # Create generation_outputs table for storing multiple AI outputs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generation_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sermon_id INTEGER NOT NULL,
            output_type TEXT NOT NULL,
            output_index INTEGER DEFAULT 0,
            content TEXT,
            word_count INTEGER,
            source_id INTEGER,
            is_selected BOOLEAN DEFAULT FALSE,
            user_rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sermon_id) REFERENCES sermons(id) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES content_sources(id) ON DELETE SET NULL
        )
    """)

    # Create content_comments table for inline commenting on content
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            content_id INTEGER NOT NULL,
            parent_comment_id INTEGER,
            author TEXT,
            comment_text TEXT,
            highlight_start INTEGER,
            highlight_end INTEGER,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_comment_id) REFERENCES content_comments(id) ON DELETE CASCADE
        )
    """)

    # Create revision_requests table for tracking revision requests
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_type TEXT NOT NULL,
            content_id INTEGER NOT NULL,
            comment_id INTEGER,
            instructions TEXT,
            target_providers TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (comment_id) REFERENCES content_comments(id) ON DELETE SET NULL
        )
    """)

    # Seed default AI providers
    _seed_default_providers(cursor)

    conn.commit()


def _seed_default_providers(cursor):
    """Seed the default AI providers if they don't exist.

    Args:
        cursor: sqlite3.Cursor to execute queries.
    """
    # Check if providers already exist
    cursor.execute("SELECT COUNT(*) FROM ai_providers")
    if cursor.fetchone()[0] > 0:
        return  # Already seeded

    default_providers = [
        {
            'provider_name': 'claude_cli',
            'display_name': 'Claude CLI',
            'default_model': 'claude-sonnet-4-20250514',
            'is_enabled': True,
            'is_default': True,
            'color_primary': '#D97706',
            'color_bg': '#FEF3C7',
            'config_json': '{"type": "cli", "command": "claude"}'
        },
        {
            'provider_name': 'claude_api',
            'display_name': 'Claude API',
            'default_model': 'claude-sonnet-4-20250514',
            'is_enabled': False,
            'is_default': False,
            'color_primary': '#D97706',
            'color_bg': '#FEF3C7',
            'config_json': '{"type": "api", "base_url": "https://api.anthropic.com"}'
        },
        {
            'provider_name': 'openai',
            'display_name': 'OpenAI',
            'default_model': 'gpt-4o',
            'is_enabled': False,
            'is_default': False,
            'color_primary': '#10B981',
            'color_bg': '#D1FAE5',
            'config_json': '{"type": "api", "base_url": "https://api.openai.com"}'
        },
        {
            'provider_name': 'gemini',
            'display_name': 'Google Gemini',
            'default_model': 'gemini-pro',
            'is_enabled': False,
            'is_default': False,
            'color_primary': '#3B82F6',
            'color_bg': '#DBEAFE',
            'config_json': '{"type": "api", "base_url": "https://generativelanguage.googleapis.com"}'
        }
    ]

    for provider in default_providers:
        cursor.execute("""
            INSERT INTO ai_providers (
                provider_name, display_name, default_model, is_enabled,
                is_default, color_primary, color_bg, config_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            provider['provider_name'],
            provider['display_name'],
            provider['default_model'],
            provider['is_enabled'],
            provider['is_default'],
            provider['color_primary'],
            provider['color_bg'],
            provider['config_json']
        ))
