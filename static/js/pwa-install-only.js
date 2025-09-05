/**
 * PWA INSTALL ONLY - SEM FUNCIONALIDADE OFFLINE
 * Sistema de instalação reativado com dados PostgreSQL
 */

class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.init();
    }

    init() {
        console.log('📱 PWA Installer iniciado');
        
        // Verificar se já está instalado
        this.checkIfInstalled();
        
        // Escutar evento de instalação
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('PWA: Install prompt disponível');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Escutar quando é instalado
        window.addEventListener('appinstalled', (e) => {
            console.log('PWA: App instalado com sucesso');
            this.isInstalled = true;
            this.hideInstallButton();
            this.showInstalledMessage();
        });

        // Verificar se está rodando como PWA
        if (window.matchMedia('(display-mode: standalone)').matches || 
            window.navigator.standalone === true) {
            this.isInstalled = true;
            console.log('PWA: Rodando como app instalado');
        }
    }

    checkIfInstalled() {
        // Verificar se está em modo standalone
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        const isIOSStandalone = window.navigator.standalone === true;
        
        this.isInstalled = isStandalone || (isIOS && isIOSStandalone);
    }

    showInstallButton() {
        if (this.isInstalled) return;
        
        // Remover botão existente
        const existingBtn = document.getElementById('pwa-install-btn');
        if (existingBtn) existingBtn.remove();
        
        // Criar botão de instalação
        const installBtn = document.createElement('div');
        installBtn.id = 'pwa-install-btn';
        installBtn.innerHTML = `
            <div class="alert alert-info alert-dismissible fade show position-fixed" 
                 style="top: 70px; right: 15px; z-index: 9999; max-width: 320px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <div class="d-flex align-items-center">
                    <i class="fas fa-download fa-2x text-primary me-3"></i>
                    <div>
                        <h6 class="mb-1"><strong>Instalar ELP App</strong></h6>
                        <p class="mb-2 small">Instale nosso app para acesso rápido e melhor experiência</p>
                        <button id="install-pwa-btn" class="btn btn-primary btn-sm">
                            <i class="fas fa-download me-1"></i>Instalar Agora
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(installBtn);
        
        // Evento do botão de instalação
        document.getElementById('install-pwa-btn').onclick = () => this.installPWA();
        
        console.log('✅ Botão de instalação mostrado');
    }

    async installPWA() {
        if (!this.deferredPrompt) {
            console.log('❌ Prompt de instalação não disponível');
            return;
        }

        try {
            // Mostrar prompt de instalação
            this.deferredPrompt.prompt();
            
            // Aguardar escolha do usuário
            const { outcome } = await this.deferredPrompt.userChoice;
            
            console.log(`PWA: Usuário escolheu: ${outcome}`);
            
            if (outcome === 'accepted') {
                console.log('✅ PWA: Instalação aceita');
                this.hideInstallButton();
            } else {
                console.log('❌ PWA: Instalação recusada');
            }
            
            this.deferredPrompt = null;
            
        } catch (error) {
            console.error('Erro na instalação PWA:', error);
        }
    }

    hideInstallButton() {
        const installBtn = document.getElementById('pwa-install-btn');
        if (installBtn) {
            installBtn.remove();
        }
    }

    showInstalledMessage() {
        const successMsg = document.createElement('div');
        successMsg.innerHTML = `
            <div class="alert alert-success alert-dismissible fade show position-fixed" 
                 style="top: 70px; right: 15px; z-index: 9999; max-width: 320px;">
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                <div class="d-flex align-items-center">
                    <i class="fas fa-check-circle fa-2x text-success me-3"></i>
                    <div>
                        <h6 class="mb-1"><strong>App Instalado!</strong></h6>
                        <p class="mb-0 small">ELP App foi instalado com sucesso</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(successMsg);
        
        // Remover após 5 segundos
        setTimeout(() => {
            if (successMsg.parentNode) {
                successMsg.remove();
            }
        }, 5000);
    }

    // Verificar se pode mostrar prompt de instalação
    canShowInstallPrompt() {
        return !this.isInstalled && this.deferredPrompt !== null;
    }

    // Verificar suporte a PWA
    isPWASupported() {
        return 'serviceWorker' in navigator && 'PushManager' in window;
    }
}

// Inicializar quando página carregar
document.addEventListener('DOMContentLoaded', function() {
    if ('serviceWorker' in navigator) {
        window.pwaInstaller = new PWAInstaller();
    }
});

console.log('📱 PWA Install-Only carregado');