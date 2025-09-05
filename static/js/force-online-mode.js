/**
 * FORÇAR MODO ONLINE - Garantir dados do PostgreSQL
 * Sistema para limpar cache offline e forçar uso do banco de dados
 */

class ForceOnlineMode {
    constructor() {
        this.init();
    }

    init() {
        console.log('🔥 FORCE ONLINE: Iniciando limpeza de cache offline');
        
        // 1. Limpar localStorage
        this.clearLocalStorage();
        
        // 2. Limpar sessionStorage  
        this.clearSessionStorage();
        
        // 3. Desregistrar Service Worker
        this.clearServiceWorker();
        
        // 4. Limpar cache do navegador
        this.clearBrowserCache();
        
        // 5. Forçar reload sem cache
        this.forceReload();
    }

    clearLocalStorage() {
        try {
            // Limpar dados específicos offline
            const offlineKeys = [
                'offline_data',
                'sync_queue', 
                'offline_reports',
                'offline_visits',
                'offline_projects',
                'offline_reimbursements'
            ];
            
            offlineKeys.forEach(key => {
                localStorage.removeItem(key);
                console.log(`🧹 CLEARED: localStorage.${key}`);
            });
            
            // Limpar tudo se necessário
            const allKeys = Object.keys(localStorage);
            allKeys.forEach(key => {
                if (key.includes('offline') || key.includes('sync') || key.includes('cache')) {
                    localStorage.removeItem(key);
                    console.log(`🧹 CLEARED: localStorage.${key}`);
                }
            });
            
        } catch (error) {
            console.error('❌ Erro ao limpar localStorage:', error);
        }
    }

    clearSessionStorage() {
        try {
            sessionStorage.clear();
            console.log('🧹 CLEARED: sessionStorage');
        } catch (error) {
            console.error('❌ Erro ao limpar sessionStorage:', error);
        }
    }

    async clearServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registrations = await navigator.serviceWorker.getRegistrations();
                for (const registration of registrations) {
                    await registration.unregister();
                    console.log('🧹 CLEARED: Service Worker');
                }
            } catch (error) {
                console.error('❌ Erro ao limpar Service Worker:', error);
            }
        }
    }

    async clearBrowserCache() {
        if ('caches' in window) {
            try {
                const cacheNames = await caches.keys();
                for (const name of cacheNames) {
                    await caches.delete(name);
                    console.log(`🧹 CLEARED: Cache ${name}`);
                }
            } catch (error) {
                console.error('❌ Erro ao limpar cache:', error);
            }
        }
    }

    forceReload() {
        console.log('🔄 FORCE RELOAD: Recarregando sem cache');
        
        // Adicionar parâmetro anti-cache
        const url = new URL(window.location);
        url.searchParams.set('force_online', Date.now());
        
        // Reload forçado sem cache
        window.location.replace(url.toString());
    }

    // Função para verificar se está em modo offline
    static isOfflineMode() {
        return localStorage.getItem('offline_data') !== null || 
               localStorage.getItem('sync_queue') !== null;
    }

    // Função para forçar modo online em qualquer página
    static forceOnlineForPage() {
        if (ForceOnlineMode.isOfflineMode()) {
            console.log('⚠️ DETECTADO MODO OFFLINE - Forçando limpeza');
            new ForceOnlineMode();
        }
    }
}

// Executar automaticamente se detectar dados offline
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se tem parâmetro para forçar online
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('force_online') || urlParams.has('clear_cache')) {
        new ForceOnlineMode();
        return;
    }
    
    // Verificar se está em modo offline
    ForceOnlineMode.forceOnlineForPage();
});

// Expor globalmente
window.ForceOnlineMode = ForceOnlineMode;