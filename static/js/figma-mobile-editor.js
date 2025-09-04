/**
 * 🚀 Editor Figma Mobile - Sistema Avançado de Edição de Fotos
 * Funcionalidades tipo Figma para mobile: mover, redimensionar, rotacionar figuras
 * Desenvolvido para máxima precisão em dispositivos touch
 */

console.log('🚀 Figma Mobile Editor v3.0 - Carregando...');

class FigmaMobileEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        
        // Estado do editor
        this.mode = 'select'; // 'select', 'pen', 'arrow', 'circle', 'rectangle', 'text'
        this.currentColor = '#ff0000';
        this.currentSize = 3;
        this.currentFont = 16;
        
        // Objetos na tela (modelo baseado em objetos como Figma)
        this.objects = [];
        this.selectedObject = null;
        this.dragStart = null;
        this.isDrawing = false;
        this.originalImageData = null;
        
        // Sistema de touch preciso
        this.touchTimeout = null;
        this.lastTouch = { x: 0, y: 0, time: 0 };
        this.pinchDistance = 0;
        this.rotationAngle = 0;
        
        // Handles de redimensionamento/rotação
        this.handleSize = 20; // Tamanho dos handles touch-friendly
        this.handles = [];
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupEventListeners();
        this.setupTouchOptimization();
        console.log('✅ Editor inicializado com sucesso');
    }
    
    setupCanvas() {
        // Otimizações para alta precisão
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        this.canvas.style.webkitTapHighlightColor = 'transparent';
        
        // Configuração do contexto para melhor qualidade
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
    }
    
    setupTouchOptimization() {
        // Prevenir comportamentos indesejados do navegador
        document.addEventListener('touchstart', (e) => {
            if (e.target === this.canvas) {
                e.preventDefault();
            }
        }, { passive: false });
        
        document.addEventListener('touchmove', (e) => {
            if (e.target === this.canvas) {
                e.preventDefault();
            }
        }, { passive: false });
        
        // Prevenir zoom duplo-toque
        let lastTouchEnd = 0;
        this.canvas.addEventListener('touchend', (e) => {
            const now = new Date().getTime();
            if (now - lastTouchEnd <= 300) {
                e.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
        
        // Prevenir gestos do sistema
        this.canvas.addEventListener('gesturestart', e => e.preventDefault());
        this.canvas.addEventListener('gesturechange', e => e.preventDefault());
        this.canvas.addEventListener('gestureend', e => e.preventDefault());
    }
    
    setupEventListeners() {
        // Mouse events (desktop)
        this.canvas.addEventListener('mousedown', (e) => this.handlePointerDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handlePointerMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handlePointerUp(e));
        
        // Touch events (mobile) - Máxima precisão
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });
    }
    
    // === SISTEMA DE COORDENADAS PRECISAS ===
    getCanvasCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        let clientX, clientY;
        
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else if (e.changedTouches && e.changedTouches.length > 0) {
            clientX = e.changedTouches[0].clientX;
            clientY = e.changedTouches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        return {
            x: Math.round((clientX - rect.left) * scaleX),
            y: Math.round((clientY - rect.top) * scaleY)
        };
    }
    
    // === EVENTOS TOUCH OTIMIZADOS ===
    handleTouchStart(e) {
        e.preventDefault();
        
        // Multi-touch para pinch/rotate (futuro)
        if (e.touches.length === 2 && this.selectedObject) {
            this.handlePinchStart(e);
            return;
        }
        
        // Single touch - tratar como pointer
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const pointerEvent = this.createPointerEvent(touch);
            this.handlePointerDown(pointerEvent);
        }
    }
    
    handleTouchMove(e) {
        e.preventDefault();
        
        if (e.touches.length === 2 && this.selectedObject) {
            this.handlePinchMove(e);
            return;
        }
        
        if (e.touches.length === 1) {
            const touch = e.touches[0];
            const pointerEvent = this.createPointerEvent(touch);
            this.handlePointerMove(pointerEvent);
        }
    }
    
    handleTouchEnd(e) {
        e.preventDefault();
        
        if (e.changedTouches.length === 1) {
            const touch = e.changedTouches[0];
            const pointerEvent = this.createPointerEvent(touch);
            this.handlePointerUp(pointerEvent);
        }
    }
    
    createPointerEvent(touch) {
        return {
            clientX: touch.clientX,
            clientY: touch.clientY,
            target: touch.target
        };
    }
    
    // === MANIPULAÇÃO DE OBJETOS TIPO FIGMA ===
    handlePointerDown(e) {
        const coords = this.getCanvasCoordinates(e);
        
        if (this.mode === 'select') {
            this.handleSelectMode(coords);
        } else {
            this.handleDrawMode(coords);
        }
        
        this.dragStart = coords;
        this.isDrawing = true;
    }
    
    handlePointerMove(e) {
        if (!this.isDrawing) return;
        
        const coords = this.getCanvasCoordinates(e);
        
        if (this.mode === 'select' && this.selectedObject) {
            this.handleObjectDrag(coords);
        } else if (this.mode !== 'select') {
            this.handleDrawingPreview(coords);
        }
    }
    
    handlePointerUp(e) {
        if (!this.isDrawing) return;
        
        const coords = this.getCanvasCoordinates(e);
        
        if (this.mode !== 'select') {
            this.finishDrawing(coords);
        }
        
        this.isDrawing = false;
        this.dragStart = null;
        this.redraw();
    }
    
    handleSelectMode(coords) {
        // Verificar se clicou em handle primeiro
        const handle = this.getHandleAt(coords);
        if (handle && this.selectedObject) {
            this.handleHandleInteraction(handle, coords);
            return;
        }
        
        // Verificar se clicou em objeto
        const object = this.getObjectAt(coords);
        if (object) {
            this.selectObject(object);
        } else {
            this.selectedObject = null;
        }
        
        this.redraw();
    }
    
    handleObjectDrag(coords) {
        if (!this.selectedObject || !this.dragStart) return;
        
        const deltaX = coords.x - this.dragStart.x;
        const deltaY = coords.y - this.dragStart.y;
        
        // Mover objeto
        this.moveObject(this.selectedObject, deltaX, deltaY);
        this.dragStart = coords;
        this.redraw();
    }
    
    // === CRIAÇÃO E MANIPULAÇÃO DE OBJETOS ===
    createObject(type, coords, endCoords = null) {
        const object = {
            id: 'obj_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
            type: type,
            color: this.currentColor,
            size: this.currentSize,
            x: coords.x,
            y: coords.y,
            selected: false,
            rotation: 0,
            scale: 1
        };
        
        switch (type) {
            case 'arrow':
                object.endX = endCoords ? endCoords.x : coords.x + 50;
                object.endY = endCoords ? endCoords.y : coords.y + 50;
                break;
            case 'circle':
                object.radius = endCoords ? 
                    Math.sqrt(Math.pow(endCoords.x - coords.x, 2) + Math.pow(endCoords.y - coords.y, 2)) : 30;
                break;
            case 'rectangle':
                object.width = endCoords ? Math.abs(endCoords.x - coords.x) : 60;
                object.height = endCoords ? Math.abs(endCoords.y - coords.y) : 40;
                break;
            case 'text':
                object.text = 'Texto';
                object.fontSize = this.currentFont;
                break;
        }
        
        return object;
    }
    
    addObject(object) {
        this.objects.push(object);
        this.selectObject(object);
    }
    
    selectObject(object) {
        // Deselecionar todos
        this.objects.forEach(obj => obj.selected = false);
        
        // Selecionar novo
        object.selected = true;
        this.selectedObject = object;
        
        this.updateHandles();
        console.log('Objeto selecionado:', object.type, object.id);
    }
    
    moveObject(object, deltaX, deltaY) {
        object.x += deltaX;
        object.y += deltaY;
        
        // Manter dentro dos limites do canvas
        object.x = Math.max(0, Math.min(this.canvas.width, object.x));
        object.y = Math.max(0, Math.min(this.canvas.height, object.y));
    }
    
    // === SISTEMA DE HANDLES (FIGMA-LIKE) ===
    updateHandles() {
        this.handles = [];
        
        if (!this.selectedObject) return;
        
        const obj = this.selectedObject;
        const bounds = this.getObjectBounds(obj);
        
        // 8 handles de redimensionamento + 1 de rotação
        this.handles = [
            { type: 'resize', position: 'nw', x: bounds.left, y: bounds.top },
            { type: 'resize', position: 'n', x: bounds.centerX, y: bounds.top },
            { type: 'resize', position: 'ne', x: bounds.right, y: bounds.top },
            { type: 'resize', position: 'e', x: bounds.right, y: bounds.centerY },
            { type: 'resize', position: 'se', x: bounds.right, y: bounds.bottom },
            { type: 'resize', position: 's', x: bounds.centerX, y: bounds.bottom },
            { type: 'resize', position: 'sw', x: bounds.left, y: bounds.bottom },
            { type: 'resize', position: 'w', x: bounds.left, y: bounds.centerY },
            { type: 'rotate', position: 'rotate', x: bounds.centerX, y: bounds.top - 30 }
        ];
    }
    
    getObjectBounds(obj) {
        let bounds = { left: obj.x, top: obj.y, right: obj.x, bottom: obj.y };
        
        switch (obj.type) {
            case 'circle':
                bounds = {
                    left: obj.x - obj.radius,
                    top: obj.y - obj.radius,
                    right: obj.x + obj.radius,
                    bottom: obj.y + obj.radius
                };
                break;
            case 'rectangle':
                bounds = {
                    left: obj.x,
                    top: obj.y,
                    right: obj.x + obj.width,
                    bottom: obj.y + obj.height
                };
                break;
            case 'arrow':
                bounds = {
                    left: Math.min(obj.x, obj.endX),
                    top: Math.min(obj.y, obj.endY),
                    right: Math.max(obj.x, obj.endX),
                    bottom: Math.max(obj.y, obj.endY)
                };
                break;
        }
        
        bounds.centerX = (bounds.left + bounds.right) / 2;
        bounds.centerY = (bounds.top + bounds.bottom) / 2;
        
        return bounds;
    }
    
    getHandleAt(coords) {
        return this.handles.find(handle => {
            const distance = Math.sqrt(
                Math.pow(coords.x - handle.x, 2) + 
                Math.pow(coords.y - handle.y, 2)
            );
            return distance <= this.handleSize;
        });
    }
    
    getObjectAt(coords) {
        // Verificar de trás para frente (objetos mais recentes primeiro)
        for (let i = this.objects.length - 1; i >= 0; i--) {
            if (this.isPointInObject(coords, this.objects[i])) {
                return this.objects[i];
            }
        }
        return null;
    }
    
    isPointInObject(coords, obj) {
        switch (obj.type) {
            case 'circle':
                const distance = Math.sqrt(Math.pow(coords.x - obj.x, 2) + Math.pow(coords.y - obj.y, 2));
                return distance <= obj.radius + 10; // Margem para touch
            case 'rectangle':
                return coords.x >= obj.x - 10 && coords.x <= obj.x + obj.width + 10 &&
                       coords.y >= obj.y - 10 && coords.y <= obj.y + obj.height + 10;
            case 'arrow':
                // Verificação mais complexa para linha
                return this.isPointNearLine(coords, obj.x, obj.y, obj.endX, obj.endY, 15);
            case 'text':
                // Aproximação baseada no tamanho do texto
                return coords.x >= obj.x - 10 && coords.x <= obj.x + (obj.text.length * obj.fontSize * 0.6) + 10 &&
                       coords.y >= obj.y - obj.fontSize - 10 && coords.y <= obj.y + 10;
            default:
                return false;
        }
    }
    
    isPointNearLine(point, x1, y1, x2, y2, threshold) {
        const A = point.x - x1;
        const B = point.y - y1;
        const C = x2 - x1;
        const D = y2 - y1;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        
        if (lenSq !== 0) param = dot / lenSq;
        
        let xx, yy;
        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }
        
        const dx = point.x - xx;
        const dy = point.y - yy;
        return Math.sqrt(dx * dx + dy * dy) <= threshold;
    }
    
    // === PINCH TO ZOOM/ROTATE (Multi-touch) ===
    handlePinchStart(e) {
        if (!this.selectedObject) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        this.pinchDistance = Math.sqrt(
            Math.pow(touch2.clientX - touch1.clientX, 2) +
            Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        
        this.rotationAngle = Math.atan2(
            touch2.clientY - touch1.clientY,
            touch2.clientX - touch1.clientX
        ) * 180 / Math.PI;
        
        console.log('Pinch iniciado - Distância:', this.pinchDistance, 'Ângulo:', this.rotationAngle);
    }
    
    handlePinchMove(e) {
        if (!this.selectedObject || !this.pinchDistance) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        const currentDistance = Math.sqrt(
            Math.pow(touch2.clientX - touch1.clientX, 2) +
            Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        
        const currentAngle = Math.atan2(
            touch2.clientY - touch1.clientY,
            touch2.clientX - touch1.clientX
        ) * 180 / Math.PI;
        
        // Redimensionar
        const scaleFactor = currentDistance / this.pinchDistance;
        this.scaleObject(this.selectedObject, scaleFactor);
        
        // Rotacionar
        const rotationDelta = currentAngle - this.rotationAngle;
        this.rotateObject(this.selectedObject, rotationDelta);
        
        this.pinchDistance = currentDistance;
        this.rotationAngle = currentAngle;
        
        this.redraw();
    }
    
    scaleObject(obj, scaleFactor) {
        switch (obj.type) {
            case 'circle':
                obj.radius = Math.max(5, obj.radius * scaleFactor);
                break;
            case 'rectangle':
                obj.width = Math.max(10, obj.width * scaleFactor);
                obj.height = Math.max(10, obj.height * scaleFactor);
                break;
            case 'text':
                obj.fontSize = Math.max(8, Math.min(72, obj.fontSize * scaleFactor));
                break;
        }
        
        this.updateHandles();
    }
    
    rotateObject(obj, angleDelta) {
        obj.rotation = (obj.rotation + angleDelta) % 360;
        this.updateHandles();
    }
    
    // === DESENHO E RENDERIZAÇÃO ===
    handleDrawMode(coords) {
        // Criar preview do objeto
        this.drawingPreview = this.createObject(this.mode, coords);
    }
    
    handleDrawingPreview(coords) {
        if (!this.drawingPreview || !this.dragStart) return;
        
        // Atualizar preview baseado na ferramenta
        switch (this.mode) {
            case 'arrow':
                this.drawingPreview.endX = coords.x;
                this.drawingPreview.endY = coords.y;
                break;
            case 'circle':
                this.drawingPreview.radius = Math.sqrt(
                    Math.pow(coords.x - this.dragStart.x, 2) + 
                    Math.pow(coords.y - this.dragStart.y, 2)
                );
                break;
            case 'rectangle':
                this.drawingPreview.width = Math.abs(coords.x - this.dragStart.x);
                this.drawingPreview.height = Math.abs(coords.y - this.dragStart.y);
                break;
        }
        
        this.redraw();
    }
    
    finishDrawing(coords) {
        if (!this.drawingPreview) return;
        
        // Finalizar objeto e adicionar à lista
        switch (this.mode) {
            case 'arrow':
                this.drawingPreview.endX = coords.x;
                this.drawingPreview.endY = coords.y;
                break;
            case 'circle':
                this.drawingPreview.radius = Math.max(10, Math.sqrt(
                    Math.pow(coords.x - this.dragStart.x, 2) + 
                    Math.pow(coords.y - this.dragStart.y, 2)
                ));
                break;
            case 'rectangle':
                this.drawingPreview.width = Math.max(10, Math.abs(coords.x - this.dragStart.x));
                this.drawingPreview.height = Math.max(10, Math.abs(coords.y - this.dragStart.y));
                break;
        }
        
        this.addObject(this.drawingPreview);
        this.drawingPreview = null;
        
        // Voltar para modo de seleção automaticamente
        this.setMode('select');
        
        console.log('Objeto criado:', this.selectedObject.type);
    }
    
    redraw() {
        // Limpar canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Redesenhar imagem de fundo se existir
        if (this.originalImageData) {
            this.ctx.putImageData(this.originalImageData, 0, 0);
        }
        
        // Desenhar todos os objetos
        this.objects.forEach(obj => this.drawObject(obj));
        
        // Desenhar preview se estiver desenhando
        if (this.drawingPreview) {
            this.drawObject(this.drawingPreview, true);
        }
        
        // Desenhar handles do objeto selecionado
        if (this.selectedObject) {
            this.drawSelectionHandles();
        }
    }
    
    drawObject(obj, isPreview = false) {
        this.ctx.save();
        
        // Configurações gerais
        this.ctx.strokeStyle = obj.color;
        this.ctx.fillStyle = obj.color;
        this.ctx.lineWidth = obj.size;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        
        if (isPreview) {
            this.ctx.globalAlpha = 0.7;
        }
        
        // Aplicar rotação se necessário
        if (obj.rotation && obj.rotation !== 0) {
            const bounds = this.getObjectBounds(obj);
            this.ctx.translate(bounds.centerX, bounds.centerY);
            this.ctx.rotate(obj.rotation * Math.PI / 180);
            this.ctx.translate(-bounds.centerX, -bounds.centerY);
        }
        
        switch (obj.type) {
            case 'arrow':
                this.drawArrow(obj.x, obj.y, obj.endX, obj.endY, obj.size);
                break;
            case 'circle':
                this.ctx.beginPath();
                this.ctx.arc(obj.x, obj.y, obj.radius, 0, 2 * Math.PI);
                this.ctx.stroke();
                break;
            case 'rectangle':
                this.ctx.beginPath();
                this.ctx.rect(obj.x, obj.y, obj.width, obj.height);
                this.ctx.stroke();
                break;
            case 'text':
                this.ctx.font = `${obj.fontSize}px Arial`;
                this.ctx.fillText(obj.text || 'Texto', obj.x, obj.y);
                break;
        }
        
        this.ctx.restore();
    }
    
    drawArrow(fromX, fromY, toX, toY, size) {
        const headLength = Math.max(10, Math.min(30, size * 8));
        const angle = Math.atan2(toY - fromY, toX - fromX);
        
        this.ctx.beginPath();
        this.ctx.moveTo(fromX, fromY);
        this.ctx.lineTo(toX, toY);
        
        // Cabeça da seta
        this.ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), 
                        toY - headLength * Math.sin(angle - Math.PI / 6));
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), 
                        toY - headLength * Math.sin(angle + Math.PI / 6));
        
        this.ctx.stroke();
    }
    
    drawSelectionHandles() {
        if (!this.selectedObject) return;
        
        this.ctx.save();
        this.ctx.strokeStyle = '#1976d2';
        this.ctx.fillStyle = '#ffffff';
        this.ctx.lineWidth = 2;
        
        this.handles.forEach(handle => {
            this.ctx.beginPath();
            
            if (handle.type === 'rotate') {
                // Handle de rotação (círculo)
                this.ctx.arc(handle.x, handle.y, this.handleSize / 2, 0, 2 * Math.PI);
                this.ctx.fill();
                this.ctx.stroke();
                
                // Ícone de rotação
                this.ctx.beginPath();
                this.ctx.arc(handle.x, handle.y, this.handleSize / 4, 0, 1.5 * Math.PI);
                this.ctx.stroke();
            } else {
                // Handles de redimensionamento (quadrados)
                const halfSize = this.handleSize / 2;
                this.ctx.rect(handle.x - halfSize, handle.y - halfSize, 
                             this.handleSize, this.handleSize);
                this.ctx.fill();
                this.ctx.stroke();
            }
        });
        
        this.ctx.restore();
    }
    
    // === API PÚBLICA ===
    setMode(mode) {
        this.mode = mode;
        this.selectedObject = null;
        this.redraw();
        
        // Atualizar cursor
        const cursors = {
            'select': 'default',
            'pen': 'crosshair',
            'arrow': 'crosshair',
            'circle': 'crosshair',
            'rectangle': 'crosshair',
            'text': 'text'
        };
        
        this.canvas.style.cursor = cursors[mode] || 'default';
        console.log('Modo alterado para:', mode);
    }
    
    setColor(color) {
        this.currentColor = color;
        if (this.selectedObject) {
            this.selectedObject.color = color;
            this.redraw();
        }
    }
    
    setSize(size) {
        this.currentSize = parseInt(size);
        if (this.selectedObject) {
            this.selectedObject.size = this.currentSize;
            this.redraw();
        }
    }
    
    loadImage(imageSrc) {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
            // Ajustar canvas
            const maxWidth = 800;
            const maxHeight = 600;
            let { width, height } = img;
            
            if (width > maxWidth) {
                height = (height * maxWidth) / width;
                width = maxWidth;
            }
            if (height > maxHeight) {
                width = (width * maxHeight) / height;
                height = maxHeight;
            }
            
            this.canvas.width = width;
            this.canvas.height = height;
            
            // Desenhar imagem
            this.ctx.drawImage(img, 0, 0, width, height);
            this.originalImageData = this.ctx.getImageData(0, 0, width, height);
            
            console.log('✅ Imagem carregada:', width, 'x', height);
            this.redraw();
        };
        
        img.onerror = () => {
            console.error('❌ Erro ao carregar imagem:', imageSrc);
            alert('Erro ao carregar a imagem. Verifique se o arquivo é válido.');
        };
        
        img.src = imageSrc;
    }
    
    deleteSelected() {
        if (this.selectedObject) {
            const index = this.objects.indexOf(this.selectedObject);
            if (index > -1) {
                this.objects.splice(index, 1);
                this.selectedObject = null;
                this.redraw();
                console.log('Objeto deletado');
            }
        }
    }
    
    undo() {
        if (this.objects.length > 0) {
            this.objects.pop();
            this.selectedObject = null;
            this.redraw();
            console.log('Última ação desfeita');
        }
    }
    
    clear() {
        if (confirm('Tem certeza que deseja limpar todas as anotações?')) {
            this.objects = [];
            this.selectedObject = null;
            this.redraw();
            console.log('Canvas limpo');
        }
    }
    
    export() {
        return this.canvas.toDataURL('image/jpeg', 0.8);
    }
    
    getObjectsData() {
        return this.objects.map(obj => ({...obj}));
    }
    
    loadObjectsData(data) {
        this.objects = data || [];
        this.selectedObject = null;
        this.redraw();
    }
}

// Exportar para uso global
window.FigmaMobileEditor = FigmaMobileEditor;

console.log('✅ Figma Mobile Editor carregado com sucesso!');