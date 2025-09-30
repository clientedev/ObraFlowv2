/**
 * SERVICE WORKER COM SUPORTE A PUSH NOTIFICATIONS
 * Sistema mantém acesso direto ao PostgreSQL sem cache agressivo
 */

const CACHE_VERSION = 'v1';
const CACHE_NAME = `elp-pwa-${CACHE_VERSION}`;

// Recursos mínimos para cache (apenas para offline básico)
const MINIMAL_CACHE = [
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png'
];

console.log('🔧 SW: Service Worker iniciado - Modo Push Notifications');

// INSTALL - Configuração inicial
self.addEventListener('install', (event) => {
    console.log('📦 SW: Instalando service worker...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 SW: Cache criado');
                return cache.addAll(MINIMAL_CACHE);
            })
            .then(() => {
                console.log('✅ SW: Instalação concluída');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('❌ SW: Erro na instalação:', error);
            })
    );
});

// ACTIVATE - Limpeza e ativação
self.addEventListener('activate', (event) => {
    console.log('🚀 SW: Ativando service worker...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME) {
                            console.log(`🧹 SW: Removendo cache antigo: ${cacheName}`);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ SW: Ativado e pronto');
                return self.clients.claim();
            })
    );
});

// FETCH - NÃO fazer cache agressivo, deixar passar direto ao servidor
self.addEventListener('fetch', (event) => {
    // Estratégia: Network First (sempre tentar servidor primeiro)
    // Isso garante dados sempre atualizados do PostgreSQL
    event.respondWith(
        fetch(event.request)
            .catch(error => {
                // Se falhar, tentar cache apenas para recursos estáticos
                if (event.request.url.includes('/static/icons/')) {
                    return caches.match(event.request);
                }
                throw error;
            })
    );
});

// PUSH - Receber notificações push
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
            console.log('📬 SW: Dados da notificação:', data);
            
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
        }).then(() => {
            console.log('✅ SW: Notificação exibida com sucesso');
        }).catch(error => {
            console.error('❌ SW: Erro ao exibir notificação:', error);
        })
    );
});

// NOTIFICATIONCLICK - Ação ao clicar na notificação
self.addEventListener('notificationclick', (event) => {
    console.log('👆 SW: Notificação clicada');
    
    event.notification.close();
    
    const urlToOpen = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(windowClients => {
                // Verificar se já existe uma janela aberta
                for (let client of windowClients) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        console.log('👆 SW: Focando janela existente');
                        return client.focus().then(client => {
                            if ('navigate' in client) {
                                return client.navigate(urlToOpen);
                            }
                        });
                    }
                }
                
                // Se não, abrir nova janela
                console.log('👆 SW: Abrindo nova janela');
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
            .catch(error => {
                console.error('❌ SW: Erro ao processar clique:', error);
            })
    );
});

// NOTIFICATIONCLOSE - Notificação fechada sem clique
self.addEventListener('notificationclose', (event) => {
    console.log('🔕 SW: Notificação fechada');
});

// MESSAGE - Comunicação com a aplicação
self.addEventListener('message', (event) => {
    console.log('💬 SW: Mensagem recebida:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'GET_VERSION') {
        event.ports[0].postMessage({ version: CACHE_VERSION });
    }
});

console.log('✅ SW: Service Worker carregado - Push Notifications habilitado');
