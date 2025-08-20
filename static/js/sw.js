// Service Worker para funcionalidade offline
const CACHE_NAME = 'elp-app-v1';
const STATIC_CACHE = 'elp-static-v1';

// Arquivos essenciais para funcionar offline
const ESSENTIAL_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/offline.js',
    '/login',
    '/dashboard',
    '/projects',
    '/visits',
    '/reports',
    '/reimbursements'
];

// Arquivos estáticos (CSS, JS, imagens)
const STATIC_FILES = [
    '/static/css/bootstrap.min.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/images/logo.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css',
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker instalando...');
    
    event.waitUntil(
        Promise.all([
            // Cache de arquivos essenciais
            caches.open(CACHE_NAME).then(cache => {
                console.log('Cacheando arquivos essenciais...');
                return cache.addAll(ESSENTIAL_FILES.map(url => new Request(url, {
                    credentials: 'same-origin'
                })));
            }).catch(error => {
                console.warn('Erro ao cachear arquivos essenciais:', error);
            }),
            
            // Cache de arquivos estáticos
            caches.open(STATIC_CACHE).then(cache => {
                console.log('Cacheando arquivos estáticos...');
                return cache.addAll(STATIC_FILES.map(url => new Request(url, {
                    mode: 'cors'
                })));
            }).catch(error => {
                console.warn('Erro ao cachear arquivos estáticos:', error);
            })
        ])
    );
    
    // Forçar ativação imediata
    self.skipWaiting();
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log('Service Worker ativando...');
    
    event.waitUntil(
        // Limpar caches antigos
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== STATIC_CACHE) {
                        console.log('Removendo cache antigo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Tomar controle de todas as páginas imediatamente
            return self.clients.claim();
        })
    );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Ignorar requisições não-HTTP
    if (!request.url.startsWith('http')) {
        return;
    }
    
    // Estratégias diferentes para diferentes tipos de requisição
    if (request.method === 'GET') {
        if (isStaticAsset(url)) {
            // Cache First para assets estáticos
            event.respondWith(cacheFirst(request));
        } else if (isEssentialPage(url)) {
            // Network First para páginas essenciais
            event.respondWith(networkFirst(request));
        } else {
            // Network First com fallback para outras páginas
            event.respondWith(networkWithFallback(request));
        }
    } else if (request.method === 'POST') {
        // Interceptar POST para funcionalidade offline
        event.respondWith(handlePostRequest(request));
    }
});

// Verificar se é um asset estático
function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') || 
           url.hostname !== location.hostname ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.jpeg') ||
           url.pathname.endsWith('.gif') ||
           url.pathname.endsWith('.svg');
}

// Verificar se é uma página essencial
function isEssentialPage(url) {
    const essentialPaths = ['/', '/dashboard', '/projects', '/visits', '/reports', '/reimbursements', '/login'];
    return essentialPaths.includes(url.pathname);
}

// Cache First - Tentar cache primeiro, depois rede
async function cacheFirst(request) {
    try {
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('Cache first falhou:', error);
        return new Response('Asset não disponível offline', { status: 503 });
    }
}

// Network First - Tentar rede primeiro, depois cache
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('Network first falhou, tentando cache:', error);
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        
        // Retornar página offline se disponível
        return getOfflinePage();
    }
}

// Network com Fallback
async function networkWithFallback(request) {
    try {
        return await fetch(request);
    } catch (error) {
        console.log('Network falhou, tentando cache:', error);
        const cached = await caches.match(request);
        if (cached) {
            return cached;
        }
        
        return getOfflinePage();
    }
}

// Lidar com requisições POST offline
async function handlePostRequest(request) {
    const isOfflineSync = request.headers.get('X-Offline-Sync');
    
    if (isOfflineSync) {
        // Esta é uma sincronização, tentar enviar
        try {
            return await fetch(request);
        } catch (error) {
            console.log('Erro na sincronização:', error);
            throw error;
        }
    } else {
        // Requisição POST normal - tentar enviar ou salvar para sincronização
        try {
            return await fetch(request);
        } catch (error) {
            console.log('POST offline detectado:', error);
            
            // Notificar o cliente que a requisição falhou (será tratada pelo offline.js)
            return new Response(JSON.stringify({
                offline: true,
                message: 'Dados salvos offline, serão sincronizados quando a conexão for restabelecida'
            }), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            });
        }
    }
}

// Retornar página offline
async function getOfflinePage() {
    const offlineHTML = `
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - ELP Consultoria</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 50px;
                background-color: #f8f9fa;
            }
            .offline-container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .offline-icon {
                font-size: 64px;
                color: #ffc107;
                margin-bottom: 20px;
            }
            h1 { color: #343a40; }
            p { color: #6c757d; margin-bottom: 30px; }
            .btn {
                background-color: #20c1e8;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                display: inline-block;
                margin: 10px;
            }
            .btn:hover { background-color: #1a9bc7; }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <div class="offline-icon">📡</div>
            <h1>Você está offline</h1>
            <p>Não é possível carregar esta página no momento. Verifique sua conexão com a internet e tente novamente.</p>
            <p><strong>ELP Consultoria e Engenharia</strong><br>
            Algumas funcionalidades ainda estão disponíveis offline.</p>
            <a href="/" class="btn">Tentar Novamente</a>
            <a href="/dashboard" class="btn">Ir para Dashboard</a>
        </div>
        
        <script>
            // Recarregar quando a conexão for restabelecida
            window.addEventListener('online', () => {
                location.reload();
            });
        </script>
    </body>
    </html>
    `;
    
    return new Response(offlineHTML, {
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}

// Sincronização em background
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        console.log('Sincronização em background iniciada');
        event.waitUntil(
            // Notificar página principal para sincronizar dados
            self.clients.matchAll().then(clients => {
                clients.forEach(client => {
                    client.postMessage({
                        type: 'BACKGROUND_SYNC',
                        message: 'Iniciando sincronização automática...'
                    });
                });
            })
        );
    }
});

// Manipular mensagens do cliente
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});