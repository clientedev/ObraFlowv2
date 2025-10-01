
// Sistema de Notificações Push - Versão Robusta com Debug Completo
class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
        this.permission = this.isSupported ? Notification.permission : 'denied';
        this.subscriptionKey = null;
        this.currentPosition = null;
        this.watchId = null;
        this.nearbyProjects = [];
        this.notifiedProjects = new Set();
        this.swRegistration = null;

        console.log('🔔 NOTIFICATIONS: Inicializando sistema de notificações');
        console.log('🔔 NOTIFICATIONS: Suporte:', this.isSupported ? 'SIM' : 'NÃO');
        console.log('🔔 NOTIFICATIONS: Permissão atual:', this.permission);

        this.init();
    }

    async init() {
        console.log('🔔 NOTIFICATIONS: Inicializando sistema de notificações');
        console.log('🔔 NOTIFICATIONS: Suporte:', this.isSupported ? 'SIM' : 'NÃO');
        console.log('🔔 NOTIFICATIONS: Permissão atual:', Notification.permission);

        if (!this.isSupported) {
            console.warn('⚠️ NOTIFICATIONS: Navegador não suporta notificações');
            return;
        }

        this.permission = Notification.permission;

        // Register service worker for push notifications
        await this.registerServiceWorker();

        // AUTO-DETECTAR E FORÇAR PERMISSÕES SE NECESSÁRIO
        await this.autoCheckPermissions();

        // Make the manager globally available
        window.notificationManager = this;
        console.log('✅ NOTIFICATIONS: Gerenciador disponível globalmente');
    }

    async registerServiceWorker() {
        try {
            console.log('🔧 NOTIFICATIONS: Registrando service worker...');

            if ('serviceWorker' in navigator) {
                // Tentar obter registration existente
                this.swRegistration = await navigator.serviceWorker.getRegistration();

                if (!this.swRegistration) {
                    console.log('📦 NOTIFICATIONS: Registrando service worker...');
                    this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js');
                    console.log('✅ NOTIFICATIONS: Service worker registrado');
                } else {
                    console.log('✅ NOTIFICATIONS: Service worker já registrado');
                }

                // Aguardar estar pronto
                await navigator.serviceWorker.ready;
                console.log('✅ NOTIFICATIONS: Service worker pronto');
            }
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao configurar service worker:', error);
            // Não fazer throw aqui para continuar funcionando sem push notifications
        }
    }

    async autoCheckPermissions() {
        console.log('🔍 NOTIFICATIONS: Auto-verificando permissões...');

        // Verificar se já temos as duas permissões
        const notificationStatus = Notification.permission;
        const hasLocationAccess = await this.checkLocationAccess();

        console.log('📊 AUTO-CHECK: Notificação:', notificationStatus, '| Localização:', hasLocationAccess);

        // Se não temos localização, mostrar aviso proativo
        if (!hasLocationAccess) {
            console.log('⚠️ AUTO-CHECK: Localização não disponível - usuário precisa ativar');
            // Não forçar agora, apenas logar
        }

        // Se não temos notificação, mostrar aviso proativo  
        if (notificationStatus === 'default') {
            console.log('⚠️ AUTO-CHECK: Notificação em default - usuário precisa ativar');
            // Não forçar agora, apenas logar
        }
    }

    async checkLocationAccess() {
        if (!navigator.geolocation) {
            return false;
        }

        try {
            // Teste rápido e silencioso se já temos acesso
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    resolve,
                    reject,
                    { enableHighAccuracy: false, timeout: 1000, maximumAge: 60000 }
                );
            });
            return true;
        } catch (error) {
            return false;
        }
    }

    async ensureServiceWorker() {
        try {
            console.log('🔧 NOTIFICATIONS: Verificando service worker...');

            if ('serviceWorker' in navigator) {
                // Tentar obter registration existente
                this.swRegistration = await navigator.serviceWorker.getRegistration();

                if (!this.swRegistration) {
                    console.log('📦 NOTIFICATIONS: Registrando service worker...');
                    this.swRegistration = await navigator.serviceWorker.register('/static/js/sw.js');
                    console.log('✅ NOTIFICATIONS: Service worker registrado');
                } else {
                    console.log('✅ NOTIFICATIONS: Service worker já registrado');
                }

                // Aguardar estar pronto
                await navigator.serviceWorker.ready;
                console.log('✅ NOTIFICATIONS: Service worker pronto');
            }
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao configurar service worker:', error);
            throw error;
        }
    }

    async checkPermissionStatus() {
        console.log('🔍 NOTIFICATIONS: Verificando status da permissão...');

        const status = Notification.permission;
        this.permission = status;

        console.log(`📊 NOTIFICATIONS: Status = "${status}"`);

        return {
            granted: status === 'granted',
            denied: status === 'denied',
            default: status === 'default',
            canAsk: status === 'default',
            needsManualEnable: status === 'denied'
        };
    }

    async requestLocationPermission() {
        console.log('📍 NOTIFICATIONS: Solicitando permissão de localização...');

        if (!navigator.geolocation) {
            console.warn('⚠️ NOTIFICATIONS: Geolocalização não suportada');
            return false;
        }

        try {
            // MOBILE: Forçar prompt de localização IMEDIATAMENTE
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    resolve,
                    reject,
                    { 
                        enableHighAccuracy: true, 
                        timeout: 15000, 
                        maximumAge: 0 // Sempre pedir permissão fresca
                    }
                );
            });

            console.log('✅ NOTIFICATIONS: Permissão de localização concedida');
            return true;
        } catch (error) {
            console.warn('🚫 NOTIFICATIONS: Permissão de localização negada:', error.message);

            this.showUserMessage(
                'Localização Necessária',
                'Para receber alertas de obras próximas, é necessário permitir o acesso à sua localização.',
                'warning',
                8000
            );

            return false;
        }
    }

    async forceLocationPermission() {
        console.log('📍 NOTIFICATIONS: Forçando prompt de permissão de localização...');

        if (!navigator.geolocation) {
            console.warn('⚠️ NOTIFICATIONS: Geolocalização não suportada');
            return false;
        }

        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    resolve,
                    reject,
                    { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 } // Tentar obter com alta precisão para garantir o prompt
                );
            });

            console.log('✅ NOTIFICATIONS: Prompt de localização ativado e concedido');
            return true;
        } catch (error) {
            console.warn('🚫 NOTIFICATIONS: Prompt de localização negado ou falhou:', error.message);
            return false;
        }
    }

    async requestPermission() {
        console.log('🔔 NOTIFICATIONS: Solicitando permissões...');

        if (!this.isSupported) {
            const error = 'Notificações não suportadas neste navegador';
            console.error('❌ NOTIFICATIONS:', error);
            this.showUserMessage('Notificações não disponíveis', 'Seu navegador não suporta notificações push.', 'warning');
            throw new Error(error);
        }

        // MOBILE FIX: Detectar se é mobile e ajustar comportamento
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        console.log('📱 MOBILE DETECTED:', isMobile);

        try {
            // 1. PRIMEIRO: Solicitar permissão de LOCALIZAÇÃO com timeout maior para mobile
            console.log('📍 NOTIFICATIONS: Passo 1/2 - Solicitando permissão de localização...');

            const hasLocation = await this.requestLocationPermissionMobile();

            if (!hasLocation) {
                this.showUserMessage(
                    'Permissão de Localização Necessária',
                    'Para receber alertas de obras próximas, é necessário permitir o acesso à sua localização.',
                    'warning',
                    8000
                );
                return false;
            }

            console.log('✅ NOTIFICATIONS: Localização permitida, verificando notificações...');

            // Small delay for mobile to process location permission
            if (isMobile) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao solicitar localização:', error);
            this.showUserMessage(
                'Erro de Localização',
                'Não foi possível obter permissão de localização. Verifique as configurações do seu navegador.',
                'error',
                6000
            );
            return false;
        }

        // Agora verificar status de notificação
        const status = await this.checkPermissionStatus();
        console.log('📊 NOTIFICATIONS: Status de notificação:', status);

        // Se já concedido, apenas configurar
        if (status.granted) {
            console.log('✅ NOTIFICATIONS: Permissão de notificação já concedida');
            await this.setupNotifications();
            return true;
        }

        // Se negado, orientar usuário
        if (status.denied) {
            console.warn('🚫 NOTIFICATIONS: Permissão de notificação negada anteriormente');
            this.showDeniedInstructions();
            return false;
        }

        // Se default, pedir permissão de NOTIFICAÇÃO
        if (status.canAsk) {
            try {
                // 2. SEGUNDO: Solicitar permissão de NOTIFICAÇÃO
                console.log('🔔 NOTIFICATIONS: Passo 2/2 - Solicitando permissão de notificação...');
                const permission = await Notification.requestPermission();
                this.permission = permission;

                console.log('📊 NOTIFICATIONS: Resposta do usuário:', permission);

                if (permission === 'granted') {
                    console.log('✅ NOTIFICATIONS: AMBAS permissões concedidas!');
                    await this.setupNotifications();
                    return true;
                } else if (permission === 'denied') {
                    console.warn('🚫 NOTIFICATIONS: Permissão de notificação negada pelo usuário');
                    this.showDeniedInstructions();
                    return false;
                } else {
                    console.warn('⚠️ NOTIFICATIONS: Permissão ignorada/fechada');
                    return false;
                }
            } catch (error) {
                console.error('❌ NOTIFICATIONS: Erro ao solicitar notificação:', error);
                this.showUserMessage('Erro', 'Erro ao solicitar permissão de notificação.', 'error');
                throw error;
            }
        }

        return false;
    }

    async requestLocationPermissionMobile() {
        console.log('📍 MOBILE: Solicitando permissão de localização específica para mobile...');

        if (!navigator.geolocation) {
            console.warn('⚠️ MOBILE: Geolocalização não suportada');
            return false;
        }

        return new Promise((resolve) => {
            // Timeout maior para mobile
            const timeout = setTimeout(() => {
                console.warn('⏰ MOBILE: Timeout ao solicitar localização');
                resolve(false);
            }, 20000);

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    clearTimeout(timeout);
                    console.log('✅ MOBILE: Permissão de localização concedida');
                    resolve(true);
                },
                (error) => {
                    clearTimeout(timeout);
                    console.warn('🚫 MOBILE: Permissão de localização negada:', error.message);
                    
                    // Mostrar instruções específicas para mobile
                    this.showMobileLocationInstructions();
                    resolve(false);
                },
                { 
                    enableHighAccuracy: true, 
                    timeout: 18000,
                    maximumAge: 0 // Sempre pedir permissão fresca
                }
            );
        });
    }

    showMobileLocationInstructions() {
        const instructions = `
            <div class="text-start">
                <p><strong>📱 Como permitir localização no mobile:</strong></p>
                <ol>
                    <li>Toque no ícone <strong>🔒</strong> na barra de endereço</li>
                    <li>Procure por <strong>"Localização"</strong> ou <strong>"Location"</strong></li>
                    <li>Altere para <strong>"Permitir"</strong> ou <strong>"Allow"</strong></li>
                    <li>Recarregue a página e tente novamente</li>
                </ol>
                <p><small>💡 <strong>Dica:</strong> Em alguns navegadores mobile, a permissão pode aparecer como uma notificação no topo da tela.</small></p>
            </div>
        `;

        this.showUserMessage(
            'Instruções para Mobile',
            instructions,
            'info',
            12000
        );
    }

    async setupNotifications() {
        try {
            console.log('⚙️ NOTIFICATIONS: Configurando notificações...');

            // 1. Garantir service worker
            await this.ensureServiceWorker();
            console.log('✅ NOTIFICATIONS: Service worker OK');

            // 2. Fazer subscription
            await this.subscribeToPush();
            console.log('✅ NOTIFICATIONS: Subscription criada');

            // 3. Mostrar notificação de boas-vindas
            this.showWelcomeNotification();
            console.log('✅ NOTIFICATIONS: Boas-vindas exibida');

            // 4. Iniciar monitoramento
            this.startLocationMonitoring();
            this.startPeriodicCheck();
            console.log('✅ NOTIFICATIONS: Monitoramento iniciado');

            // 5. Mensagem de sucesso ao usuário
            this.showUserMessage(
                'Notificações Ativadas!',
                'Você receberá alertas sobre obras próximas e novidades do sistema.',
                'success'
            );

        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao configurar:', error);
            this.showUserMessage(
                'Erro ao Ativar Notificações',
                'Ocorreu um erro ao configurar as notificações. Tente novamente.',
                'danger'
            );
            throw error;
        }
    }

    async subscribeToPush() {
        try {
            console.log('📡 NOTIFICATIONS: Iniciando subscription push...');

            if (!this.swRegistration) {
                await this.ensureServiceWorker();
            }

            // Verificar se já existe uma subscription
            let subscription = await this.swRegistration.pushManager.getSubscription();

            if (subscription) {
                console.log('✅ NOTIFICATIONS: Subscription existente encontrada');
                this.subscriptionKey = subscription;
            } else {
                console.log('📡 NOTIFICATIONS: Criando nova subscription...');

                // Criar nova subscription
                subscription = await this.swRegistration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(this.getVapidPublicKey())
                });

                console.log('✅ NOTIFICATIONS: Nova subscription criada');
                this.subscriptionKey = subscription;
            }

            // Obter localização atual (obrigatória para notificações de proximidade)
            console.log('📍 NOTIFICATIONS: Obtendo localização para registro...');
            let locationData = null;

            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(
                        resolve,
                        reject,
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                });

                locationData = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };

                console.log('✅ NOTIFICATIONS: Localização obtida para registro:', locationData);
            } catch (locationError) {
                console.error('❌ NOTIFICATIONS: Erro ao obter localização:', locationError);
                this.showUserMessage(
                    'Localização Necessária',
                    'É obrigatório permitir acesso à localização para ativar notificações de proximidade.',
                    'warning',
                    8000
                );
                throw new Error('Localização é obrigatória para ativar notificações');
            }

            // Enviar subscription para o servidor COM localização
            console.log('📤 NOTIFICATIONS: Enviando subscription ao servidor...');
            const response = await fetch('/api/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON(),
                    user_agent: navigator.userAgent,
                    timestamp: new Date().toISOString(),
                    location: locationData
                })
            });

            if (response.ok) {
                console.log('✅ NOTIFICATIONS: Subscription registrada no servidor');
            } else {
                const errorData = await response.json();
                console.warn('⚠️ NOTIFICATIONS: Falha ao registrar no servidor:', response.status, errorData);
                throw new Error(errorData.error || 'Falha ao registrar notificações');
            }

        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao criar push subscription:', error);
            console.error('❌ NOTIFICATIONS: Detalhes do erro:', error.message, error.stack);
            throw error;
        }
    }

    async checkExistingSubscription() {
        try {
            console.log('🔍 NOTIFICATIONS: Verificando subscription existente...');

            if (!this.swRegistration) {
                await this.ensureServiceWorker();
            }

            const subscription = await this.swRegistration.pushManager.getSubscription();

            if (subscription) {
                this.subscriptionKey = subscription;
                console.log('✅ NOTIFICATIONS: Subscription ativa encontrada');
                console.log('📊 NOTIFICATIONS: Endpoint:', subscription.endpoint);
            } else {
                console.log('ℹ️ NOTIFICATIONS: Nenhuma subscription ativa');
            }
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao verificar subscription:', error);
        }
    }

    startLocationMonitoring() {
        if (!window.geoLocation) {
            console.warn('⚠️ NOTIFICATIONS: Sistema de geolocalização não disponível');
            return;
        }

        console.log('📍 NOTIFICATIONS: Iniciando monitoramento de localização com sistema avançado...');

        // Usar o sistema de geolocalização avançado com fallback para IP
        window.geoLocation.getLocation({
            enableHighAccuracy: false,
            timeout: 30000,
            maximumAge: 300000,
            showUI: false,  // Não mostrar UI para notificações em background
            fallbackToIP: true,  // Usar IP se GPS falhar
            reverseGeocode: false  // Não precisa de endereço para notificações
        })
        .then((position) => {
            this.currentPosition = position;
            console.log('📍 NOTIFICATIONS: Localização inicial obtida:', {
                lat: position.coords.latitude,
                lon: position.coords.longitude,
                source: position.source || 'gps'
            });
            this.checkNearbyProjects();

            // Monitorar mudanças de localização com sistema avançado
            this.watchId = window.geoLocation.watchLocation(
                (newPosition, error) => {
                    if (error) {
                        console.warn('⚠️ NOTIFICATIONS: Erro no monitoramento:', error.message);
                        return;
                    }

                    if (newPosition) {
                        this.currentPosition = newPosition;
                        console.log('📍 NOTIFICATIONS: Localização atualizada');
                        this.checkNearbyProjects();
                    }
                },
                {
                    enableHighAccuracy: false,
                    timeout: 60000,
                    maximumAge: 300000
                }
            );
            console.log('✅ NOTIFICATIONS: Watch position ativo (ID:', this.watchId, ')');
        })
        .catch((error) => {
            console.warn('⚠️ NOTIFICATIONS: Não foi possível obter localização:', error.message);
            // Mostrar erro ao usuário com instruções
            this.showUserMessage(
                'Erro de Localização',
                'Não foi possível obter sua localização. Verifique as permissões do GPS.',
                'warning',
                3000
            );
        });
    }

    async checkNearbyProjects() {
        if (!this.currentPosition) return;

        try {
            const lat = this.currentPosition.coords.latitude;
            const lon = this.currentPosition.coords.longitude;

            console.log(`🔍 NOTIFICATIONS: Buscando obras próximas (${lat.toFixed(4)}, ${lon.toFixed(4)})`);

            const response = await fetch(`/api/nearby-projects?lat=${lat}&lon=${lon}&radius=1`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.nearbyProjects = data.projects || [];

                console.log(`📊 NOTIFICATIONS: ${this.nearbyProjects.length} obra(s) próxima(s)`);

                this.nearbyProjects.forEach(project => {
                    if (!this.notifiedProjects.has(project.id) && project.distance < 500) {
                        console.log(`🔔 NOTIFICATIONS: Notificando obra próxima: ${project.nome}`);
                        this.showProximityNotification(project);
                        this.notifiedProjects.add(project.id);
                    }
                });
            }
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao verificar projetos próximos:', error);
        }
    }

    startPeriodicCheck() {
        console.log('⏰ NOTIFICATIONS: Iniciando verificação periódica de atualizações');

        // Verificar a cada 30 minutos
        setInterval(() => {
            console.log('⏰ NOTIFICATIONS: Executando verificação periódica...');
            this.checkForUpdates();
        }, 30 * 60 * 1000);

        // Verificar imediatamente
        this.checkForUpdates();
    }

    async checkForUpdates() {
        try {
            console.log('🔍 NOTIFICATIONS: Verificando atualizações...');

            const response = await fetch('/api/notifications/check-updates');

            if (response.ok) {
                const data = await response.json();

                if (data.has_updates) {
                    console.log(`📬 NOTIFICATIONS: ${data.updates.length} atualização(ões) encontrada(s)`);
                    data.updates.forEach(update => {
                        this.showUpdateNotification(update);
                    });
                } else {
                    console.log('ℹ️ NOTIFICATIONS: Nenhuma atualização');
                }
            }
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao verificar atualizações:', error);
        }
    }

    showWelcomeNotification() {
        if (this.permission === 'granted') {
            console.log('🎉 NOTIFICATIONS: Exibindo boas-vindas');

            new Notification('ELP Relatórios', {
                body: 'Notificações ativadas! Você será avisado sobre obras próximas e novidades.',
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                tag: 'welcome'
            });
        }
    }

    showProximityNotification(project) {
        if (this.permission === 'granted') {
            console.log(`📍 NOTIFICATIONS: Exibindo alerta de proximidade: ${project.nome}`);

            new Notification('Obra Próxima Detectada', {
                body: `Você está próximo da obra: ${project.nome}\nDistância: ${Math.round(project.distance)}m`,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                vibrate: [200, 100, 200],
                tag: `proximity-${project.id}`,
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
            console.log(`📢 NOTIFICATIONS: Exibindo atualização: ${update.title}`);

            new Notification(update.title || 'Novidade no App', {
                body: update.message,
                icon: '/static/icons/icon-192x192.png',
                badge: '/static/icons/icon-96x96.png',
                tag: `update-${update.id}`,
                data: { 
                    type: 'update', 
                    update_id: update.id,
                    url: update.url || '/'
                }
            });
        }
    }

    showDeniedInstructions() {
        const instructions = this.getBrowserInstructions();

        this.showUserMessage(
            'Notificações Bloqueadas',
            `<p>As notificações foram bloqueadas anteriormente. Para ativá-las:</p>${instructions}`,
            'warning',
            10000
        );
    }

    getBrowserInstructions() {
        const userAgent = navigator.userAgent.toLowerCase();

        if (userAgent.includes('chrome')) {
            return `
                <ol class="text-start">
                    <li>Clique no ícone <strong>🔒</strong> ao lado da URL</li>
                    <li>Procure por <strong>"Notificações"</strong></li>
                    <li>Altere para <strong>"Permitir"</strong></li>
                    <li>Recarregue a página</li>
                </ol>
            `;
        } else if (userAgent.includes('firefox')) {
            return `
                <ol class="text-start">
                    <li>Clique no ícone <strong>🔒</strong> ao lado da URL</li>
                    <li>Clique em <strong>"Limpar Permissões"</strong></li>
                    <li>Recarregue e permita notificações novamente</li>
                </ol>
            `;
        } else if (userAgent.includes('safari')) {
            return `
                <ol class="text-start">
                    <li>Abra <strong>Preferências do Safari</strong></li>
                    <li>Vá em <strong>"Sites"</strong> → <strong>"Notificações"</strong></li>
                    <li>Encontre este site e altere para <strong>"Permitir"</strong></li>
                </ol>
            `;
        } else {
            return `
                <ol class="text-start">
                    <li>Acesse as configurações do navegador</li>
                    <li>Procure por "Notificações" ou "Permissões"</li>
                    <li>Encontre este site e permita notificações</li>
                    <li>Recarregue a página</li>
                </ol>
            `;
        }
    }

    showUserMessage(title, message, type = 'info', duration = 5000) {
        // Remover mensagens anteriores
        const existing = document.querySelector('.notification-user-message');
        if (existing) existing.remove();

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show notification-user-message`;
        alertDiv.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            min-width: 320px;
            max-width: 450px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        alertDiv.innerHTML = `
            <strong>${title}</strong><br>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alertDiv);

        if (duration > 0) {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, duration);
        }
    }

    // Utilitários
    getVapidPublicKey() {
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
            console.log('🔕 NOTIFICATIONS: Desativando notificações...');

            if (this.subscriptionKey) {
                await this.subscriptionKey.unsubscribe();
                console.log('✅ NOTIFICATIONS: Subscription removida');

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

            if (this.watchId && window.geoLocation) {
                window.geoLocation.stopWatching(this.watchId);
                this.watchId = null;
                console.log('✅ NOTIFICATIONS: Monitoramento de localização parado');
            }

            this.showUserMessage(
                'Notificações Desativadas',
                'Você não receberá mais alertas de proximidade e novidades.',
                'info'
            );

            console.log('✅ NOTIFICATIONS: Notificações desativadas completamente');
        } catch (error) {
            console.error('❌ NOTIFICATIONS: Erro ao desativar:', error);
        }
    }
}

// Inicializar gerenciador de notificações
let notificationManager;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 NOTIFICATIONS: DOM carregado, inicializando...');
    notificationManager = new NotificationManager();

    // Expor globalmente
    window.notificationManager = notificationManager;
    console.log('✅ NOTIFICATIONS: Gerenciador disponível globalmente');
});

// Interface para ativar/desativar notificações
async function toggleNotifications() {
    console.log('🔄 NOTIFICATIONS: Toggle solicitado');

    if (notificationManager.permission === 'granted') {
        console.log('🔕 NOTIFICATIONS: Desativando (já concedido)');
        await notificationManager.unsubscribe();
        return false;
    } else {
        console.log('🔔 NOTIFICATIONS: Ativando (não concedido)');
        return await notificationManager.requestPermission();
    }
}
