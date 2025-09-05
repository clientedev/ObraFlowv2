/**
 * DEBUG USER SESSION - Identificar problema de dados diferentes
 * Analisa qual usuário está logado e seus dados
 */

function debugUserSession() {
    console.log('=== DEBUG USER SESSION ===');
    console.log('URL:', window.location.href);
    console.log('UserAgent:', navigator.userAgent);
    console.log('Mobile:', window.innerWidth <= 768);
    
    // Verificar se há informação de usuário na página
    const userInfo = document.querySelector('[data-user-id]');
    if (userInfo) {
        console.log('User ID encontrado:', userInfo.getAttribute('data-user-id'));
    }
    
    // Verificar cookies de sessão
    console.log('Cookies:', document.cookie);
    
    // Tentar fazer requisição para obter dados do usuário atual
    fetch('/api/current-user', {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('=== CURRENT USER ===');
        console.log('ID:', data.id);
        console.log('Username:', data.username);
        console.log('Email:', data.email);
        console.log('Is Master:', data.is_master);
    })
    .catch(error => {
        console.error('Erro ao obter usuário atual:', error);
    });
    
    // Verificar contadores de dados
    fetch('/api/user-data-counts', {
        method: 'GET',
        headers: {
            'Cache-Control': 'no-cache'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('=== USER DATA COUNTS ===');
        console.log('Projetos:', data.projetos);
        console.log('Relatórios:', data.relatorios);
        console.log('Visitas:', data.visitas);
        console.log('Reembolsos:', data.reembolsos);
    })
    .catch(error => {
        console.error('Erro ao obter contadores:', error);
    });
}

// Executar debug ao carregar
document.addEventListener('DOMContentLoaded', debugUserSession);

// Expor globalmente para debug manual
window.debugUserSession = debugUserSession;