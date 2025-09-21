
/**
 * Sistema global robusto para lidar com erros de imagem
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

    // Tentar diferentes caminhos antes do placeholder
    const alternativePaths = [
        `/uploads/${filename}`,
        `/attached_assets/${filename}`,
        `/static/uploads/${filename}`,
        `/static/img/${filename}`,
        // Caminhos adicionais para recuperação
        `/attached_assets/stock_images/${filename}`,
        `/attached_assets/generated_images/${filename}`,
        // Tentar com prefixos comuns
        `/uploads/express_${filename}`,
        `/uploads/relatorio_${filename}`
    ];

    let pathIndex = 0;
    
    function tryNextPath() {
        if (pathIndex < alternativePaths.length) {
            const testImg = new Image();
            testImg.onload = function() {
                // Sucesso - usar este caminho
                img.src = alternativePaths[pathIndex];
                console.log(`✅ Imagem encontrada em: ${alternativePaths[pathIndex]}`);
                // Remover indicadores de erro
                img.classList.remove('image-error');
                img.style.border = '';
                img.style.opacity = '';
            };
            testImg.onerror = function() {
                pathIndex++;
                tryNextPath();
            };
            testImg.src = alternativePaths[pathIndex];
        } else {
            // Nenhum caminho funcionou - usar placeholder
            useImagePlaceholder();
        }
    }
    
    function useImagePlaceholder() {
        img.src = '/static/img/no-image.png';
        img.alt = `Imagem não encontrada: ${filename}`;
        img.title = `Arquivo de imagem não localizado: ${filename}`;

        // Adicionar classe de erro e informações visuais
        img.classList.add('image-error');
        img.style.border = '2px dashed #dc3545';
        img.style.opacity = '0.7';
        
        // Log detalhado para admin/debug
        const shortFilename = filename && filename.length > 20 ? `${filename.substring(0, 20)}...` : filename;
        console.warn(`⚠️ Imagem perdida: ${shortFilename}`);
        console.warn(`📍 Caminhos testados:`, alternativePaths);
        console.warn(`🔗 URL original tentada:`, originalSrc);
        
        // Reportar ao servidor para análise (opcional)
        if (typeof fetch !== 'undefined') {
            fetch('/admin/report-missing-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    originalSrc: originalSrc,
                    timestamp: new Date().toISOString()
                })
            }).catch(() => {}); // Silenciar erros para não impactar UX
        }
        
        // Adicionar evento de clique para tentar recuperar
        img.addEventListener('click', function() {
            if (confirm('Imagem não encontrada. Tentar recarregar?')) {
                img.dataset.errorHandled = '';
                img.src = img.dataset.originalSrc || originalSrc;
            }
        });
    }
    
    // Iniciar tentativas de caminhos alternativos
    tryNextPath();
}

// Aplicar handler global quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    // Adicionar handler para imagens existentes
    const images = document.querySelectorAll('img[src*="/uploads/"], img[src*="/attached_assets/"], img[src*="/static/uploads/"]');
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
                            node.querySelectorAll('img[src*="/uploads/"], img[src*="/attached_assets/"], img[src*="/static/uploads/"]') : [];

                        newImages.forEach(img => {
                            img.onerror = function() {
                                handleImageError(this);
                            };
                        });

                        // Se o próprio node for uma imagem
                        if (node.tagName === 'IMG' && node.src && 
                            (node.src.includes('/uploads/') || node.src.includes('/attached_assets/') || node.src.includes('/static/uploads/'))) {
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

// Função global para forçar recarregamento de imagens
window.reloadBrokenImages = function() {
    const brokenImages = document.querySelectorAll('img.image-error');
    brokenImages.forEach(img => {
        img.dataset.errorHandled = '';
        img.classList.remove('image-error');
        img.style.border = '';
        img.style.opacity = '';
        const originalSrc = img.dataset.originalSrc || img.src;
        img.src = originalSrc + '?reload=' + Date.now();
    });
    console.log(`🔄 Tentando recarregar ${brokenImages.length} imagens com erro`);
};
