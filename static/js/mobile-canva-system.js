/**
 * Sistema Mobile Canva Profissional - Funcionalidades Completas
 * Implementa todas as funcionalidades pedidas:
 * - Tap-to-add objetos
 * - Pinch-to-resize 
 * - Rotação -15°/+15°
 * - Seletor de cores
 * - Sistema OK de confirmação
 * - Coordenadas precisas
 */

class MobileCanvaSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.currentTool = null;
        this.currentColor = '#ff0000';
        this.objects = [];
        this.activeObject = null;
        this.baseImage = null;
        
        // Estados de interação
        this.isDragging = false;
        this.isResizing = false;
        this.startTouch = null;
        this.initialDistance = 0;
        this.initialSize = 1;
        
        console.log('🎯 Mobile Canva System iniciado');
    }
    
    init(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('❌ Canvas não encontrado');
            return false;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.setupCanvas();
        this.setupEventListeners();
        this.setupToolbar();
        
        console.log('✅ Canvas configurado com sucesso');
        return true;
    }
    
    setupCanvas() {
        // Configurar canvas para mobile
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        this.canvas.style.position = 'relative';
        this.canvas.style.display = 'block';
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
        
        // Prevenir comportamentos padrão
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
        this.canvas.addEventListener('selectstart', e => e.preventDefault());
    }
    
    setupEventListeners() {
        // Touch events otimizados
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
    }
    
    setupToolbar() {
        // Configurar botões de ferramentas
        this.setupToolButtons();
        this.setupColorPicker();
        this.setupControlButtons();
    }
    
    setupToolButtons() {
        const tools = ['arrow', 'circle', 'rectangle', 'text'];
        
        tools.forEach(tool => {
            const btn = document.querySelector(`[data-tool="${tool}"]`);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.selectTool(tool);
                });
                
                // Área de toque mínima 44px
                btn.style.minWidth = '44px';
                btn.style.minHeight = '44px';
                btn.style.padding = '12px';
                btn.style.touchAction = 'manipulation';
            }
        });
    }
    
    setupColorPicker() {
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff', '#000000', '#ffffff'];
        
        colors.forEach(color => {
            const btn = document.querySelector(`[data-color="${color}"]`);
            if (btn) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.selectColor(color);
                });
                
                // Configurar área de toque
                btn.style.minWidth = '44px';
                btn.style.minHeight = '44px';
                btn.style.touchAction = 'manipulation';
            }
        });
    }
    
    setupControlButtons() {
        // Botões de rotação
        const rotateLeft = document.getElementById('rotateLeft');
        const rotateRight = document.getElementById('rotateRight');
        const confirmBtn = document.getElementById('confirmObject');
        
        if (rotateLeft) {
            rotateLeft.addEventListener('click', (e) => {
                e.preventDefault();
                this.rotateActiveObject(-15);
            });
        }
        
        if (rotateRight) {
            rotateRight.addEventListener('click', (e) => {
                e.preventDefault();
                this.rotateActiveObject(15);
            });
        }
        
        if (confirmBtn) {
            confirmBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.confirmActiveObject();
            });
        }
    }
    
    selectTool(tool) {
        this.currentTool = tool;
        
        // Atualizar UI
        document.querySelectorAll('[data-tool]').forEach(btn => {
            btn.classList.remove('active', 'btn-primary');
            btn.classList.add('btn-outline-primary');
        });
        
        const activeBtn = document.querySelector(`[data-tool="${tool}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('btn-outline-primary');
            activeBtn.classList.add('active', 'btn-primary');
        }
        
        console.log(`🔧 Ferramenta selecionada: ${tool}`);
        this.showInstructions(`Toque na imagem para adicionar ${tool}`);
    }
    
    selectColor(color) {
        this.currentColor = color;
        
        // Atualizar UI
        document.querySelectorAll('[data-color]').forEach(btn => {
            btn.classList.remove('selected');
            btn.style.border = '2px solid #ddd';
        });
        
        const activeColor = document.querySelector(`[data-color="${color}"]`);
        if (activeColor) {
            activeColor.classList.add('selected');
            activeColor.style.border = '3px solid #007bff';
        }
        
        console.log(`🎨 Cor selecionada: ${color}`);
    }
    
    handleTouchStart(event) {
        event.preventDefault();
        
        const touches = event.touches;
        const rect = this.canvas.getBoundingClientRect();
        
        if (touches.length === 1) {
            // Toque único - adicionar objeto
            const touch = touches[0];
            
            // Coordenadas normalizadas precisas
            const x = ((touch.clientX - rect.left) / rect.width) * this.canvas.width;
            const y = ((touch.clientY - rect.top) / rect.height) * this.canvas.height;
            
            console.log(`📍 Toque em: (${Math.round(x)}, ${Math.round(y)})`);
            
            if (this.currentTool) {
                this.addObject(x, y);
            }
        } else if (touches.length === 2 && this.activeObject) {
            // Pinch-to-resize
            this.startPinchResize(touches);
        }
    }
    
    handleTouchMove(event) {
        event.preventDefault();
        
        if (event.touches.length === 2 && this.activeObject && this.isResizing) {
            this.updatePinchResize(event.touches);
        }
    }
    
    handleTouchEnd(event) {
        event.preventDefault();
        
        if (this.isResizing) {
            this.isResizing = false;
            console.log(`📏 Redimensionamento finalizado: ${this.activeObject.size}`);
        }
    }
    
    addObject(x, y) {
        if (!this.currentTool) return;
        
        const object = {
            id: Date.now(),
            type: this.currentTool,
            x: x,
            y: y,
            color: this.currentColor,
            size: 50,
            rotation: 0,
            text: this.currentTool === 'text' ? 'Texto' : null,
            confirmed: false
        };
        
        this.objects.push(object);
        this.activeObject = object;
        this.redrawCanvas();
        this.showObjectControls();
        
        console.log(`✨ Objeto ${this.currentTool} adicionado em (${Math.round(x)}, ${Math.round(y)})`);
    }
    
    startPinchResize(touches) {
        this.isResizing = true;
        this.initialDistance = this.getTouchDistance(touches);
        this.initialSize = this.activeObject.size;
        
        console.log('🤏 Iniciando pinch-to-resize');
    }
    
    updatePinchResize(touches) {
        const currentDistance = this.getTouchDistance(touches);
        const scale = currentDistance / this.initialDistance;
        
        this.activeObject.size = Math.max(20, Math.min(200, this.initialSize * scale));
        this.redrawCanvas();
    }
    
    getTouchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    rotateActiveObject(degrees) {
        if (!this.activeObject) return;
        
        this.activeObject.rotation += degrees;
        
        // Normalizar rotação (0-360)
        if (this.activeObject.rotation >= 360) this.activeObject.rotation -= 360;
        if (this.activeObject.rotation < 0) this.activeObject.rotation += 360;
        
        this.redrawCanvas();
        console.log(`🔄 Rotação: ${this.activeObject.rotation}°`);
    }
    
    confirmActiveObject() {
        if (!this.activeObject) return;
        
        this.activeObject.confirmed = true;
        console.log(`✅ Objeto confirmado: ${this.activeObject.type}`);
        
        this.activeObject = null;
        this.hideObjectControls();
        this.showInstructions('Objeto confirmado! Selecione uma ferramenta para continuar.');
    }
    
    setBaseImage(img) {
        this.baseImage = img;
        
        // Ajustar canvas para imagem
        const aspectRatio = img.height / img.width;
        this.canvas.width = 800;
        this.canvas.height = 800 * aspectRatio;
        
        this.redrawCanvas();
        console.log('🖼️ Imagem base carregada');
    }
    
    redrawCanvas() {
        // Limpar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Desenhar imagem base
        if (this.baseImage) {
            this.ctx.drawImage(this.baseImage, 0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Desenhar todos os objetos
        this.objects.forEach(obj => this.drawObject(obj));
        
        // Destacar objeto ativo
        if (this.activeObject && !this.activeObject.confirmed) {
            this.drawObjectHighlight(this.activeObject);
        }
    }
    
    drawObject(obj) {
        this.ctx.save();
        this.ctx.translate(obj.x, obj.y);
        this.ctx.rotate((obj.rotation * Math.PI) / 180);
        this.ctx.strokeStyle = obj.color;
        this.ctx.fillStyle = obj.color;
        this.ctx.lineWidth = 3;
        
        switch (obj.type) {
            case 'arrow':
                this.drawArrow(obj.size);
                break;
            case 'circle':
                this.drawCircle(obj.size);
                break;
            case 'rectangle':
                this.drawRectangle(obj.size);
                break;
            case 'text':
                this.drawText(obj.text, obj.size);
                break;
        }
        
        this.ctx.restore();
    }
    
    drawArrow(size) {
        this.ctx.beginPath();
        this.ctx.moveTo(-size/2, 0);
        this.ctx.lineTo(size/2, 0);
        this.ctx.lineTo(size/2 - 10, -8);
        this.ctx.moveTo(size/2, 0);
        this.ctx.lineTo(size/2 - 10, 8);
        this.ctx.stroke();
    }
    
    drawCircle(size) {
        this.ctx.beginPath();
        this.ctx.arc(0, 0, size/2, 0, 2 * Math.PI);
        this.ctx.stroke();
    }
    
    drawRectangle(size) {
        const half = size / 2;
        this.ctx.strokeRect(-half, -half, size, size);
    }
    
    drawText(text, size) {
        this.ctx.font = `${size/3}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.fillText(text || 'Texto', 0, 0);
    }
    
    drawObjectHighlight(obj) {
        this.ctx.save();
        this.ctx.translate(obj.x, obj.y);
        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        
        const size = obj.size + 20;
        const half = size / 2;
        this.ctx.strokeRect(-half, -half, size, size);
        
        this.ctx.restore();
    }
    
    showObjectControls() {
        const controls = document.getElementById('objectControls');
        if (controls) {
            controls.style.display = 'block';
        }
        
        this.showInstructions('Use os controles abaixo para ajustar o objeto');
    }
    
    hideObjectControls() {
        const controls = document.getElementById('objectControls');
        if (controls) {
            controls.style.display = 'none';
        }
    }
    
    showInstructions(message) {
        const instructions = document.getElementById('canvaInstructions');
        if (instructions) {
            instructions.textContent = message;
            instructions.style.display = 'block';
            
            // Auto hide após 3 segundos
            setTimeout(() => {
                instructions.style.display = 'none';
            }, 3000);
        }
    }
    
    exportCanvas() {
        return this.canvas.toDataURL('image/jpeg', 0.8);
    }
}

// Instância global
window.mobileCanvaSystem = null;

// Função de inicialização
function initializeMobileCanva(canvasId) {
    if (!window.mobileCanvaSystem) {
        window.mobileCanvaSystem = new MobileCanvaSystem();
    }
    
    return window.mobileCanvaSystem.init(canvasId);
}

// Funções globais para compatibilidade
function selectTool(tool) {
    if (window.mobileCanvaSystem) {
        window.mobileCanvaSystem.selectTool(tool);
    }
}

function selectColor(color) {
    if (window.mobileCanvaSystem) {
        window.mobileCanvaSystem.selectColor(color);
    }
}

function rotateActiveObject(degrees) {
    if (window.mobileCanvaSystem) {
        window.mobileCanvaSystem.rotateActiveObject(degrees);
    }
}

function confirmActiveObject() {
    if (window.mobileCanvaSystem) {
        window.mobileCanvaSystem.confirmActiveObject();
    }
}

console.log('📱 Mobile Canva System carregado');