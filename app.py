"""Flask application for AutomatedPastor sermon generation service."""
import os

from flask import Flask, jsonify, request, redirect, url_for, session


DEFAULT_PORT = 8787


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

    # Apply custom configuration if provided
    if config:
        app.config.update(config)

    @app.route('/')
    def home():
        """Home page."""
        return jsonify({'message': 'Welcome to AutomatedPastor'}), 200

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

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors with JSON response."""
        return jsonify({'error': 'Not found'}), 404

    return app


if __name__ == '__main__':
    application = create_app()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    application.run(host=host, port=DEFAULT_PORT)
