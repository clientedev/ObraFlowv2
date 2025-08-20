# Rotas específicas para PWA
from flask import send_from_directory, jsonify
from app import app

@app.route('/manifest.json')
def manifest():
    """Servir manifest.json do PWA"""
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/browserconfig.xml')
def browserconfig():
    """Servir browserconfig.xml para Windows/IE"""
    return send_from_directory('static', 'browserconfig.xml', mimetype='application/xml')

@app.route('/sw.js')
def service_worker():
    """Servir Service Worker do diretório static/js"""
    return send_from_directory('static/js', 'sw.js', mimetype='application/javascript')

@app.route('/offline')
def offline():
    """Página offline para PWA"""
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - ELP Relatórios</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; }
            .offline-container {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <div class="text-center">
                <div class="mb-4">
                    <i class="fas fa-wifi-slash text-warning" style="font-size: 4rem;"></i>
                </div>
                <h1 class="mb-3">Você está offline</h1>
                <p class="text-muted mb-4">Verifique sua conexão com a internet e tente novamente.</p>
                <div class="d-grid gap-2 d-md-block">
                    <button class="btn btn-primary" onclick="window.location.reload()">
                        <i class="fas fa-sync me-2"></i>Tentar Novamente
                    </button>
                    <a href="/" class="btn btn-outline-secondary">
                        <i class="fas fa-home me-2"></i>Página Inicial
                    </a>
                </div>
                
                <div class="mt-5">
                    <img src="/static/icons/icon-128x128.png" alt="ELP Logo" class="mb-3">
                    <h5>ELP Consultoria e Engenharia</h5>
                    <p class="text-muted small">Sistema de Relatórios de Obra</p>
                </div>
            </div>
        </div>
        
        <script>
            // Recarregar quando voltar online
            window.addEventListener('online', () => {
                window.location.reload();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/pwa/install-info')
def pwa_install_info():
    """Informações sobre instalação do PWA"""
    return jsonify({
        'name': 'ELP Consultoria - Sistema de Relatórios',
        'short_name': 'ELP Relatórios',
        'installable': True,
        'features': [
            'Trabalha offline',
            'Acesso rápido da tela inicial',
            'Notificações push (futuro)',
            'Interface nativa',
            'Atualizações automáticas'
        ],
        'requirements': [
            'Navegador compatível (Chrome, Firefox, Safari)',
            'Conexão HTTPS',
            'Suporte a Service Workers'
        ]
    })