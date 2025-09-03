/**
 * PWA Update Manager - Força atualização automática
 * Garante que o aplicativo móvel sempre tenha a versão mais recente
 */

// Service Worker com Update Forçado
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(function(registration) {
            console.log('PWA: Service Worker v2 registrado:', registration);
            
            // Verificar atualizações a cada 15 segundos
            setInterval(() => {
                registration.update().then(() => {
                    console.log('PWA: Verificação de update concluída');
                });
            }, 15000);
            
            // Forçar atualização quando nova versão estiver disponível
            registration.addEventListener('updatefound', () => {
                console.log('PWA: Nova versão encontrada!');
                const newWorker = registration.installing;
                
                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        console.log('PWA: Versão v2 (Editor Figma) pronta - atualizando...');
                        showFigmaUpdateNotification();
                    }
                });
            });
        })
        .catch(function(error) {
            console.log('PWA: Falha ao registrar Service Worker:', error);
        });
}

/**
 * Mostra notificação de atualização específica para Editor Figma
 */
function showFigmaUpdateNotification() {
    // Remover notificação existente se houver
    const existingNotification = document.getElementById('pwa-update-notification');
    if (existingNotification) {
        existingNotification.remove();
    }
    
    // Criar notificação visual de atualização
    const notification = document.createElement('div');
    notification.id = 'pwa-update-notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        z-index: 10000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
        font-size: 14px;
        max-width: 320px;
        animation: slideInRight 0.5s ease-out;
        border: 2px solid rgba(255,255,255,0.2);
    `;
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px;">
            <i class="fas fa-vector-square" style="font-size: 24px; color: #fff;"></i>
            <div>
                <div style="font-weight: bold; margin-bottom: 4px;">✨ Editor Figma Atualizado!</div>
                <div style="font-size: 12px; opacity: 0.9;">Novas ferramentas de edição mobile disponíveis</div>
            </div>
        </div>
        <div style="margin-top: 12px; text-align: center;">
            <button onclick="reloadAppForUpdate()" style="
                background: rgba(255,255,255,0.9);
                color: #333;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.2s;
            " onmouseover="this.style.background='white'" onmouseout="this.style.background='rgba(255,255,255,0.9)'">
                Atualizar Agora
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-reload após 8 segundos se não clicado
    setTimeout(() => {
        if (document.getElementById('pwa-update-notification')) {
            reloadAppForUpdate();
        }
    }, 8000);
}

/**
 * Recarrega o aplicativo para aplicar as atualizações
 */
function reloadAppForUpdate() {
    const notification = document.getElementById('pwa-update-notification');
    if (notification) {
        notification.style.animation = 'slideOutRight 0.3s ease-in forwards';
        
        setTimeout(() => {
            notification.remove();
            
            // Mostrar loading
            showUpdateLoader();
            
            // Forçar reload após pequeno delay
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }, 300);
    } else {
        window.location.reload();
    }
}

/**
 * Mostra indicador de carregamento da atualização
 */
function showUpdateLoader() {
    const loader = document.createElement('div');
    loader.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(52, 58, 64, 0.95);
        z-index: 10001;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    `;
    
    loader.innerHTML = `
        <div style="text-align: center;">
            <div style="width: 50px; height: 50px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #20c1e8; animation: spin 1s ease-in-out infinite; margin: 0 auto 20px;"></div>
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 8px;">Aplicando Atualizações</div>
            <div style="font-size: 14px; opacity: 0.8;">Editor Figma Mobile sendo instalado...</div>
        </div>
    `;
    
    document.body.appendChild(loader);
}

// Adicionar estilos de animação
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

console.log('🚀 PWA Update Manager v2.0 carregado - Editor Figma Mobile');