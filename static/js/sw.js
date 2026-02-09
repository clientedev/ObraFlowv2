/**
 * SERVICE WORKER COM SUPORTE A OFFLINE E PUSH NOTIFICATIONS
 * Estratégia: NetworkFirst para HTML, StaleWhileRevalidate para estáticos
 */

const CACHE_VERSION = 'v2-offline';
const CACHE_NAME = `elp-pwa-${CACHE_VERSION}`;

// Recursos para pré-cache (Offline Básico)
const PRECACHE_URLS = [
    '/',
    '/offline',
    '/static/css/style.css',
    '/static/css/mobile.css',
    '/static/js/main.js',
    '/static/js/offline-db.js',
    '/static/js/sync-manager.js',
    '/static/js/offline-forms.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/logo_elp_navbar.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

console.log('🔧 SW: Service Worker iniciado - Offline & Push Enabled');

// INSTALL
self.addEventListener('install', (event) => {
    console.log('📦 SW: Instalando e fazendo cache de recursos...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                // Tenta adicionar um por um para não falhar tudo se um 404
                return Promise.allSettled(
                    PRECACHE_URLS.map(url => cache.add(url).catch(e => console.warn(`⚠️ Falha ao cachear ${url}:`, e)))
                );
            })
            .then(() => {
                console.log('✅ SW: Pré-cache concluído');
                return self.skipWaiting();
            })
    );
});

// ACTIVATE
self.addEventListener('activate', (event) => {
    console.log('🚀 SW: Ativando e limpando caches antigos...');

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        // Limpa caches antigos do app, mantém outros se necessário
                        if (cacheName.startsWith('elp-pwa-') && cacheName !== CACHE_NAME) {
                            console.log(`🧹 SW: Removendo cache antigo: ${cacheName}`);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ SW: Pronto e ativo');
                return self.clients.claim();
            })
    );
});

// FETCH
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Ignorar requisições não-GET ou extensões de navegador
    if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
        return;
    }

    // 1. Navegação (HTML) -> NetworkFirst
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Caching dinâmica da página visitada
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
                    return response;
                })
                .catch(async () => {
                    console.log('📡 SW: Falha na rede (HTML), tentando cache...');
                    const cachedResponse = await caches.match(request);
                    if (cachedResponse) return cachedResponse;

                    // Fallback para página offline se não tiver cache
                    const offlinePage = await caches.match('/offline');
                    if (offlinePage) return offlinePage;

                    return new Response('Você está offline e esta página não está em cache.', {
                        status: 503,
                        statusText: 'Service Unavailable',
                        headers: new Headers({ 'Content-Type': 'text/plain' })
                    });
                })
        );
        return;
    }

    // 2. Estáticos (JS, CSS, Imagens) -> StaleWhileRevalidate
    if (
        url.pathname.startsWith('/static/') ||
        url.href.includes('cdn.jsdelivr.net') ||
        url.href.includes('cdnjs.cloudflare.com') ||
        request.destination === 'script' ||
        request.destination === 'style' ||
        request.destination === 'image'
    ) {
        event.respondWith(
            caches.match(request).then(cachedResponse => {
                const networkFetch = fetch(request).then(response => {
                    // Atualiza cache em background
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
                    return response;
                }).catch(() => {
                    // Se falhar rede, ok, já retornamos cache ou undefined
                });

                // Retorna cache se existir, senão espera rede
                return cachedResponse || networkFetch;
            })
        );
        return;
    }

    // 3. API/Outros -> NetworkOnly (Default)
    // Deixa o browser lidar normal
});

// PUSH - Receber notificações push (Mantido original)
self.addEventListener('push', (event) => {
    console.log('📬 SW: Push notification recebida');

    let notificationData = {
        title: 'ELP Relatórios',
        body: 'Nova notificação',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-96x96.png',
        vibrate: [200, 100, 200],
        data: {
            url: '/'
        }
    };

    if (event.data) {
        try {
            const data = event.data.json();

            notificationData = {
                title: data.title || notificationData.title,
                body: data.body || data.message || notificationData.body,
                icon: data.icon || notificationData.icon,
                badge: data.badge || notificationData.badge,
                vibrate: data.vibrate || notificationData.vibrate,
                data: {
                    url: data.url || data.click_action || '/',
                    ...data.data
                },
                tag: data.tag,
                requireInteraction: data.requireInteraction || false
            };
        } catch (error) {
            console.error('❌ SW: Erro ao parsear dados da notificação:', error);
        }
    }

    event.waitUntil(
        self.registration.showNotification(notificationData.title, {
            body: notificationData.body,
            icon: notificationData.icon,
            badge: notificationData.badge,
            vibrate: notificationData.vibrate,
            data: notificationData.data,
            tag: notificationData.tag,
            requireInteraction: notificationData.requireInteraction
        })
    );
});

// NOTIFICATIONCLICK (Mantido original)
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const urlToOpen = event.notification.data?.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(windowClients => {
                for (let client of windowClients) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus().then(client => {
                            if ('navigate' in client) {
                                return client.navigate(urlToOpen);
                            }
                        });
                    }
                }
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// MESSAGE (Mantido original)
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
