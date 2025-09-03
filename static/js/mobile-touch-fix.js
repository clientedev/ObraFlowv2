/**
 * Mobile Touch Fix - Elimina vibração e melhora precisão
 * Carregado automaticamente em dispositivos móveis
 */

// Detectar se é dispositivo móvel
function isMobileDevice() {
    return /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
           ('ontouchstart' in window) ||
           (navigator.maxTouchPoints > 0);
}

// Aplicar correções apenas em dispositivos móveis
if (isMobileDevice()) {
    
    // ELIMINAR VIBRAÇÃO COMPLETA
    document.addEventListener('DOMContentLoaded', function() {
        
        // Aplicar estilos anti-vibração ao body e html
        const antiVibeStyles = `
            * {
                -webkit-tap-highlight-color: transparent !important;
                -webkit-touch-callout: none !important;
                -webkit-user-select: none !important;
                -moz-user-select: none !important;
                -ms-user-select: none !important;
                user-select: none !important;
                touch-action: manipulation !important;
            }
            
            input[type="text"], input[type="email"], input[type="password"], 
            textarea, [contenteditable="true"] {
                -webkit-user-select: text !important;
                user-select: text !important;
            }
            
            .table-responsive {
                overflow-x: auto !important;
                -webkit-overflow-scrolling: touch !important;
                touch-action: pan-x pan-y !important;
                overscroll-behavior: contain !important;
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.textContent = antiVibeStyles;
        document.head.appendChild(styleSheet);
        
        // Prevenir bounce scroll global
        document.body.style.overscrollBehavior = 'contain';
        document.documentElement.style.overscrollBehavior = 'contain';
        
        // Prevenir zoom duplo-toque global
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = Date.now();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Melhorar scroll em tabelas
        const tableResponsives = document.querySelectorAll('.table-responsive');
        tableResponsives.forEach(table => {
            table.style.overflowX = 'auto';
            table.style.WebkitOverflowScrolling = 'touch';
            table.style.touchAction = 'pan-x pan-y';
            table.style.overscrollBehavior = 'contain';
        });
        
        // Log para debug
        console.log('Mobile Touch Fix: Correções aplicadas para dispositivo móvel');
    });
    
    // Prevenir gestos indesejados
    document.addEventListener('gesturestart', e => e.preventDefault());
    document.addEventListener('gesturechange', e => e.preventDefault());
    document.addEventListener('gestureend', e => e.preventDefault());
    
    // Prevenir menu de contexto em toque longo
    document.addEventListener('contextmenu', e => {
        // Permitir context menu apenas em inputs de texto
        if (!e.target.matches('input[type="text"], input[type="email"], input[type="password"], textarea')) {
            e.preventDefault();
        }
    });
    
    // Otimizar performance do scroll
    document.addEventListener('touchmove', function(e) {
        // Permitir scroll apenas em elementos scrolláveis
        const target = e.target;
        const scrollableParent = target.closest('.table-responsive, .modal-body, .overflow-auto, [style*="overflow"]');
        
        if (!scrollableParent) {
            // Se não há elemento scrollável pai, prevenir o scroll padrão que pode causar bounce
            const shouldPrevent = !target.matches('input, textarea, select, [contenteditable="true"]');
            if (shouldPrevent) {
                e.preventDefault();
            }
        }
    }, { passive: false });
}