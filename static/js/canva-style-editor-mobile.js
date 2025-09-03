/**
 * Sistema de Edição Profissional Estilo Canva - Mobile Otimizado
 * Funcionalidades: Pinch-to-zoom, rotação, confirmação de objetos
 */

class CanvaStyleEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.shapes = [];
        this.selectedShape = null;
        this.confirmedShapes = [];
        this.isEditing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.isRotating = false;
        this.dragStart = { x: 0, y: 0 };
        this.initialDistance = 0;
        this.initialSize = { width: 0, height: 0 };
        this.initialRotation = 0;
        this.editMode = 'view';
        this.currentTool = null;
        this.currentColor = '#ff0000';
        this.baseImage = null;
        
        this.setupCanvas();
        this.setupEventListeners();
        this.setupUI();
    }
    
    setupCanvas() {
        // Configurar canvas responsivo
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
    }

    setupEventListeners() {
        // Touch events com prevenção de comportamentos padrão
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events para desktop
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Prevenir zoom e scroll durante edição
        this.canvas.addEventListener('touchstart', (e) => {
            if (this.editMode === 'add' || this.selectedShape) {
                e.preventDefault();
            }
        });
        this.canvas.addEventListener('touchmove', (e) => {
            if (this.editMode === 'add' || this.selectedShape) {
                e.preventDefault();
            }
        });
    }

    getCanvasCoordinates(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
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

    handleTouchStart(e) {
        e.preventDefault();
        const touches = e.touches;
        
        if (touches.length === 1) {
            // Toque simples
            const pos = this.getTouchPos(touches[0]);
            this.handleSingleTouch(pos);
        } else if (touches.length === 2 && this.selectedShape) {
            // Pinch para redimensionar
            this.initialDistance = this.getPinchDistance(touches[0], touches[1]);
            this.initialSize = { 
                width: this.selectedShape.width, 
                height: this.selectedShape.height 
            };
            this.isResizing = true;
        }
    }

    handleSingleTouch(pos) {
        if (this.editMode === 'add' && this.currentTool) {
            this.addShape(pos);
        } else {
            this.selectShapeAt(pos);
            if (this.selectedShape) {
                this.isDragging = true;
                this.dragStart = pos;
            }
        }
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touches = e.touches;
        
        if (touches.length === 1 && this.isDragging && this.selectedShape) {
            // Arrastar
            const pos = this.getTouchPos(touches[0]);
            this.moveShape(pos);
        } else if (touches.length === 2 && this.isResizing && this.selectedShape) {
            // Redimensionar com pinch
            const currentDistance = this.getPinchDistance(touches[0], touches[1]);
            const scale = currentDistance / this.initialDistance;
            this.resizeShape(scale);
        }
        
        this.redraw();
    }

    handleTouchEnd(e) {
        e.preventDefault();
        this.isDragging = false;
        this.isResizing = false;
        
        if (this.selectedShape && !this.selectedShape.confirmed) {
            this.showConfirmationButtons();
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
            this.showConfirmationButtons();
        }
    }

    addShape(pos) {
        const shape = this.createShape(this.currentTool, pos);
        this.shapes.push(shape);
        this.selectedShape = shape;
        this.editMode = 'edit';
        this.redraw();
    }

    createShape(type, pos) {
        const baseShape = {
            id: Date.now(),
            type: type,
            x: pos.x,
            y: pos.y,
            color: this.currentColor,
            rotation: 0,
            confirmed: false
        };

        switch (type) {
            case 'arrow':
                return { ...baseShape, width: 80, height: 20, direction: 0 };
            case 'circle':
                return { ...baseShape, width: 60, height: 60 };
            case 'rectangle':
                return { ...baseShape, width: 80, height: 50 };
            case 'text':
                return { ...baseShape, width: 100, height: 30, text: 'Texto', fontSize: 16 };
            default:
                return baseShape;
        }
    }

    selectShapeAt(pos) {
        this.selectedShape = null;
        
        // Verificar shapes não confirmadas primeiro
        for (let i = this.shapes.length - 1; i >= 0; i--) {
            if (!this.shapes[i].confirmed && this.isPointInShape(pos, this.shapes[i])) {
                this.selectedShape = this.shapes[i];
                break;
            }
        }
        
        this.redraw();
    }

    isPointInShape(pos, shape) {
        return pos.x >= shape.x - 10 && pos.x <= shape.x + shape.width + 10 &&
               pos.y >= shape.y - 10 && pos.y <= shape.y + shape.height + 10;
    }

    moveShape(pos) {
        if (this.selectedShape) {
            this.selectedShape.x = pos.x - this.selectedShape.width / 2;
            this.selectedShape.y = pos.y - this.selectedShape.height / 2;
        }
    }

    resizeShape(scale) {
        if (this.selectedShape) {
            this.selectedShape.width = Math.max(20, this.initialSize.width * scale);
            this.selectedShape.height = Math.max(20, this.initialSize.height * scale);
        }
    }

    rotateShape(angle) {
        if (this.selectedShape) {
            this.selectedShape.rotation = (this.selectedShape.rotation + angle) % 360;
            this.redraw();
        }
    }

    changeShapeColor(color) {
        if (this.selectedShape) {
            this.selectedShape.color = color;
            this.redraw();
        }
    }

    confirmShape() {
        if (this.selectedShape) {
            this.selectedShape.confirmed = true;
            this.confirmedShapes.push(this.selectedShape);
            this.selectedShape = null;
            this.editMode = 'view';
            this.hideConfirmationButtons();
            this.redraw();
            this.showSuccessToast('Figura confirmada!');
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
            this.hideConfirmationButtons();
            this.redraw();
        }
    }

    showConfirmationButtons() {
        let panel = document.getElementById('canva-confirmation-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'canva-confirmation-panel';
            panel.className = 'position-fixed bg-white border rounded shadow-lg p-3';
            panel.style.cssText = `
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
                min-width: 280px;
            `;
            
            panel.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0"><i class="fas fa-edit me-2"></i>Editar Figura</h6>
                </div>
                <div class="d-flex gap-2 mb-3">
                    <button class="btn btn-outline-primary btn-sm" onclick="canvaEditor.rotateShape(-15)">
                        <i class="fas fa-undo me-1"></i>↶
                    </button>
                    <button class="btn btn-outline-primary btn-sm" onclick="canvaEditor.rotateShape(15)">
                        <i class="fas fa-redo me-1"></i>↷
                    </button>
                    <input type="color" class="form-control form-control-sm" style="width: 50px;" 
                           onchange="canvaEditor.changeShapeColor(this.value)" value="${this.currentColor}">
                </div>
                <div class="d-flex gap-2 justify-content-center">
                    <button class="btn btn-success btn-sm" onclick="canvaEditor.confirmShape()">
                        <i class="fas fa-check me-1"></i>OK
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="canvaEditor.cancelShape()">
                        <i class="fas fa-times me-1"></i>Cancelar
                    </button>
                </div>
            `;
            
            document.body.appendChild(panel);
        }
        panel.style.display = 'block';
    }

    hideConfirmationButtons() {
        const panel = document.getElementById('canva-confirmation-panel');
        if (panel) {
            panel.style.display = 'none';
        }
    }

    setupUI() {
        this.createToolbar();
    }

    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'canva-mobile-toolbar p-3 border-bottom bg-light';
        toolbar.innerHTML = `
            <div class="row g-2">
                <div class="col-12 mb-2">
                    <h6 class="text-center mb-0"><i class="fas fa-tools me-2"></i>Ferramentas Canva</h6>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="arrow">
                        <i class="fas fa-arrow-right d-block mb-1"></i>
                        <small>Seta</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="circle">
                        <i class="far fa-circle d-block mb-1"></i>
                        <small>Círculo</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="rectangle">
                        <i class="far fa-square d-block mb-1"></i>
                        <small>Retângulo</small>
                    </button>
                </div>
                <div class="col-3">
                    <button class="btn btn-outline-primary btn-sm w-100 canva-tool-btn" data-tool="text">
                        <i class="fas fa-font d-block mb-1"></i>
                        <small>Texto</small>
                    </button>
                </div>
            </div>
        `;
        
        const container = document.getElementById('canva-toolbar-container');
        if (container) {
            container.appendChild(toolbar);
        }

        // Event listeners
        toolbar.querySelectorAll('.canva-tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;
                this.selectTool(tool);
                
                // Visual feedback
                toolbar.querySelectorAll('.canva-tool-btn').forEach(b => b.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });
    }

    selectTool(tool) {
        this.currentTool = tool;
        this.editMode = 'add';
        this.selectedShape = null;
        this.hideConfirmationButtons();
        this.showToolFeedback(`Toque na imagem para adicionar ${this.getToolName(tool)}`);
    }

    getToolName(tool) {
        const names = {
            'arrow': 'seta',
            'circle': 'círculo', 
            'rectangle': 'retângulo',
            'text': 'texto'
        };
        return names[tool] || tool;
    }

    showToolFeedback(message) {
        let toast = document.getElementById('canva-tool-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'canva-tool-toast';
            toast.className = 'position-fixed bg-primary text-white rounded px-3 py-2';
            toast.style.cssText = `
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 9999;
            `;
            document.body.appendChild(toast);
        }
        
        toast.textContent = message;
        toast.style.display = 'block';
        
        setTimeout(() => {
            toast.style.display = 'none';
        }, 2000);
    }

    showSuccessToast(message) {
        const toast = document.createElement('div');
        toast.className = 'position-fixed bg-success text-white rounded px-3 py-2';
        toast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        toast.innerHTML = `<i class="fas fa-check me-2"></i>${message}`;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 2000);
    }

    setBaseImage(img) {
        this.baseImage = img;
        
        // Ajustar canvas para imagem
        const maxWidth = 800;
        const maxHeight = 600;
        const ratio = Math.min(maxWidth / img.width, maxHeight / img.height);
        
        this.canvas.width = img.width * ratio;
        this.canvas.height = img.height * ratio;
        
        this.redraw();
    }

    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Desenhar imagem base
        if (this.baseImage) {
            this.ctx.drawImage(this.baseImage, 0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Desenhar todas as shapes
        this.shapes.forEach(shape => {
            this.drawShape(shape);
        });
        
        // Desenhar seleção
        if (this.selectedShape && !this.selectedShape.confirmed) {
            this.drawSelectionBox(this.selectedShape);
        }
    }

    drawShape(shape) {
        this.ctx.save();
        this.ctx.translate(shape.x + shape.width / 2, shape.y + shape.height / 2);
        this.ctx.rotate((shape.rotation * Math.PI) / 180);
        this.ctx.translate(-shape.width / 2, -shape.height / 2);
        
        this.ctx.strokeStyle = shape.color;
        this.ctx.fillStyle = shape.color;
        this.ctx.lineWidth = shape.confirmed ? 2 : 3;
        
        if (shape.confirmed) {
            this.ctx.globalAlpha = 0.8;
        }
        
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
        const headLength = Math.min(shape.width * 0.3, 20);
        
        ctx.beginPath();
        // Corpo da seta
        ctx.moveTo(0, shape.height / 2);
        ctx.lineTo(shape.width - headLength, shape.height / 2);
        
        // Ponta da seta
        ctx.lineTo(shape.width - headLength, shape.height / 4);
        ctx.lineTo(shape.width, shape.height / 2);
        ctx.lineTo(shape.width - headLength, (shape.height * 3) / 4);
        ctx.lineTo(shape.width - headLength, shape.height / 2);
        
        ctx.stroke();
    }

    drawCircle(shape) {
        const ctx = this.ctx;
        const radius = Math.min(shape.width, shape.height) / 2;
        const centerX = shape.width / 2;
        const centerY = shape.height / 2;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius - 2, 0, 2 * Math.PI);
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
        ctx.fillText(shape.text || 'Texto', 5, shape.height / 2 + 5);
    }

    drawSelectionBox(shape) {
        this.ctx.save();
        this.ctx.strokeStyle = '#007bff';
        this.ctx.setLineDash([5, 5]);
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(shape.x - 5, shape.y - 5, shape.width + 10, shape.height + 10);
        
        // Pontos de redimensionamento
        this.ctx.fillStyle = '#007bff';
        const handles = [
            { x: shape.x - 5, y: shape.y - 5 },
            { x: shape.x + shape.width + 5, y: shape.y - 5 },
            { x: shape.x - 5, y: shape.y + shape.height + 5 },
            { x: shape.x + shape.width + 5, y: shape.y + shape.height + 5 }
        ];
        
        handles.forEach(handle => {
            this.ctx.fillRect(handle.x - 3, handle.y - 3, 6, 6);
        });
        
        this.ctx.restore();
    }

    getCanvasDataURL() {
        return this.canvas.toDataURL('image/png');
    }

    clearAll() {
        this.shapes = [];
        this.confirmedShapes = [];
        this.selectedShape = null;
        this.editMode = 'view';
        this.hideConfirmationButtons();
        this.redraw();
    }
}

// Funções globais para integração com templates
let canvaEditor = null;

function initializeCanvaEditor(canvasId = 'photoCanvas') {
    canvaEditor = new CanvaStyleEditor(canvasId);
    return canvaEditor;
}

function applyCanvaEdits() {
    if (canvaEditor) {
        const editedImageData = canvaEditor.getCanvasDataURL();
        
        // Converter para blob e atualizar input
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
                
                showSuccessMessage('✓ Edições aplicadas com sucesso!');
            });
    }
}

function resetToOriginalPhoto() {
    const input = document.getElementById('foto');
    if (input && input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('imagePreview');
            if (preview) {
                preview.src = e.target.result;
            }
            
            if (canvaEditor) {
                canvaEditor.clearAll();
                
                const img = new Image();
                img.onload = function() {
                    canvaEditor.setBaseImage(img);
                };
                img.src = e.target.result;
            }
            
            showSuccessMessage('✓ Imagem original restaurada!');
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function clearAllShapes() {
    if (canvaEditor) {
        canvaEditor.clearAll();
        showSuccessMessage('✓ Todas as figuras foram removidas!');
    }
}

function showSuccessMessage(message) {
    const toast = document.createElement('div');
    toast.className = 'alert alert-success alert-dismissible fade show position-fixed';
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}