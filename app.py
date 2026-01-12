"""Flask application for AutomatedPastor sermon generation service."""
import os

from flask import Flask, jsonify, request, redirect, url_for, session, render_template_string, render_template, g
from flask_socketio import SocketIO
from database import get_db, init_db, close_db as db_close


DEFAULT_PORT = 8787

# Module-level SocketIO instance (initialized in create_app)
socketio = None

# Base HTML template
BASE_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}AutomatedPastor{% endblock %}</title>
    <style>
        body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { margin-right: 15px; }
        .error { color: red; }
        form label { display: block; margin-top: 10px; }
        form input, form textarea { width: 100%; padding: 8px; margin-top: 5px; }
        form textarea { height: 200px; }
        form button { margin-top: 15px; padding: 10px 20px; }
        .sermon-list { list-style: none; padding: 0; }
        .sermon-list li { padding: 10px; border-bottom: 1px solid #ccc; }
        .empty-state { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <div class="nav">
        <a href="/">Dashboard</a>
        <a href="/sermons">Sermons</a>
        <a href="/sermon/new">New Sermon</a>
    </div>
    {% block content %}{% endblock %}
</body>
</html>'''


def create_app(config=None, testing=False):
    """Create and configure the Flask application.

    Args:
        config: Optional dictionary of configuration values to override defaults.
        testing: If True, use testing configuration.

    Returns:
        Configured Flask application instance.
    """
    # Reset auth state when creating a new app (important for testing)
    from auth import reset_auth_state
    reset_auth_state()

    # Get project root directory for template and static paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    template_folder = os.path.join(project_root, 'templates')
    static_folder = os.path.join(project_root, 'static')

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    if testing:
        app.config['TESTING'] = True
        app.config['DATABASE'] = ':memory:'
        # Initialize database tables for testing
        with app.app_context():
            conn = get_db()
            init_db(conn)
            # Add test data
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sermons (id, title, scripture, manuscript) VALUES (?, ?, ?, ?)",
                (1, 'Test Sermon', 'John 3:16', 'Test manuscript content')
            )
            # Add test discussion for chat UI tests
            cursor.execute(
                "INSERT INTO panel_discussions (id, sermon_id, status) VALUES (?, ?, ?)",
                (1, 1, 'active')
            )
            conn.commit()

    # Set secret key for sessions
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['DATABASE'] = ':memory:'

    # Apply custom configuration if provided
    if config:
        app.config.update(config)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = g.pop('db', None)
        # Don't close in-memory connections - they're cached and shared
        if db is not None and app.config.get('DATABASE') != ':memory:':
            db_close(db)

    @app.route('/')
    def home():
        """Dashboard/home page showing recent sermons."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, scripture, theme, word_count, created_at FROM sermons ORDER BY created_at DESC LIMIT 5")
        recent_sermons = cursor.fetchall()

        # Get total sermon count
        cursor.execute("SELECT COUNT(*) as count FROM sermons")
        total_sermons = cursor.fetchone()['count']

        # Get this month's sermon count
        cursor.execute("SELECT COUNT(*) as count FROM sermons WHERE created_at >= date('now', 'start of month')")
        this_month = cursor.fetchone()['count']

        # Get average word count
        cursor.execute("SELECT AVG(word_count) as avg FROM sermons WHERE word_count IS NOT NULL")
        avg_result = cursor.fetchone()
        avg_word_count = int(avg_result['avg']) if avg_result and avg_result['avg'] else 0

        # Build stats object for template
        stats = {
            'total_sermons': total_sermons,
            'this_month': this_month,
            'avg_word_count': avg_word_count,
            'practice_hours': 0
        }

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'dashboard.html')):
            return render_template('pages/dashboard.html',
                recent_sermons=recent_sermons,
                stats=stats,
                total_sermons=total_sermons), 200

        # Fallback to inline template
        content = '''
        {% extends base %}
        {% block title %}Dashboard - AutomatedPastor{% endblock %}
        {% block content %}
        <h1>Dashboard</h1>
        <h2>Recent Sermons</h2>
        {% if recent_sermons %}
        <ul class="sermon-list">
            {% for sermon in recent_sermons %}
            <li><a href="/sermon/{{ sermon.id }}">{{ sermon.title }}</a> - {{ sermon.scripture }}</li>
            {% endfor %}
        </ul>
        {% else %}
        <p class="empty-state">No sermons yet. <a href="/sermon/new">Create your first sermon</a></p>
        {% endif %}
        {% endblock %}
        '''
        return render_template_string(BASE_TEMPLATE.replace('{% block content %}{% endblock %}',
            content.replace('{% extends base %}', '').replace('{% block title %}Dashboard - AutomatedPastor{% endblock %}', '')),
            recent_sermons=recent_sermons), 200

    @app.route('/sermons')
    def sermons_list():
        """List all sermons."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, scripture, theme, word_count, estimated_minutes, confirmed_preached, created_at FROM sermons ORDER BY created_at DESC")
        sermons = cursor.fetchall()

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'sermons', 'list.html')):
            return render_template('pages/sermons/list.html', sermons=sermons), 200

        # Fallback to inline template
        html = '''<!DOCTYPE html>
<html>
<head><title>Sermons - AutomatedPastor</title>
<style>
body { font-family: sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
.sermon-list { list-style: none; padding: 0; }
.sermon-list li { padding: 10px; border-bottom: 1px solid #ccc; }
.empty-state { color: #666; font-style: italic; }
</style>
</head>
<body>
<div class="nav">
    <a href="/">Dashboard</a>
    <a href="/sermons">Sermons</a>
    <a href="/sermon/new">New Sermon</a>
</div>
<h1>All Sermons</h1>
{% if sermons %}
<ul class="sermon-list">
    {% for sermon in sermons %}
    <li>
        <a href="/sermon/{{ sermon.id }}">{{ sermon.title }}</a> - {{ sermon.scripture }}
        {% if sermon.theme %}<br><small>Theme: {{ sermon.theme }}</small>{% endif %}
    </li>
    {% endfor %}
</ul>
{% else %}
<p class="empty-state">No sermons yet. <a href="/sermon/new">Create your first sermon</a></p>
{% endif %}
</body>
</html>'''
        return render_template_string(html, sermons=sermons), 200

    @app.route('/sermon/new')
    @app.route('/sermon/create')
    def sermon_new():
        """Create sermon form."""
        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'sermons', 'create.html')):
            return render_template('pages/sermons/create.html'), 200

        # Fallback to inline template
        html = '''<!DOCTYPE html>
<html>
<head><title>New Sermon - AutomatedPastor</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
form label { display: block; margin-top: 10px; font-weight: bold; }
form input, form textarea { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
form textarea { height: 100px; }
form button { margin-top: 15px; padding: 10px 20px; }
</style>
</head>
<body>
<div class="nav">
    <a href="/">Dashboard</a>
    <a href="/sermons">Sermons</a>
    <a href="/sermon/new">New Sermon</a>
</div>
<h1>Create New Sermon</h1>
<form method="post" action="/sermon">
    <label for="title">Title (required)</label>
    <input type="text" id="title" name="title" required>

    <label for="scripture">Scripture (required)</label>
    <input type="text" id="scripture" name="scripture" required>

    <label for="theme">Theme</label>
    <input type="text" id="theme" name="theme">

    <label for="main_point">Main Point</label>
    <input type="text" id="main_point" name="main_point">

    <button type="submit">Create Sermon</button>
</form>
</body>
</html>'''
        return html, 200

    @app.route('/sermon', methods=['POST'])
    def sermon_create():
        """Create a new sermon."""

        title = request.form.get('title', '').strip()
        scripture = request.form.get('scripture', '').strip()
        theme = request.form.get('theme', '').strip() or None
        main_point = request.form.get('main_point', '').strip() or None

        if not title:
            return '<html><body><p class="error">Error: Title is required</p></body></html>', 400
        if not scripture:
            return '<html><body><p class="error">Error: Scripture is required</p></body></html>', 400

        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sermons (title, scripture, theme, main_point) VALUES (?, ?, ?, ?)",
            (title, scripture, theme, main_point)
        )
        conn.commit()
        sermon_id = cursor.lastrowid

        return redirect(url_for('sermon_view', sermon_id=sermon_id))

    @app.route('/sermon/<int:sermon_id>')
    def sermon_view(sermon_id):
        """View a single sermon."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return not_found_html(None)

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'sermons', 'detail.html')):
            # Get references for the sermon
            from reference_materials import list_references
            references = list_references(conn, sermon_id=sermon_id)

            # Get agent logs if available
            agent_logs = []

            return render_template('pages/sermons/detail.html',
                sermon=sermon,
                references=references,
                agent_logs=agent_logs), 200

        # Fallback to inline template
        html = '''<!DOCTYPE html>
<html>
<head><title>{{ sermon.title }} - AutomatedPastor</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
.actions { margin-top: 20px; }
.actions a { margin-right: 10px; }
.manuscript { background: #f5f5f5; padding: 15px; margin-top: 20px; white-space: pre-wrap; }
</style>
</head>
<body>
<div class="nav">
    <a href="/">Dashboard</a>
    <a href="/sermons">Sermons</a>
    <a href="/sermon/new">New Sermon</a>
</div>
<h1>{{ sermon.title }}</h1>
<p><strong>Scripture:</strong> {{ sermon.scripture }}</p>
{% if sermon.theme %}<p><strong>Theme:</strong> {{ sermon.theme }}</p>{% endif %}
{% if sermon.main_point %}<p><strong>Main Point:</strong> {{ sermon.main_point }}</p>{% endif %}
{% if sermon.manuscript %}
<h2>Manuscript</h2>
<div class="manuscript">{{ sermon.manuscript }}</div>
{% endif %}
<div class="actions">
    <a href="/sermon/{{ sermon.id }}/edit">Edit</a>
</div>
</body>
</html>'''
        return render_template_string(html, sermon=sermon), 200

    @app.route('/sermon/<int:sermon_id>/edit')
    def sermon_edit(sermon_id):
        """Edit sermon form."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return not_found_html(None)

        html = '''<!DOCTYPE html>
<html>
<head><title>Edit {{ sermon.title }} - AutomatedPastor</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
.nav { margin-bottom: 20px; }
.nav a { margin-right: 15px; }
form label { display: block; margin-top: 10px; font-weight: bold; }
form input, form textarea { width: 100%; padding: 8px; margin-top: 5px; box-sizing: border-box; }
form textarea { height: 100px; }
form button { margin-top: 15px; padding: 10px 20px; }
</style>
</head>
<body>
<div class="nav">
    <a href="/">Dashboard</a>
    <a href="/sermons">Sermons</a>
    <a href="/sermon/new">New Sermon</a>
</div>
<h1>Edit Sermon</h1>
<form method="post" action="/sermon/{{ sermon.id }}">
    <input type="hidden" name="_method" value="PUT">
    <label for="title">Title (required)</label>
    <input type="text" id="title" name="title" value="{{ sermon.title }}" required>

    <label for="scripture">Scripture (required)</label>
    <input type="text" id="scripture" name="scripture" value="{{ sermon.scripture }}" required>

    <label for="theme">Theme</label>
    <input type="text" id="theme" name="theme" value="{{ sermon.theme or '' }}">

    <label for="main_point">Main Point</label>
    <input type="text" id="main_point" name="main_point" value="{{ sermon.main_point or '' }}">

    <button type="submit">Update Sermon</button>
</form>
</body>
</html>'''
        return render_template_string(html, sermon=sermon), 200

    @app.route('/sermon/<int:sermon_id>', methods=['PUT', 'POST'])
    def sermon_update(sermon_id):
        """Update a sermon."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()

        # Check if sermon exists
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if not cursor.fetchone():
            if request.method == 'PUT':
                return jsonify({'error': 'Not found'}), 404
            return not_found_html(None)

        title = request.form.get('title', '').strip()
        scripture = request.form.get('scripture', '').strip()
        theme = request.form.get('theme', '').strip() or None
        main_point = request.form.get('main_point', '').strip() or None

        cursor.execute(
            "UPDATE sermons SET title = ?, scripture = ?, theme = ?, main_point = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (title, scripture, theme, main_point, sermon_id)
        )
        conn.commit()

        return redirect(url_for('sermon_view', sermon_id=sermon_id))

    @app.route('/sermon/<int:sermon_id>', methods=['DELETE'])
    def sermon_delete(sermon_id):
        """Delete a sermon."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()

        # Check if sermon exists
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Not found'}), 404

        # Delete sermon (cascade will handle related records)
        cursor.execute("DELETE FROM sermons WHERE id = ?", (sermon_id,))
        conn.commit()

        return '', 204

    @app.route('/sermon/<int:sermon_id>/export/word')
    def sermon_export_word(sermon_id):
        """Export sermon to Word document."""
        from export import export_to_word
        from flask import Response

        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return jsonify({'error': 'Not found'}), 404

        # Convert Row to dict
        sermon_dict = {
            'title': sermon['title'],
            'scripture': sermon['scripture'],
            'manuscript': sermon['manuscript'],
            'outline': sermon['outline']
        }

        doc_bytes = export_to_word(sermon_dict)

        # Create safe filename
        safe_title = ''.join(c for c in sermon['title'] if c.isalnum() or c in ' -_').strip()
        filename = f"{safe_title}.docx"

        return Response(
            doc_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    @app.route('/sermon/<int:sermon_id>/export/pdf')
    def sermon_export_pdf(sermon_id):
        """Export sermon to PDF document."""
        from export import export_to_pdf
        from flask import Response

        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return jsonify({'error': 'Not found'}), 404

        # Convert Row to dict
        sermon_dict = {
            'title': sermon['title'],
            'scripture': sermon['scripture'],
            'manuscript': sermon['manuscript'],
            'outline': sermon['outline']
        }

        pdf_bytes = export_to_pdf(sermon_dict)

        # Create safe filename
        safe_title = ''.join(c for c in sermon['title'] if c.isalnum() or c in ' -_').strip()
        filename = f"{safe_title}.pdf"

        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    @app.route('/api/sermons')
    def api_sermons():
        """API endpoint to list all sermons as JSON."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, scripture, theme, main_point, created_at FROM sermons ORDER BY created_at DESC")
        sermons = cursor.fetchall()

        result = []
        for sermon in sermons:
            result.append({
                'id': sermon['id'],
                'title': sermon['title'],
                'scripture': sermon['scripture'],
                'theme': sermon['theme'],
                'main_point': sermon['main_point'],
                'created_at': sermon['created_at']
            })

        return jsonify(result), 200

    @app.route('/api/sermon/<int:sermon_id>')
    def api_sermon(sermon_id):
        """API endpoint to get a single sermon as JSON."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return jsonify({'error': 'Not found'}), 404

        return jsonify({
            'id': sermon['id'],
            'title': sermon['title'],
            'scripture': sermon['scripture'],
            'theme': sermon['theme'],
            'main_point': sermon['main_point'],
            'manuscript': sermon['manuscript'],
            'created_at': sermon['created_at']
        }), 200

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'healthy'}), 200

    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        """Login page and form handler."""
        from auth import login, is_authenticated

        if request.method == 'POST':
            password = request.form.get('password', '')
            if login(password):
                next_url = request.args.get('next', '/')
                return redirect(next_url)
            else:
                return '<html><body><form method="post"><input type="password" name="password"><button>Login</button></form><p>Invalid password</p></body></html>', 200

        return '<html><body><form method="post"><input type="password" name="password"><button>Login</button></form></body></html>', 200

    @app.route('/logout')
    def logout_page():
        """Logout and redirect to login."""
        from auth import logout

        logout()
        return redirect(url_for('login_page'))

    @app.route('/protected')
    def protected():
        """Protected route requiring authentication."""
        from auth import is_authenticated

        if not is_authenticated():
            return redirect(url_for('login_page', next=request.path))

        return jsonify({'message': 'Welcome to protected area'}), 200

    @app.route('/protected/resource')
    def protected_resource():
        """Protected resource route requiring authentication."""
        from auth import is_authenticated

        if not is_authenticated():
            return redirect(url_for('login_page', next=request.path))

        return jsonify({'message': 'Protected resource'}), 200

    def not_found_html(error):
        """Return HTML 404 page."""
        html = '''<!DOCTYPE html>
<html>
<head><title>404 Not Found - AutomatedPastor</title>
<style>
body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }
h1 { color: #666; }
</style>
</head>
<body>
<h1>404 - Not Found</h1>
<p>The page you requested could not be found.</p>
<a href="/">Return to Dashboard</a>
</body>
</html>'''
        return html, 404

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors with appropriate response type."""
        # Check Accept header for content negotiation
        accept = request.headers.get('Accept', '')
        # Return HTML only if explicitly requested, otherwise JSON
        if 'text/html' in accept and 'application/json' not in accept:
            return not_found_html(error)
        return jsonify({'error': 'Not found'}), 404

    @app.route('/sermon/<int:sermon_id>/references', methods=['GET'])
    def list_sermon_references(sermon_id):
        """List all references for a sermon."""
        from reference_materials import list_references

        conn = get_db()
        init_db(conn)

        # Check if sermon exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Sermon not found'}), 404

        references = list_references(conn, sermon_id=sermon_id)
        return jsonify(references), 200

    @app.route('/sermon/<int:sermon_id>/references', methods=['POST'])
    def create_sermon_reference(sermon_id):
        """Create a new reference for a sermon."""
        from reference_materials import (
            create_text_reference, create_url_reference,
            InvalidReferenceError, SermonNotFoundError
        )

        conn = get_db()
        init_db(conn)

        data = request.get_json() or {}
        ref_type = data.get('type', '')
        content = data.get('content', '')
        url = data.get('url', '')

        try:
            if ref_type == 'text':
                ref_id = create_text_reference(conn, sermon_id=sermon_id, content=content)
            elif ref_type == 'url':
                ref_id = create_url_reference(conn, sermon_id=sermon_id, url=url)
            else:
                return jsonify({'error': 'Invalid reference type'}), 400

            return jsonify({'id': ref_id}), 201

        except SermonNotFoundError:
            return jsonify({'error': 'Sermon not found'}), 404
        except InvalidReferenceError as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/sermon/<int:sermon_id>/references/<int:ref_id>', methods=['DELETE'])
    def delete_sermon_reference(sermon_id, ref_id):
        """Delete a reference from a sermon."""
        from reference_materials import delete_reference

        conn = get_db()
        init_db(conn)

        # Check if sermon exists
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if cursor.fetchone() is None:
            return jsonify({'error': 'Sermon not found'}), 404

        deleted = delete_reference(conn, reference_id=ref_id)
        if deleted:
            return '', 204
        else:
            return jsonify({'error': 'Reference not found'}), 404

    @app.route('/sermon/<int:sermon_id>/panel-feedback', methods=['GET'])
    def get_panel_feedback(sermon_id):
        """Get panel feedback for a sermon."""
        from panel_feedback import FeedbackPanel, get_stored_feedback
        from cli_bridge import CLIBridge

        conn = get_db()
        init_db(conn)

        # Check if sermon exists
        cursor = conn.cursor()
        cursor.execute("SELECT id, manuscript FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()
        if sermon is None:
            return jsonify({'error': 'Sermon not found'}), 404

        # Try to get stored feedback first
        feedbacks = []
        for reviewer_type in ['theological', 'pastoral', 'structural', 'engagement',
                              'illustration', 'scripture', 'language']:
            stored = get_stored_feedback(conn, sermon_id, reviewer_type)
            if stored:
                feedbacks.append(stored)

        # If no stored feedback, generate it
        if not feedbacks and sermon['manuscript']:
            bridge = CLIBridge(command='echo')
            panel = FeedbackPanel(bridge, db_conn=conn)
            feedbacks = panel.get_all_feedback(sermon['manuscript'], sermon_id=sermon_id)

        return jsonify({
            'sermon_id': sermon_id,
            'feedbacks': feedbacks,
            'count': len(feedbacks)
        }), 200

    @app.route('/sermon/<int:sermon_id>/panel-feedback', methods=['POST'])
    def trigger_panel_feedback(sermon_id):
        """Trigger panel review for a sermon."""
        from panel_feedback import FeedbackPanel
        from cli_bridge import CLIBridge

        conn = get_db()
        init_db(conn)

        # Check if sermon exists
        cursor = conn.cursor()
        cursor.execute("SELECT id, manuscript FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()
        if sermon is None:
            return jsonify({'error': 'Sermon not found'}), 404

        # Generate feedback
        bridge = CLIBridge(command='echo')
        panel = FeedbackPanel(bridge, db_conn=conn)

        manuscript = sermon['manuscript'] or 'No manuscript available'
        feedbacks = panel.get_all_feedback(manuscript, sermon_id=sermon_id)

        return jsonify({
            'sermon_id': sermon_id,
            'feedbacks': feedbacks,
            'count': len(feedbacks),
            'status': 'completed'
        }), 200

    # Feedback display routes
    @app.route('/api/sermon/<sermon_id>/feedback')
    def api_get_sermon_feedback(sermon_id):
        """API endpoint for sermon feedback."""
        from feedback_display import (get_feedback_for_sermon, InvalidSermonIdError,
                                      SermonNotFoundError, DatabaseError)

        try:
            sid = int(sermon_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid sermon ID'}), 400

        conn = get_db()
        try:
            # Check if sermon exists
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM sermons WHERE id = ?", (sid,))
            if not cursor.fetchone():
                return jsonify({'error': 'Sermon not found'}), 404

            feedback = get_feedback_for_sermon(conn, sid)
            return jsonify({'feedback': feedback, 'count': len(feedback)}), 200

        except (InvalidSermonIdError, SermonNotFoundError):
            return jsonify({'error': 'Invalid sermon ID'}), 404
        except DatabaseError as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/sermon/<int:sermon_id>/feedback')
    def view_sermon_feedback(sermon_id):
        """Display feedback page for a sermon."""
        from feedback_display import prepare_template_context

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sermons WHERE id = ?", (sermon_id,))
        if not cursor.fetchone():
            return "Sermon not found", 404

        context = prepare_template_context(conn, sermon_id)
        return f"""<!DOCTYPE html>
<html>
<head><title>Feedback for {context.get('sermon_title', 'Sermon')}</title></head>
<body>
<h1>Feedback for {context.get('sermon_title', 'Sermon')}</h1>
<p>Total reviewers: {context.get('reviewer_count', 0)}</p>
<ul>
{''.join(f"<li>{fb.get('reviewer')}: {fb.get('comment', '')}</li>" for fb in context.get('feedback_list', []))}
</ul>
</body>
</html>"""

    # Custom reviewer routes
    @app.route('/custom-reviewers')
    def list_custom_reviewers():
        """List all custom reviewers page."""
        from custom_reviewers import list_custom_reviewers as get_reviewers
        conn = get_db()
        try:
            reviewers = get_reviewers(conn)
            reviewers_list = [r.to_dict() for r in reviewers]
        except Exception:
            reviewers_list = []

        return f"""<!DOCTYPE html>
<html>
<head><title>Custom Reviewers</title></head>
<body>
<h1>Custom Reviewers</h1>
<a href="/custom-reviewers/new">Create New Reviewer</a>
<ul>
{''.join(f"<li>{r['name']}: {r['focus_area']}</li>" for r in reviewers_list)}
</ul>
</body>
</html>"""

    @app.route('/custom-reviewers/new')
    def new_custom_reviewer():
        """Create new custom reviewer page."""
        return """<!DOCTYPE html>
<html>
<head><title>Create Custom Reviewer</title></head>
<body>
<h1>Create Custom Reviewer</h1>
<form method="post" action="/api/custom-reviewers">
<label>Name: <input name="name" required></label><br>
<label>Focus Area: <input name="focus_area" required></label><br>
<button type="submit">Create</button>
</form>
</body>
</html>"""

    @app.route('/api/custom-reviewers', methods=['POST'])
    def api_create_custom_reviewer():
        """API endpoint for creating custom reviewer."""
        from custom_reviewers import create_custom_reviewer, ValidationError

        conn = get_db()
        data = request.get_json() or {}

        name = data.get('name', '')
        focus_area = data.get('focus_area', '')

        if not name or not focus_area:
            return jsonify({'error': 'Name and focus_area are required'}), 400

        try:
            reviewer = create_custom_reviewer(
                conn, name=name, focus_area=focus_area,
                identifier=data.get('identifier'),
                prompt_template=data.get('prompt_template'),
                created_by=data.get('created_by')
            )
            return jsonify({'id': reviewer.id, 'identifier': reviewer.identifier, **reviewer.to_dict()}), 201
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/custom-reviewers/<int:reviewer_id>', methods=['PUT'])
    def api_update_custom_reviewer(reviewer_id):
        """API endpoint for updating custom reviewer."""
        from custom_reviewers import update_custom_reviewer, ReviewerNotFoundError

        conn = get_db()
        data = request.get_json() or {}

        try:
            reviewer = update_custom_reviewer(conn, reviewer_id, **data)
            return jsonify(reviewer.to_dict()), 200
        except ReviewerNotFoundError:
            return jsonify({'error': 'Reviewer not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/custom-reviewers/<int:reviewer_id>', methods=['DELETE'])
    def api_delete_custom_reviewer(reviewer_id):
        """API endpoint for deleting custom reviewer."""
        from custom_reviewers import delete_custom_reviewer, ReviewerNotFoundError

        conn = get_db()
        try:
            delete_custom_reviewer(conn, reviewer_id=reviewer_id)
            return jsonify({'success': True}), 200
        except ReviewerNotFoundError:
            return jsonify({'error': 'Reviewer not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    # Panel chat routes
    @app.route('/api/discussion/start', methods=['POST'])
    def api_start_discussion():
        """API endpoint for starting a panel discussion."""
        from panel_chat import start_discussion, InsufficientParticipantsError
        from cli_bridge import CLIBridge

        conn = get_db()
        init_db(conn)
        data = request.get_json() or {}

        sermon_id = data.get('sermon_id')
        participants = data.get('participants', [])
        mode = data.get('mode', 'discussion')

        if not sermon_id:
            return jsonify({'error': 'sermon_id required'}), 400

        try:
            bridge = CLIBridge(command='echo')
            discussion = start_discussion(
                conn, bridge,
                sermon_id=sermon_id,
                participants=participants,
                mode=mode
            )
            return jsonify(discussion.to_dict()), 201
        except InsufficientParticipantsError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/discussion/<int:discussion_id>/messages')
    def api_get_discussion_messages(discussion_id):
        """API endpoint for getting discussion messages."""
        from panel_chat import get_message_history, get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        messages = get_message_history(conn, discussion_id)
        return jsonify({'messages': messages, 'count': len(messages)}), 200

    @app.route('/api/discussion/<int:discussion_id>/message', methods=['POST'])
    def api_post_discussion_message(discussion_id):
        """API endpoint for posting a message to a discussion."""
        from panel_chat import post_user_message, get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        data = request.get_json() or {}
        content = data.get('content', '')

        message = post_user_message(conn, discussion_id, content)
        return jsonify(message.to_dict()), 201

    @app.route('/api/discussion/<int:discussion_id>/end', methods=['POST'])
    def api_end_discussion(discussion_id):
        """API endpoint for ending a discussion."""
        from panel_chat import end_discussion, get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        ended = end_discussion(conn, discussion_id)
        return jsonify(ended.to_dict()), 200

    @app.route('/api/discussion/<int:discussion_id>/stream')
    def api_discussion_stream(discussion_id):
        """SSE endpoint for real-time discussion updates."""
        from panel_chat import get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        def generate():
            yield 'data: {"event": "connected"}\n\n'

        return app.response_class(generate(), mimetype='text/event-stream')

    # Chat UI routes
    @app.route('/chat/<int:discussion_id>')
    def chat_page(discussion_id):
        """Chat page for a discussion."""
        from chat_ui import prepare_chat_context
        from panel_chat import get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return "Discussion not found", 404

        context = prepare_chat_context(conn, discussion_id)

        # Get the sermon for this discussion
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (discussion.sermon_id,))
        sermon = cursor.fetchone()

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'chat', 'green_room.html')):
            return render_template('pages/chat/green_room.html',
                discussion=discussion,
                sermon=sermon,
                messages=context.get('messages', [])), 200

        # Fallback to inline template
        html_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>The Green Room - Discussion {discussion_id}</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .messages {{ height: 400px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }}
        .message {{ margin: 10px 0; padding: 10px; border-radius: 5px; }}
        .message.user {{ background: #e3f2fd; margin-left: 50px; }}
        .message.reviewer {{ background: #f5f5f5; margin-right: 50px; }}
        .sender {{ font-weight: bold; }}
        .time {{ color: #666; font-size: 0.8em; }}
        .input-area {{ display: flex; }}
        .input-area input {{ flex: 1; padding: 10px; }}
        .input-area button {{ padding: 10px 20px; }}
    </style>
</head>
<body>
    <h1>The Green Room</h1>
    <p>Status: {context.get('status', 'unknown')}</p>
    <div class="messages" id="messages">
        {''.join(f'<div class="message {m.get("sender_type", "reviewer")}"><span class="sender">{m.get("sender", "")}</span>: {m.get("content", "")}</div>' for m in context.get('messages', []))}
    </div>
    <div class="input-area">
        <input type="text" id="message" placeholder="Type your message...">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        const socket = io();
        socket.emit('join', {{discussion_id: {discussion_id}}});
        socket.on('new_message', function(msg) {{
            const div = document.createElement('div');
            div.className = 'message ' + msg.sender_type;
            div.innerHTML = '<span class="sender">' + msg.sender + '</span>: ' + msg.content;
            document.getElementById('messages').appendChild(div);
        }});
        function sendMessage() {{
            const input = document.getElementById('message');
            fetch('/chat/{discussion_id}/message', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{content: input.value}})
            }});
            input.value = '';
        }}
    </script>
</body>
</html>'''
        return html_content, 200, {'Content-Type': 'text/html'}

    @app.route('/chat/<int:discussion_id>/message', methods=['POST'])
    def chat_post_message(discussion_id):
        """Post a message to a chat discussion."""
        from panel_chat import get_discussion_by_id, post_user_message

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        data = request.get_json() or {}
        content = data.get('content', '')

        if not content or not content.strip():
            return jsonify({'error': 'Message cannot be empty'}), 400

        message = post_user_message(conn, discussion_id, content)
        return jsonify(message.to_dict()), 201

    @app.route('/sermon/<int:sermon_id>/start-chat', methods=['POST'])
    def sermon_start_chat(sermon_id):
        """Start a new chat discussion for a sermon."""
        from panel_chat import start_discussion
        from cli_bridge import CLIBridge

        conn = get_db()
        init_db(conn)

        participants = request.form.getlist('participants') or ['theological', 'structural']

        bridge = CLIBridge(command='echo')
        discussion = start_discussion(
            conn, bridge,
            sermon_id=sermon_id,
            participants=participants
        )

        return redirect(url_for('chat_page', discussion_id=discussion.id))

    @app.route('/api/chat/<int:discussion_id>/messages')
    def api_chat_messages(discussion_id):
        """API endpoint for getting chat messages."""
        from chat_ui import get_message_history
        from panel_chat import get_discussion_by_id

        conn = get_db()
        init_db(conn)

        discussion = get_discussion_by_id(conn, discussion_id)
        if not discussion:
            return jsonify({'error': 'Discussion not found'}), 404

        messages = get_message_history(conn, discussion_id)
        return jsonify({'messages': messages, 'count': len(messages)}), 200

    # ========================================
    # BRAINSTORMING / GREEN ROOM ROUTES
    # ========================================

    @app.route('/green-room')
    def green_room_landing():
        """Landing page for The Green Room - start a brainstorming session."""
        # Get available reviewers for selection
        reviewers = [
            {'id': 'theological', 'name': 'Theological Scholar', 'description': 'Wesleyan theological integrity'},
            {'id': 'pastoral', 'name': 'Pastoral Mentor', 'description': 'Pastoral sensitivity & sustainability'},
            {'id': 'structural', 'name': 'Homiletics Professor', 'description': 'Sermon organization & flow'},
            {'id': 'engagement', 'name': 'Congregation Member', 'description': 'Layperson relevance & connection'},
            {'id': 'illustration', 'name': 'Visitor Perspective', 'description': 'Illustration quality & accessibility'},
            {'id': 'scripture', 'name': 'Elder Voice', 'description': 'Scripture handling & interpretation'},
            {'id': 'language', 'name': 'Youth Leader', 'description': 'Language clarity & accessibility'},
        ]

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'chat', 'green_room_start.html')):
            return render_template('pages/chat/green_room_start.html', reviewers=reviewers)

        # Fallback to inline template
        html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>The Green Room - Brainstorming</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="max-w-2xl mx-auto p-6" x-data="{
        topic: '',
        selectedReviewers: ['theological', 'pastoral'],
        reviewers: ''' + str(reviewers).replace("'", '"') + ''',
        starting: false,
        startSession() {
            if (this.selectedReviewers.length < 2) {
                alert('Please select at least 2 collaborators');
                return;
            }
            this.starting = true;
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/brainstorm/start';

            const topicInput = document.createElement('input');
            topicInput.type = 'hidden';
            topicInput.name = 'topic';
            topicInput.value = this.topic;
            form.appendChild(topicInput);

            this.selectedReviewers.forEach(r => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'participants';
                input.value = r;
                form.appendChild(input);
            });

            document.body.appendChild(form);
            form.submit();
        },
        toggleReviewer(id) {
            const idx = this.selectedReviewers.indexOf(id);
            if (idx === -1) {
                this.selectedReviewers.push(id);
            } else {
                this.selectedReviewers.splice(idx, 1);
            }
        }
    }">
        <div class="bg-white rounded-lg shadow-lg p-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">The Green Room</h1>
            <p class="text-gray-600 mb-6">Start a brainstorming session with your AI collaborators</p>

            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Topic (optional)</label>
                <input type="text" x-model="topic"
                    placeholder="e.g., Advent sermon ideas, Stewardship themes..."
                    class="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500">
                <p class="text-sm text-gray-500 mt-1">Leave empty for open-ended brainstorming</p>
            </div>

            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-3">Choose your collaborators (at least 2)</label>
                <div class="grid grid-cols-1 gap-2">
                    <template x-for="reviewer in reviewers" :key="reviewer.id">
                        <label class="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                            :class="{'bg-indigo-50 border-indigo-300': selectedReviewers.includes(reviewer.id)}">
                            <input type="checkbox"
                                :checked="selectedReviewers.includes(reviewer.id)"
                                @change="toggleReviewer(reviewer.id)"
                                class="h-4 w-4 text-indigo-600 rounded">
                            <div class="ml-3">
                                <span class="font-medium text-gray-800" x-text="reviewer.name"></span>
                                <span class="text-gray-500 text-sm ml-2" x-text="reviewer.description"></span>
                            </div>
                        </label>
                    </template>
                </div>
            </div>

            <button @click="startSession()"
                :disabled="starting || selectedReviewers.length < 2"
                class="w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed">
                <span x-show="!starting">Start Brainstorming Session</span>
                <span x-show="starting">Starting...</span>
            </button>

            <p class="text-center text-gray-500 text-sm mt-4">
                <span x-text="selectedReviewers.length"></span> collaborators selected
            </p>
        </div>

        <div class="mt-6 text-center">
            <a href="/" class="text-indigo-600 hover:text-indigo-800">Back to Dashboard</a>
        </div>
    </div>
</body>
</html>'''
        return html_content, 200, {'Content-Type': 'text/html'}

    @app.route('/api/brainstorm/start', methods=['POST'])
    def api_start_brainstorm():
        """API endpoint for starting a brainstorming session."""
        from panel_chat import start_brainstorm, InsufficientParticipantsError
        from cli_bridge import CLIBridge

        conn = get_db()
        init_db(conn)

        # Handle both form data and JSON
        if request.is_json:
            data = request.get_json() or {}
            topic = data.get('topic', '')
            participants = data.get('participants', ['theological', 'pastoral'])
        else:
            topic = request.form.get('topic', '')
            participants = request.form.getlist('participants') or ['theological', 'pastoral']

        try:
            bridge = CLIBridge(command='echo')
            discussion = start_brainstorm(
                conn, bridge,
                topic=topic,
                participants=participants
            )

            # For form submission, redirect to the chat page
            if not request.is_json:
                return redirect(url_for('chat_page', discussion_id=discussion.id))

            return jsonify(discussion.to_dict()), 201
        except InsufficientParticipantsError as e:
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            return f"Error: {e}", 400
        except Exception as e:
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            return f"Error: {e}", 400

    @app.route('/api/brainstorm/recent')
    def api_recent_brainstorms():
        """API endpoint for getting recent brainstorming sessions."""
        from panel_chat import get_discussion_by_id

        conn = get_db()
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic, mode, status, started_at, ended_at
            FROM panel_discussions
            WHERE sermon_id IS NULL AND mode = 'brainstorm'
            ORDER BY started_at DESC
            LIMIT 10
        """)

        sessions = []
        for row in cursor.fetchall():
            if hasattr(row, 'keys'):
                sessions.append(dict(row))
            else:
                sessions.append({
                    'id': row[0],
                    'topic': row[1],
                    'mode': row[2],
                    'status': row[3],
                    'started_at': row[4],
                    'ended_at': row[5]
                })

        return jsonify({'sessions': sessions}), 200

    # ========================================
    # NEW ROUTES FOR FRONTEND REDESIGN
    # ========================================

    # Human Conditions API Routes
    @app.route('/api/human-conditions')
    def api_list_human_conditions():
        """API endpoint for listing all human conditions."""
        from human_conditions import list_conditions, init_human_conditions_tables, seed_default_conditions

        conn = get_db()
        init_db(conn)
        init_human_conditions_tables(conn)
        seed_default_conditions(conn)

        conditions = list_conditions(conn)
        return jsonify(conditions), 200

    @app.route('/api/human-conditions/categories')
    def api_human_conditions_categories():
        """API endpoint for listing condition categories."""
        from human_conditions import get_categories, init_human_conditions_tables

        conn = get_db()
        init_db(conn)
        init_human_conditions_tables(conn)

        categories = get_categories(conn)
        return jsonify(categories), 200

    @app.route('/api/human-conditions/suggest', methods=['POST'])
    def api_suggest_conditions():
        """API endpoint for suggesting conditions based on scripture/theme."""
        from human_conditions import (
            suggest_conditions_for_scripture, suggest_conditions_for_theme,
            init_human_conditions_tables, seed_default_conditions
        )

        conn = get_db()
        init_db(conn)
        init_human_conditions_tables(conn)
        seed_default_conditions(conn)

        data = request.get_json() or {}
        scripture = data.get('scripture', '')
        theme = data.get('theme', '')

        suggestions = []
        seen_ids = set()

        # Get scripture-based suggestions
        if scripture:
            for s in suggest_conditions_for_scripture(conn, scripture):
                if s['id'] not in seen_ids:
                    suggestions.append(s)
                    seen_ids.add(s['id'])

        # Get theme-based suggestions
        if theme:
            for s in suggest_conditions_for_theme(conn, theme):
                if s['id'] not in seen_ids:
                    suggestions.append(s)
                    seen_ids.add(s['id'])

        return jsonify(suggestions[:10]), 200

    @app.route('/api/human-conditions', methods=['POST'])
    def api_create_condition():
        """API endpoint for creating a new human condition."""
        from human_conditions import create_condition, init_human_conditions_tables, DuplicateConditionError

        conn = get_db()
        init_db(conn)
        init_human_conditions_tables(conn)

        data = request.get_json() or {}
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        try:
            condition = create_condition(
                conn,
                name=name,
                description=description,
                category=category or 'general',
                scripture_associations=data.get('scripture_associations')
            )
            return jsonify(condition), 201
        except DuplicateConditionError as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/sermon/<int:sermon_id>/conditions')
    def api_sermon_conditions(sermon_id):
        """API endpoint for getting conditions linked to a sermon."""
        from human_conditions import get_sermon_conditions, init_human_conditions_tables

        conn = get_db()
        init_db(conn)
        init_human_conditions_tables(conn)

        conditions = get_sermon_conditions(conn, sermon_id)
        return jsonify(conditions), 200

    # New Page Routes

    @app.route('/series')
    def series_list():
        """List all sermon series."""
        conn = get_db()
        init_db(conn)

        # Check if new templates exist
        if os.path.exists(os.path.join(template_folder, 'pages', 'series', 'list.html')):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sermon_series ORDER BY start_date DESC")
            series_list = cursor.fetchall() if cursor.description else []
            return render_template('pages/series/list.html', series_list=series_list, filter=request.args.get('filter')), 200

        return jsonify({'error': 'Template not found'}), 404

    @app.route('/series/new')
    def series_new():
        """Create new sermon series."""
        if os.path.exists(os.path.join(template_folder, 'pages', 'series', 'wizard.html')):
            return render_template('pages/series/wizard.html'), 200
        return jsonify({'error': 'Template not found'}), 404

    @app.route('/lectionary')
    def lectionary_page():
        """Lectionary calendar page."""
        if os.path.exists(os.path.join(template_folder, 'pages', 'lectionary.html')):
            return render_template('pages/lectionary.html', upcoming_sundays=[]), 200
        return jsonify({'error': 'Template not found'}), 404

    @app.route('/practice')
    def practice_index():
        """Practice timer index page - list sermons available for practice."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title, scripture, word_count, estimated_minutes
            FROM sermons
            WHERE manuscript IS NOT NULL AND manuscript != ''
            ORDER BY created_at DESC
        """)
        sermons = cursor.fetchall()

        return render_template('pages/practice_index.html', sermons=sermons), 200

    @app.route('/sermon/<int:sermon_id>/practice')
    def practice_page(sermon_id):
        """Practice timer page for a sermon."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sermons WHERE id = ?", (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return not_found_html(None)

        if os.path.exists(os.path.join(template_folder, 'pages', 'practice.html')):
            return render_template('pages/practice.html', sermon=sermon, target_minutes=15), 200

        return jsonify({'error': 'Template not found'}), 404

    @app.route('/statistics')
    def statistics_page():
        """Statistics dashboard page."""
        if os.path.exists(os.path.join(template_folder, 'pages', 'statistics.html')):
            return render_template('pages/statistics.html'), 200
        return jsonify({'error': 'Template not found'}), 404

    @app.route('/api/statistics')
    def api_statistics():
        """API endpoint for statistics data."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()

        # Total sermons
        cursor.execute("SELECT COUNT(*) as count FROM sermons")
        total_sermons = cursor.fetchone()['count']

        # Total words
        cursor.execute("SELECT SUM(word_count) as total FROM sermons WHERE word_count IS NOT NULL")
        result = cursor.fetchone()
        total_words = result['total'] if result and result['total'] else 0

        # Average word count
        cursor.execute("SELECT AVG(word_count) as avg FROM sermons WHERE word_count IS NOT NULL")
        result = cursor.fetchone()
        avg_word_count = result['avg'] if result and result['avg'] else 0

        return jsonify({
            'total_sermons': total_sermons,
            'total_words': total_words,
            'avg_word_count': int(avg_word_count),
            'practice_hours': 0,
            'average_score': 0,
            'avg_wpm': 135,
            'practice_sessions': 0
        }), 200

    @app.route('/settings/church')
    def settings_church():
        """Church settings page."""
        if os.path.exists(os.path.join(template_folder, 'pages', 'settings', 'church.html')):
            return render_template('pages/settings/church.html', church={}), 200
        return jsonify({'error': 'Template not found'}), 404

    @app.route('/settings/reviewers')
    def settings_reviewers():
        """Reviewer panel settings page."""
        if os.path.exists(os.path.join(template_folder, 'pages', 'settings', 'reviewers.html')):
            return render_template('pages/settings/reviewers.html', reviewers=[]), 200
        return jsonify({'error': 'Template not found'}), 404

    @app.route('/api/settings/church', methods=['POST'])
    def api_save_church_settings():
        """API endpoint for saving church settings."""
        data = request.get_json() or {}
        # In production, save to database
        return jsonify({'success': True}), 200

    @app.route('/api/settings/reviewers', methods=['POST'])
    def api_save_reviewers():
        """API endpoint for saving reviewer settings."""
        data = request.get_json() or {}
        # In production, save to database
        return jsonify({'success': True}), 200

    # ========================================
    # SERMON GENERATION API
    # ========================================

    @app.route('/api/sermon/generate', methods=['POST'])
    def api_generate_sermon():
        """API endpoint for generating a sermon with streaming progress."""
        import json as json_module
        import time
        from sermon_generator import generate_sermon_simple
        from cli_bridge import CLIBridge

        data = request.get_json() or {}
        scripture = data.get('scripture', '').strip()
        title = data.get('title', '').strip()
        theme = data.get('theme', '').strip()
        main_point = data.get('main_point', '').strip()
        liturgical_season = data.get('liturgical_season', '').strip()
        special_occasion = data.get('special_occasion', '').strip()

        if not scripture:
            return jsonify({'error': 'Scripture is required'}), 400

        # Get database connection and prepare params before streaming
        # This ensures we're in the application context
        conn = get_db()
        init_db(conn)
        bridge = CLIBridge(command='echo')
        params = {
            'scripture': scripture,
            'title': title or f'Sermon on {scripture}',
            'theme': theme,
            'main_point': main_point,
            'liturgical_season': liturgical_season,
            'special_occasion': special_occasion
        }

        def generate_stream():
            """Generator for streaming progress updates."""
            try:
                # Stage 1: Research (0-25%)
                yield f"data: {json_module.dumps({'stage': 'research', 'progress': 5})}\n\n"
                time.sleep(0.3)
                yield f"data: {json_module.dumps({'stage': 'research', 'progress': 15})}\n\n"
                time.sleep(0.3)
                yield f"data: {json_module.dumps({'stage': 'research', 'progress': 25})}\n\n"

                # Stage 2: Structure (25-50%)
                yield f"data: {json_module.dumps({'stage': 'structure', 'progress': 30})}\n\n"
                time.sleep(0.3)
                yield f"data: {json_module.dumps({'stage': 'structure', 'progress': 40})}\n\n"
                time.sleep(0.3)
                yield f"data: {json_module.dumps({'stage': 'structure', 'progress': 50})}\n\n"

                # Stage 3: Writing (50-80%) - actual generation happens here
                yield f"data: {json_module.dumps({'stage': 'writing', 'progress': 55})}\n\n"
                yield f"data: {json_module.dumps({'stage': 'writing', 'progress': 65})}\n\n"

                # Perform actual generation (uses conn/bridge/params from closure)
                result = generate_sermon_simple(params, bridge, conn)
                yield f"data: {json_module.dumps({'stage': 'writing', 'progress': 80})}\n\n"

                # Stage 4: Review (80-100%)
                yield f"data: {json_module.dumps({'stage': 'review', 'progress': 85})}\n\n"
                time.sleep(0.2)
                yield f"data: {json_module.dumps({'stage': 'review', 'progress': 95})}\n\n"
                time.sleep(0.2)

                # Complete
                yield f"data: {json_module.dumps({'stage': 'review', 'progress': 100, 'sermon_id': result.get('sermon_id')})}\n\n"

            except Exception as e:
                yield f"data: {json_module.dumps({'error': str(e)})}\n\n"

        return app.response_class(
            generate_stream(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    # ========================================
    # PRACTICE TIMER API
    # ========================================

    @app.route('/api/sermon/<int:sermon_id>/practice/start', methods=['POST'])
    def api_start_practice(sermon_id):
        """Start a practice timer for a sermon."""
        from practice_timing import start_practice_timer

        conn = get_db()
        init_db(conn)

        # Check sermon exists and get word count
        cursor = conn.cursor()
        cursor.execute('SELECT word_count FROM sermons WHERE id = ?', (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return jsonify({'error': 'Sermon not found'}), 404

        result = start_practice_timer(conn, sermon_id)
        if result:
            result['word_count'] = sermon['word_count'] if sermon['word_count'] else 0
            return jsonify(result), 201

        return jsonify({'error': 'Failed to start practice session'}), 500

    @app.route('/api/practice/<int:session_id>/pause', methods=['POST'])
    def api_pause_practice(session_id):
        """Pause a practice timer."""
        from practice_timing import pause_practice_timer

        conn = get_db()
        init_db(conn)

        success = pause_practice_timer(conn, session_id)
        if success:
            return jsonify({'success': True, 'status': 'paused'}), 200

        return jsonify({'error': 'Failed to pause session'}), 400

    @app.route('/api/practice/<int:session_id>/resume', methods=['POST'])
    def api_resume_practice(session_id):
        """Resume a paused practice timer."""
        from practice_timing import resume_practice_timer

        conn = get_db()
        init_db(conn)

        success = resume_practice_timer(conn, session_id)
        if success:
            return jsonify({'success': True, 'status': 'running'}), 200

        return jsonify({'error': 'Failed to resume session'}), 400

    @app.route('/api/practice/<int:session_id>/stop', methods=['POST'])
    def api_stop_practice(session_id):
        """Stop a practice timer and get feedback."""
        from practice_timing import stop_practice_timer, get_pacing_feedback

        conn = get_db()
        init_db(conn)

        result = stop_practice_timer(conn, session_id)
        if result:
            feedback = get_pacing_feedback(conn, session_id)
            result['feedback'] = feedback
            return jsonify(result), 200

        return jsonify({'error': 'Failed to stop session'}), 400

    @app.route('/api/sermon/<int:sermon_id>/practice/history')
    def api_practice_history(sermon_id):
        """Get practice history for a sermon."""
        from practice_timing import get_practice_history, get_timing_stats

        conn = get_db()
        init_db(conn)

        history = get_practice_history(conn, sermon_id)
        stats = get_timing_stats(conn, sermon_id)

        return jsonify({
            'sessions': history,
            'statistics': stats
        }), 200

    # ========================================
    # SERMON RESEARCH API
    # ========================================

    @app.route('/api/sermon/<int:sermon_id>/research')
    def api_sermon_research(sermon_id):
        """Get research data for a sermon."""
        import json

        conn = get_db()
        init_db(conn)

        cursor = conn.cursor()
        cursor.execute('SELECT research_data, scripture, theme FROM sermons WHERE id = ?', (sermon_id,))
        sermon = cursor.fetchone()

        if not sermon:
            return jsonify({'error': 'Sermon not found'}), 404

        research_data = {}
        if sermon['research_data']:
            try:
                research_data = json.loads(sermon['research_data'])
            except json.JSONDecodeError:
                research_data = {'raw': sermon['research_data']}

        return jsonify({
            'sermon_id': sermon_id,
            'scripture': sermon['scripture'],
            'theme': sermon['theme'],
            'research': research_data
        }), 200

    # ========================================
    # PASSAGE SUGGESTIONS API
    # ========================================

    @app.route('/api/passage-suggestions', methods=['POST'])
    def api_passage_suggestions():
        """Get passage suggestions based on theme."""
        from passage_suggestions import suggest_passages_for_theme

        data = request.get_json() or {}
        theme = data.get('theme', '')
        count = data.get('count', 5)

        try:
            count = int(count)
            if count < 1:
                count = 5
            if count > 20:
                count = 20
        except (ValueError, TypeError):
            count = 5

        suggestions = suggest_passages_for_theme(theme, count=count)

        return jsonify(suggestions), 200

    # ========================================
    # SERIES API
    # ========================================

    @app.route('/api/series', methods=['POST'])
    def api_create_series():
        """Create a new sermon series."""
        from series import create_series

        conn = get_db()
        init_db(conn)

        data = request.get_json() or {}
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        theme = data.get('theme', '').strip()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        planned_weeks = data.get('planned_weeks', 4)

        if not title:
            return jsonify({'error': 'Title is required'}), 400

        try:
            series_id = create_series(
                conn,
                name=title,
                description=description,
                theme=theme,
                start_date=start_date,
                end_date=end_date,
                status='planning'
            )

            # Handle sermon slots if provided
            sermon_slots = data.get('sermon_slots', [])
            for i, slot in enumerate(sermon_slots):
                if slot.get('title') or slot.get('scripture'):
                    # Create sermon for the slot
                    cursor = conn.cursor()
                    cursor.execute(
                        '''INSERT INTO sermons (title, scripture, theme, series_id, series_week)
                           VALUES (?, ?, ?, ?, ?)''',
                        (
                            slot.get('title', f'Week {i+1}'),
                            slot.get('scripture', ''),
                            slot.get('focus', theme),
                            series_id,
                            i + 1
                        )
                    )
                    conn.commit()

            return jsonify({'id': series_id, 'title': title}), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/series')
    def api_list_series():
        """List all sermon series."""
        from series import list_series

        conn = get_db()
        init_db(conn)

        status = request.args.get('status')
        series_list = list_series(conn, status=status)

        return jsonify(series_list), 200

    @app.route('/api/series/<int:series_id>')
    def api_get_series(series_id):
        """Get a specific sermon series."""
        from series import get_series, get_sermons_in_series

        conn = get_db()
        init_db(conn)

        series = get_series(conn, series_id)
        if not series:
            return jsonify({'error': 'Series not found'}), 404

        sermons = get_sermons_in_series(conn, series_id)
        series['sermons'] = sermons

        return jsonify(series), 200

    @app.route('/api/series/<int:series_id>', methods=['PUT'])
    def api_update_series(series_id):
        """Update a sermon series."""
        from series import update_series

        conn = get_db()
        init_db(conn)

        data = request.get_json() or {}

        success = update_series(conn, series_id, **data)
        if success:
            return jsonify({'success': True}), 200

        return jsonify({'error': 'Series not found'}), 404

    @app.route('/api/series/<int:series_id>', methods=['DELETE'])
    def api_delete_series(series_id):
        """Delete a sermon series."""
        from series import delete_series

        conn = get_db()
        init_db(conn)

        success = delete_series(conn, series_id)
        if success:
            return '', 204

        return jsonify({'error': 'Series not found'}), 404

    # Initialize SocketIO for real-time features
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # Register SocketIO event handlers
    @socketio.on('connect')
    def on_connect():
        """Handle client connection."""
        pass

    @socketio.on('join_generation')
    def on_join_generation(data):
        """Handle client joining a generation room."""
        from flask_socketio import join_room
        sermon_id = data.get('sermon_id')
        if sermon_id:
            join_room(f'generation_{sermon_id}')

    @socketio.on('join_stream')
    def on_join_stream(data):
        """Handle client joining a chat stream room."""
        from flask_socketio import join_room
        discussion_id = data.get('discussion_id')
        if discussion_id:
            join_room(f'stream_{discussion_id}')

    return app


def get_socketio():
    """Get the SocketIO instance."""
    global socketio
    return socketio


if __name__ == '__main__':
    application = create_app()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    # Use socketio.run() instead of app.run() for WebSocket support
    socketio.run(application, host=host, port=DEFAULT_PORT, debug=False, allow_unsafe_werkzeug=True)
