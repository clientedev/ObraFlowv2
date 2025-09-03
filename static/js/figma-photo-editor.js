/**
 * EDITOR DE FOTOS ESTILO FIGMA - MOBILE FIRST
 * Sistema profissional de edição com coordenadas precisas
 */

class FigmaPhotoEditor {
    constructor(canvasId) {
        console.log('🎨 Inicializando Figma Photo Editor');
        
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.baseImage = null;
        
        // Sistema de objetos
        this.objects = [];
        this.selectedObject = null;
        this.currentTool = null;
        this.currentColor = '#ff0000';
        
        // Estados de interação
        this.isDragging = false;
        this.isResizing = false;
        this.dragStartPos = { x: 0, y: 0 };
        this.objectStartPos = { x: 0, y: 0 };
        this.lastTouchDistance = 0;
        this.initialObjectSize = 0;
        
        this.setupCanvas();
        this.setupEventListeners();
        
        console.log('✅ Figma Editor iniciado');
    }
    
    setupCanvas() {
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        this.canvas.style.cursor = 'crosshair';
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
    }
    
    setupEventListeners() {
        // Touch Events
        this.canvas.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.onTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.onTouchEnd.bind(this), { passive: false });
        
        // Mouse Events
        this.canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
    }
    
    // === COORDENADAS PRECISAS - CORRIGIDO ===
    getCanvasCoordinates(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        
        // Coordenadas exatas sem escala - aparece onde tocou
        const x = clientX - rect.left;
        const y = clientY - rect.top;
        
        // Verificar se está dentro do canvas
        if (x >= 0 && y >= 0 && x <= rect.width && y <= rect.height) {
            return { x, y };
        }
        
        return { x: 0, y: 0 };
    }
    
    // === EVENTOS TOUCH ===
    onTouchStart(event) {
        event.preventDefault();
        
        const touches = event.touches;
        if (touches.length === 1) {
            const touch = touches[0];
            const coords = this.getCanvasCoordinates(touch.clientX, touch.clientY);
            this.handleSingleTouch(coords.x, coords.y);
        } else if (touches.length === 2) {
            this.handlePinchStart(touches);
        }
    }
    
    onTouchMove(event) {
        event.preventDefault();
        
        const touches = event.touches;
        if (touches.length === 1 && this.isDragging) {
            const touch = touches[0];
            const coords = this.getCanvasCoordinates(touch.clientX, touch.clientY);
            this.handleDragMove(coords.x, coords.y);
        } else if (touches.length === 2 && this.isResizing) {
            this.handlePinchMove(touches);
        }
    }
    
    onTouchEnd(event) {
        event.preventDefault();
        this.handleInteractionEnd();
    }
    
    // === EVENTOS MOUSE ===
    onMouseDown(event) {
        const coords = this.getCanvasCoordinates(event.clientX, event.clientY);
        this.handleSingleTouch(coords.x, coords.y);
    }
    
    onMouseMove(event) {
        if (this.isDragging) {
            const coords = this.getCanvasCoordinates(event.clientX, event.clientY);
            this.handleDragMove(coords.x, coords.y);
        }
    }
    
    onMouseUp(event) {
        this.handleInteractionEnd();
    }
    
    // === LÓGICA DE INTERAÇÃO ===
    handleSingleTouch(x, y) {
        console.log(`👆 Touch em: (${Math.round(x)}, ${Math.round(y)})`);
        
        const clickedObject = this.getObjectAtPosition(x, y);
        
        if (clickedObject) {
            this.selectObject(clickedObject);
            this.startDragging(x, y);
        } else {
            if (this.currentTool) {
                this.createNewObject(x, y);
            } else {
                this.deselectAll();
            }
        }
    }
    
    createNewObject(x, y) {
        if (!this.currentTool) return;
        
        const newObject = {
            id: Date.now(),
            type: this.currentTool,
            x: x,
            y: y,
            width: 60,
            height: 60,
            rotation: 0,
            color: this.currentColor,
            selected: true,
            text: this.currentTool === 'text' ? 'Texto' : null
        };
        
        this.objects.forEach(obj => obj.selected = false);
        this.objects.push(newObject);
        this.selectedObject = newObject;
        
        this.redraw();
        this.showObjectControls();
        
        console.log(`✨ Novo ${this.currentTool} criado em (${Math.round(x)}, ${Math.round(y)})`);
    }
    
    selectObject(object) {
        this.objects.forEach(obj => obj.selected = false);
        object.selected = true;
        this.selectedObject = object;
        
        this.redraw();
        this.showObjectControls();
        
        console.log(`🎯 Objeto selecionado: ${object.type}`);
    }
    
    deselectAll() {
        this.objects.forEach(obj => obj.selected = false);
        this.selectedObject = null;
        this.hideObjectControls();
        this.redraw();
    }
    
    startDragging(x, y) {
        if (!this.selectedObject) return;
        
        this.isDragging = true;
        this.dragStartPos = { x, y };
        this.objectStartPos = { x: this.selectedObject.x, y: this.selectedObject.y };
        this.canvas.style.cursor = 'move';
    }
    
    handleDragMove(x, y) {
        if (!this.isDragging || !this.selectedObject) return;
        
        const deltaX = x - this.dragStartPos.x;
        const deltaY = y - this.dragStartPos.y;
        
        this.selectedObject.x = this.objectStartPos.x + deltaX;
        this.selectedObject.y = this.objectStartPos.y + deltaY;
        
        this.redraw();
    }
    
    handlePinchStart(touches) {
        if (!this.selectedObject) return;
        
        this.isResizing = true;
        this.lastTouchDistance = this.getTouchDistance(touches);
        this.initialObjectSize = Math.max(this.selectedObject.width, this.selectedObject.height);
        
        console.log('🤏 Pinch-to-resize iniciado');
    }
    
    handlePinchMove(touches) {
        if (!this.isResizing || !this.selectedObject) return;
        
        const currentDistance = this.getTouchDistance(touches);
        const scale = currentDistance / this.lastTouchDistance;
        
        const newSize = Math.max(20, Math.min(200, this.initialObjectSize * scale));
        this.selectedObject.width = newSize;
        this.selectedObject.height = newSize;
        
        this.redraw();
    }
    
    getTouchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    handleInteractionEnd() {
        this.isDragging = false;
        this.isResizing = false;
        this.canvas.style.cursor = this.currentTool ? 'crosshair' : 'default';
    }
    
    // === DETECÇÃO DE OBJETOS ===
    getObjectAtPosition(x, y) {
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (this.isPointInObject(x, y, obj)) {
                return obj;
            }
        }
        return null;
    }
    
    isPointInObject(x, y, obj) {
        const halfWidth = obj.width / 2;
        const halfHeight = obj.height / 2;
        
        return x >= obj.x - halfWidth && 
               x <= obj.x + halfWidth &&
               y >= obj.y - halfHeight && 
               y <= obj.y + halfHeight;
    }
    
    // === RENDERIZAÇÃO ===
    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.baseImage) {
            this.ctx.drawImage(this.baseImage, 0, 0, this.canvas.width, this.canvas.height);
        }
        
        this.objects.forEach(obj => this.drawObject(obj));
    }
    
    drawObject(obj) {
        this.ctx.save();
        
        this.ctx.translate(obj.x, obj.y);
        
        if (obj.rotation) {
            this.ctx.rotate((obj.rotation * Math.PI) / 180);
        }
        
        this.ctx.strokeStyle = obj.color;
        this.ctx.fillStyle = obj.color;
        this.ctx.lineWidth = 3;
        
        switch (obj.type) {
            case 'arrow':
                this.drawArrow(obj);
                break;
            case 'circle':
                this.drawCircle(obj);
                break;
            case 'rectangle':
                this.drawRectangle(obj);
                break;
            case 'text':
                this.drawText(obj);
                break;
        }
        
        this.ctx.restore();
        
        if (obj.selected) {
            this.drawSelectionIndicator(obj);
        }
    }
    
    drawArrow(obj) {
        const length = obj.width;
        this.ctx.beginPath();
        this.ctx.moveTo(-length/2, 0);
        this.ctx.lineTo(length/2, 0);
        this.ctx.moveTo(length/2 - 12, -8);
        this.ctx.lineTo(length/2, 0);
        this.ctx.lineTo(length/2 - 12, 8);
        this.ctx.stroke();
    }
    
    drawCircle(obj) {
        this.ctx.beginPath();
        this.ctx.arc(0, 0, obj.width/2, 0, 2 * Math.PI);
        this.ctx.stroke();
    }
    
    drawRectangle(obj) {
        const x = -obj.width / 2;
        const y = -obj.height / 2;
        this.ctx.strokeRect(x, y, obj.width, obj.height);
    }
    
    drawText(obj) {
        this.ctx.font = `${obj.height/2}px Arial`;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(obj.text || 'Texto', 0, 0);
    }
    
    drawSelectionIndicator(obj) {
        this.ctx.save();
        this.ctx.strokeStyle = '#007bff';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([8, 4]);
        
        const padding = 10;
        const x = obj.x - obj.width/2 - padding;
        const y = obj.y - obj.height/2 - padding;
        const w = obj.width + padding * 2;
        const h = obj.height + padding * 2;
        
        this.ctx.strokeRect(x, y, w, h);
        
        this.ctx.setLineDash([]);
        this.ctx.fillStyle = '#007bff';
        this.ctx.fillRect(x + w - 6, y + h - 6, 12, 12);
        
        this.ctx.restore();
    }
    
    // === INTERFACE PÚBLICA ===
    setTool(tool) {
        this.currentTool = tool;
        this.canvas.style.cursor = tool ? 'crosshair' : 'default';
        
        document.querySelectorAll('[data-tool]').forEach(btn => {
            btn.classList.remove('active');
            btn.classList.remove('express-btn-primary');
            btn.classList.add('express-btn-outline-primary');
            if (btn.dataset.tool === tool) {
                btn.classList.add('active');
                btn.classList.remove('express-btn-outline-primary');
                btn.classList.add('express-btn-primary');
            }
        });
        
        console.log(`🔧 Ferramenta: ${tool}`);
        this.showInstructions(`Toque na imagem para adicionar ${tool}`);
    }
    
    setColor(color) {
        this.currentColor = color;
        
        document.querySelectorAll('[data-color]').forEach(btn => {
            btn.classList.remove('selected');
            btn.style.border = '2px solid #ddd';
            if (btn.dataset.color === color) {
                btn.classList.add('selected');
                btn.style.border = '3px solid #007bff';
            }
        });
        
        if (this.selectedObject) {
            this.selectedObject.color = color;
            this.redraw();
        }
        
        console.log(`🎨 Cor: ${color}`);
    }
    
    rotateSelected(degrees) {
        if (this.selectedObject) {
            this.selectedObject.rotation += degrees;
            if (this.selectedObject.rotation >= 360) this.selectedObject.rotation -= 360;
            if (this.selectedObject.rotation < 0) this.selectedObject.rotation += 360;
            this.redraw();
            console.log(`🔄 Rotação: ${this.selectedObject.rotation}°`);
        }
    }
    
    confirmSelected() {
        if (this.selectedObject) {
            this.deselectAll();
            this.showInstructions('Objeto confirmado! Selecione uma ferramenta para continuar.');
        }
    }
    
    clearAll() {
        this.objects = [];
        this.selectedObject = null;
        this.hideObjectControls();
        this.redraw();
        console.log('🗑️ Objetos removidos');
    }
    
    setBaseImage(image) {
        this.baseImage = image;
        
        const aspectRatio = image.height / image.width;
        this.canvas.width = 800;
        this.canvas.height = 800 * aspectRatio;
        
        this.redraw();
        console.log('🖼️ Imagem carregada');
    }
    
    exportCanvas() {
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }
    
    // === UI CONTROLS ===
    showObjectControls() {
        const controls = document.getElementById('objectControls');
        if (controls) {
            controls.style.display = 'block';
        }
    }
    
    hideObjectControls() {
        const controls = document.getElementById('objectControls');
        if (controls) {
            controls.style.display = 'none';
        }
    }
    
    showInstructions(text) {
        const instructions = document.getElementById('figmaInstructions');
        if (instructions) {
            instructions.querySelector('span').textContent = text;
            instructions.style.display = 'block';
            
            setTimeout(() => {
                instructions.style.display = 'none';
            }, 3000);
        }
    }
}

// === GLOBAL INSTANCE ===
window.figmaEditor = null;

// === GLOBAL FUNCTIONS ===
function initializeFigmaEditor(canvasId) {
    if (!window.figmaEditor) {
        window.figmaEditor = new FigmaPhotoEditor(canvasId);
    }
    return window.figmaEditor;
}

function setFigmaTool(tool) {
    if (window.figmaEditor) {
        window.figmaEditor.setTool(tool);
    }
}

function setFigmaColor(color) {
    if (window.figmaEditor) {
        window.figmaEditor.setColor(color);
    }
}

function rotateFigmaObject(degrees) {
    if (window.figmaEditor) {
        window.figmaEditor.rotateSelected(degrees);
    }
}

function confirmFigmaObject() {
    if (window.figmaEditor) {
        window.figmaEditor.confirmSelected();
    }
}

function clearFigmaObjects() {
    if (window.figmaEditor) {
        window.figmaEditor.clearAll();
    }
}

function applyFigmaEdits() {
    if (window.figmaEditor) {
        const editedImage = window.figmaEditor.exportCanvas();
        
        const preview = document.getElementById('imagePreview');
        if (preview) {
            preview.src = editedImage;
        }
        
        document.getElementById('figma-editor-container').style.display = 'none';
        
        console.log('✅ Edições aplicadas');
        alert('✅ Edições aplicadas com sucesso!');
    }
}

console.log('🎨 Figma Photo Editor carregado!');