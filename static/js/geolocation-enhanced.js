/**
 * Sistema de Geolocalização Avançado
 * - Tratamento robusto de erros
 * - Fallback para IP quando GPS falha
 * - HTTPS enforcement
 * - Reverse geocoding
 * - Mensagens claras para o usuário
 */

class EnhancedGeolocation {
    constructor() {
        this.currentPosition = null;
        this.fallbackUsed = false;
        this.isHTTPS = window.location.protocol === 'https:';
        
        console.log('🌍 GEOLOCALIZAÇÃO: Sistema inicializado');
        console.log('🔒 HTTPS:', this.isHTTPS ? 'SIM' : 'NÃO');
        
        // Avisar se não estiver em HTTPS
        if (!this.isHTTPS && window.location.hostname !== 'localhost') {
            this.showWarning('⚠️ Geolocalização pode não funcionar em HTTP. Use HTTPS.');
        }
    }

    /**
     * Verificar status da permissão de geolocalização
     */
    async checkPermission() {
        try {
            // Tentar usar a API de Permissions (não suportada em todos os navegadores)
            if ('permissions' in navigator) {
                const permission = await navigator.permissions.query({ name: 'geolocation' });
                console.log('🔐 PERMISSÃO: Status atual:', permission.state);
                
                // Configurar listener para mudanças na permissão
                permission.onchange = () => {
                    console.log('🔐 PERMISSÃO: Mudou para:', permission.state);
                    if (permission.state === 'granted') {
                        console.log('✅ PERMISSÃO: Concedida! Capturando localização automaticamente...');
                        // Reagir à mudança de permissão capturando localização
                        this.getLocation({
                            enableHighAccuracy: true,
                            timeout: 15000,
                            maximumAge: 0,
                            showUI: true,
                            fallbackToIP: true,
                            reverseGeocode: true
                        }).catch(error => {
                            console.error('❌ Erro ao capturar localização após permissão concedida:', error);
                        });
                    }
                };
                
                return permission.state; // 'granted', 'prompt', ou 'denied'
            }
            
            // Fallback se a API de Permissions não estiver disponível
            console.log('⚠️ PERMISSÃO: API não disponível, tentando geolocalização diretamente');
            return 'prompt'; // Assume que precisará solicitar
            
        } catch (error) {
            console.warn('⚠️ PERMISSÃO: Erro ao verificar:', error);
            return 'prompt'; // Em caso de erro, assume que precisará solicitar
        }
    }

    /**
     * Obter localização com fallback automático
     */
    async getLocation(options = {}) {
        const defaultOptions = {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0,  // Sempre pegar localização fresca
            showUI: true,
            fallbackToIP: true,
            reverseGeocode: true
        };

        const config = { ...defaultOptions, ...options };

        console.log('📍 GEOLOCALIZAÇÃO: Iniciando captura...', config);

        // Verificar suporte
        if (!navigator.geolocation) {
            console.error('❌ GEOLOCALIZAÇÃO: Não suportada');
            
            if (config.showUI) {
                this.showError(
                    'Geolocalização não suportada',
                    'Seu navegador não suporta geolocalização. Usando localização aproximada por IP.'
                );
            }
            
            if (config.fallbackToIP) {
                return await this.getLocationByIP();
            }
            
            throw new Error('Geolocalização não suportada');
        }

        // NOVO: Verificar permissão antes de tentar obter localização
        const permissionStatus = await this.checkPermission();
        
        if (permissionStatus === 'denied') {
            console.error('❌ GEOLOCALIZAÇÃO: Permissão negada permanentemente');
            
            if (config.showUI) {
                this.showDetailedError(
                    '🚫 Permissão de Localização Negada',
                    'Você bloqueou o acesso à sua localização.',
                    this.getPermissionInstructions()
                );
            }
            
            // Se permissão negada, usar fallback por IP
            if (config.fallbackToIP) {
                console.log('🔄 GEOLOCALIZAÇÃO: Usando fallback por IP devido a permissão negada');
                return await this.getLocationByIP();
            }
            
            throw new Error('Permissão de geolocalização negada');
        }
        
        console.log('✅ GEOLOCALIZAÇÃO: Permissão OK, capturando localização...');

        // Tentar obter localização GPS
        try {
            const position = await this.getGPSLocation(config);
            
            if (config.showUI) {
                this.showSuccess('📍 Localização capturada com sucesso!');
            }
            
            // Reverse geocoding se solicitado
            if (config.reverseGeocode) {
                const address = await this.reverseGeocode(
                    position.coords.latitude,
                    position.coords.longitude
                );
                position.address = address;
            }
            
            this.currentPosition = position;
            return position;
            
        } catch (error) {
            console.error('❌ GEOLOCALIZAÇÃO GPS falhou:', error);
            
            // Tentar fallback por IP
            if (config.fallbackToIP) {
                console.log('🔄 GEOLOCALIZAÇÃO: Tentando fallback por IP...');
                
                if (config.showUI) {
                    this.showInfo(
                        'Usando localização aproximada',
                        'Não foi possível obter sua localização exata. Usando localização aproximada por IP.'
                    );
                }
                
                return await this.getLocationByIP();
            }
            
            // Se não tem fallback, mostrar erro detalhado
            this.handleGeolocationError(error, config.showUI);
            throw error;
        }
    }

    /**
     * Obter localização GPS nativa
     */
    getGPSLocation(config) {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    console.log('✅ GPS: Localização obtida', {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                    resolve(position);
                },
                (error) => {
                    console.error('❌ GPS: Erro', error);
                    reject(error);
                },
                {
                    enableHighAccuracy: config.enableHighAccuracy,
                    timeout: config.timeout,
                    maximumAge: config.maximumAge
                }
            );
        });
    }

    /**
     * Obter localização aproximada por IP (fallback)
     */
    async getLocationByIP() {
        try {
            console.log('🌐 IP GEOLOCATION: Iniciando...');
            
            const response = await fetch('https://ipapi.co/json/');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            console.log('✅ IP GEOLOCATION: Localização obtida', {
                city: data.city,
                region: data.region,
                country: data.country_name
            });
            
            const position = {
                coords: {
                    latitude: data.latitude,
                    longitude: data.longitude,
                    accuracy: 5000, // Aproximado a 5km
                },
                timestamp: Date.now(),
                address: `${data.city}, ${data.region}, ${data.country_name}`,
                source: 'ip',
                ip: data.ip
            };
            
            this.currentPosition = position;
            this.fallbackUsed = true;
            
            return position;
            
        } catch (error) {
            console.error('❌ IP GEOLOCATION: Falhou', error);
            throw new Error('Não foi possível obter localização por IP: ' + error.message);
        }
    }

    /**
     * Reverse geocoding (converter coordenadas em endereço)
     */
    async reverseGeocode(lat, lng) {
        try {
            console.log('🗺️ REVERSE GEOCODING: Convertendo coordenadas...');
            
            const response = await fetch('/api/reverse-geocoding', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({ latitude: lat, longitude: lng })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.endereco) {
                console.log('✅ REVERSE GEOCODING: Endereço obtido:', data.endereco);
                return data.endereco;
            }
            
            // Fallback para formato simples
            return `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
            
        } catch (error) {
            console.error('❌ REVERSE GEOCODING: Falhou', error);
            return `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`;
        }
    }

    /**
     * Monitorar localização em tempo real
     */
    watchLocation(callback, options = {}) {
        if (!navigator.geolocation) {
            console.error('❌ WATCH: Geolocalização não suportada');
            return null;
        }

        const defaultOptions = {
            enableHighAccuracy: false,
            timeout: 60000,
            maximumAge: 300000  // Cache de 5 minutos
        };

        const config = { ...defaultOptions, ...options };

        console.log('👁️ WATCH: Iniciando monitoramento...', config);

        const watchId = navigator.geolocation.watchPosition(
            (position) => {
                console.log('📍 WATCH: Localização atualizada');
                this.currentPosition = position;
                if (callback) callback(position, null);
            },
            (error) => {
                console.warn('⚠️ WATCH: Erro', error);
                if (callback) callback(null, error);
            },
            config
        );

        console.log('✅ WATCH: Monitoramento ativo (ID:', watchId, ')');
        return watchId;
    }

    /**
     * Parar monitoramento
     */
    stopWatching(watchId) {
        if (watchId) {
            navigator.geolocation.clearWatch(watchId);
            console.log('🛑 WATCH: Monitoramento parado (ID:', watchId, ')');
        }
    }

    /**
     * Tratar erros de geolocalização com mensagens claras
     */
    handleGeolocationError(error, showUI = true) {
        let title = '';
        let message = '';
        let instructions = '';

        switch(error.code) {
            case error.PERMISSION_DENIED:
                title = '🚫 Permissão de Localização Negada';
                message = 'Você negou o acesso à sua localização.';
                instructions = this.getPermissionInstructions();
                break;
                
            case error.POSITION_UNAVAILABLE:
                title = '📍 Localização Indisponível';
                message = 'Não foi possível determinar sua localização.';
                instructions = `
                    <ul class="text-start">
                        <li>Verifique se o GPS está ativado</li>
                        <li>Certifique-se de estar em um local aberto</li>
                        <li>Tente novamente em alguns segundos</li>
                    </ul>
                `;
                break;
                
            case error.TIMEOUT:
                title = '⏰ Tempo Limite Excedido';
                message = 'A busca pela localização demorou muito.';
                instructions = `
                    <ul class="text-start">
                        <li>Verifique sua conexão com a internet</li>
                        <li>Ative o GPS nas configurações</li>
                        <li>Tente novamente</li>
                    </ul>
                `;
                break;
                
            default:
                title = '❌ Erro de Geolocalização';
                message = error.message || 'Erro desconhecido ao obter localização.';
                instructions = '<p>Por favor, tente novamente ou use a localização aproximada.</p>';
                break;
        }

        console.error('❌ GEOLOCATION ERROR:', { title, message, error });

        if (showUI) {
            this.showDetailedError(title, message, instructions);
        }
    }

    /**
     * Instruções específicas por dispositivo/navegador
     */
    getPermissionInstructions() {
        const ua = navigator.userAgent.toLowerCase();
        const isAndroid = /android/i.test(ua);
        const isIOS = /iphone|ipad|ipod/i.test(ua);
        const isChrome = /chrome/i.test(ua);
        const isFirefox = /firefox/i.test(ua);
        const isSafari = /safari/i.test(ua) && !/chrome/i.test(ua);

        if (isAndroid && isChrome) {
            return `
                <strong>📱 Android + Chrome:</strong>
                <ol class="text-start">
                    <li>Toque no ícone <strong>🔒</strong> ou <strong>ⓘ</strong> na barra de endereço</li>
                    <li>Selecione <strong>"Permissões"</strong> ou <strong>"Configurações do site"</strong></li>
                    <li>Encontre <strong>"Localização"</strong> e altere para <strong>"Permitir"</strong></li>
                    <li>Recarregue a página e tente novamente</li>
                </ol>
            `;
        } else if (isIOS) {
            return `
                <strong>📱 iPhone/iPad:</strong>
                <ol class="text-start">
                    <li>Abra <strong>Ajustes</strong> (Configurações)</li>
                    <li>Role até <strong>Privacidade</strong> → <strong>Localização</strong></li>
                    <li>Certifique-se de que <strong>"Serviços de Localização"</strong> está ativado</li>
                    <li>Role até o navegador (Safari/Chrome) e selecione <strong>"Ao Usar o App"</strong></li>
                    <li>Volte ao app e tente novamente</li>
                </ol>
            `;
        } else if (isChrome) {
            return `
                <strong>💻 Chrome:</strong>
                <ol class="text-start">
                    <li>Clique no ícone <strong>🔒</strong> antes da URL</li>
                    <li>Procure <strong>"Localização"</strong></li>
                    <li>Altere para <strong>"Permitir"</strong></li>
                    <li>Recarregue a página</li>
                </ol>
            `;
        } else if (isFirefox) {
            return `
                <strong>💻 Firefox:</strong>
                <ol class="text-start">
                    <li>Clique no ícone <strong>🔒</strong> antes da URL</li>
                    <li>Clique na seta ao lado de "Bloqueado"</li>
                    <li>Clique em <strong>"Limpar essa permissão"</strong></li>
                    <li>Recarregue e permita quando solicitado</li>
                </ol>
            `;
        } else if (isSafari) {
            return `
                <strong>💻 Safari:</strong>
                <ol class="text-start">
                    <li>Abra <strong>Preferências do Safari</strong></li>
                    <li>Vá em <strong>Sites</strong> → <strong>Localização</strong></li>
                    <li>Encontre este site e altere para <strong>"Permitir"</strong></li>
                    <li>Recarregue a página</li>
                </ol>
            `;
        }

        return `
            <strong>💻 Como permitir localização:</strong>
            <ol class="text-start">
                <li>Clique no ícone de localização/cadeado na barra de endereço</li>
                <li>Procure por "Localização" nas permissões</li>
                <li>Altere para "Permitir"</li>
                <li>Recarregue a página</li>
            </ol>
        `;
    }

    /**
     * UI: Mostrar erro detalhado
     */
    showDetailedError(title, message, instructions) {
        // Criar modal de erro
        const modal = document.createElement('div');
        modal.className = 'modal fade show';
        modal.style.display = 'block';
        modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
        modal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close btn-close-white" onclick="this.closest('.modal').remove()"></button>
                    </div>
                    <div class="modal-body">
                        <p class="lead">${message}</p>
                        <div class="alert alert-warning">
                            ${instructions}
                        </div>
                        <div class="alert alert-info">
                            <strong>💡 Alternativa:</strong> Podemos usar sua localização aproximada baseada no seu IP.
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">
                            Cancelar
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.location.reload()">
                            Recarregar Página
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    /**
     * UI: Mostrar sucesso
     */
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    /**
     * UI: Mostrar aviso
     */
    showWarning(message) {
        this.showToast(message, 'warning');
    }

    /**
     * UI: Mostrar erro simples
     */
    showError(title, message) {
        this.showToast(`${title}: ${message}`, 'danger');
    }

    /**
     * UI: Mostrar informação
     */
    showInfo(title, message) {
        this.showToast(`${title}: ${message}`, 'info');
    }

    /**
     * UI: Toast notification
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show`;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        `;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" onclick="this.remove()"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) toast.remove();
        }, 5000);
    }

    /**
     * Utilitários
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    getCurrentPosition() {
        return this.currentPosition;
    }

    wasFallbackUsed() {
        return this.fallbackUsed;
    }

    /**
     * Solicitar localização e enviar ao backend automaticamente
     * Método público para ser usado em botões "Tentar Novamente"
     */
    async requestAndSaveLocation(options = {}) {
        try {
            console.log('🔄 Solicitando localização...');
            
            // Obter localização (já verifica permissões internamente)
            const position = await this.getLocation({
                ...options,
                showUI: true,
                fallbackToIP: true,
                reverseGeocode: true
            });

            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const accuracy = position.coords.accuracy || 5000;
            const source = position.source || 'gps';
            const address = position.address || '';

            console.log('📍 Localização obtida, enviando ao backend...');

            // Enviar ao backend
            const response = await fetch('/save_location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    lat: lat,
                    lng: lng,
                    accuracy: accuracy,
                    source: source,
                    address: address,
                    projeto_id: options.projeto_id,
                    relatorio_id: options.relatorio_id
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('✅ Localização salva no backend:', data);
                return { success: true, position, data };
            } else {
                console.error('❌ Erro ao salvar no backend:', response.status);
                return { success: false, position, error: 'Falha ao salvar' };
            }

        } catch (error) {
            console.error('❌ Erro ao solicitar/salvar localização:', error);
            return { success: false, error: error.message };
        }
    }
}

// Instanciar globalmente
window.geoLocation = new EnhancedGeolocation();

console.log('✅ GEOLOCALIZAÇÃO: Sistema avançado carregado');
