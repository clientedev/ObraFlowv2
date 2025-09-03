/**
 * Sistema de Edição Profissional Estilo Canva - Coordenadas Corrigidas
 * Objetivos:
 * 1. Corrigir posicionamento (não mais canto superior esquerdo)
 * 2. Implementar pinch-to-resize 
 * 3. Rotação em qualquer grau
 * 4. Sistema de confirmação OK
 * 5. Múltiplos objetos
 */

class CanvaStyleEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.shapes = [];
        this.selectedShape = null;
        this.confirmedShapes = [];
        
        // Estados de interação
        this.isEditing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.isPinching = false;
        
        // Dados de controle
        this.dragStart = { x: 0, y: 0 };
        this.initialDistance = 0;
        this.initialSize = { width: 0, height: 0 };
        this.lastTouchDistance = 0;
        
        // Configuração do editor
        this.editMode = 'view'; // 'view', 'add', 'edit'
        this.currentTool = null;
        this.currentColor = '#ff0000';
        this.baseImage = null;
        this.devicePixelRatio = window.devicePixelRatio || 1;
        
        this.initializeCanvas();
        this.setupEventListeners();
        this.setupUI();
    }
    
    initializeCanvas() {
        // Configurar canvas com DPR correto
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * this.devicePixelRatio;
        this.canvas.height = rect.height * this.devicePixelRatio;
        this.ctx.scale(this.devicePixelRatio, this.devicePixelRatio);
        
        // Configurar CSS
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        
        // Prevenir comportamentos padrão
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
        this.canvas.addEventListener('selectstart', e => e.preventDefault());
    }

    setupEventListeners() {
        // Touch events com passive: false para preventDefault
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        this.canvas.addEventListener('touchcancel', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events para desktop
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('mouseleave', this.handleMouseUp.bind(this));
        
        // Prevenir zoom e scroll durante edição
        document.addEventListener('touchstart', (e) => {
            if (e.target === this.canvas || this.canvas.contains(e.target)) {
                if (this.editMode === 'add' || this.selectedShape) {
                    document.body.style.overflow = 'hidden';
                }
            }
        }, { passive: false });
        
        document.addEventListener('touchend', () => {
            document.body.style.overflow = '';
        });
    }

    /**
     * CORREÇÃO PRINCIPAL: Normalizar coordenadas corretamente
     * Considerando devicePixelRatio, scale e posição do canvas
     */
    getCanvasCoordinates(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        
        // Coordenadas CSS normalizadas
        const cssX = clientX - rect.left;
        const cssY = clientY - rect.top;
        
        // Coordenadas no sistema do canvas (considerando CSS sizing)
        const canvasX = (cssX / rect.width) * (this.canvas.width / this.devicePixelRatio);
        const canvasY = (cssY / rect.height) * (this.canvas.height / this.devicePixelRatio);
        
        return {
            x: Math.max(0, Math.min(canvasX, this.canvas.width / this.devicePixelRatio)),
            y: Math.max(0, Math.min(canvasY, this.canvas.height / this.devicePixelRatio))
        };
    }

    getTouchPos(touch) {
        return this.getCanvasCoordinates(touch.clientX, touch.clientY);
    }

    getMousePos(e) {
        return this.getCanvasCoordinates(e.clientX, e.clientY);
    }

    getPinchDistance(touch1, touch2) {
        const pos1 = this.getTouchPos(touch1);
        const pos2 = this.getTouchPos(touch2);
        
        return Math.sqrt(
            Math.pow(pos2.x - pos1.x, 2) + Math.pow(pos2.y - pos1.y, 2)
        );
    }

    getPinchCenter(touch1, touch2) {
        const pos1 = this.getTouchPos(touch1);
        const pos2 = this.getTouchPos(touch2);
        
        return {
            x: (pos1.x + pos2.x) / 2,
            y: (pos1.y + pos2.y) / 2
        };
    }

    handleTouchStart(e) {
        e.preventDefault();
        const touches = Array.from(e.touches);
        
        if (touches.length === 1) {
            // Toque simples - adicionar ou selecionar
            const pos = this.getTouchPos(touches[0]);
            this.handleSingleTouch(pos);
        } else if (touches.length === 2 && this.selectedShape) {
            // Pinch para redimensionar
            this.isPinching = true;
            this.initialDistance = this.getPinchDistance(touches[0], touches[1]);
            this.initialSize = { 
                width: this.selectedShape.width, 
                height: this.selectedShape.height 
            };
            
            console.log('Iniciando pinch:', {
                initialDistance: this.initialDistance,
                initialSize: this.initialSize
            });
        }
    }

    handleSingleTouch(pos) {
        console.log('Touch em:', pos);
        
        if (this.editMode === 'add' && this.currentTool) {
            this.addShape(pos);
        } else {
            this.selectShapeAt(pos);
            if (this.selectedShape && !this.selectedShape.confirmed) {
                this.isDragging = true;
                this.dragStart = {
                    x: pos.x - this.selectedShape.x,
                    y: pos.y - this.selectedShape.y
                };
            }
        }
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touches = Array.from(e.touches);
        
        if (touches.length === 1 && this.isDragging && this.selectedShape) {
            // Arrastar objeto
            const pos = this.getTouchPos(touches[0]);
            this.moveShape(pos);
            this.redraw();
        } else if (touches.length === 2 && this.isPinching && this.selectedShape) {
            // Redimensionar com pinch
            const currentDistance = this.getPinchDistance(touches[0], touches[1]);
            
            if (this.initialDistance > 0) {
                const scale = Math.max(0.2, Math.min(3, currentDistance / this.initialDistance));
                this.resizeShapeWithPinch(scale);
                this.redraw();
            }
        }
    }

    handleTouchEnd(e) {
        e.preventDefault();
        
        this.isDragging = false;
        this.isPinching = false;
        
        // Se há shape selecionada não confirmada, mostrar painel
        if (this.selectedShape && !this.selectedShape.confirmed) {
            this.showConfirmationPanel();
        }
    }

    handleMouseDown(e) {
        const pos = this.getMousePos(e);
        this.handleSingleTouch(pos);
    }

    handleMouseMove(e) {
        if (this.isDragging && this.selectedShape) {
            const pos = this.getMousePos(e);
            this.moveShape(pos);
            this.redraw();
        }
    }

    handleMouseUp(e) {
        this.isDragging = false;
        if (this.selectedShape && !this.selectedShape.confirmed) {
            this.showConfirmationPanel();
        }
    }

    addShape(pos) {
        console.log('Adicionando shape em:', pos);
        
        const shape = this.createShape(this.currentTool, pos);
        this.shapes.push(shape);
        this.selectedShape = shape;
        this.editMode = 'edit';
        
        this.redraw();
        this.showToolFeedback(`${this.getToolName(this.currentTool)} adicionado! Use pinça para redimensionar.`);
    }

    createShape(type, pos) {
        const baseShape = {
            id: Date.now(),
            type: type,
            x: pos.x - 40, // Centralizar no ponto tocado
            y: pos.y - 20,
            color: this.currentColor,
            rotation: 0,
            confirmed: false
        };

        switch (type) {
            case 'arrow':
                return { ...baseShape, width: 80, height: 20, direction: 0 };
            case 'circle':
                return { ...baseShape, width: 60, height: 60, x: pos.x - 30, y: pos.y - 30 };
            case 'rectangle':
                return { ...baseShape, width: 80, height: 50, x: pos.x - 40, y: pos.y - 25 };
            case 'text':
                return { ...baseShape, width: 100, height: 30, text: 'Texto', fontSize: 16, x: pos.x - 50, y: pos.y - 15 };
            default:
                return baseShape;
        }
    }

    selectShapeAt(pos) {
        this.selectedShape = null;
        
        // Verificar shapes não confirmadas primeiro (editáveis)
        for (let i = this.shapes.length - 1; i >= 0; i--) {
            const shape = this.shapes[i];
            if (!shape.confirmed && this.isPointInShape(pos, shape)) {
                this.selectedShape = shape;
                break;
            }
        }
        
        this.redraw();
        console.log('Shape selecionada:', this.selectedShape?.id || 'nenhuma');
    }

    isPointInShape(pos, shape) {
        const margin = 10;
        return pos.x >= shape.x - margin && 
               pos.x <= shape.x + shape.width + margin &&
               pos.y >= shape.y - margin && 
               pos.y <= shape.y + shape.height + margin;
    }

    moveShape(pos) {
        if (this.selectedShape) {
            this.selectedShape.x = pos.x - this.dragStart.x;
            this.selectedShape.y = pos.y - this.dragStart.y;
            
            // Manter dentro do canvas
            const maxX = (this.canvas.width / this.devicePixelRatio) - this.selectedShape.width;
            const maxY = (this.canvas.height / this.devicePixelRatio) - this.selectedShape.height;
            
            this.selectedShape.x = Math.max(0, Math.min(this.selectedShape.x, maxX));
            this.selectedShape.y = Math.max(0, Math.min(this.selectedShape.y, maxY));
        }
    }

    resizeShapeWithPinch(scale) {
        if (this.selectedShape) {
            const newWidth = Math.max(20, Math.min(200, this.initialSize.width * scale));
            const newHeight = Math.max(20, Math.min(200, this.initialSize.height * scale));
            
            // Ajustar posição para manter centro
            const deltaWidth = newWidth - this.selectedShape.width;
            const deltaHeight = newHeight - this.selectedShape.height;
            
            this.selectedShape.width = newWidth;
            this.selectedShape.height = newHeight;
            this.selectedShape.x -= deltaWidth / 2;
            this.selectedShape.y -= deltaHeight / 2;
            
            console.log('Redimensionando:', { scale, newWidth, newHeight });
        }
    }

    rotateShape(degrees) {
        if (this.selectedShape) {
            this.selectedShape.rotation = (this.selectedShape.rotation + degrees) % 360;
            this.redraw();
        }
    }

    changeShapeColor(color) {
        if (this.selectedShape) {
            this.selectedShape.color = color;
            this.redraw();
        }
        this.currentColor = color;
    }

    confirmShape() {
        if (this.selectedShape) {
            this.selectedShape.confirmed = true;
            this.confirmedShapes.push(this.selectedShape);
            
            const confirmedId = this.selectedShape.id;
            this.selectedShape = null;
            this.editMode = 'view';
            
            this.hideConfirmationPanel();
            this.redraw();
            
            this.showSuccessToast('✅ Figura confirmada e fixada!');
            console.log('Shape confirmada:', confirmedId);
        }
    }

    cancelShape() {
        if (this.selectedShape) {
            const index = this.shapes.indexOf(this.selectedShape);
            if (index > -1) {
                this.shapes.splice(index, 1);
            }
            this.selectedShape = null;
            this.editMode = 'view';
            
            this.hideConfirmationPanel();
            this.redraw();
            
            this.showSuccessToast('❌ Figura removida');
        }
    }

    showConfirmationPanel() {
        this.hideConfirmationPanel(); // Remove existing
        
        const panel = document.createElement('div');
        panel.id = 'canva-confirmation-panel';
        panel.className = 'position-fixed bg-white border rounded-3 shadow-lg p-3';
        panel.style.cssText = `
            bottom: 80px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            min-width: 320px;
            max-width: 90vw;
        `;
        
        panel.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-bold">
                    <i class="fas fa-edit me-2 text-primary"></i>Editando Figura
                </h6>
                <small class="text-muted">Toque ou use pinça</small>
            </div>
            
            <div class="d-flex justify-content-center gap-2 mb-3">
                <button class="btn btn-outline-primary btn-sm" onclick="canvaEditor.rotateShape(-15)" style="min-width: 50px;">
                    <i class="fas fa-undo"></i><br><small>-15°</small>
                </button>
                <button class="btn btn-outline-primary btn-sm" onclick="canvaEditor.rotateShape(15)" style="min-width: 50px;">
                    <i class="fas fa-redo"></i><br><small>+15°</small>
                </button>
                <div class="d-flex flex-column align-items-center">
                    <input type="color" class="form-control form-control-sm mb-1" 
                           style="width: 50px; height: 35px; border-radius: 25px;" 
                           onchange="canvaEditor.changeShapeColor(this.value)" 
                           value="${this.currentColor}">
                    <small class="text-muted">Cor</small>
                </div>
            </div>
            
            <div class="d-flex gap-2 justify-content-center">
                <button class="btn btn-success btn-sm px-4" onclick="canvaEditor.confirmShape()">
                    <i class="fas fa-check me-1"></i>OK
                </button>
                <button class="btn btn-outline-secondary btn-sm px-3" onclick="canvaEditor.cancelShape()">
                    <i class="fas fa-times me-1"></i>Cancelar
                </button>
            </div>
        `;
        
        document.body.appendChild(panel);
        
        // Auto-hide após 10 segundos
        setTimeout(() => {
            if (document.getElementById('canva-confirmation-panel') === panel) {
                this.hideConfirmationPanel();
            }
        }, 10000);
    }

    hideConfirmationPanel() {
        const panel = document.getElementById('canva-confirmation-panel');
        if (panel) {
            panel.remove();
        }
    }

    setupUI() {
        this.createToolbar();
    }

    createToolbar() {
        const container = document.getElementById('canva-toolbar-container');
        if (!container) return;
        
        const toolbar = document.createElement('div');
        toolbar.className = 'canva-mobile-toolbar p-3 border-bottom bg-light';
        toolbar.innerHTML = `
            <div class="row g-2">
                <div class="col-12 text-center mb-2">
                    <h6 class="mb-1 fw-bold text-primary">
                        <i class="fas fa-palette me-2"></i>Ferramentas de Desenho
                    </h6>
                    <small class="text-muted">Toque para adicionar · Pinça para redimensionar</small>
                </div>
                
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="arrow" style="min-height: 60px;">
                        <i class="fas fa-arrow-right d-block mb-1" style="font-size: 1.2rem;"></i>
                        <small class="fw-semibold">Seta</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="circle" style="min-height: 60px;">
                        <i class="far fa-circle d-block mb-1" style="font-size: 1.2rem;"></i>
                        <small class="fw-semibold">Círculo</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="rectangle" style="min-height: 60px;">
                        <i class="far fa-square d-block mb-1" style="font-size: 1.2rem;"></i>
                        <small class="fw-semibold">Retângulo</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="text" style="min-height: 60px;">
                        <i class="fas fa-font d-block mb-1" style="font-size: 1.2rem;"></i>
                        <small class="fw-semibold">Texto</small>
                    </button>
                </div>
            </div>
            
            <div class="row mt-3">
                <div class="col-12 text-center">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Objetos confirmados ficam fixos. Para editar, adicione novos.
                    </small>
                </div>
            </div>
        `;
        
        container.appendChild(toolbar);

        // Event listeners
        toolbar.querySelectorAll('.canva-tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;
                this.selectTool(tool);
                
                // Visual feedback
                toolbar.querySelectorAll('.canva-tool-btn').forEach(b => {
                    b.classList.remove('active', 'btn-primary');
                    b.classList.add('btn-outline-primary');
                });
                e.currentTarget.classList.remove('btn-outline-primary');
                e.currentTarget.classList.add('btn-primary', 'active');
            });
        });
    }

    selectTool(tool) {
        this.currentTool = tool;
        this.editMode = 'add';
        this.selectedShape = null;
        this.hideConfirmationPanel();
        
        const toolName = this.getToolName(tool);
        this.showToolFeedback(`${toolName} selecionado! Toque na imagem para adicionar.`);
        
        console.log('Ferramenta selecionada:', tool);
    }

    getToolName(tool) {
        const names = {
            'arrow': 'Seta',
            'circle': 'Círculo', 
            'rectangle': 'Retângulo',
            'text': 'Texto'
        };
        return names[tool] || tool;
    }

    showToolFeedback(message) {
        // Remove existing toast
        const existing = document.getElementById('canva-tool-toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.id = 'canva-tool-toast';
        toast.className = 'position-fixed bg-primary text-white rounded-3 px-3 py-2 shadow';
        toast.style.cssText = `
            top: 90px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            max-width: 90vw;
            text-align: center;
        `;
        toast.innerHTML = `<i class="fas fa-info-circle me-2"></i>${message}`;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transition = 'opacity 0.3s ease';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 3000);
    }

    showSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'position-fixed bg-success text-white rounded-3 px-3 py-2 shadow';
        toast.style.cssText = `
            top: 120px;
            right: 20px;
            z-index: 9999;
            max-width: 250px;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.transition = 'opacity 0.3s ease';
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }
        }, 2500);
    }

    setBaseImage(img) {
        this.baseImage = img;
        
        // Redimensionar canvas proporcionalmente
        const maxWidth = 800;
        const maxHeight = 600;
        const ratio = Math.min(maxWidth / img.width, maxHeight / img.height);
        
        const newWidth = img.width * ratio;
        const newHeight = img.height * ratio;
        
        this.canvas.width = newWidth * this.devicePixelRatio;
        this.canvas.height = newHeight * this.devicePixelRatio;
        this.ctx.scale(this.devicePixelRatio, this.devicePixelRatio);
        
        this.canvas.style.width = newWidth + 'px';
        this.canvas.style.height = newHeight + 'px';
        
        this.redraw();
        console.log('Imagem base definida:', { width: newWidth, height: newHeight, ratio });
    }

    redraw() {
        // Limpar canvas
        this.ctx.clearRect(0, 0, this.canvas.width / this.devicePixelRatio, this.canvas.height / this.devicePixelRatio);
        
        // Desenhar imagem base
        if (this.baseImage) {
            this.ctx.drawImage(this.baseImage, 0, 0, 
                this.canvas.width / this.devicePixelRatio, 
                this.canvas.height / this.devicePixelRatio);
        }
        
        // Desenhar todas as shapes
        this.shapes.forEach(shape => {
            this.drawShape(shape);
        });
        
        // Desenhar seleção se existir
        if (this.selectedShape && !this.selectedShape.confirmed) {
            this.drawSelectionBox(this.selectedShape);
        }
    }

    drawShape(shape) {
        this.ctx.save();
        
        // Aplicar transformações
        this.ctx.translate(shape.x + shape.width / 2, shape.y + shape.height / 2);
        this.ctx.rotate((shape.rotation * Math.PI) / 180);
        this.ctx.translate(-shape.width / 2, -shape.height / 2);
        
        // Estilo
        this.ctx.strokeStyle = shape.color;
        this.ctx.fillStyle = shape.color;
        this.ctx.lineWidth = shape.confirmed ? 2 : 3;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        if (shape.confirmed) {
            this.ctx.globalAlpha = 0.8;
        }
        
        // Desenhar por tipo
        switch (shape.type) {
            case 'arrow':
                this.drawArrow(shape);
                break;
            case 'circle':
                this.drawCircle(shape);
                break;
            case 'rectangle':
                this.drawRectangle(shape);
                break;
            case 'text':
                this.drawText(shape);
                break;
        }
        
        this.ctx.restore();
    }

    drawArrow(shape) {
        const ctx = this.ctx;
        const headLength = Math.min(shape.width * 0.25, 15);
        const bodyThickness = 4;
        
        ctx.beginPath();
        
        // Corpo da seta
        ctx.moveTo(0, shape.height / 2 - bodyThickness / 2);
        ctx.lineTo(shape.width - headLength, shape.height / 2 - bodyThickness / 2);
        ctx.lineTo(shape.width - headLength, shape.height / 4);
        ctx.lineTo(shape.width, shape.height / 2);
        ctx.lineTo(shape.width - headLength, (shape.height * 3) / 4);
        ctx.lineTo(shape.width - headLength, shape.height / 2 + bodyThickness / 2);
        ctx.lineTo(0, shape.height / 2 + bodyThickness / 2);
        ctx.closePath();
        
        ctx.fill();
    }

    drawCircle(shape) {
        const ctx = this.ctx;
        const radius = Math.min(shape.width, shape.height) / 2 - 2;
        const centerX = shape.width / 2;
        const centerY = shape.height / 2;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.stroke();
    }

    drawRectangle(shape) {
        const ctx = this.ctx;
        ctx.beginPath();
        ctx.rect(2, 2, shape.width - 4, shape.height - 4);
        ctx.stroke();
    }

    drawText(shape) {
        const ctx = this.ctx;
        ctx.font = `${shape.fontSize || 16}px Arial`;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'middle';
        ctx.fillText(shape.text || 'Texto', 5, shape.height / 2);
    }

    drawSelectionBox(shape) {
        this.ctx.save();
        this.ctx.strokeStyle = '#007bff';
        this.ctx.setLineDash([4, 4]);
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(shape.x - 6, shape.y - 6, shape.width + 12, shape.height + 12);
        
        // Handles de redimensionamento
        this.ctx.fillStyle = '#007bff';
        this.ctx.setLineDash([]);
        
        const handles = [
            { x: shape.x - 6, y: shape.y - 6 },
            { x: shape.x + shape.width + 6, y: shape.y - 6 },
            { x: shape.x - 6, y: shape.y + shape.height + 6 },
            { x: shape.x + shape.width + 6, y: shape.y + shape.height + 6 }
        ];
        
        handles.forEach(handle => {
            this.ctx.beginPath();
            this.ctx.arc(handle.x, handle.y, 4, 0, 2 * Math.PI);
            this.ctx.fill();
        });
        
        this.ctx.restore();
    }

    getCanvasDataURL() {
        // Criar canvas temporário sem seleção
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.canvas.width;
        tempCanvas.height = this.canvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCtx.scale(this.devicePixelRatio, this.devicePixelRatio);
        
        // Desenhar imagem base
        if (this.baseImage) {
            tempCtx.drawImage(this.baseImage, 0, 0, 
                this.canvas.width / this.devicePixelRatio, 
                this.canvas.height / this.devicePixelRatio);
        }
        
        // Desenhar apenas shapes confirmadas
        this.shapes.filter(s => s.confirmed).forEach(shape => {
            this.drawShapeOnContext(tempCtx, shape);
        });
        
        return tempCanvas.toDataURL('image/png');
    }

    drawShapeOnContext(ctx, shape) {
        ctx.save();
        
        ctx.translate(shape.x + shape.width / 2, shape.y + shape.height / 2);
        ctx.rotate((shape.rotation * Math.PI) / 180);
        ctx.translate(-shape.width / 2, -shape.height / 2);
        
        ctx.strokeStyle = shape.color;
        ctx.fillStyle = shape.color;
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        const originalCtx = this.ctx;
        this.ctx = ctx;
        
        switch (shape.type) {
            case 'arrow':
                this.drawArrow(shape);
                break;
            case 'circle':
                this.drawCircle(shape);
                break;
            case 'rectangle':
                this.drawRectangle(shape);
                break;
            case 'text':
                this.drawText(shape);
                break;
        }
        
        this.ctx = originalCtx;
        ctx.restore();
    }

    clearAll() {
        this.shapes = [];
        this.confirmedShapes = [];
        this.selectedShape = null;
        this.editMode = 'view';
        this.hideConfirmationPanel();
        this.redraw();
        this.showSuccessToast('🗑️ Todas as figuras removidas');
    }

    // Função para desfazer última ação
    undo() {
        if (this.shapes.length > 0) {
            const removed = this.shapes.pop();
            if (this.selectedShape === removed) {
                this.selectedShape = null;
                this.hideConfirmationPanel();
            }
            this.redraw();
            this.showSuccessToast('↶ Última figura removida');
        }
    }
}

// === FUNÇÕES GLOBAIS PARA INTEGRAÇÃO ===

let canvaEditor = null;

function initializeCanvaEditor(canvasId = 'photoCanvas') {
    try {
        canvaEditor = new CanvaStyleEditor(canvasId);
        console.log('✅ Canva Editor inicializado com sucesso');
        return canvaEditor;
    } catch (error) {
        console.error('❌ Erro ao inicializar Canva Editor:', error);
        return null;
    }
}

function applyCanvaEdits() {
    if (!canvaEditor) {
        console.error('Editor não inicializado');
        return;
    }
    
    try {
        const editedImageData = canvaEditor.getCanvasDataURL();
        
        // Converter para blob e atualizar input de arquivo
        fetch(editedImageData)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], 'edited-photo.png', { type: 'image/png' });
                const dt = new DataTransfer();
                dt.items.add(file);
                
                const fileInput = document.getElementById('foto');
                if (fileInput) {
                    fileInput.files = dt.files;
                }
                
                // Atualizar preview
                const preview = document.getElementById('imagePreview');
                if (preview) {
                    preview.src = editedImageData;
                }
                
                showGlobalSuccessMessage('✅ Edições aplicadas com sucesso! Imagem atualizada.');
                console.log('✅ Edições aplicadas com sucesso');
            })
            .catch(error => {
                console.error('Erro ao aplicar edições:', error);
                showGlobalErrorMessage('❌ Erro ao aplicar edições. Tente novamente.');
            });
    } catch (error) {
        console.error('Erro ao obter dados do canvas:', error);
        showGlobalErrorMessage('❌ Erro ao processar imagem editada.');
    }
}

function resetToOriginalPhoto() {
    const input = document.getElementById('foto');
    if (input && input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            // Atualizar preview
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
            }
            
            // Resetar editor
            if (canvaEditor) {
                canvaEditor.clearAll();
                
                const img = new Image();
                img.onload = function() {
                    canvaEditor.setBaseImage(img);
                };
                img.src = e.target.result;
            }
            
            showGlobalSuccessMessage('✅ Imagem original restaurada!');
            console.log('✅ Imagem original restaurada');
        };
        reader.readAsDataURL(input.files[0]);
    } else {
        showGlobalErrorMessage('❌ Nenhuma imagem original encontrada.');
    }
}

function clearAllShapes() {
    if (canvaEditor) {
        canvaEditor.clearAll();
        console.log('✅ Todas as figuras removidas');
    }
}

function undoLastShape() {
    if (canvaEditor) {
        canvaEditor.undo();
        console.log('✅ Última ação desfeita');
    }
}

// === SISTEMA DE MENSAGENS GLOBAIS ===

function showGlobalSuccessMessage(message, duration = 3000) {
    showGlobalMessage(message, 'success', duration);
}

function showGlobalErrorMessage(message, duration = 4000) {
    showGlobalMessage(message, 'danger', duration);
}

function showGlobalMessage(message, type = 'success', duration = 3000) {
    // Remove mensagem existente
    const existing = document.getElementById('global-toast-message');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.id = 'global-toast-message';
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed shadow-lg`;
    toast.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        min-width: 280px;
        max-width: 90vw;
        border-radius: 10px;
        border: none;
    `;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove
    setTimeout(() => {
        if (toast.parentNode) {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 150);
        }
    }, duration);
}

// === INICIALIZAÇÃO AUTOMÁTICA ===
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Canva Style Editor Fixed carregado');
    
    // Inicializar automaticamente se canvas existir
    setTimeout(() => {
        const canvas = document.getElementById('photoCanvas');
        if (canvas && !canvaEditor) {
            initializeCanvaEditor('photoCanvas');
        }
    }, 500);
});

// === DEBUGGING E LOGS ===
window.canvaEditor = canvaEditor;
window.canvaDebug = {
    getShapes: () => canvaEditor?.shapes || [],
    getConfirmedShapes: () => canvaEditor?.confirmedShapes || [],
    getCurrentTool: () => canvaEditor?.currentTool,
    getEditMode: () => canvaEditor?.editMode,
    clearAll: () => canvaEditor?.clearAll(),
    showInfo: () => {
        if (!canvaEditor) return console.log('Editor não inicializado');
        console.log('=== CANVA EDITOR STATUS ===');
        console.log('Shapes totais:', canvaEditor.shapes.length);
        console.log('Shapes confirmadas:', canvaEditor.confirmedShapes.length);
        console.log('Shape selecionada:', canvaEditor.selectedShape?.id || 'nenhuma');
        console.log('Ferramenta atual:', canvaEditor.currentTool || 'nenhuma');
        console.log('Modo de edição:', canvaEditor.editMode);
        console.log('DPR:', canvaEditor.devicePixelRatio);
        console.log('Canvas:', canvaEditor.canvas.width, 'x', canvaEditor.canvas.height);
    }
};