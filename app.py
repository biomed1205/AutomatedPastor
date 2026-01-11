"""Flask application for AutomatedPastor sermon generation service."""
import os

from flask import Flask, jsonify


DEFAULT_PORT = 8787


def create_app(config=None):
    """Create and configure the Flask application.

    Args:
        config: Optional dictionary of configuration values to override defaults.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Apply custom configuration if provided
    if config:
        app.config.update(config)

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'healthy'}), 200

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors with JSON response."""
        return jsonify({'error': 'Not found'}), 404

    return app


if __name__ == '__main__':
    application = create_app()
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    application.run(host=host, port=DEFAULT_PORT)
