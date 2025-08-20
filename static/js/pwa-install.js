// PWA Installation Manager
class PWAInstaller {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.init();
    }

    init() {
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
        // Verificar se está rodando em modo standalone
        if (window.matchMedia('(display-mode: standalone)').matches) {
            this.isInstalled = true;
            return true;
        }
        
        // Verificar no iOS
        if (window.navigator.standalone === true) {
            this.isInstalled = true;
            return true;
        }
        
        return false;
    }

    showInstallButton() {
        if (this.isInstalled) return;

        // Remover botão anterior se existir
        const existingButton = document.getElementById('pwa-install-button');
        if (existingButton) existingButton.remove();

        // Criar botão de instalação
        const installButton = document.createElement('div');
        installButton.id = 'pwa-install-button';
        installButton.className = 'pwa-install-prompt';
        installButton.innerHTML = `
            <div class="card border-primary" style="position: fixed; bottom: 20px; left: 20px; z-index: 9999; max-width: 350px;">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                    <div>
                        <i class="fas fa-mobile-alt me-2"></i>
                        <strong>Instalar App</strong>
                    </div>
                    <button type="button" class="btn-close btn-close-white" onclick="this.closest('.pwa-install-prompt').remove()"></button>
                </div>
                <div class="card-body">
                    <p class="mb-3">
                        <i class="fas fa-download text-primary me-2"></i>
                        Instale o app ELP Relatórios no seu dispositivo para acesso rápido e funcionalidades offline!
                    </p>
                    <div class="d-grid gap-2">
                        <button class="btn btn-primary" onclick="window.pwaInstaller.installApp()">
                            <i class="fas fa-download me-2"></i>
                            Instalar Agora
                        </button>
                        <button class="btn btn-outline-secondary btn-sm" onclick="window.pwaInstaller.showManualInstructions()">
                            <i class="fas fa-question-circle me-2"></i>
                            Como instalar manualmente?
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(installButton);
    }

    hideInstallButton() {
        const button = document.getElementById('pwa-install-button');
        if (button) button.remove();
    }

    async installApp() {
        if (!this.deferredPrompt) {
            this.showManualInstructions();
            return;
        }

        try {
            // Mostrar prompt de instalação
            this.deferredPrompt.prompt();
            
            // Aguardar resposta do usuário
            const result = await this.deferredPrompt.userChoice;
            
            if (result.outcome === 'accepted') {
                console.log('PWA: Usuário aceitou instalação');
                this.showSuccessMessage();
            } else {
                console.log('PWA: Usuário recusou instalação');
            }
            
            this.deferredPrompt = null;
            this.hideInstallButton();
            
        } catch (error) {
            console.error('PWA: Erro na instalação:', error);
            this.showManualInstructions();
        }
    }

    showManualInstructions() {
        const userAgent = navigator.userAgent.toLowerCase();
        let instructions = '';
        
        if (userAgent.includes('android')) {
            if (userAgent.includes('chrome')) {
                instructions = `
                    <strong>Para instalar no Android Chrome:</strong><br>
                    1. Toque no menu (⋮) no canto superior direito<br>
                    2. Selecione "Instalar app" ou "Adicionar à tela inicial"<br>
                    3. Confirme a instalação<br><br>
                    <strong>Ou:</strong> Procure por "Adicionar à tela inicial" na barra de endereços
                `;
            } else if (userAgent.includes('firefox')) {
                instructions = `
                    <strong>Para instalar no Android Firefox:</strong><br>
                    1. Toque no menu (⋯) no canto superior direito<br>
                    2. Selecione "Instalar" ou "Adicionar à tela inicial"<br>
                    3. Confirme a instalação
                `;
            } else {
                instructions = `
                    <strong>Para instalar no Android:</strong><br>
                    1. Abra este site no Chrome ou Firefox<br>
                    2. Use o menu do navegador<br>
                    3. Procure por "Instalar app" ou "Adicionar à tela inicial"
                `;
            }
        } else if (userAgent.includes('iphone') || userAgent.includes('ipad')) {
            instructions = `
                <strong>Para instalar no iOS Safari:</strong><br>
                1. Toque no botão de compartilhar (📤)<br>
                2. Role para baixo e toque em "Adicionar à Tela de Início"<br>
                3. Toque em "Adicionar" no canto superior direito<br><br>
                <em>Nota: Funciona apenas no Safari, não em outros navegadores iOS</em>
            `;
        } else {
            instructions = `
                <strong>Para instalar no desktop:</strong><br>
                1. Procure pelo ícone de instalação na barra de endereços<br>
                2. Ou use o menu do navegador<br>
                3. Selecione "Instalar ELP Relatórios"<br><br>
                <strong>Dispositivos móveis:</strong><br>
                Use o menu do seu navegador e procure por "Adicionar à tela inicial" ou "Instalar app"
            `;
        }

        this.showModal('Como Instalar o App', instructions);
    }

    showSuccessMessage() {
        this.showNotification(
            '<i class="fas fa-check-circle text-success me-2"></i>' +
            '<strong>App instalado com sucesso!</strong><br>' +
            'Agora você pode acessar o ELP Relatórios diretamente da sua tela inicial.',
            'success'
        );
    }

    showInstalledMessage() {
        this.showNotification(
            '<i class="fas fa-mobile-alt text-info me-2"></i>' +
            '<strong>App detectado!</strong><br>' +
            'Você está usando a versão instalada do ELP Relatórios.',
            'info'
        );
    }

    showNotification(message, type = 'info') {
        // Remove notificações anteriores
        const existing = document.querySelector('.pwa-notification');
        if (existing) existing.remove();

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} pwa-notification`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
        `;
        notification.innerHTML = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    showModal(title, content) {
        // Criar modal se não existir
        let modal = document.getElementById('pwa-instructions-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'pwa-instructions-modal';
            modal.className = 'modal fade';
            modal.innerHTML = `
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="pwa-modal-title"></h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="pwa-modal-body"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        // Atualizar conteúdo
        document.getElementById('pwa-modal-title').textContent = title;
        document.getElementById('pwa-modal-body').innerHTML = content;

        // Mostrar modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
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

// Inicializar PWA Installer quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    if ('serviceWorker' in navigator) {
        window.pwaInstaller = new PWAInstaller();
        
        // Registrar Service Worker
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('PWA: Service Worker registrado:', registration);
            })
            .catch(error => {
                console.log('PWA: Erro ao registrar Service Worker:', error);
            });
    } else {
        console.log('PWA: Service Worker não suportado');
    }
});