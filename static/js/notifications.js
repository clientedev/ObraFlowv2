// Sistema de Notificações Push
class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
        this.permission = this.isSupported ? Notification.permission : 'denied';
        this.subscriptionKey = null;
        this.currentPosition = null;
        this.watchId = null;
        this.nearbyProjects = [];
        this.notifiedProjects = new Set();
        
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.log('Notificações não suportadas neste navegador');
            return;
        }

        // Verificar se há uma subscription ativa
        await this.checkExistingSubscription();
        
        // Iniciar monitoramento de localização se permitido
        this.startLocationMonitoring();
        
        // Verificar novidades periodicamente
        this.startPeriodicCheck();
    }

    async requestPermission() {
        if (!this.isSupported) {
            throw new Error('Notificações não suportadas');
        }

        if (this.permission === 'granted') {
            return true;
        }

        const permission = await Notification.requestPermission();
        this.permission = permission;
        
        if (permission === 'granted') {
            await this.subscribeToPush();
            this.showWelcomeNotification();
            return true;
        }
        
        return false;
    }

    async subscribeToPush() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Verificar se já existe uma subscription
            let subscription = await registration.pushManager.getSubscription();
            
            if (!subscription) {
                // Criar nova subscription
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(this.getVapidPublicKey())
                });
            }
            
            // Enviar subscription para o servidor
            await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    user_agent: navigator.userAgent
                })
            });
            
            this.subscriptionKey = subscription;
            console.log('Push subscription criada:', subscription);
            
        } catch (error) {
            console.error('Erro ao criar push subscription:', error);
            throw error;
        }
    }

    async checkExistingSubscription() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                this.subscriptionKey = subscription;
                console.log('Push subscription existente encontrada');
            }
        } catch (error) {
            console.error('Erro ao verificar subscription:', error);
        }
    }

    startLocationMonitoring() {
        if (!navigator.geolocation) {
            console.log('Geolocalização não suportada');
            return;
        }

        // Solicitar permissão de localização
        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.currentPosition = position;
                this.checkNearbyProjects();
                
                // Monitorar mudanças de localização
                this.watchId = navigator.geolocation.watchPosition(
                    (newPosition) => {
                        this.currentPosition = newPosition;
                        this.checkNearbyProjects();
                    },
                    (error) => {
                        console.log('Erro de geolocalização:', error);
                    },
                    {
                        enableHighAccuracy: false,
                        timeout: 60000,
                        maximumAge: 300000 // 5 minutos
                    }
                );
            },
            (error) => {
                console.log('Geolocalização negada ou erro:', error);
            }
        );
    }

    async checkNearbyProjects() {
        if (!this.currentPosition) return;

        try {
            const lat = this.currentPosition.coords.latitude;
            const lon = this.currentPosition.coords.longitude;
            const response = await fetch(`/api/nearby-projects?lat=${lat}&lon=${lon}&radius=1`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.nearbyProjects = data.projects || [];
                
                // Verificar projetos próximos não notificados
                this.nearbyProjects.forEach(project => {
                    if (!this.notifiedProjects.has(project.id) && project.distance < 500) {
                        this.showProximityNotification(project);
                        this.notifiedProjects.add(project.id);
                    }
                });
            }
        } catch (error) {
            console.error('Erro ao verificar projetos próximos:', error);
        }
    }

    startPeriodicCheck() {
        // Verificar novidades a cada 30 minutos
        setInterval(() => {
            this.checkForUpdates();
        }, 30 * 60 * 1000);

        // Verificar imediatamente
        this.checkForUpdates();
    }

    async checkForUpdates() {
        try {
            const response = await fetch('/api/notifications/check-updates');
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.has_updates) {
                    data.updates.forEach(update => {
                        this.showUpdateNotification(update);
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao verificar atualizações:', error);
        }
    }

    showWelcomeNotification() {
        if (this.permission === 'granted') {
            new Notification('ELP Relatórios', {
                body: 'Notificações ativadas! Você será avisado sobre obras próximas e novidades.',
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png'
            });
        }
    }

    showProximityNotification(project) {
        if (this.permission === 'granted') {
            new Notification('Obra Próxima Detectada', {
                body: `Você está próximo da obra: ${project.nome}\nDistância: ${Math.round(project.distance)}m`,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                vibrate: [200, 100, 200],
                data: { 
                    type: 'proximity', 
                    project_id: project.id,
                    url: `/projects/${project.id}`
                }
            });
        }
    }

    showUpdateNotification(update) {
        if (this.permission === 'granted') {
            new Notification(update.title || 'Novidade no App', {
                body: update.message,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                data: { 
                    type: 'update', 
                    update_id: update.id,
                    url: update.url || '/'
                }
            });
        }
    }

    // Utilitários
    getVapidPublicKey() {
        // Chave pública VAPID (deve ser configurada no servidor)
        return 'BEl62iUYgUivxIkv69yViEuiBIa40HI0staDiGnwSiGcC0K7QkU6g8R6T6I8O2fZllh7Z8i3K8E6NjwL5Q2v0G8';
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    // Desativar notificações
    async unsubscribe() {
        try {
            if (this.subscriptionKey) {
                await this.subscriptionKey.unsubscribe();
                
                // Informar o servidor
                await fetch('/api/notifications/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });
                
                this.subscriptionKey = null;
            }
            
            if (this.watchId) {
                navigator.geolocation.clearWatch(this.watchId);
                this.watchId = null;
            }
            
            console.log('Notificações desativadas');
        } catch (error) {
            console.error('Erro ao desativar notificações:', error);
        }
    }
}

// Inicializar gerenciador de notificações
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    notificationManager = new NotificationManager();
    
    // Expor globalmente para uso em outros scripts
    window.notificationManager = notificationManager;
});

// Interface para ativar/desativar notificações
function toggleNotifications() {
    if (notificationManager.permission === 'granted') {
        notificationManager.unsubscribe();
        return false;
    } else {
        return notificationManager.requestPermission();
    }
}