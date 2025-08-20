// Service Worker para PWA e Notificações Push
const CACHE_NAME = 'elp-relatorios-v1';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/simple-offline.js',
  '/static/js/pwa-install.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/offline'
];

// Instalação do Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('SW: Cache aberto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Ativação do Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('SW: Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Interceptação de requisições
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Retorna do cache se encontrado
        if (response) {
          return response;
        }
        
        // Tenta buscar da rede
        return fetch(event.request).catch(() => {
          // Se offline e é uma página, retorna página offline
          if (event.request.destination === 'document') {
            return caches.match('/offline');
          }
        });
      })
  );
});

// Escutar mensagens push
self.addEventListener('push', event => {
  console.log('SW: Push recebido:', event);
  
  const options = {
    body: 'Você tem uma nova notificação',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver detalhes',
        icon: '/static/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Fechar',
        icon: '/static/icons/icon-96x96.png'
      }
    ]
  };
  
  if (event.data) {
    const data = event.data.json();
    options.body = data.message || options.body;
    options.title = data.title || 'ELP Relatórios';
    options.data = { ...options.data, ...data };
  }
  
  event.waitUntil(
    self.registration.showNotification('ELP Relatórios', options)
  );
});

// Clique em notificação
self.addEventListener('notificationclick', event => {
  console.log('SW: Notificação clicada:', event);
  
  event.notification.close();
  
  if (event.action === 'explore') {
    // Abrir o app
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // Apenas fechar
    event.notification.close();
  } else {
    // Clique na notificação principal
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Background Sync para dados offline
self.addEventListener('sync', event => {
  console.log('SW: Background sync:', event.tag);
  
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  // Implementar sincronização de dados offline
  return fetch('/api/sync')
    .then(response => response.json())
    .then(data => {
      console.log('SW: Sync realizado:', data);
    })
    .catch(error => {
      console.error('SW: Erro no sync:', error);
    });
}