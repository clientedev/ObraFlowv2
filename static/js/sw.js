/**
 * SERVICE WORKER DESABILITADO
 * Sistema agora usa PostgreSQL diretamente
 */

// Desinstalar este service worker
self.addEventListener('install', function(event) {
    console.log('SW: Desinstalando service worker...');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('SW: Removendo caches...');
    
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    console.log('SW: Removendo cache:', cacheName);
                    return caches.delete(cacheName);
                })
            );
        }).then(function() {
            console.log('SW: Auto-desregistrando...');
            return self.registration.unregister();
        })
    );
});

// Não interceptar mais requests - deixar ir direto para o servidor
self.addEventListener('fetch', function(event) {
    // Não fazer nada - deixar requests passarem direto
    return;
});

console.log('SW: Service Worker desabilitado - PostgreSQL direct mode');