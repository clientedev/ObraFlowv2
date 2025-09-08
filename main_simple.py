#!/usr/bin/env python3
"""
Versão ultra-simples para garantir que o Railway funciona
"""
import os
from flask import Flask, jsonify
from datetime import datetime

# App minimalista
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "railway-test")

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'construction-tracker'
    }), 200

@app.route('/')
def index():
    return jsonify({
        'message': 'Sistema de Gestão de Construção - ELP',
        'status': 'FUNCIONANDO',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)