
/**
 * Sistema robusto para carregamento de imagens do banco de dados
 * Garante que imagens existentes sejam carregadas corretamente
 */

// Cache para imagens verificadas
const imageCache = new Map();
const retryAttempts = new Map();
const maxRetries = 2;

// Função principal para lidar com erros de imagem
function handleImageError(img) {
    const originalSrc = img.src;
    const filename = originalSrc.split('/').pop();
    
    console.log('🖼️ Tentando carregar imagem:', filename);
    
    // Evitar loop infinito
    if (img.dataset.errorHandled === 'processing' || img.src.includes('no-image.png')) {
        return;
    }
    
    // Marcar como sendo processada
    img.dataset.errorHandled = 'processing';
    
    // Salvar src original se ainda não foi salvo
    if (!img.dataset.originalSrc) {
        img.dataset.originalSrc = originalSrc;
    }
    
    // Verificar cache primeiro
    if (imageCache.has(filename)) {
        const cachedResult = imageCache.get(filename);
        if (cachedResult.exists) {
            img.src = cachedResult.url + '?cache=' + Date.now();
            img.dataset.errorHandled = 'resolved';
            return;
        } else {
            useImagePlaceholder();
            return;
        }
    }
    
    // Tentar diferentes caminhos para a imagem
    tryImagePaths();
    
    function tryImagePaths() {
        const attempts = retryAttempts.get(filename) || 0;
        
        if (attempts >= maxRetries) {
            console.warn(`⚠️ Máximo de tentativas atingido para: ${filename}`);
            useImagePlaceholder();
            return;
        }
        
        // Lista de caminhos possíveis para a imagem
        const possiblePaths = [
            `/uploads/${filename}`,
            `/uploads/${filename}?t=${Date.now()}`,
            `/static/uploads/${filename}`,
            `/attached_assets/${filename}`,
            `/static/img/${filename}`,
            originalSrc + '?reload=' + Date.now(),
            originalSrc.replace('/uploads/', '/attached_assets/'),
            originalSrc.replace('/attached_assets/', '/uploads/')
        ];
        
        let currentAttempt = 0;
        
        function tryNextPath() {
            if (currentAttempt >= possiblePaths.length) {
                console.warn(`⚠️ Todos os caminhos falharam para: ${filename}`);
                useImagePlaceholder();
                return;
            }
            
            const testPath = possiblePaths[currentAttempt];
            console.log(`🔍 Tentando caminho ${currentAttempt + 1}/${possiblePaths.length}: ${testPath}`);
            
            // Criar uma nova imagem para testar o caminho
            const testImg = new Image();
            
            testImg.onload = function() {
                console.log(`✅ Sucesso no caminho: ${testPath}`);
                
                // Cachear resultado positivo
                imageCache.set(filename, { exists: true, url: testPath });
                
                // Aplicar à imagem original
                img.src = testPath;
                img.dataset.errorHandled = 'resolved';
                
                // Remover indicadores visuais de erro
                img.classList.remove('image-error');
                img.style.border = '';
                img.style.opacity = '';
                img.title = '';
            };
            
            testImg.onerror = function() {
                console.log(`❌ Falhou caminho: ${testPath}`);
                currentAttempt++;
                
                // Pequeno delay antes da próxima tentativa
                setTimeout(tryNextPath, 100);
            };
            
            // Iniciar teste do caminho
            testImg.src = testPath;
        }
        
        // Incrementar contador de tentativas
        retryAttempts.set(filename, attempts + 1);
        
        // Iniciar tentativas
        tryNextPath();
    }
    
    function useImagePlaceholder() {
        // Cachear resultado negativo
        imageCache.set(filename, { exists: false, url: null });
        
        img.src = '/static/img/no-image.png';
        img.alt = `Imagem: ${filename}`;
        img.title = `Clique para tentar recarregar: ${filename}`;
        
        // Adicionar classe de erro e estilo visual
        img.classList.add('image-error');
        img.style.border = '2px dashed #ffc107';
        img.style.opacity = '0.8';
        img.dataset.errorHandled = 'placeholder';
        
        console.log(`📋 Placeholder aplicado para: ${filename}`);
        
        // Adicionar evento de clique para tentar recarregar manualmente
        img.addEventListener('click', function() {
            if (confirm(`Tentar recarregar imagem: ${filename}?`)) {
                // Limpar cache e tentar novamente
                imageCache.delete(filename);
                retryAttempts.delete(filename);
                img.dataset.errorHandled = '';
                img.classList.remove('image-error');
                img.style.border = '';
                img.style.opacity = '';
                
                // Tentar carregar novamente
                img.src = img.dataset.originalSrc || originalSrc;
            }
        });
    }
}

// Aplicar handler global quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🖼️ Sistema robusto de imagens inicializado');
    
    // Aplicar handler para imagens existentes
    applyImageHandlers();
    
    // Observer para imagens adicionadas dinamicamente
    const observer = new MutationObserver(function(mutations) {
        let hasNewImages = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) {
                        if (node.tagName === 'IMG' || node.querySelectorAll) {
                            hasNewImages = true;
                        }
                    }
                });
            }
        });
        
        if (hasNewImages) {
            setTimeout(applyImageHandlers, 100);
        }
    });
    
    // Observar mudanças no DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Função para aplicar handlers em imagens
function applyImageHandlers() {
    const images = document.querySelectorAll('img[src*="/uploads/"], img[src*="/attached_assets/"], img[src*="express_"], img[src*="_edited"], img[src*="relatorio_"]');
    
    images.forEach(img => {
        // Só aplicar se ainda não foi processado
        if (!img.dataset.handlerApplied) {
            img.dataset.handlerApplied = 'true';
            
            img.onerror = function() {
                handleImageError(this);
            };
            
            // Se a imagem já falhou no carregamento, tentar recarregar
            if (!img.complete || img.naturalWidth === 0) {
                setTimeout(() => {
                    if (!img.complete || img.naturalWidth === 0) {
                        handleImageError(img);
                    }
                }, 500);
            }
        }
    });
    
    console.log(`🖼️ Handlers aplicados em ${images.length} imagens`);
}

// Função global para forçar recarregamento de todas as imagens com erro
window.reloadAllBrokenImages = function() {
    const brokenImages = document.querySelectorAll('img.image-error');
    let reloadCount = 0;
    
    brokenImages.forEach(img => {
        const filename = img.dataset.originalSrc?.split('/').pop();
        if (filename) {
            // Limpar cache e contadores
            imageCache.delete(filename);
            retryAttempts.delete(filename);
            
            // Limpar estado de erro
            img.dataset.errorHandled = '';
            img.classList.remove('image-error');
            img.style.border = '';
            img.style.opacity = '';
            
            // Tentar recarregar
            const originalSrc = img.dataset.originalSrc;
            img.src = originalSrc + '?force=' + Date.now();
            reloadCount++;
        }
    });
    
    console.log(`🔄 Tentando recarregar ${reloadCount} imagens com erro`);
    return reloadCount;
};

// Função para limpar cache de imagens
window.clearImageCache = function() {
    imageCache.clear();
    retryAttempts.clear();
    console.log('🧹 Cache de imagens limpo');
};

// Função para verificar status das imagens
window.getImageStatus = function() {
    const total = document.querySelectorAll('img[src*="/uploads/"], img[src*="/attached_assets/"]').length;
    const errors = document.querySelectorAll('img.image-error').length;
    const cached = imageCache.size;
    
    console.log(`📊 Status das imagens: ${total} total, ${errors} com erro, ${cached} em cache`);
    return { total, errors, cached };
};
