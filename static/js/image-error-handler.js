
/**
 * Sistema global para lidar com erros de imagem
 */

// Função para lidar com erros de imagem
function handleImageError(img) {
    console.log('🖼️ Imagem não encontrada:', img.src);
    
    // Evitar loop infinito
    if (img.src.includes('no-image.png') || img.dataset.errorHandled) {
        return;
    }
    
    // Marcar como processada
    img.dataset.errorHandled = 'true';
    
    // Salvar src original
    if (!img.dataset.originalSrc) {
        img.dataset.originalSrc = img.src;
    }
    
    // Tentar placeholder local primeiro
    img.src = '/static/img/no-image.png';
    img.alt = 'Imagem não encontrada';
    img.title = 'Arquivo de imagem não localizado no servidor';
    
    // Adicionar classe de erro
    img.classList.add('image-error');
}

// Aplicar handler global quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar handler para imagens existentes
    const images = document.querySelectorAll('img[src*="/uploads/"]');
    images.forEach(img => {
        img.onerror = function() {
            handleImageError(this);
        };
    });
    
    // Observer para imagens adicionadas dinamicamente
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        const newImages = node.querySelectorAll ? 
                            node.querySelectorAll('img[src*="/uploads/"]') : [];
                        
                        newImages.forEach(img => {
                            img.onerror = function() {
                                handleImageError(this);
                            };
                        });
                        
                        // Se o próprio node for uma imagem
                        if (node.tagName === 'IMG' && node.src && node.src.includes('/uploads/')) {
                            node.onerror = function() {
                                handleImageError(this);
                            };
                        }
                    }
                });
            }
        });
    });
    
    // Observar mudanças no DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('🖼️ Sistema de tratamento de erros de imagem inicializado');
});
