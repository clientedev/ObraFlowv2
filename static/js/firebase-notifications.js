/**
 * Firebase Cloud Messaging (FCM) - Push Notifications
 * Sistema de Push Notifications Externas para ELP Consultoria
 * 
 * USO: Incluir este script após configurar firebaseConfig no HTML
 * 
 * Exemplo:
 * <script type="module">
 *   import FirebaseNotificationsManager from '/static/js/firebase-notifications.js';
 *   
 *   const firebaseConfig = {
 *     apiKey: "...",
 *     authDomain: "...",
 *     projectId: "...",
 *     // ...
 *   };
 *   
 *   const fcmManager = new FirebaseNotificationsManager();
 *   await fcmManager.initialize(firebaseConfig);
 *   await fcmManager.requestPermissionAndGetToken('YOUR_VAPID_KEY');
 * </script>
 */

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";
import { getMessaging, getToken, onMessage } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js";

class FirebaseNotificationsManager {
    constructor() {
        this.app = null;
        this.messaging = null;
        this.currentToken = null;
        this.isInitialized = false;
        
        console.log('🔥 Firebase Notifications Manager - Inicializando...');
    }

    /**
     * Inicializar Firebase com configuração do servidor
     */
    async initialize(firebaseConfig) {
        try {
            if (this.isInitialized) {
                console.log('✅ Firebase já inicializado');
                return true;
            }

            if (!firebaseConfig) {
                console.error('❌ Firebase config não fornecida');
                return false;
            }

            console.log('🔧 Inicializando Firebase App...');
            this.app = initializeApp(firebaseConfig);
            this.messaging = getMessaging(this.app);
            
            this.isInitialized = true;
            console.log('✅ Firebase App inicializado com sucesso');
            
            await this.setupMessageListener();
            
            return true;
        } catch (error) {
            console.error('❌ Erro ao inicializar Firebase:', error);
            return false;
        }
    }

    /**
     * Configurar listener para mensagens quando app está aberto
     */
    async setupMessageListener() {
        try {
            onMessage(this.messaging, (payload) => {
                console.log('📬 Mensagem FCM recebida (app aberto):', payload);
                
                const { title, body } = payload.notification || {};
                
                if (title && body) {
                    this.showNotification(title, body, payload.data);
                }
            });
            
            console.log('✅ Message listener configurado');
        } catch (error) {
            console.error('❌ Erro ao configurar message listener:', error);
        }
    }

    /**
     * Solicitar permissão e obter FCM token
     */
    async requestPermissionAndGetToken(vapidKey) {
        try {
            if (!this.isInitialized) {
                console.error('❌ Firebase não inicializado');
                return null;
            }

            if (!vapidKey) {
                console.error('❌ VAPID Key não fornecida');
                return null;
            }

            console.log('🔔 Solicitando permissão de notificações...');
            
            // Check if permission is already denied
            if (Notification.permission === 'denied') {
                console.warn('⚠️ Permissão de notificações negada anteriormente.');
                alert('As notificações estão bloqueadas nas configurações do seu navegador. Para ativar:\n\n1. Clique no ícone de "Cadeado" ou "Configurações" na barra de endereços (ao lado do link do site).\n2. Mude a opção "Notificações" para "Permitir".\n3. Recarregue a página.');
                return null;
            }
            
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('✅ Permissão concedida');
                
                console.log('🔑 Obtendo FCM token...');
                const token = await getToken(this.messaging, { vapidKey: vapidKey });
                
                if (token) {
                    console.log('✅ FCM Token obtido:', token.substring(0, 20) + '...');
                    this.currentToken = token;
                    
                    await this.sendTokenToServer(token);
                    
                    return token;
                } else {
                    console.warn('⚠️ Nenhum token FCM disponível');
                    return null;
                }
            } else if (permission === 'denied') {
                console.warn('⚠️ Permissão de notificações negada pelo usuário');
                return null;
            } else {
                console.warn('⚠️ Permissão de notificações em default');
                return null;
            }
        } catch (error) {
            console.error('❌ Erro ao obter FCM token:', error);
            
            if (error.code === 'messaging/permission-blocked') {
                console.error('🚫 Notificações bloqueadas pelo navegador');
            }
            
            return null;
        }
    }

    /**
     * Enviar token para o servidor
     */
    async sendTokenToServer(token) {
        try {
            console.log('📤 Enviando token para servidor...');
            
            const response = await fetch('/api/update_fcm_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ fcm_token: token })
            });

            const data = await response.json();
            
            if (response.ok && data.success) {
                console.log('✅ Token salvo no servidor com sucesso');
                return true;
            } else {
                console.error('❌ Erro ao salvar token no servidor:', data);
                return false;
            }
        } catch (error) {
            console.error('❌ Erro ao enviar token para servidor:', error);
            return false;
        }
    }

    /**
     * Mostrar notificação no navegador
     */
    showNotification(title, body, data = {}) {
        try {
            if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification(title, {
                    body: body,
                    icon: '/static/img/logo-elp.png',
                    badge: '/static/img/badge-icon.png',
                    tag: data.tag || 'elp-notification',
                    requireInteraction: false,
                    data: data
                });

                notification.onclick = function(event) {
                    event.preventDefault();
                    
                    if (data.url) {
                        window.open(data.url, '_blank');
                    }
                    
                    notification.close();
                };

                console.log('✅ Notificação exibida:', title);
            }
        } catch (error) {
            console.error('❌ Erro ao exibir notificação:', error);
        }
    }

    /**
     * Verificar se notificações estão habilitadas
     */
    isNotificationEnabled() {
        return 'Notification' in window && Notification.permission === 'granted';
    }

    /**
     * Obter status da permissão
     */
    getPermissionStatus() {
        if (!('Notification' in window)) {
            return 'unsupported';
        }
        return Notification.permission;
    }

    /**
     * Deletar token FCM
     */
    async deleteToken() {
        try {
            if (this.messaging) {
                const { deleteToken } = await import("https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js");
                await deleteToken(this.messaging);
                this.currentToken = null;
                console.log('✅ Token FCM deletado');
                return true;
            }
            return false;
        } catch (error) {
            console.error('❌ Erro ao deletar token:', error);
            return false;
        }
    }
}

window.FirebaseNotificationsManager = FirebaseNotificationsManager;

export default FirebaseNotificationsManager;
