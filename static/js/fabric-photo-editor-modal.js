/**
 * Editor de Fotos Modal - Integrado com Fabric.js
 * Versão otimizada para relatórios express
 * ==============================================
 */

class FabricPhotoEditorModal {
    constructor(modalId, canvasId) {
        this.modalId = modalId;
        this.canvasId = canvasId;
        this.canvas = null;
        this.photoEditor = null;
        this.currentPhotoData = null;
        this.currentPhotoId = null;
        this.onSaveCallback = null;
        
        console.log('🎨 Fabric Photo Editor Modal inicializado');
    }
    
    async openEditor(photoData, photoId, saveCallback) {
        console.log('📷 Abrindo editor para foto:', photoId);
        
        this.currentPhotoData = photoData;
        this.currentPhotoId = photoId;
        this.onSaveCallback = saveCallback;
        
        // Abrir modal
        const modal = document.getElementById(this.modalId);
        if (modal) {
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Aguardar modal estar totalmente visível
            modal.addEventListener('shown.bs.modal', () => {
                this.initEditor();
            }, { once: true });
        }
    }
    
    async initEditor() {
        try {
            console.log('🚀 Inicializando Fabric.js no modal');
            
            // Limpar editor anterior se existir
            if (this.photoEditor) {
                this.photoEditor.destroy();
                this.photoEditor = null;
            }
            
            // Criar novo editor
            this.photoEditor = new FabricPhotoEditor(this.canvasId, this.currentPhotoData);
            
            // Configurar eventos do modal
            this.setupModalEvents();
            
            console.log('✅ Editor modal inicializado');
            
            // Auto-scroll para o centro da imagem após inicializar
            setTimeout(() => {
                this.scrollToImageCenter();
            }, 200);
            
        } catch (error) {
            console.error('❌ Erro ao inicializar editor modal:', error);
        }
    }
    
    // Função para fazer auto-scroll para o centro da imagem - Melhorada para mobile
    scrollToImageCenter() {
        const modal = document.getElementById(this.modalId);
        const canvasContainer = modal?.querySelector('.canvas-container');
        const isMobile = window.innerWidth <= 768;
        
        if (canvasContainer) {
            // Para mobile, usar scroll suave com fallback
            if (isMobile) {
                // Scroll manual para mobile com melhor suporte
                const containerRect = canvasContainer.getBoundingClientRect();
                const viewportHeight = window.innerHeight;
                const scrollTop = window.pageYOffset + containerRect.top - (viewportHeight / 2) + (containerRect.height / 2);
                
                window.scrollTo({
                    top: Math.max(0, scrollTop),
                    behavior: 'smooth'
                });
            } else {
                // Desktop - usar scrollIntoView
                canvasContainer.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center',
                    inline: 'center'
                });
            }
            
            console.log('🎨 Auto-scroll para centro da imagem executado');
        }
    }
    
    setupModalEvents() {
        const modal = document.getElementById(this.modalId);
        if (!modal) return;
        
        // Botão salvar
        const saveBtn = modal.querySelector('#modal-save-btn');
        if (saveBtn) {
            saveBtn.onclick = () => this.saveAndClose();
        }
        
        // Botão cancelar
        const cancelBtn = modal.querySelector('#modal-cancel-btn');
        if (cancelBtn) {
            cancelBtn.onclick = () => this.closeEditor();
        }
        
        // Limpar ao fechar modal
        modal.addEventListener('hidden.bs.modal', () => {
            this.cleanup();
        });
    }
    
    async saveAndClose() {
        if (!this.photoEditor) return;
        
        try {
            console.log('💾 Salvando foto editada...');
            
            // Obter dados da imagem editada
            const imageData = this.photoEditor.getCanvasImage('image/jpeg', 0.9);
            const legend = document.getElementById('modal-custom-legend')?.value || '';
            
            // Chamar callback de salvamento
            if (this.onSaveCallback) {
                await this.onSaveCallback({
                    photoId: this.currentPhotoId,
                    imageData: imageData,
                    legend: legend
                });
            }
            
            this.closeEditor();
            
        } catch (error) {
            console.error('❌ Erro ao salvar foto:', error);
            alert('Erro ao salvar foto. Tente novamente.');
        }
    }
    
    closeEditor() {
        const modal = document.getElementById(this.modalId);
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }
    
    cleanup() {
        if (this.photoEditor) {
            this.photoEditor.destroy();
            this.photoEditor = null;
        }
        
        this.currentPhotoData = null;
        this.currentPhotoId = null;
        this.onSaveCallback = null;
        
        console.log('🧹 Editor modal limpo');
    }
    
    // Métodos para controlar o editor
    setTool(tool) {
        if (this.photoEditor) {
            this.photoEditor.setTool(tool);
        }
    }
    
    setColor(color) {
        if (this.photoEditor) {
            this.photoEditor.setColor(color);
        }
    }
    
    setStrokeWidth(width) {
        if (this.photoEditor) {
            this.photoEditor.setStrokeWidth(width);
        }
    }
    
    undo() {
        if (this.photoEditor) {
            this.photoEditor.undo();
        }
    }
    
    redo() {
        if (this.photoEditor) {
            this.photoEditor.redo();
        }
    }
    
    clear() {
        if (this.photoEditor) {
            this.photoEditor.clear();
        }
    }
}

// Instância global do editor modal
window.fabricPhotoEditorModal = null;

// Função para inicializar o editor modal
function initFabricPhotoEditorModal() {
    if (!window.fabricPhotoEditorModal) {
        window.fabricPhotoEditorModal = new FabricPhotoEditorModal('fabricPhotoEditorModal', 'fabricModalCanvas');
        console.log('📱 Editor modal pronto para uso');
    }
}

// Função para abrir editor de uma foto
async function openPhotoEditorFromElement(photoElement) {
    try {
        const photoSrc = photoElement.src;
        const photoId = photoElement.dataset.photoId || Date.now();
        
        if (!window.fabricPhotoEditorModal) {
            initFabricPhotoEditorModal();
        }
        
        // Callback para salvar a foto editada
        const saveCallback = async (data) => {
            console.log('💾 Salvando foto via callback:', data.photoId);
            
            // Atualizar preview da foto
            if (photoElement) {
                photoElement.src = data.imageData;
                photoElement.dataset.edited = 'true';
                photoElement.dataset.legend = data.legend;
            }
            
            // Marcar como editada visualmente
            const photoContainer = photoElement.closest('.photo-container');
            if (photoContainer) {
                photoContainer.classList.add('edited');
                
                // Adicionar badge de editado
                if (!photoContainer.querySelector('.edited-badge')) {
                    const badge = document.createElement('div');
                    badge.className = 'edited-badge';
                    badge.innerHTML = '<i class="fas fa-edit"></i> Editado';
                    photoContainer.appendChild(badge);
                }
            }
            
            console.log('✅ Foto salva com sucesso');
        };
        
        await window.fabricPhotoEditorModal.openEditor(photoSrc, photoId, saveCallback);
        
    } catch (error) {
        console.error('❌ Erro ao abrir editor:', error);
        alert('Erro ao abrir editor de fotos. Tente novamente.');
    }
}

// Event listeners globais para editor
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Configurando listeners do editor modal');
    
    // Listeners para botões de ferramentas do modal - OTIMIZADO PARA MOBILE
    const isMobile = 'ontouchstart' in window || window.innerWidth <= 768;
    
    // Função para lidar com seleção de ferramenta
    function handleToolSelection(e, tool) {
        e.preventDefault();
        e.stopPropagation();
        
        // Feedback visual imediato
        e.target.style.transform = 'scale(0.95)';
        setTimeout(() => {
            e.target.style.transform = '';
        }, 100);
        
        if (window.fabricPhotoEditorModal) {
            window.fabricPhotoEditorModal.setTool(tool);
            
            // Atualizar estado visual dos botões
            document.querySelectorAll('[data-modal-tool]').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.modalTool === tool);
            });
            
            console.log('🔧 Ferramenta modal selecionada:', tool);
        }
    }
    
    if (isMobile) {
        // Para mobile: usar apenas touchend para evitar conflitos
        document.addEventListener('touchend', function(e) {
            if (e.target.matches('[data-modal-tool]')) {
                const tool = e.target.dataset.modalTool;
                handleToolSelection(e, tool);
            }
        }, { passive: false });
        
        // Prevenir click em mobile para evitar duplo disparo
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-modal-tool]')) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
        
        // Prevenir touchstart e touchmove em botões para evitar scroll
        document.addEventListener('touchstart', function(e) {
            if (e.target.matches('[data-modal-tool]')) {
                e.preventDefault();
            }
        }, { passive: false });
        
        document.addEventListener('touchmove', function(e) {
            if (e.target.matches('[data-modal-tool]')) {
                e.preventDefault();
            }
        }, { passive: false });
        
    } else {
        // Para desktop: usar click normal
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-modal-tool]')) {
                const tool = e.target.dataset.modalTool;
                handleToolSelection(e, tool);
            }
        });
    }
    
    // Click listener para outros elementos
    document.addEventListener('click', function(e) {
        // Botão de editar foto
        if (e.target.matches('.edit-photo-btn') || e.target.closest('.edit-photo-btn')) {
            const btn = e.target.matches('.edit-photo-btn') ? e.target : e.target.closest('.edit-photo-btn');
            const photoElement = btn.closest('.photo-container')?.querySelector('img');
            
            if (photoElement) {
                openPhotoEditor(photoElement);
            }
        }
    });
    
    // Listener para mudanças de cor
    document.addEventListener('change', function(e) {
        if (e.target.matches('#modal-color-picker')) {
            const color = e.target.value;
            if (window.fabricPhotoEditorModal) {
                window.fabricPhotoEditorModal.setColor(color);
            }
        }
        
        if (e.target.matches('#modal-stroke-width')) {
            const width = parseInt(e.target.value);
            if (window.fabricPhotoEditorModal) {
                window.fabricPhotoEditorModal.setStrokeWidth(width);
            }
        }
    });
});

console.log('📱 Fabric Photo Editor Modal v2.0 - Sistema carregado');