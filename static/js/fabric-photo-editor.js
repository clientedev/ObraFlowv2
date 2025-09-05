/**
 * Editor de Fotos Professional com Fabric.js
 * Otimizado para Mobile - Experiência Figma-like
 * ================================================
 */

class FabricPhotoEditor {
    constructor(canvasId, imageUrl) {
        console.log('🎨 Inicializando Fabric Photo Editor v2.0');
        
        this.canvasId = canvasId;
        this.imageUrl = imageUrl;
        this.canvas = null;
        this.backgroundImage = null;
        this.isDrawingMode = false;
        this.currentTool = 'select';
        this.currentColor = '#FF0000';
        this.currentStrokeWidth = 3;
        this.opacity = 1;
        this.history = [];
        this.historyIndex = -1;
        this.maxHistory = 50;
        
        // Controles da seta melhorados
        this.isDrawingArrow = false;
        this.arrowStartPoint = null;
        this.currentArrow = null;
        
        // Mobile específico
        this.isMobile = window.innerWidth <= 768;
        this.isTouch = 'ontouchstart' in window;
        this.touchPoints = {};
        this.lastDistance = 0;
        this.isMultiTouch = false;
        
        this.init();
    }
    
    async init() {
        try {
            // Configuração do canvas Fabric.js
            this.canvas = new fabric.Canvas(this.canvasId, {
                width: 800,
                height: 600,
                backgroundColor: 'white',
                selection: true,
                preserveObjectStacking: true,
                // Otimizações mobile
                enableRetinaScaling: true,
                allowTouchScrolling: false,
                // Configurações de interatividade
                hoverCursor: 'grab',
                moveCursor: 'grabbing',
                defaultCursor: 'default'
            });
            
            // Carregar imagem de fundo
            await this.loadBackgroundImage();
            
            // Configurar eventos
            this.setupCanvasEvents();
            this.setupMobileOptimizations();
            this.setupKeyboardShortcuts();
            
            // MOBILE: Garantir compatibilidade do textarea
            this.ensureMobileTextareaCompatibility();
            
            // Salvar estado inicial
            this.saveState();
            
            console.log('✅ Editor inicializado com sucesso');
            
        } catch (error) {
            console.error('❌ Erro ao inicializar editor:', error);
        }
    }
    
    async loadBackgroundImage() {
        if (!this.imageUrl) return;
        
        return new Promise((resolve, reject) => {
            fabric.Image.fromURL(this.imageUrl, (img) => {
                if (!img) {
                    reject(new Error('Falha ao carregar imagem'));
                    return;
                }
                
                // Ajustar tamanho do canvas para a imagem
                const canvasContainer = this.canvas.wrapperEl.parentElement;
                const maxWidth = canvasContainer.clientWidth - 40;
                const maxHeight = this.isMobile ? 400 : 600;
                
                const scale = Math.min(
                    maxWidth / img.width,
                    maxHeight / img.height
                );
                
                const newWidth = img.width * scale;
                const newHeight = img.height * scale;
                
                // Configurar canvas
                this.canvas.setDimensions({
                    width: newWidth,
                    height: newHeight
                });
                
                // Configurar imagem de fundo
                img.set({
                    left: 0,
                    top: 0,
                    scaleX: scale,
                    scaleY: scale,
                    selectable: false,
                    evented: false
                });
                
                this.canvas.backgroundImage = img;
                this.backgroundImage = img;
                this.canvas.renderAll();
                
                // Auto-scroll para o centro da imagem após carregar
                setTimeout(() => {
                    this.scrollToImageCenter();
                }, 100);
                
                resolve(img);
            });
        });
    }
    
    // Função para fazer auto-scroll para o centro da imagem - Melhorada para mobile
    scrollToImageCenter() {
        const canvasContainer = this.canvas.wrapperEl.parentElement;
        
        if (canvasContainer) {
            // Para mobile, usar scroll suave com fallback
            if (this.isMobile) {
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
    
    setupCanvasEvents() {
        // Eventos de seleção
        this.canvas.on('selection:created', (e) => {
            this.updateSelectionControls(e.selected);
        });
        
        this.canvas.on('selection:updated', (e) => {
            this.updateSelectionControls(e.selected);
        });
        
        this.canvas.on('selection:cleared', () => {
            this.updateSelectionControls([]);
        });
        
        // Eventos de modificação
        this.canvas.on('object:modified', () => {
            this.saveState();
        });
        
        // Eventos de desenho livre
        this.canvas.on('path:created', () => {
            this.saveState();
        });
        
        // MOBILE: Evento de clique duplo em texto para abrir teclado
        this.canvas.on('mouse:dblclick', (e) => {
            if (e.target && (e.target.type === 'i-text' || e.target.type === 'text')) {
                console.log('📱 Clique duplo em texto - forçando teclado móvel');
                this.editText(e.target);
            }
        });
        
        // MOBILE: Capturar quando texto entra em modo de edição automaticamente
        this.canvas.on('text:editing:entered', (e) => {
            console.log('📱 EVENTO CAPTURADO: Texto entrou em modo de edição');
            const textObject = e.target;
            if (textObject && (textObject.type === 'i-text' || textObject.type === 'text')) {
                // ANÁLISE PROFUNDA: Detectar mobile com logs detalhados
                const userAgent = navigator.userAgent;
                const hasTouch = 'ontouchstart' in window;
                const maxTouchPoints = navigator.maxTouchPoints > 0;
                const screenWidth = window.innerWidth <= 768;
                
                console.log('📱 ANÁLISE MOBILE:', {
                    userAgent,
                    hasTouch,
                    maxTouchPoints,
                    screenWidth,
                    navigator: navigator
                });
                
                const isMobileDevice = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent) ||
                                      hasTouch ||
                                      maxTouchPoints ||
                                      screenWidth;
                
                console.log('📱 DECISÃO MOBILE:', isMobileDevice);
                
                if (isMobileDevice) {
                    console.log('📱 MOBILE DETECTADO - Criando input customizado');
                    // Cancelar edição padrão do Fabric.js
                    textObject.exitEditing();
                    
                    // Aguardar um pouco para garantir que o Fabric.js processou
                    setTimeout(() => {
                        this.createSimpleMobileInput(textObject);
                    }, 50);
                } else {
                    console.log('📱 DESKTOP DETECTADO - Permitindo edição normal');
                }
            }
        });
        
        // Prevenção de contexto mobile
        this.canvas.on('mouse:down', (e) => {
            if (this.isTouch) {
                e.e.preventDefault();
            }
        });
    }
    
    setupMobileOptimizations() {
        if (!this.isTouch) return;
        
        const canvasElement = this.canvas.upperCanvasEl;
        
        // Configurações CSS para mobile
        canvasElement.style.touchAction = 'none';
        canvasElement.style.userSelect = 'none';
        canvasElement.style.webkitUserSelect = 'none';
        canvasElement.style.webkitTapHighlightColor = 'transparent';
        
        // Eventos touch customizados para gestos avançados
        let touchStartTime = 0;
        let initialTouches = {};
        
        canvasElement.addEventListener('touchstart', (e) => {
            touchStartTime = Date.now();
            this.isMultiTouch = e.touches.length > 1;
            
            // Armazenar posições iniciais dos toques
            for (let i = 0; i < e.touches.length; i++) {
                const touch = e.touches[i];
                initialTouches[touch.identifier] = {
                    x: touch.clientX,
                    y: touch.clientY
                };
            }
            
            // Prevenir zoom duplo toque iOS
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        }, { passive: false });
        
        canvasElement.addEventListener('touchmove', (e) => {
            // Prevenir scroll durante edição
            if (this.currentTool !== 'select' || this.canvas.getActiveObject()) {
                e.preventDefault();
            }
            
            // Gestão de multitouch para rotação/escala
            if (e.touches.length === 2 && this.canvas.getActiveObject()) {
                this.handleMultiTouchGesture(e);
            }
        }, { passive: false });
        
        canvasElement.addEventListener('touchend', (e) => {
            const touchDuration = Date.now() - touchStartTime;
            
            // Detectar toque longo (contexto)
            if (touchDuration > 500 && e.touches.length === 0) {
                this.handleLongPress(e);
            }
            
            this.isMultiTouch = false;
            initialTouches = {};
        });
    }
    
    handleMultiTouchGesture(e) {
        const activeObject = this.canvas.getActiveObject();
        if (!activeObject || e.touches.length !== 2) return;
        
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        
        // Calcular distância entre toques
        const distance = Math.sqrt(
            Math.pow(touch2.clientX - touch1.clientX, 2) +
            Math.pow(touch2.clientY - touch1.clientY, 2)
        );
        
        // Calcular ângulo
        const angle = Math.atan2(
            touch2.clientY - touch1.clientY,
            touch2.clientX - touch1.clientX
        ) * 180 / Math.PI;
        
        // Aplicar transformações
        if (this.lastDistance > 0) {
            const scale = distance / this.lastDistance;
            if (Math.abs(scale - 1) > 0.01) {
                activeObject.scale(scale);
            }
        }
        
        this.lastDistance = distance;
        this.canvas.renderAll();
    }
    
    handleLongPress(e) {
        // Implementar menu de contexto mobile
        console.log('Long press detected');
        this.showContextMenu(e);
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key.toLowerCase()) {
                    case 'z':
                        e.preventDefault();
                        if (e.shiftKey) {
                            this.redo();
                        } else {
                            this.undo();
                        }
                        break;
                    case 'y':
                        e.preventDefault();
                        this.redo();
                        break;
                    case 'c':
                        e.preventDefault();
                        this.copy();
                        break;
                    case 'v':
                        e.preventDefault();
                        this.paste();
                        break;
                    case 'delete':
                    case 'backspace':
                        e.preventDefault();
                        this.deleteSelected();
                        break;
                }
            }
        });
    }
    
    // =================== FERRAMENTAS ===================
    
    setTool(tool) {
        console.log(`🔧 Ferramenta alterada para: ${tool}`);
        
        // Se mudando de seta para outra ferramenta, limpar controles de seta
        if (this.currentTool === 'arrow' && tool !== 'arrow') {
            this.currentArrow = null;
            this.isDrawingArrow = false;
            this.arrowStartPoint = null;
        }
        
        // Se selecionando ferramenta seta, limpar setas existentes
        if (tool === 'arrow') {
            this.clearAllArrows();
        }
        
        this.currentTool = tool;
        
        // Resetar modo de desenho
        this.canvas.isDrawingMode = false;
        this.canvas.selection = true;
        
        // Configurar cursor
        this.updateCanvasCursor();
        
        // Configurações específicas por ferramenta
        switch (tool) {
            case 'select':
                this.canvas.selection = true;
                break;
                
            case 'brush':
                this.canvas.isDrawingMode = true;
                this.canvas.freeDrawingBrush.color = this.currentColor;
                this.canvas.freeDrawingBrush.width = this.currentStrokeWidth;
                break;
                
            case 'arrow':
            case 'circle':
            case 'rectangle':
            case 'text':
                this.canvas.selection = false;
                this.setupShapeDrawing(tool);
                break;
        }
        
        // Atualizar UI
        this.updateToolButtons();
    }
    
    updateCanvasCursor() {
        const cursors = {
            select: 'default',
            brush: 'crosshair',
            arrow: 'crosshair',
            circle: 'crosshair',
            rectangle: 'crosshair',
            text: 'text'
        };
        
        this.canvas.defaultCursor = cursors[this.currentTool] || 'default';
        this.canvas.renderAll();
    }
    
    setupShapeDrawing(shapeType) {
        let isDrawing = false;
        let startPoint = {};
        let shape = null;
        let drawingLocked = false;
        
        // Remover eventos anteriores
        this.canvas.off('mouse:down');
        this.canvas.off('mouse:move');
        this.canvas.off('mouse:up');
        
        // Suporte para eventos touch
        const getPointer = (e) => {
            if (e.touches && e.touches[0]) {
                const rect = this.canvas.upperCanvasEl.getBoundingClientRect();
                return {
                    x: e.touches[0].clientX - rect.left,
                    y: e.touches[0].clientY - rect.top
                };
            }
            return this.canvas.getPointer(e);
        };
        
        const startDrawing = (e) => {
            if (this.currentTool !== shapeType || drawingLocked || isDrawing) return;
            
            // Prevenir comportamento padrão em mobile
            if (e.touches) {
                e.preventDefault();
            }
            
            drawingLocked = true;
            isDrawing = true;
            
            const pointer = getPointer(e);
            startPoint = { x: pointer.x, y: pointer.y };
            
            // Para SETAS: Limpar setas existentes e criar UMA nova
            if (shapeType === 'arrow') {
                this.clearAllArrows();
                this.isDrawingArrow = true;
                this.arrowStartPoint = startPoint;
                
                // Criar UMA seta inicial
                shape = this.createShape(shapeType, startPoint, startPoint);
                if (shape) {
                    shape.arrowType = 'arrow';
                    this.canvas.add(shape);
                    this.currentArrow = shape;
                }
            } else {
                // Para outras formas
                shape = this.createShape(shapeType, startPoint, startPoint);
                if (shape) {
                    this.canvas.add(shape);
                    this.canvas.setActiveObject(shape);
                }
            }
        };
        
        const updateDrawing = (e) => {
            if (!isDrawing || !shape || !drawingLocked) return;
            
            const pointer = getPointer(e);
            
            // ATUALIZAR a seta existente, NÃO criar nova
            if (shapeType === 'arrow' && this.currentArrow) {
                // Remover seta atual temporariamente
                this.canvas.remove(this.currentArrow);
                
                // Criar nova seta atualizada
                const updatedArrow = this.createShape(shapeType, startPoint, pointer);
                if (updatedArrow) {
                    updatedArrow.arrowType = 'arrow';
                    this.canvas.add(updatedArrow);
                    this.currentArrow = updatedArrow;
                    shape = updatedArrow;
                }
            } else {
                // Para outras formas, usar updateShape normal
                this.updateShape(shape, shapeType, startPoint, pointer);
            }
            
            this.canvas.renderAll();
        };
        
        const endDrawing = (e) => {
            if (!drawingLocked || !isDrawing) return;
            
            isDrawing = false;
            this.isDrawingArrow = false;
            
            if (shape) {
                this.saveState();
                
                // Para texto, abrir editor automaticamente
                if (shapeType === 'text') {
                    // Aguardar o objeto ser adicionado ao canvas
                    setTimeout(() => {
                        this.canvas.setActiveObject(shape);
                        this.editText(shape);
                    }, 50);
                }
            }
            
            shape = null;
            drawingLocked = false;
        };
        
        // Eventos mouse
        this.canvas.on('mouse:down', startDrawing);
        this.canvas.on('mouse:move', updateDrawing);
        this.canvas.on('mouse:up', endDrawing);
        
        // Eventos touch para mobile
        const canvasEl = this.canvas.upperCanvasEl;
        canvasEl.addEventListener('touchstart', startDrawing, { passive: false });
        canvasEl.addEventListener('touchmove', updateDrawing, { passive: false });
        canvasEl.addEventListener('touchend', endDrawing, { passive: false });
    }
    
    createShape(type, start, end) {
        const commonProps = {
            fill: 'transparent',
            stroke: this.currentColor,
            strokeWidth: this.currentStrokeWidth,
            opacity: this.opacity
        };
        
        switch (type) {
            case 'arrow':
                return this.createArrow(start, end, commonProps);
                
            case 'circle':
                const radius = Math.abs(end.x - start.x) / 2;
                return new fabric.Circle({
                    ...commonProps,
                    left: Math.min(start.x, end.x),
                    top: Math.min(start.y, end.y),
                    radius: radius
                });
                
            case 'rectangle':
                return new fabric.Rect({
                    ...commonProps,
                    left: Math.min(start.x, end.x),
                    top: Math.min(start.y, end.y),
                    width: Math.abs(end.x - start.x),
                    height: Math.abs(end.y - start.y)
                });
                
            case 'text':
                return new fabric.IText('Digite aqui', {
                    left: start.x,
                    top: start.y,
                    fill: this.currentColor,
                    fontSize: 24,
                    fontFamily: 'Arial',
                    opacity: this.opacity,
                    editable: true
                });
                
            default:
                return null;
        }
    }
    
    createArrow(start, end, props) {
        const line = new fabric.Line([start.x, start.y, end.x, end.y], props);
        
        // Calcular ângulo da seta
        const angle = Math.atan2(end.y - start.y, end.x - start.x);
        const headLength = 20;
        
        // Pontas da seta
        const x1 = end.x - headLength * Math.cos(angle - Math.PI / 6);
        const y1 = end.y - headLength * Math.sin(angle - Math.PI / 6);
        const x2 = end.x - headLength * Math.cos(angle + Math.PI / 6);
        const y2 = end.y - headLength * Math.sin(angle + Math.PI / 6);
        
        const arrowHead1 = new fabric.Line([end.x, end.y, x1, y1], props);
        const arrowHead2 = new fabric.Line([end.x, end.y, x2, y2], props);
        
        // Agrupar elementos da seta
        const arrow = new fabric.Group([line, arrowHead1, arrowHead2], {
            selectable: true,
            opacity: props.opacity
        });
        
        return arrow;
    }
    
    updateShape(shape, type, start, current) {
        switch (type) {
            case 'circle':
                const radius = Math.abs(current.x - start.x) / 2;
                shape.set({
                    left: Math.min(start.x, current.x),
                    top: Math.min(start.y, current.y),
                    radius: radius
                });
                break;
                
            case 'rectangle':
                shape.set({
                    left: Math.min(start.x, current.x),
                    top: Math.min(start.y, current.y),
                    width: Math.abs(current.x - start.x),
                    height: Math.abs(current.y - start.y)
                });
                break;
                
            case 'arrow':
                // Para setas, esta função não deve ser chamada
                // O updateDrawing já cuida das setas diretamente
                console.warn('updateShape chamado para arrow - usar updateDrawing');
                break;
        }
        
        return shape;
    }
    
    // Função específica para limpar todas as setas
    clearAllArrows() {
        const allObjects = this.canvas.getObjects();
        const arrows = allObjects.filter(obj => 
            (obj.type === 'group' && obj._objects && obj._objects.length >= 3) || 
            (obj.arrowType === 'arrow')
        );
        arrows.forEach(arrow => this.canvas.remove(arrow));
        this.currentArrow = null;
        this.canvas.renderAll();
        console.log(`🗑️ ${arrows.length} setas removidas`);
    }
    
    // =================== CONTROLES ==================="
    
    setColor(color) {
        console.log(`🎨 Cor alterada para: ${color}`);
        this.currentColor = color;
        
        // Aplicar à ferramenta atual
        if (this.canvas.isDrawingMode) {
            this.canvas.freeDrawingBrush.color = color;
        }
        
        // Aplicar aos objetos selecionados
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach(obj => {
            if (obj.type === 'i-text' || obj.type === 'text') {
                obj.set('fill', color);
            } else {
                obj.set('stroke', color);
            }
        });
        
        this.canvas.renderAll();
        this.updateColorDisplay();
    }
    
    setStrokeWidth(width) {
        console.log(`📏 Espessura alterada para: ${width}`);
        this.currentStrokeWidth = parseInt(width);
        
        // Aplicar à ferramenta de desenho
        if (this.canvas.isDrawingMode) {
            this.canvas.freeDrawingBrush.width = this.currentStrokeWidth;
        }
        
        // Aplicar aos objetos selecionados
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach(obj => {
            if (obj.type !== 'i-text' && obj.type !== 'text') {
                obj.set('strokeWidth', this.currentStrokeWidth);
            }
        });
        
        this.canvas.renderAll();
        this.updateStrokeWidthDisplay();
    }
    
    setOpacity(opacity) {
        this.opacity = parseFloat(opacity);
        
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach(obj => {
            obj.set('opacity', this.opacity);
        });
        
        this.canvas.renderAll();
    }
    
    // =================== AÇÕES ===================
    
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.history[this.historyIndex];
            this.canvas.loadFromJSON(state, () => {
                this.canvas.renderAll();
                console.log('⬅️ Undo realizado');
            });
        }
    }
    
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            const state = this.history[this.historyIndex];
            this.canvas.loadFromJSON(state, () => {
                this.canvas.renderAll();
                console.log('➡️ Redo realizado');
            });
        }
    }
    
    clear() {
        if (confirm('Deseja limpar todas as anotações?')) {
            this.canvas.clear();
            if (this.backgroundImage) {
                this.canvas.backgroundImage = this.backgroundImage;
            }
            this.canvas.renderAll();
            this.saveState();
            console.log('🗑️ Canvas limpo');
        }
    }
    
    deleteSelected() {
        const activeObjects = this.canvas.getActiveObjects();
        if (activeObjects.length > 0) {
            activeObjects.forEach(obj => this.canvas.remove(obj));
            this.canvas.discardActiveObject();
            this.canvas.renderAll();
            this.saveState();
            console.log('🗑️ Objetos selecionados removidos');
        }
    }
    
    copy() {
        const activeObject = this.canvas.getActiveObject();
        if (activeObject) {
            activeObject.clone(clone => {
                this.clipboard = clone;
                console.log('📋 Objeto copiado');
            });
        }
    }
    
    paste() {
        if (this.clipboard) {
            this.clipboard.clone(cloned => {
                cloned.set({
                    left: cloned.left + 10,
                    top: cloned.top + 10,
                    evented: true
                });
                
                if (cloned.type === 'activeSelection') {
                    cloned.canvas = this.canvas;
                    cloned.forEachObject(obj => {
                        this.canvas.add(obj);
                    });
                    cloned.setCoords();
                } else {
                    this.canvas.add(cloned);
                }
                
                this.canvas.setActiveObject(cloned);
                this.canvas.renderAll();
                this.saveState();
                console.log('📋 Objeto colado');
            });
        }
    }
    
    // =================== ESTADO ===================
    
    saveState() {
        const state = JSON.stringify(this.canvas.toJSON());
        
        // Limitar histórico
        if (this.history.length >= this.maxHistory) {
            this.history.shift();
            this.historyIndex--;
        }
        
        // Remover estados futuros se não estivermos no final
        if (this.historyIndex < this.history.length - 1) {
            this.history = this.history.slice(0, this.historyIndex + 1);
        }
        
        this.history.push(state);
        this.historyIndex++;
        
        // Atualizar botões undo/redo
        this.updateHistoryButtons();
    }
    
    // =================== UI UPDATES ===================
    
    updateToolButtons() {
        document.querySelectorAll('[data-tool]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === this.currentTool);
        });
    }
    
    updateColorDisplay() {
        const colorDisplay = document.getElementById('current-color');
        if (colorDisplay) {
            colorDisplay.style.backgroundColor = this.currentColor;
        }
    }
    
    updateStrokeWidthDisplay() {
        const widthDisplay = document.getElementById('stroke-width-value');
        const widthSlider = document.getElementById('stroke-width-slider');
        
        if (widthDisplay) {
            widthDisplay.textContent = this.currentStrokeWidth + 'px';
        }
        
        if (widthSlider) {
            widthSlider.value = this.currentStrokeWidth;
        }
    }
    
    updateHistoryButtons() {
        const undoBtn = document.getElementById('undo-btn');
        const redoBtn = document.getElementById('redo-btn');
        
        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
        }
        
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
        }
    }
    
    updateSelectionControls(selectedObjects) {
        const hasSelection = selectedObjects && selectedObjects.length > 0;
        
        // Mostrar/ocultar controles de seleção
        const selectionControls = document.getElementById('selection-controls');
        if (selectionControls) {
            selectionControls.style.display = hasSelection ? 'block' : 'none';
        }
        
        if (hasSelection && selectedObjects.length === 1) {
            const obj = selectedObjects[0];
            
            // Atualizar controles baseado no objeto
            if (obj.type === 'i-text' || obj.type === 'text') {
                this.currentColor = obj.fill || this.currentColor;
            } else {
                this.currentColor = obj.stroke || this.currentColor;
                this.currentStrokeWidth = obj.strokeWidth || this.currentStrokeWidth;
            }
            
            this.updateColorDisplay();
            this.updateStrokeWidthDisplay();
        }
    }
    
    // =================== UTILS ===================
    
    editText(textObject) {
        // Detectar dispositivos móveis de forma robusta
        const isMobileDevice = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
                              ('ontouchstart' in window) ||
                              (navigator.maxTouchPoints > 0) ||
                              (window.innerWidth <= 768);
        
        console.log('📱 Editando texto - Mobile detectado:', isMobileDevice);
        
        if (isMobileDevice) {
            // MOBILE: Usar interface customizada
            this.createSimpleMobileInput(textObject);
        } else {
            // DESKTOP: Usar edição nativa do Fabric.js
            this.canvas.setActiveObject(textObject);
            textObject.enterEditing();
            textObject.selectAll();
        }
    }
    
    createSimpleMobileInput(textObject) {
        console.log('📱 Criando input mobile simplificado');
        
        // Limpar qualquer input existente
        this.clearMobileInput();
        
        // Criar container principal fixo
        const container = document.createElement('div');
        container.id = 'mobile-text-container';
        container.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: rgba(0,0,0,0.8) !important;
            z-index: 999999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 20px !important;
        `;
        
        // Criar card de edição
        const editCard = document.createElement('div');
        editCard.style.cssText = `
            background: white !important;
            border-radius: 15px !important;
            padding: 25px !important;
            width: 100% !important;
            max-width: 400px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3) !important;
        `;
        
        // Título
        const title = document.createElement('h5');
        title.textContent = 'Editar Texto';
        title.style.cssText = `
            margin: 0 0 15px 0 !important;
            color: #333 !important;
            text-align: center !important;
        `;
        
        // Input principal
        const input = document.createElement('input');
        input.type = 'text';
        input.id = 'mobile-text-input';
        input.value = textObject.text === 'Digite aqui' ? '' : (textObject.text || '');
        input.placeholder = 'Digite o texto aqui...';
        
        // Estilo otimizado para mobile
        input.style.cssText = `
            width: 100% !important;
            padding: 15px !important;
            font-size: 18px !important;
            border: 2px solid #007bff !important;
            border-radius: 8px !important;
            outline: none !important;
            margin-bottom: 20px !important;
            box-sizing: border-box !important;
            -webkit-appearance: none !important;
            appearance: none !important;
        `;
        
        // Atributos para forçar teclado
        input.setAttribute('inputmode', 'text');
        input.setAttribute('enterkeyhint', 'done');
        input.autocomplete = 'off';
        input.autocorrect = 'off';
        input.autocapitalize = 'sentences';
        input.spellcheck = true;
        
        // Container de botões
        const buttonContainer = document.createElement('div');
        buttonContainer.style.cssText = `
            display: flex !important;
            gap: 10px !important;
            justify-content: space-between !important;
        `;
        
        // Botão Confirmar
        const confirmBtn = document.createElement('button');
        confirmBtn.textContent = 'Confirmar';
        confirmBtn.style.cssText = `
            flex: 1 !important;
            padding: 12px !important;
            background: #007bff !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 16px !important;
            font-weight: bold !important;
            touch-action: manipulation !important;
        `;
        
        // Botão Cancelar
        const cancelBtn = document.createElement('button');
        cancelBtn.textContent = 'Cancelar';
        cancelBtn.style.cssText = `
            flex: 1 !important;
            padding: 12px !important;
            background: #6c757d !important;
            color: white !important;
            border: none !important;
            border-radius: 6px !important;
            font-size: 16px !important;
            touch-action: manipulation !important;
        `;
        
        // Montar estrutura
        editCard.appendChild(title);
        editCard.appendChild(input);
        buttonContainer.appendChild(cancelBtn);
        buttonContainer.appendChild(confirmBtn);
        editCard.appendChild(buttonContainer);
        container.appendChild(editCard);
        
        // Adicionar ao DOM
        document.body.appendChild(container);
        
        // FORÇAR FOCO NO INPUT - Estratégia agressiva mas limpa
        const focusInput = () => {
            input.focus();
            input.select();
            console.log('📱 Foco aplicado ao input mobile');
        };
        
        // Múltiplas tentativas de foco
        requestAnimationFrame(() => {
            focusInput();
            setTimeout(focusInput, 100);
            setTimeout(focusInput, 300);
        });
        
        // Event listeners
        input.addEventListener('input', (e) => {
            textObject.text = e.target.value;
            this.canvas.renderAll();
        });
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.finalizeMobileTextEdit(textObject, input.value, container);
            }
        });
        
        confirmBtn.addEventListener('click', () => {
            this.finalizeMobileTextEdit(textObject, input.value, container);
        });
        
        cancelBtn.addEventListener('click', () => {
            container.remove();
        });
        
        // Clique no fundo para cancelar
        container.addEventListener('click', (e) => {
            if (e.target === container) {
                container.remove();
            }
        });
        
        console.log('📱 Input mobile criado e configurado');
    }
    
    finalizeMobileTextEdit(textObject, text, container) {
        textObject.text = text || 'Digite aqui';
        this.canvas.renderAll();
        this.saveState();
        container.remove();
        console.log('📱 Edição de texto finalizada:', text);
    }
    
    clearMobileInput() {
        const existing = document.getElementById('mobile-text-container');
        if (existing) {
            existing.remove();
        }
    }
    
    
    ensureMobileTextareaCompatibility() {
        // Garantir que textarea do Fabric.js seja acessível em mobile
        if (this.isMobile || this.isTouch) {
            // CSS para garantir que textarea do Fabric.js funcione
            const mobileStyleElement = document.createElement('style');
            mobileStyleElement.textContent = `
                .canvas-container textarea {
                    position: absolute !important;
                    opacity: 0 !important;
                    z-index: 1000 !important;
                    left: 0px !important;
                    top: 0px !important;
                    width: 1px !important;
                    height: 1px !important;
                    border: none !important;
                    background: transparent !important;
                    resize: none !important;
                    outline: none !important;
                    -webkit-user-select: text !important;
                    user-select: text !important;
                    touch-action: manipulation !important;
                }
                
                .upper-canvas {
                    -webkit-user-select: none !important;
                    user-select: none !important;
                }
            `;
            document.head.appendChild(mobileStyleElement);
            
            console.log('📱 CSS de compatibilidade móvel aplicado');
        }
    }
    
    showContextMenu(e) {
        // Implementar menu de contexto mobile
        console.log('Context menu at:', e.clientX, e.clientY);
    }
    
    getCanvasImage(format = 'image/png', quality = 1) {
        return this.canvas.toDataURL({
            format: format,
            quality: quality,
            multiplier: 1
        });
    }
    
    exportImage() {
        const link = document.createElement('a');
        link.download = 'foto-editada.png';
        link.href = this.getCanvasImage();
        link.click();
    }
    
    destroy() {
        // Limpar inputs mobile
        this.clearMobileInput();
        
        if (this.canvas) {
            this.canvas.dispose();
        }
        console.log('🔚 Editor destruído');
    }
}

// Export para uso global
window.FabricPhotoEditor = FabricPhotoEditor;

// MOBILE: Configuração de event listeners para botões de ferramentas - CORREÇÃO PARA MOBILE
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Configurando event listeners para botões de ferramentas principais');
    
    // Função unificada para seleção de ferramentas principais (não-modal)
    function selectMainTool(tool, buttonElement) {
        // Feedback visual imediato
        buttonElement.style.transform = 'scale(0.95)';
        setTimeout(() => {
            buttonElement.style.transform = '';
        }, 100);
        
        // Encontrar o editor ativo
        if (window.currentEditor && typeof window.currentEditor.setTool === 'function') {
            window.currentEditor.setTool(tool);
            
            // Atualizar estado visual dos botões
            document.querySelectorAll('[data-tool], .tool-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            buttonElement.classList.add('active');
            
            console.log('🔧 Ferramenta principal selecionada:', tool);
        }
    }
    
    // MOBILE: Touch event handler para botões principais
    let touchHandled = false;
    
    document.addEventListener('touchstart', function(e) {
        const toolButton = e.target.closest('[data-tool], .tool-btn');
        if (toolButton && !toolButton.closest('#fabricPhotoEditorModal')) { // Excluir modal
            e.preventDefault();
            e.stopPropagation();
            
            // Feedback táctil imediato
            toolButton.classList.add('touching');
            
            touchHandled = true;
            const tool = toolButton.dataset.tool || toolButton.getAttribute('data-tool');
            if (tool) {
                selectMainTool(tool, toolButton);
            }
            
            // Reset flag após um tempo
            setTimeout(() => { touchHandled = false; }, 300);
        }
    }, { passive: false });
    
    // Remover classe touching ao finalizar toque
    document.addEventListener('touchend', function(e) {
        const toolButton = e.target.closest('[data-tool], .tool-btn');
        if (toolButton && !toolButton.closest('#fabricPhotoEditorModal')) {
            setTimeout(() => {
                toolButton.classList.remove('touching');
            }, 150);
        }
    });
    
    // DESKTOP: Click event handler para botões principais - fallback
    document.addEventListener('click', function(e) {
        const toolButton = e.target.closest('[data-tool], .tool-btn');
        if (toolButton && !toolButton.closest('#fabricPhotoEditorModal') && !touchHandled) {
            e.preventDefault();
            e.stopPropagation();
            
            const tool = toolButton.dataset.tool || toolButton.getAttribute('data-tool');
            if (tool) {
                selectMainTool(tool, toolButton);
            }
        }
    });
});