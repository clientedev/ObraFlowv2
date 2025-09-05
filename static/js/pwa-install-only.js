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
            <div class="position-fixed" 
                 style="bottom: 20px; left: 20px; z-index: 9999; max-width: 380px;">
                <div class="card shadow-lg border-0" 
                     style="border-radius: 20px; background: linear-gradient(135deg, #343a40 0%, #20c1e8 100%); color: white; animation: slideInLeft 0.6s ease-out;">
                    <button type="button" class="btn-close btn-close-white position-absolute" 
                            style="top: 12px; right: 12px; z-index: 10; opacity: 0.8;" 
                            onclick="this.closest('.position-fixed').remove()"></button>
                    
                    <div class="card-body p-4">
                        <div class="d-flex align-items-center mb-3">
                            <div class="rounded-circle p-3 me-3" 
                                 style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px);">
                                <i class="fas fa-mobile-alt fa-2x text-white"></i>
                            </div>
                            <div>
                                <h5 class="mb-1 fw-bold text-white">📱 ELP Consultoria</h5>
                                <small class="text-white-50">Sistema de Vistorias Mobile</small>
                            </div>
                        </div>
                        
                        <p class="mb-3 text-white-75" style="font-size: 14px; line-height: 1.4;">
                            🏗️ Gestão de vistorias<br>
                            📋 Relatórios profissionais<br>
                            📷 Editor de fotos integrado<br>
                            🔧 Acesso offline completo
                        </p>
                        
                        <button id="install-pwa-btn" class="btn btn-lg w-100 fw-bold" 
                                style="border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: all 0.3s ease; background: #20c1e8; border: none; color: white;">
                            <i class="fas fa-download me-2"></i>Instalar Sistema ELP
                        </button>
                        
                        <div class="text-center mt-2">
                            <small class="text-white-50">⚡ ELP Consultoria e Engenharia</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
                @keyframes slideInLeft {
                    from {
                        transform: translateX(-100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                
                #install-pwa-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(32,193,232,0.3) !important;
                    background: #1aa8c7 !important;
                }
                
                .text-white-75 {
                    color: rgba(255,255,255,0.85) !important;
                }
                
                .text-white-50 {
                    color: rgba(255,255,255,0.7) !important;
                }
            </style>
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
            <div class="position-fixed" 
                 style="bottom: 20px; left: 20px; z-index: 9999; max-width: 380px;">
                <div class="card shadow-lg border-0" 
                     style="border-radius: 20px; background: linear-gradient(135deg, #20c1e8 0%, #20c997 100%); color: white; animation: bounceIn 0.8s ease-out;">
                    <button type="button" class="btn-close btn-close-white position-absolute" 
                            style="top: 12px; right: 12px; z-index: 10; opacity: 0.8;" 
                            onclick="this.closest('.position-fixed').remove()"></button>
                    
                    <div class="card-body p-4 text-center">
                        <div class="mb-3">
                            <div class="rounded-circle mx-auto p-3 mb-3" 
                                 style="background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-check-circle fa-3x text-white"></i>
                            </div>
                            
                            <h4 class="mb-2 fw-bold text-white">🎉 Sucesso!</h4>
                            <h6 class="mb-0 text-white-75">Sistema ELP Instalado</h6>
                        </div>
                        
                        <p class="mb-3 text-white-75" style="font-size: 14px;">
                            Agora você pode acessar o Sistema ELP diretamente da tela inicial do seu dispositivo!
                        </p>
                        
                        <div class="d-flex align-items-center justify-content-center text-white-50">
                            <i class="fas fa-hard-hat me-2"></i>
                            <small>Procure pelo ícone "ELP Consultoria" na sua tela inicial</small>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
                @keyframes bounceIn {
                    0% {
                        transform: scale(0.3);
                        opacity: 0;
                    }
                    50% {
                        transform: scale(1.05);
                    }
                    70% {
                        transform: scale(0.9);
                    }
                    100% {
                        transform: scale(1);
                        opacity: 1;
                    }
                }
            </style>
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