/**
 * Sistema de imagens com função global disponível imediatamente
 */

// Definir função global IMEDIATAMENTE
window.handleImageError = function(img) {
    // Evitar reprocessamento
    if (img.dataset.errorProcessed === 'true') {
        return;
    }

    const originalSrc = img.src;
    const filename = originalSrc.split('/').pop().split('?')[0];

    console.log('❌ Erro ao carregar imagem:', filename);

    // Marcar como processado
    img.dataset.errorProcessed = 'true';
    img.dataset.originalSrc = originalSrc;

    // Se já está usando placeholder, não fazer nada
    if (img.src.includes('no-image.png') || img.src.includes('placeholder')) {
        return;
    }

    // Tentar caminho correto: /uploads/filename
    const correctPath = `/uploads/${filename}`;

    console.log(`🔄 Tentando caminho correto: ${correctPath}`);

    // Criar imagem de teste
    const testImg = new Image();

    testImg.onload = function() {
        console.log(`✅ Sucesso: ${correctPath}`);
        img.src = correctPath;
        img.dataset.errorProcessed = 'false';

        // Remover estilos de erro
        img.classList.remove('image-error');
        img.style.border = '';
        img.style.opacity = '1';
        img.title = filename;
    };

    testImg.onerror = function() {
        console.log(`❌ Falhou: ${correctPath}, usando placeholder`);
        useImagePlaceholder(img, filename);
    };

    // Testar caminho
    testImg.src = correctPath;
};

// Função para usar placeholder
function useImagePlaceholder(img, filename) {
    // Usar placeholder específico
    img.src = '/static/img/no-image.png';
    img.alt = `Imagem não encontrada: ${filename}`;
    img.title = `Clique para tentar recarregar: ${filename}`;

    // Aplicar estilos de erro
    img.classList.add('image-error');
    img.style.border = '2px dashed #ffc107';
    img.style.opacity = '0.7';

    console.log(`📋 Placeholder aplicado: ${filename}`);

    // Adicionar evento de clique para reload manual
    img.onclick = function(e) {
        e.preventDefault();
        if (confirm(`Tentar recarregar ${filename}?`)) {
            const originalSrc = this.dataset.originalSrc;
            this.dataset.errorProcessed = 'false';
            this.classList.remove('image-error');
            this.style.border = '';
            this.style.opacity = '1';
            this.onclick = null;
            this.src = originalSrc + '?reload=' + Date.now();
        }
    };
}

// Função global para recarregar imagens com erro
window.reloadBrokenImages = function() {
    const brokenImages = document.querySelectorAll('img.image-error');
    console.log(`🔄 Recarregando ${brokenImages.length} imagens com erro`);

    brokenImages.forEach(img => {
        const originalSrc = img.dataset.originalSrc;
        if (originalSrc) {
            img.dataset.errorProcessed = 'false';
            img.classList.remove('image-error');
            img.style.border = '';
            img.style.opacity = '1';
            img.onclick = null;
            img.src = originalSrc + '?force=' + Date.now();
        }
    });

    return brokenImages.length;
};

// Log de carregamento
console.log('🖼️ Sistema de imagens carregado - handleImageError disponível globalmente');

// Aplicar handlers quando DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('🖼️ Inicializando handlers de imagem');

    // Função para aplicar handlers
    function applyImageHandlers() {
        // Selecionar todas as imagens que podem ter problemas
        const images = document.querySelectorAll('img[src*="/uploads/"], img[src*="/attached_assets/"], img[src*="relatorio"], img[src*="express"]');

        images.forEach(img => {
            if (!img.dataset.handlerApplied) {
                img.dataset.handlerApplied = 'true';

                // Aplicar handler de erro usando a função global
                img.onerror = function() {
                    window.handleImageError(this);
                };

                // Verificar se a imagem já falhou ao carregar
                if (img.complete && img.naturalWidth === 0) {
                    window.handleImageError(img);
                }
            }
        });

        console.log(`🖼️ Handlers aplicados em ${images.length} imagens`);
    }

    // Aplicar handlers iniciais
    applyImageHandlers();

    // Observer para novas imagens
    const observer = new MutationObserver(function(mutations) {
        let hasNewImages = false;

        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    if (node.tagName === 'IMG' || node.querySelector && node.querySelector('img')) {
                        hasNewImages = true;
                    }
                }
            });
        });

        if (hasNewImages) {
            setTimeout(applyImageHandlers, 200);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});