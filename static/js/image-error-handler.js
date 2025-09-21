/**
 * Sistema global para lidar com erros de imagem
 */

// Função para lidar com erros de imagem
function handleImageError(img) {
    const originalSrc = img.src;
    const filename = originalSrc.split('/').pop();
    
    console.log('🖼️ Erro ao carregar imagem:', originalSrc);

    // Evitar loop infinito
    if (img.src.includes('no-image.png') || img.dataset.errorHandled) {
        return;
    }

    // Marcar como processada
    img.dataset.errorHandled = 'true';

    // Salvar src original
    if (!img.dataset.originalSrc) {
        img.dataset.originalSrc = originalSrc;
    }

    // Tentar placeholder local primeiro
    img.src = '/static/img/no-image.png';
    img.alt = `Imagem não encontrada: ${filename}`;
    img.title = `Arquivo de imagem não localizado: ${filename}`;

    // Adicionar classe de erro e informações visuais
    img.classList.add('image-error');
    img.style.border = '2px dashed #dc3545';
    img.style.opacity = '0.7';
    
    // Log para admin/debug
    if (filename.length > 20) {
        console.warn(`⚠️ Imagem perdida: ${filename.substring(0, 20)}...`);
    }
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