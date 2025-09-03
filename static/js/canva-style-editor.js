/**
 * Sistema de Edição Profissional Estilo Canva
 * Funcionalidade: Adicionar formas, redimensionar, posicionar, confirmar
 */

class CanvaStyleEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.shapes = [];
        this.selectedShape = null;
        this.isEditing = false;
        this.isDragging = false;
        this.isResizing = false;
        this.dragStart = { x: 0, y: 0 };
        this.resizeHandle = null;
        this.editMode = 'view'; // 'view', 'add', 'edit'
        this.pendingShape = null;
        this.currentTool = null;
        
        this.setupEventListeners();
        this.setupUI();
    }

    setupEventListeners() {
        // Touch events otimizados
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events para desktop
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        
        // Prevent default behaviors
        this.canvas.addEventListener('touchstart', (e) => e.preventDefault());
        this.canvas.addEventListener('touchmove', (e) => e.preventDefault());
    }

    setupUI() {
        this.createCanvaToolbar();
        this.createEditingPanel();
    }

    createCanvaToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'canva-toolbar';
        toolbar.innerHTML = `
            <div class="canva-tool-section">
                <h6><i class="fas fa-shapes me-2"></i>Figuras</h6>
                <div class="canva-shapes-grid">
                    <button class="canva-shape-btn" data-shape="arrow">
                        <i class="fas fa-arrow-right"></i>
                        <span>Seta</span>
                    </button>
                    <button class="canva-shape-btn" data-shape="circle">
                        <i class="far fa-circle"></i>
                        <span>Círculo</span>
                    </button>
                    <button class="canva-shape-btn" data-shape="rectangle">
                        <i class="far fa-square"></i>
                        <span>Retângulo</span>
                    </button>
                    <button class="canva-shape-btn" data-shape="text">
                        <i class="fas fa-font"></i>
                        <span>Texto</span>
                    </button>
                </div>
            </div>
            
            <div class="canva-tool-section">
                <h6><i class="fas fa-palette me-2"></i>Cores</h6>
                <div class="canva-color-grid">
                    <div class="canva-color-preset" data-color="#ff0000" style="background: #ff0000"></div>
                    <div class="canva-color-preset" data-color="#00ff00" style="background: #00ff00"></div>
                    <div class="canva-color-preset" data-color="#0066ff" style="background: #0066ff"></div>
                    <div class="canva-color-preset" data-color="#ffff00" style="background: #ffff00"></div>
                    <div class="canva-color-preset" data-color="#ff8800" style="background: #ff8800"></div>
                    <div class="canva-color-preset" data-color="#8800ff" style="background: #8800ff"></div>
                    <input type="color" id="canva-custom-color" value="#ff0000">
                </div>
            </div>
        `;
        
        const container = this.canvas.parentElement;
        container.insertBefore(toolbar, this.canvas);
        
        // Event listeners para shapes
        toolbar.querySelectorAll('.canva-shape-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectShapeTool(e.currentTarget.dataset.shape);
            });
        });
        
        // Event listeners para cores
        toolbar.querySelectorAll('.canva-color-preset').forEach(preset => {
            preset.addEventListener('click', (e) => {
                this.selectColor(e.currentTarget.dataset.color);
            });
        });
        
        document.getElementById('canva-custom-color').addEventListener('change', (e) => {
            this.selectColor(e.target.value);
        });
    }

    createEditingPanel() {
        const panel = document.createElement('div');
        panel.className = 'canva-editing-panel';
        panel.style.display = 'none';
        panel.innerHTML = `
            <div class="canva-edit-header">
                <h5><i class="fas fa-edit me-2"></i>Editando Figura</h5>
                <button class="btn btn-sm btn-outline-secondary" id="canva-cancel-edit">
                    <i class="fas fa-times me-1"></i>Cancelar
                </button>
            </div>
            
            <div class="canva-edit-controls">
                <div class="row">
                    <div class="col-6">
                        <label class="form-label">Largura</label>
                        <input type="range" class="form-range" id="canva-width-slider" 
                               min="20" max="200" value="100">
                        <span id="canva-width-value">100px</span>
                    </div>
                    <div class="col-6">
                        <label class="form-label">Altura</label>
                        <input type="range" class="form-range" id="canva-height-slider" 
                               min="20" max="200" value="100">
                        <span id="canva-height-value">100px</span>
                    </div>
                </div>
                
                <div class="row mt-3">
                    <div class="col-6">
                        <label class="form-label">Posição X</label>
                        <input type="range" class="form-range" id="canva-x-slider" 
                               min="0" max="400" value="100">
                        <span id="canva-x-value">100px</span>
                    </div>
                    <div class="col-6">
                        <label class="form-label">Posição Y</label>
                        <input type="range" class="form-range" id="canva-y-slider" 
                               min="0" max="400" value="100">
                        <span id="canva-y-value">100px</span>
                    </div>
                </div>
                
                <div class="mt-3" id="canva-text-controls" style="display: none;">
                    <label class="form-label">Texto</label>
                    <input type="text" class="form-control" id="canva-text-input" 
                           placeholder="Digite o texto...">
                    <label class="form-label mt-2">Tamanho da Fonte</label>
                    <input type="range" class="form-range" id="canva-font-size" 
                           min="12" max="48" value="16">
                    <span id="canva-font-value">16px</span>
                </div>
            </div>
            
            <div class="canva-edit-actions">
                <button class="btn btn-danger me-2" id="canva-delete-shape">
                    <i class="fas fa-trash me-1"></i>Excluir
                </button>
                <button class="btn btn-success" id="canva-confirm-edit">
                    <i class="fas fa-check me-1"></i>Confirmar
                </button>
            </div>
        `;
        
        const container = this.canvas.parentElement;
        container.appendChild(panel);
        
        this.setupEditingListeners();
    }

    setupEditingListeners() {
        // Sliders de controle
        document.getElementById('canva-width-slider').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('width', parseInt(e.target.value));
            document.getElementById('canva-width-value').textContent = e.target.value + 'px';
        });
        
        document.getElementById('canva-height-slider').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('height', parseInt(e.target.value));
            document.getElementById('canva-height-value').textContent = e.target.value + 'px';
        });
        
        document.getElementById('canva-x-slider').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('x', parseInt(e.target.value));
            document.getElementById('canva-x-value').textContent = e.target.value + 'px';
        });
        
        document.getElementById('canva-y-slider').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('y', parseInt(e.target.value));
            document.getElementById('canva-y-value').textContent = e.target.value + 'px';
        });
        
        document.getElementById('canva-text-input').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('text', e.target.value);
        });
        
        document.getElementById('canva-font-size').addEventListener('input', (e) => {
            this.updateSelectedShapeProperty('fontSize', parseInt(e.target.value));
            document.getElementById('canva-font-value').textContent = e.target.value + 'px';
        });
        
        // Botões de ação
        document.getElementById('canva-cancel-edit').addEventListener('click', () => {
            this.cancelEdit();
        });
        
        document.getElementById('canva-delete-shape').addEventListener('click', () => {
            this.deleteSelectedShape();
        });
        
        document.getElementById('canva-confirm-edit').addEventListener('click', () => {
            this.confirmEdit();
        });
    }

    selectShapeTool(shapeType) {
        this.currentTool = shapeType;
        this.editMode = 'add';
        this.canvas.style.cursor = 'crosshair';
        
        // Highlight selected tool
        document.querySelectorAll('.canva-shape-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-shape="${shapeType}"]`).classList.add('active');
        
        console.log(`Ferramenta selecionada: ${shapeType}`);
    }

    selectColor(color) {
        this.currentColor = color;
        
        // Highlight selected color
        document.querySelectorAll('.canva-color-preset').forEach(preset => {
            preset.classList.remove('active');
        });
        document.querySelector(`[data-color="${color}"]`)?.classList.add('active');
        
        if (this.selectedShape) {
            this.updateSelectedShapeProperty('color', color);
        }
        
        console.log(`Cor selecionada: ${color}`);
    }

    handleTouchStart(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const x = (touch.clientX - rect.left) * (this.canvas.width / rect.width);
        const y = (touch.clientY - rect.top) * (this.canvas.height / rect.height);
        
        this.handleStart(x, y);
    }

    handleTouchMove(e) {
        e.preventDefault();
        const touch = e.touches[0];
        const rect = this.canvas.getBoundingClientRect();
        const x = (touch.clientX - rect.left) * (this.canvas.width / rect.width);
        const y = (touch.clientY - rect.top) * (this.canvas.height / rect.height);
        
        this.handleMove(x, y);
    }

    handleTouchEnd(e) {
        e.preventDefault();
        this.handleEnd();
    }

    handleMouseDown(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        
        this.handleStart(x, y);
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left) * (this.canvas.width / rect.width);
        const y = (e.clientY - rect.top) * (this.canvas.height / rect.height);
        
        this.handleMove(x, y);
    }

    handleMouseUp(e) {
        this.handleEnd();
    }

    handleStart(x, y) {
        if (this.editMode === 'add' && this.currentTool) {
            this.createNewShape(x, y);
        } else if (this.editMode === 'view' || this.editMode === 'edit') {
            this.handleShapeSelection(x, y);
        }
    }

    handleMove(x, y) {
        if (this.isDragging && this.selectedShape) {
            this.selectedShape.x = x - this.dragStart.x;
            this.selectedShape.y = y - this.dragStart.y;
            this.redraw();
            this.updateEditingPanel();
        }
    }

    handleEnd() {
        this.isDragging = false;
        this.isResizing = false;
    }

    createNewShape(x, y) {
        const shape = {
            id: Date.now(),
            type: this.currentTool,
            x: x - 50,
            y: y - 50,
            width: 100,
            height: 100,
            color: this.currentColor || '#ff0000',
            text: this.currentTool === 'text' ? 'Texto' : '',
            fontSize: 16
        };
        
        this.shapes.push(shape);
        this.selectShape(shape);
        this.editMode = 'edit';
        this.currentTool = null;
        
        // Reset tool selection
        document.querySelectorAll('.canva-shape-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        this.canvas.style.cursor = 'default';
        this.redraw();
        this.showEditingPanel();
        
        console.log(`Nova forma criada: ${shape.type}`);
    }

    handleShapeSelection(x, y) {
        const clickedShape = this.getShapeAtPoint(x, y);
        
        if (clickedShape) {
            this.selectShape(clickedShape);
            this.editMode = 'edit';
            this.showEditingPanel();
            
            // Setup dragging
            this.isDragging = true;
            this.dragStart = {
                x: x - clickedShape.x,
                y: y - clickedShape.y
            };
        } else {
            this.deselectShape();
        }
    }

    getShapeAtPoint(x, y) {
        // Check shapes in reverse order (last drawn first)
        for (let i = this.shapes.length - 1; i >= 0; i--) {
            const shape = this.shapes[i];
            if (x >= shape.x && x <= shape.x + shape.width &&
                y >= shape.y && y <= shape.y + shape.height) {
                return shape;
            }
        }
        return null;
    }

    selectShape(shape) {
        this.selectedShape = shape;
        this.redraw();
    }

    deselectShape() {
        this.selectedShape = null;
        this.editMode = 'view';
        this.hideEditingPanel();
        this.redraw();
    }

    showEditingPanel() {
        const panel = document.querySelector('.canva-editing-panel');
        panel.style.display = 'block';
        this.updateEditingPanel();
    }

    hideEditingPanel() {
        const panel = document.querySelector('.canva-editing-panel');
        panel.style.display = 'none';
    }

    updateEditingPanel() {
        if (!this.selectedShape) return;
        
        const shape = this.selectedShape;
        
        // Update sliders
        document.getElementById('canva-width-slider').value = shape.width;
        document.getElementById('canva-width-value').textContent = shape.width + 'px';
        
        document.getElementById('canva-height-slider').value = shape.height;
        document.getElementById('canva-height-value').textContent = shape.height + 'px';
        
        document.getElementById('canva-x-slider').value = shape.x;
        document.getElementById('canva-x-value').textContent = shape.x + 'px';
        
        document.getElementById('canva-y-slider').value = shape.y;
        document.getElementById('canva-y-value').textContent = shape.y + 'px';
        
        // Show/hide text controls
        const textControls = document.getElementById('canva-text-controls');
        if (shape.type === 'text') {
            textControls.style.display = 'block';
            document.getElementById('canva-text-input').value = shape.text;
            document.getElementById('canva-font-size').value = shape.fontSize;
            document.getElementById('canva-font-value').textContent = shape.fontSize + 'px';
        } else {
            textControls.style.display = 'none';
        }
    }

    updateSelectedShapeProperty(property, value) {
        if (!this.selectedShape) return;
        
        this.selectedShape[property] = value;
        this.redraw();
    }

    deleteSelectedShape() {
        if (!this.selectedShape) return;
        
        const index = this.shapes.findIndex(s => s.id === this.selectedShape.id);
        if (index > -1) {
            this.shapes.splice(index, 1);
        }
        
        this.deselectShape();
        console.log('Forma excluída');
    }

    confirmEdit() {
        this.deselectShape();
        console.log('Edição confirmada');
        
        // Show success message
        this.showSuccessMessage('Figura editada com sucesso!');
    }

    cancelEdit() {
        // If it's a new shape, remove it
        if (this.selectedShape && !this.shapes.some(s => s.id === this.selectedShape.id)) {
            // Shape was just created, remove it
        }
        
        this.deselectShape();
        console.log('Edição cancelada');
    }

    showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'canva-toast';
        toast.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }

    drawShape(shape) {
        this.ctx.fillStyle = shape.color;
        this.ctx.strokeStyle = shape.color;
        this.ctx.lineWidth = 3;
        
        switch (shape.type) {
            case 'rectangle':
                this.ctx.fillRect(shape.x, shape.y, shape.width, shape.height);
                break;
                
            case 'circle':
                this.ctx.beginPath();
                const radius = Math.min(shape.width, shape.height) / 2;
                this.ctx.arc(
                    shape.x + shape.width / 2,
                    shape.y + shape.height / 2,
                    radius,
                    0,
                    2 * Math.PI
                );
                this.ctx.fill();
                break;
                
            case 'arrow':
                this.drawArrow(shape);
                break;
                
            case 'text':
                this.ctx.font = `${shape.fontSize}px Arial`;
                this.ctx.fillText(shape.text, shape.x, shape.y + shape.fontSize);
                break;
        }
        
        // Draw selection handles if selected
        if (this.selectedShape && this.selectedShape.id === shape.id) {
            this.drawSelectionHandles(shape);
        }
    }

    drawArrow(shape) {
        const startX = shape.x;
        const startY = shape.y + shape.height / 2;
        const endX = shape.x + shape.width;
        const endY = shape.y + shape.height / 2;
        
        // Arrow line
        this.ctx.beginPath();
        this.ctx.moveTo(startX, startY);
        this.ctx.lineTo(endX, endY);
        this.ctx.stroke();
        
        // Arrow head
        const headLength = 15;
        const angle = Math.atan2(endY - startY, endX - startX);
        
        this.ctx.beginPath();
        this.ctx.moveTo(endX, endY);
        this.ctx.lineTo(
            endX - headLength * Math.cos(angle - Math.PI / 6),
            endY - headLength * Math.sin(angle - Math.PI / 6)
        );
        this.ctx.moveTo(endX, endY);
        this.ctx.lineTo(
            endX - headLength * Math.cos(angle + Math.PI / 6),
            endY - headLength * Math.sin(angle + Math.PI / 6)
        );
        this.ctx.stroke();
    }

    drawSelectionHandles(shape) {
        this.ctx.fillStyle = '#20c1e8';
        this.ctx.strokeStyle = '#fff';
        this.ctx.lineWidth = 2;
        
        const handleSize = 8;
        const handles = [
            { x: shape.x - handleSize / 2, y: shape.y - handleSize / 2 },
            { x: shape.x + shape.width - handleSize / 2, y: shape.y - handleSize / 2 },
            { x: shape.x - handleSize / 2, y: shape.y + shape.height - handleSize / 2 },
            { x: shape.x + shape.width - handleSize / 2, y: shape.y + shape.height - handleSize / 2 }
        ];
        
        handles.forEach(handle => {
            this.ctx.fillRect(handle.x, handle.y, handleSize, handleSize);
            this.ctx.strokeRect(handle.x, handle.y, handleSize, handleSize);
        });
        
        // Selection border
        this.ctx.strokeStyle = '#20c1e8';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        this.ctx.strokeRect(shape.x, shape.y, shape.width, shape.height);
        this.ctx.setLineDash([]);
    }

    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Redraw base image if exists
        if (this.baseImage) {
            this.ctx.drawImage(this.baseImage, 0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Draw all shapes
        this.shapes.forEach(shape => {
            this.drawShape(shape);
        });
    }

    setBaseImage(image) {
        this.baseImage = image;
        this.redraw();
    }

    getCanvasDataURL() {
        return this.canvas.toDataURL('image/png');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const canvas = document.getElementById('photoCanvas');
    if (canvas) {
        window.canvaEditor = new CanvaStyleEditor('photoCanvas');
        console.log('Editor estilo Canva inicializado');
    }
});