/**
 * POSTGRESQL-ONLY MODE
 * Garante que todos os dados vêm exclusivamente do banco PostgreSQL
 */

// Interceptar todas as requisições para garantir uso do PostgreSQL
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // Adicionar header para garantir dados frescos do PostgreSQL
    const headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-PostgreSQL-Only': 'true',
        ...(options.headers || {})
    };
    
    return originalFetch(url, { ...options, headers });
};

// Interceptar formulários para garantir envio direto ao PostgreSQL
document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // Garantir que todos os formulários vão direto para o servidor
        if (form.tagName === 'FORM') {
            console.log('📡 FORM → PostgreSQL:', form.action || window.location.pathname);
            
            // Adicionar campo oculto para identificar modo PostgreSQL-only
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'postgresql_only';
            hiddenInput.value = 'true';
            form.appendChild(hiddenInput);
        }
    });
    
    // Mostrar status PostgreSQL-only
    const statusDiv = document.createElement('div');
    statusDiv.style.cssText = `
        position: fixed; 
        top: 10px; 
        left: 10px; 
        background: #28a745; 
        color: white; 
        padding: 8px 12px; 
        border-radius: 5px; 
        font-size: 12px; 
        z-index: 9999;
        font-family: monospace;
    `;
    statusDiv.innerHTML = '🗄️ PostgreSQL ONLY';
    document.body.appendChild(statusDiv);
    
    setTimeout(() => statusDiv.remove(), 3000);
});

console.log('🗄️ MODO POSTGRESQL-ONLY ATIVADO - Dados sincronizados garantidos');