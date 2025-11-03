"""
Simple Flask webhook server for n8n to trigger dashboard updates.

Install dependencies:
    pip install flask

Run:
    python webhook_server.py

The server listens on http://localhost:5000/update-dashboard
"""
from flask import Flask, jsonify, request
import subprocess
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Add the project root to path so we can import the script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

@app.route('/update-dashboard', methods=['POST', 'GET'])
def update_dashboard():
    """Webhook endpoint to trigger dashboard update."""
    try:
        # Get optional parameters from request
        data = request.get_json() if request.is_json else {}

        # For GET requests, just provide info
        if request.method == 'GET':
            return jsonify({
                'status': 'info',
                'message': 'Webhook is running. Use POST to trigger update.',
                'endpoint': '/update-dashboard'
            }), 200

        # Priority 1: Check environment variable (SECURE)
        creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE')

        if not creds_file:
            # Priority 2: Fall back to config.json (LEGACY - use .env instead!)
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            creds_file = 'credentials/service-account.json'  # default

            if os.path.exists(config_path):
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if 'credentials_file' in config and config['credentials_file'] != 'credentials/your-service-account.json':
                        creds_file = config['credentials_file']

        # Set environment variable for credentials
        env = os.environ.copy()
        env['GOOGLE_CREDENTIALS_FILE'] = creds_file

        # Pass Google Drive file ID if set
        if 'GOOGLE_DRIVE_FILE_ID' in os.environ:
            env['GOOGLE_DRIVE_FILE_ID'] = os.environ['GOOGLE_DRIVE_FILE_ID']

        # Run the fetch script
        result = subprocess.run(
            ['python', 'scripts/fetch_from_sheets.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=env
        )

        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Dashboard updated successfully',
                'output': result.stdout
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Update failed',
                'error': result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Update timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # Run on localhost:5000
    # For production, use a proper WSGI server like gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)
