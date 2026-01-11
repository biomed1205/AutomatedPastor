"""Flask application for AutomatedPastor sermon generation service."""
import os

from flask import Flask, jsonify, request, redirect, url_for, session, render_template_string, g
from database import get_db, init_db, close_db as db_close


DEFAULT_PORT = 8787

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

    app = Flask(__name__)

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
        cursor.execute("SELECT id, title, scripture, created_at FROM sermons ORDER BY created_at DESC LIMIT 5")
        sermons = cursor.fetchall()

        content = '''
        {% extends base %}
        {% block title %}Dashboard - AutomatedPastor{% endblock %}
        {% block content %}
        <h1>Dashboard</h1>
        <h2>Recent Sermons</h2>
        {% if sermons %}
        <ul class="sermon-list">
            {% for sermon in sermons %}
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
            sermons=sermons), 200

    @app.route('/sermons')
    def sermons_list():
        """List all sermons."""
        conn = get_db()
        init_db(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, scripture, theme, created_at FROM sermons ORDER BY created_at DESC")
        sermons = cursor.fetchall()

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
    def sermon_new():
        """Create sermon form."""
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

    return app


if __name__ == '__main__':
    application = create_app()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    application.run(host=host, port=DEFAULT_PORT)
