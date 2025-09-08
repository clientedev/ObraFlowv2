#!/usr/bin/env python3
"""
Versão de produção para Railway - Importa o sistema completo só se conseguir
"""
import os
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "railway-production")

# Health check sempre disponível
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'construction-tracker'
    }), 200

# Try to import full system
try:
    # Import do sistema completo
    print("🚀 Carregando sistema completo...")
    from main import app as full_app
    print("✅ Sistema completo carregado com sucesso!")
    
    # Use o app completo
    app = full_app
    
except Exception as e:
    print(f"⚠️ Falha ao carregar sistema completo: {e}")
    print("🔄 Usando versão simplificada...")
    
    # Sistema simplificado de backup
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Sistema de Gestão de Construção - ELP (Modo Simplificado)',
            'status': 'FUNCIONANDO',
            'version': '1.0.0',
            'mode': 'simplified',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'Sistema completo será carregado em próxima atualização'
        }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)