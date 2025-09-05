/**
 * FORÇA SINCRONIZAÇÃO TOTAL COM POSTGRESQL
 * Remove todos os dados locais e força reload do banco
 */

(function() {
    'use strict';
    
    console.log('🔥 INICIANDO SINCRONIZAÇÃO FORÇADA COM POSTGRESQL');
    
    // 1. LIMPAR TUDO - ABSOLUTAMENTE TUDO
    function clearAllLocalData() {
        try {
            // Limpar localStorage completamente
            localStorage.clear();
            console.log('✅ localStorage limpo');
            
            // Limpar sessionStorage completamente
            sessionStorage.clear();
            console.log('✅ sessionStorage limpo');
            
            // Limpar IndexedDB se existir
            if ('indexedDB' in window) {
                indexedDB.databases().then(databases => {
                    databases.forEach(db => {
                        indexedDB.deleteDatabase(db.name);
                        console.log('✅ IndexedDB limpo:', db.name);
                    });
                });
            }
            
            // Limpar WebSQL (depreciado mas pode existir)
            try {
                if (window.openDatabase) {
                    window.openDatabase('', '', '', '', function() {});
                }
            } catch (e) {}
            
        } catch (error) {
            console.error('Erro ao limpar dados:', error);
        }
    }
    
    // 2. DESABILITAR CACHE AGRESSIVAMENTE
    function disableAllCaching() {
        // Interceptar fetch
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Force-Fresh': Date.now(),
                ...(options.headers || {})
            };
            
            return originalFetch(url, { ...options, headers });
        };
        
        // Interceptar XMLHttpRequest
        const originalXMLHttpRequest = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXMLHttpRequest();
            const originalOpen = xhr.open;
            
            xhr.open = function(method, url, ...args) {
                const freshUrl = url + (url.includes('?') ? '&' : '?') + '_t=' + Date.now();
                return originalOpen.call(this, method, freshUrl, ...args);
            };
            
            const originalSetRequestHeader = xhr.setRequestHeader;
            xhr.setRequestHeader = function(header, value) {
                originalSetRequestHeader.call(this, header, value);
                if (header.toLowerCase() !== 'cache-control') {
                    originalSetRequestHeader.call(this, 'Cache-Control', 'no-cache');
                }
            };
            
            return xhr;
        };
        
        console.log('✅ Cache desabilitado globalmente');
    }
    
    // 3. FORÇAR RELOAD SEM CACHE
    function forceHardReload() {
        // Adicionar timestamp para evitar cache
        const url = new URL(window.location);
        url.searchParams.set('_force_sync', Date.now());
        url.searchParams.set('_clear_cache', 'true');
        
        // Recarregar sem cache
        window.location.replace(url.toString());
    }
    
    // 4. VERIFICAR SE PRECISAMOS EXECUTAR
    const urlParams = new URLSearchParams(window.location.search);
    const isForceSync = urlParams.has('_force_sync');
    
    if (!isForceSync) {
        // Primeira execução - limpar e recarregar
        clearAllLocalData();
        disableAllCaching();
        
        setTimeout(() => {
            console.log('🔄 RECARREGANDO COM DADOS LIMPOS...');
            forceHardReload();
        }, 1000);
    } else {
        // Segunda execução - aplicar apenas desabilitação de cache
        console.log('✅ SINCRONIZAÇÃO CONCLUÍDA - PostgreSQL ONLY');
        disableAllCaching();
        
        // Remover parâmetros da URL sem recarregar
        const cleanUrl = new URL(window.location);
        cleanUrl.searchParams.delete('_force_sync');
        cleanUrl.searchParams.delete('_clear_cache');
        window.history.replaceState({}, '', cleanUrl.toString());
    }
    
})();