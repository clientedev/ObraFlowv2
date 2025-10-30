/**
 * Firebase Cloud Messaging Service Worker
 * Gerencia notificações push em background (app fechado)
 * 
 * IMPORTANTE: Este arquivo DEVE estar na raiz de /static/
 * para que o escopo do service worker cubra toda a aplicação
 */

importScripts("https://www.gstatic.com/firebasejs/11.0.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging-compat.js");

// IMPORTANTE: Configure estas variáveis com seus dados do Firebase
// Estes valores devem vir do console Firebase → Configurações do projeto
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

try {
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();

    messaging.onBackgroundMessage((payload) => {
        console.log('📬 [Service Worker] Mensagem recebida em background:', payload);

        const { title, body, icon } = payload.notification || {};
        const data = payload.data || {};

        const notificationTitle = title || 'ELP Consultoria';
        const notificationOptions = {
            body: body || 'Nova notificação',
            icon: icon || '/static/img/logo-elp.png',
            badge: '/static/img/badge-icon.png',
            tag: data.tag || 'elp-notification',
            requireInteraction: false,
            data: data,
            vibrate: [200, 100, 200],
            actions: [
                {
                    action: 'open',
                    title: 'Abrir',
                    icon: '/static/img/open-icon.png'
                },
                {
                    action: 'close',
                    title: 'Fechar',
                    icon: '/static/img/close-icon.png'
                }
            ]
        };

        self.registration.showNotification(notificationTitle, notificationOptions);

        console.log('✅ [Service Worker] Notificação exibida:', notificationTitle);
    });

    self.addEventListener('notificationclick', (event) => {
        console.log('👆 [Service Worker] Notificação clicada:', event.notification.tag);
        
        event.notification.close();

        const urlToOpen = event.notification.data?.url || '/';

        event.waitUntil(
            clients.matchAll({ type: 'window', includeUncontrolled: true })
                .then((windowClients) => {
                    for (let client of windowClients) {
                        if (client.url === urlToOpen && 'focus' in client) {
                            return client.focus();
                        }
                    }
                    
                    if (clients.openWindow) {
                        return clients.openWindow(urlToOpen);
                    }
                })
        );
    });

    console.log('✅ [Service Worker] Firebase Messaging inicializado com sucesso');
    
} catch (error) {
    console.error('❌ [Service Worker] Erro ao inicializar Firebase:', error);
}

self.addEventListener('push', (event) => {
    console.log('📬 [Service Worker] Push event recebido:', event);
    
    if (!event.data) {
        console.warn('⚠️ [Service Worker] Push event sem dados');
        return;
    }

    try {
        const data = event.data.json();
        const { title, body, icon, tag, url } = data;

        const options = {
            body: body || 'Nova mensagem',
            icon: icon || '/static/img/logo-elp.png',
            badge: '/static/img/badge-icon.png',
            tag: tag || 'elp-notification',
            data: { url: url || '/' },
            vibrate: [200, 100, 200]
        };

        event.waitUntil(
            self.registration.showNotification(title || 'ELP Consultoria', options)
        );
    } catch (error) {
        console.error('❌ [Service Worker] Erro ao processar push event:', error);
    }
});

console.log('🔥 [Service Worker] Firebase Messaging Service Worker carregado');
