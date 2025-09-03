/**
 * Editor de Imagens com Precisão Máxima
 * Sistema completo com zoom, pan, snap, ferramentas geométricas e histórico
 */

class PrecisionImageEditor {
    constructor(canvasId, options = {}) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            throw new Error(`Canvas com ID '${canvasId}' não encontrado`);
        }

        this.ctx = this.canvas.getContext('2d');
        this.options = {
            maxZoom: 8,
            minZoom: 0.25,
            snapToGrid: true,
            gridSize: 8,
            hitTolerance: 12,
            devicePixelRatio: window.devicePixelRatio || 1,
            ...options
        };

        this.state = {
            zoom: 1,
            panX: 0,
            panY: 0,
            tool: 'select',
            isDrawing: false,
            isPanning: false,
            selectedObject: null,
            gridVisible: false
        };

        this.objects = [];
        this.history = [];
        this.historyIndex = -1;
        this.maxHistory = 50;
        
        this.originalImage = null;
        this.imageData = null;
        
        this.setupCanvas();
        this.setupEventListeners();
        this.setupUI();
        
        console.log('Editor de Imagens com Precisão Máxima inicializado');
    }

    setupCanvas() {
        // Configurar alta densidade de pixels
        const rect = this.canvas.getBoundingClientRect();
        const ratio = this.options.devicePixelRatio;
        
        this.canvas.width = rect.width * ratio;
        this.canvas.height = rect.height * ratio;
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        this.ctx.scale(ratio, ratio);
        this.ctx.imageSmoothingEnabled = true;
        this.ctx.imageSmoothingQuality = 'high';
        
        // Configurar CSS para precisão
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.cursor = 'crosshair';
    }

    setupEventListeners() {
        // Mouse events
        this.canvas.addEventListener('mousedown', this.handlePointerDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handlePointerMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handlePointerUp.bind(this));
        this.canvas.addEventListener('wheel', this.handleWheel.bind(this), { passive: false });

        // Touch events com máxima precisão
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });

        // Keyboard events
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        
        // Prevent context menu
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
    }

    setupUI() {
        this.createToolbar();
        this.createPropertiesPanel();
        this.createZoomControls();
    }

    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'precision-toolbar';
        toolbar.innerHTML = `
            <div class="toolbar-group">
                <button class="tool-btn active" data-tool="select" title="Selecionar (V)">
                    <i class="fas fa-mouse-pointer"></i>
                </button>
                <button class="tool-btn" data-tool="pen" title="Pincel (B)">
                    <i class="fas fa-paint-brush"></i>
                </button>
                <button class="tool-btn" data-tool="arrow" title="Seta (A)">
                    <i class="fas fa-arrow-right"></i>
                </button>
                <button class="tool-btn" data-tool="rectangle" title="Retângulo (R)">
                    <i class="fas fa-square"></i>
                </button>
                <button class="tool-btn" data-tool="circle" title="Círculo (C)">
                    <i class="fas fa-circle"></i>
                </button>
                <button class="tool-btn" data-tool="text" title="Texto (T)">
                    <i class="fas fa-font"></i>
                </button>
            </div>
            
            <div class="toolbar-group">
                <button class="tool-btn" data-action="undo" title="Desfazer (Ctrl+Z)">
                    <i class="fas fa-undo"></i>
                </button>
                <button class="tool-btn" data-action="redo" title="Refazer (Ctrl+Y)">
                    <i class="fas fa-redo"></i>
                </button>
                <button class="tool-btn" data-action="clear" title="Limpar Tudo">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            
            <div class="toolbar-group">
                <button class="tool-btn" data-action="grid" title="Toggle Grade (G)">
                    <i class="fas fa-th"></i>
                </button>
                <button class="tool-btn" data-action="fit" title="Ajustar à Tela">
                    <i class="fas fa-expand-arrows-alt"></i>
                </button>
            </div>
        `;

        // Inserir antes do canvas
        this.canvas.parentNode.insertBefore(toolbar, this.canvas);

        // Event listeners para toolbar
        toolbar.addEventListener('click', (e) => {
            const btn = e.target.closest('.tool-btn');
            if (!btn) return;

            const tool = btn.getAttribute('data-tool');
            const action = btn.getAttribute('data-action');

            if (tool) {
                this.setTool(tool);
                // Atualizar botões ativos
                toolbar.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            } else if (action) {
                this.executeAction(action);
            }
        });

        this.toolbar = toolbar;
    }

    createZoomControls() {
        const zoomControls = document.createElement('div');
        zoomControls.className = 'zoom-controls';
        zoomControls.innerHTML = `
            <button class="zoom-btn" data-action="zoom-out" title="Diminuir Zoom">
                <i class="fas fa-minus"></i>
            </button>
            <span class="zoom-level">100%</span>
            <button class="zoom-btn" data-action="zoom-in" title="Aumentar Zoom">
                <i class="fas fa-plus"></i>
            </button>
            <button class="zoom-btn" data-action="zoom-fit" title="Ajustar">
                <i class="fas fa-expand"></i>
            </button>
        `;

        this.canvas.parentNode.appendChild(zoomControls);

        zoomControls.addEventListener('click', (e) => {
            const btn = e.target.closest('.zoom-btn');
            if (!btn) return;

            const action = btn.getAttribute('data-action');
            switch (action) {
                case 'zoom-in':
                    this.zoomIn();
                    break;
                case 'zoom-out':
                    this.zoomOut();
                    break;
                case 'zoom-fit':
                    this.fitToCanvas();
                    break;
            }
        });

        this.zoomControls = zoomControls;
    }

    createPropertiesPanel() {
        const panel = document.createElement('div');
        panel.className = 'properties-panel';
        panel.style.display = 'none';
        panel.innerHTML = `
            <h4>Propriedades do Objeto</h4>
            <div class="prop-group">
                <label>X:</label>
                <input type="number" class="prop-input" data-prop="x" step="1">
            </div>
            <div class="prop-group">
                <label>Y:</label>
                <input type="number" class="prop-input" data-prop="y" step="1">
            </div>
            <div class="prop-group">
                <label>Largura:</label>
                <input type="number" class="prop-input" data-prop="width" step="1">
            </div>
            <div class="prop-group">
                <label>Altura:</label>
                <input type="number" class="prop-input" data-prop="height" step="1">
            </div>
            <div class="prop-group">
                <label>Cor:</label>
                <input type="color" class="prop-input" data-prop="color">
            </div>
            <div class="prop-group">
                <label>Espessura:</label>
                <input type="range" class="prop-input" data-prop="strokeWidth" min="1" max="20" step="1">
            </div>
            <div class="prop-group">
                <label>Opacidade:</label>
                <input type="range" class="prop-input" data-prop="opacity" min="0" max="1" step="0.1">
            </div>
        `;

        this.canvas.parentNode.appendChild(panel);

        // Event listeners para propriedades
        panel.addEventListener('change', (e) => {
            if (e.target.classList.contains('prop-input') && this.state.selectedObject) {
                const prop = e.target.getAttribute('data-prop');
                const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value;
                
                this.updateObjectProperty(this.state.selectedObject, prop, value);
                this.render();
                this.addToHistory();
            }
        });

        this.propertiesPanel = panel;
    }

    // Métodos de manipulação de eventos
    handlePointerDown(e) {
        e.preventDefault();
        const pos = this.getPointerPosition(e);
        
        if (this.state.tool === 'select') {
            const hitObject = this.hitTest(pos.x, pos.y);
            if (hitObject) {
                this.selectObject(hitObject);
            } else if (e.shiftKey || e.ctrlKey || this.isTwoFingerTouch(e)) {
                this.startPan(pos);
            } else {
                this.deselectAll();
            }
        } else {
            this.startDrawing(pos);
        }
    }

    handlePointerMove(e) {
        e.preventDefault();
        const pos = this.getPointerPosition(e);
        
        if (this.state.isPanning) {
            this.updatePan(pos);
        } else if (this.state.isDrawing) {
            this.updateDrawing(pos);
        } else {
            this.updateCursor(pos);
        }
    }

    handlePointerUp(e) {
        e.preventDefault();
        
        if (this.state.isDrawing) {
            this.finishDrawing();
        }
        
        if (this.state.isPanning) {
            this.finishPan();
        }
    }

    handleTouchStart(e) {
        e.preventDefault();
        
        if (e.touches.length === 2) {
            this.startPinchZoom(e);
        } else if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY,
                buttons: 1
            });
            this.handlePointerDown(mouseEvent);
        }
    }

    handleTouchMove(e) {
        e.preventDefault();
        
        if (e.touches.length === 2 && this.pinchZoomActive) {
            this.updatePinchZoom(e);
        } else if (e.touches.length === 1) {
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY,
                buttons: 1
            });
            this.handlePointerMove(mouseEvent);
        }
    }

    handleTouchEnd(e) {
        e.preventDefault();
        
        if (this.pinchZoomActive && e.touches.length < 2) {
            this.endPinchZoom();
        }
        
        if (e.touches.length === 0) {
            const mouseEvent = new MouseEvent('mouseup', {
                buttons: 0
            });
            this.handlePointerUp(mouseEvent);
        }
    }

    handleWheel(e) {
        e.preventDefault();
        
        const pos = this.getPointerPosition(e);
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        
        this.zoomAt(pos.x, pos.y, delta);
    }

    handleKeyDown(e) {
        if (e.target.tagName === 'INPUT') return;
        
        switch (e.key) {
            case 'v':
            case 'V':
                this.setTool('select');
                break;
            case 'b':
            case 'B':
                this.setTool('pen');
                break;
            case 'a':
            case 'A':
                this.setTool('arrow');
                break;
            case 'r':
            case 'R':
                this.setTool('rectangle');
                break;
            case 'c':
            case 'C':
                this.setTool('circle');
                break;
            case 't':
            case 'T':
                this.setTool('text');
                break;
            case 'g':
            case 'G':
                this.toggleGrid();
                break;
            case 'Delete':
            case 'Backspace':
                if (this.state.selectedObject) {
                    this.deleteSelected();
                }
                break;
            case 'z':
                if (e.ctrlKey || e.metaKey) {
                    if (e.shiftKey) {
                        this.redo();
                    } else {
                        this.undo();
                    }
                }
                break;
            case 'y':
                if (e.ctrlKey || e.metaKey) {
                    this.redo();
                }
                break;
            case 'ArrowUp':
            case 'ArrowDown':
            case 'ArrowLeft':
            case 'ArrowRight':
                if (this.state.selectedObject) {
                    this.nudgeSelected(e.key, e.shiftKey ? 10 : 1);
                    e.preventDefault();
                }
                break;
        }
    }

    // Métodos utilitários
    getPointerPosition(e) {
        const rect = this.canvas.getBoundingClientRect();
        const clientX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
        const clientY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
        
        // Converter para coordenadas do canvas considerando zoom e pan
        const canvasX = (clientX - rect.left) / this.state.zoom - this.state.panX / this.state.zoom;
        const canvasY = (clientY - rect.top) / this.state.zoom - this.state.panY / this.state.zoom;
        
        return {
            x: this.snapToGrid(canvasX),
            y: this.snapToGrid(canvasY),
            rawX: canvasX,
            rawY: canvasY
        };
    }

    snapToGrid(value) {
        if (!this.options.snapToGrid || !this.state.gridVisible) {
            return value;
        }
        return Math.round(value / this.options.gridSize) * this.options.gridSize;
    }

    // Métodos de zoom
    zoomIn() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        this.zoomAt(centerX, centerY, 0.25);
    }

    zoomOut() {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        this.zoomAt(centerX, centerY, -0.25);
    }

    zoomAt(x, y, delta) {
        const newZoom = Math.max(this.options.minZoom, 
                       Math.min(this.options.maxZoom, this.state.zoom + delta));
        
        if (newZoom !== this.state.zoom) {
            // Calcular novo pan para manter o ponto sob o cursor
            const zoomFactor = newZoom / this.state.zoom;
            this.state.panX = x - (x - this.state.panX) * zoomFactor;
            this.state.panY = y - (y - this.state.panY) * zoomFactor;
            
            this.state.zoom = newZoom;
            this.updateZoomDisplay();
            this.render();
        }
    }

    fitToCanvas() {
        if (!this.originalImage) return;
        
        const canvasRect = this.canvas.getBoundingClientRect();
        const imageAspect = this.originalImage.width / this.originalImage.height;
        const canvasAspect = canvasRect.width / canvasRect.height;
        
        let zoom;
        if (imageAspect > canvasAspect) {
            zoom = canvasRect.width / this.originalImage.width;
        } else {
            zoom = canvasRect.height / this.originalImage.height;
        }
        
        this.state.zoom = Math.max(this.options.minZoom, Math.min(this.options.maxZoom, zoom * 0.9));
        this.state.panX = (canvasRect.width - this.originalImage.width * this.state.zoom) / 2;
        this.state.panY = (canvasRect.height - this.originalImage.height * this.state.zoom) / 2;
        
        this.updateZoomDisplay();
        this.render();
    }

    updateZoomDisplay() {
        if (this.zoomControls) {
            const level = this.zoomControls.querySelector('.zoom-level');
            if (level) {
                level.textContent = Math.round(this.state.zoom * 100) + '%';
            }
        }
    }

    // Métodos de renderização
    render() {
        this.clear();
        this.drawImage();
        if (this.state.gridVisible) {
            this.drawGrid();
        }
        this.drawObjects();
        this.drawSelection();
    }

    clear() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    drawImage() {
        if (!this.originalImage) return;
        
        this.ctx.save();
        this.ctx.scale(this.state.zoom, this.state.zoom);
        this.ctx.translate(this.state.panX / this.state.zoom, this.state.panY / this.state.zoom);
        
        this.ctx.drawImage(this.originalImage, 0, 0);
        
        this.ctx.restore();
    }

    // Métodos públicos
    loadImage(imageElement) {
        this.originalImage = imageElement;
        this.fitToCanvas();
        this.addToHistory();
    }

    setTool(tool) {
        this.state.tool = tool;
        this.deselectAll();
        
        // Atualizar cursor
        const cursors = {
            select: 'default',
            pan: 'grab',
            pen: 'crosshair',
            arrow: 'crosshair',
            rectangle: 'crosshair',
            circle: 'crosshair',
            text: 'text'
        };
        
        this.canvas.style.cursor = cursors[tool] || 'crosshair';
        
        // Atualizar toolbar
        if (this.toolbar) {
            this.toolbar.querySelectorAll('.tool-btn').forEach(btn => {
                btn.classList.toggle('active', btn.getAttribute('data-tool') === tool);
            });
        }
    }

    exportCanvas() {
        // Criar canvas temporário com a imagem final
        const tempCanvas = document.createElement('canvas');
        const tempCtx = tempCanvas.getContext('2d');
        
        // Usar dimensões originais da imagem
        if (this.originalImage) {
            tempCanvas.width = this.originalImage.width;
            tempCanvas.height = this.originalImage.height;
            
            // Desenhar imagem original
            tempCtx.drawImage(this.originalImage, 0, 0);
            
            // Desenhar objetos em escala original
            this.drawObjectsToContext(tempCtx, 1, 0, 0);
        }
        
        return tempCanvas.toDataURL('image/png');
    }

    // Histórico
    addToHistory() {
        // Remover histórico posterior ao índice atual
        this.history = this.history.slice(0, this.historyIndex + 1);
        
        // Adicionar novo estado
        const state = {
            objects: JSON.parse(JSON.stringify(this.objects)),
            zoom: this.state.zoom,
            panX: this.state.panX,
            panY: this.state.panY
        };
        
        this.history.push(state);
        
        // Limitar tamanho do histórico
        if (this.history.length > this.maxHistory) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.restoreFromHistory();
        }
    }

    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.restoreFromHistory();
        }
    }

    restoreFromHistory() {
        const state = this.history[this.historyIndex];
        this.objects = JSON.parse(JSON.stringify(state.objects));
        this.state.zoom = state.zoom;
        this.state.panX = state.panX;
        this.state.panY = state.panY;
        
        this.deselectAll();
        this.updateZoomDisplay();
        this.render();
    }

    // Métodos de ação
    executeAction(action) {
        switch (action) {
            case 'undo':
                this.undo();
                break;
            case 'redo':
                this.redo();
                break;
            case 'clear':
                if (confirm('Limpar todas as anotações?')) {
                    this.objects = [];
                    this.deselectAll();
                    this.render();
                    this.addToHistory();
                }
                break;
            case 'grid':
                this.toggleGrid();
                break;
            case 'fit':
                this.fitToCanvas();
                break;
        }
    }

    toggleGrid() {
        this.state.gridVisible = !this.state.gridVisible;
        this.render();
        
        // Atualizar botão da grade
        if (this.toolbar) {
            const gridBtn = this.toolbar.querySelector('[data-action="grid"]');
            if (gridBtn) {
                gridBtn.classList.toggle('active', this.state.gridVisible);
            }
        }
    }

    // Método de limpeza
    destroy() {
        // Remover event listeners
        this.canvas.removeEventListener('mousedown', this.handlePointerDown);
        this.canvas.removeEventListener('mousemove', this.handlePointerMove);
        this.canvas.removeEventListener('mouseup', this.handlePointerUp);
        this.canvas.removeEventListener('wheel', this.handleWheel);
        this.canvas.removeEventListener('touchstart', this.handleTouchStart);
        this.canvas.removeEventListener('touchmove', this.handleTouchMove);
        this.canvas.removeEventListener('touchend', this.handleTouchEnd);
        document.removeEventListener('keydown', this.handleKeyDown);
        
        // Remover elementos UI
        if (this.toolbar) this.toolbar.remove();
        if (this.zoomControls) this.zoomControls.remove();
        if (this.propertiesPanel) this.propertiesPanel.remove();
    }
}

// Expor classe globalmente
window.PrecisionImageEditor = PrecisionImageEditor;