#!/usr/bin/env python3
"""
Simplified Railway-compatible version of the Flask app
This is a backup deployment option if the main app has dependency issues
"""
import os
from flask import Flask, jsonify

# Create simple Flask app for Railway deployment test
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "railway-test-secret")

@app.route('/health')
def health():
    """Simple health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'service': 'construction-tracker',
        'message': 'Railway deployment successful'
    }), 200

@app.route('/')
def index():
    """Simple index page"""
    return jsonify({
        'message': 'Construction Site Tracker - Running on Railway',
        'status': 'active',
        'endpoints': ['/health', '/']
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)