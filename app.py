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


def create_app(config=None):
    """Create and configure the Flask application.

    Args:
        config: Optional dictionary of configuration values to override defaults.

    Returns:
        Configured Flask application instance.
    """
    # Reset auth state when creating a new app (important for testing)
    from auth import reset_auth_state
    reset_auth_state()

    app = Flask(__name__)

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

    return app


if __name__ == '__main__':
    application = create_app()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    application.run(host=host, port=DEFAULT_PORT)
