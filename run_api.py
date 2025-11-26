"""
Flask API server entry point.

Run this script to start the dashboard API server.

Usage:
    python run_api.py
"""
from scripts.api.app import create_app
from scripts.logger_config import get_logger

logger = get_logger(__name__)

if __name__ == '__main__':
    # Create Flask app
    app = create_app()

    # Run development server
    logger.info("Starting Flask API server on http://127.0.0.1:5000")
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
