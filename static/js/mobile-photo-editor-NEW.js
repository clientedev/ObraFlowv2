/**
 * EDITOR DE FOTOS MOBILE - REESCRITO DO ZERO
 * Coordenadas precisas, funcionalidade completa, design profissional
 */

class MobilePhotoEditor {
    constructor(canvasId) {
        console.log('🎨 Iniciando Mobile Photo Editor NOVO');
        
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Canvas não encontrado:', canvasId);
            return;
        }
        
        this.ctx = this.canvas.getContext('2d');
        this.image = null;
        this.objects = [];
        this.selectedObject = null;
        this.currentTool = null;
        this.currentColor = '#ff0000';
        
        // Estados
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.objectStart = { x: 0, y: 0 };
        
        this.init();
    }
    
    init() {
        this.setupCanvas();
        this.setupEvents();
        this.setupToolbar();
        console.log('✅ Editor iniciado com sucesso');
    }
    
    setupCanvas() {
        // Configuração mobile-first
        this.canvas.style.touchAction = 'none';
        this.canvas.style.userSelect = 'none';
        this.canvas.style.webkitUserSelect = 'none';
        this.canvas.style.cursor = 'crosshair';
        this.canvas.style.display = 'block';
        this.canvas.style.maxWidth = '100%';
        this.canvas.style.height = 'auto';
        
        // Prevenir menu de contexto
        this.canvas.addEventListener('contextmenu', e => e.preventDefault());
        
        // Dimensões responsivas
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }
    
    resizeCanvas() {
        const container = this.canvas.parentElement;
        const containerWidth = container.offsetWidth;
        const aspectRatio = this.canvas.height / this.canvas.width;
        
        this.canvas.style.width = containerWidth + 'px';
        this.canvas.style.height = (containerWidth * aspectRatio) + 'px';
    }
    
    setupEvents() {
        // Touch events
        this.canvas.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.canvas.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.canvas.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });
        
        // Mouse events (desktop)
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
    }
    
    setupToolbar() {
        // Criar toolbar se não existir
        let toolbar = document.getElementById('photo-editor-toolbar');
        if (!toolbar) {
            toolbar = this.createToolbar();
            this.canvas.parentElement.insertBefore(toolbar, this.canvas);
        }
        
        this.attachToolbarEvents(toolbar);
    }
    
    createToolbar() {
        const toolbar = document.createElement('div');
        toolbar.id = 'photo-editor-toolbar';
        toolbar.className = 'mobile-editor-toolbar';
        toolbar.innerHTML = `
            <div class="toolbar-section">
                <button class="tool-btn" data-tool="brush" title="Pincel">
                    <i class="fas fa-paint-brush"></i>
                </button>
                <button class="tool-btn" data-tool="arrow" title="Seta">
                    <i class="fas fa-arrow-right"></i>
                </button>
                <button class="tool-btn" data-tool="circle" title="Círculo">
                    <i class="far fa-circle"></i>
                </button>
                <button class="tool-btn" data-tool="square" title="Quadrado">
                    <i class="far fa-square"></i>
                </button>
                <button class="tool-btn" data-tool="text" title="Texto">
                    <i class="fas fa-font"></i>
                </button>
            </div>
            <div class="toolbar-section">
                <div class="color-picker">
                    <div class="color-option" data-color="#ff0000" style="background: #ff0000;"></div>
                    <div class="color-option" data-color="#00ff00" style="background: #00ff00;"></div>
                    <div class="color-option" data-color="#0000ff" style="background: #0000ff;"></div>
                    <div class="color-option" data-color="#ffff00" style="background: #ffff00;"></div>
                    <div class="color-option" data-color="#ff00ff" style="background: #ff00ff;"></div>
                    <div class="color-option" data-color="#ffffff" style="background: #ffffff;"></div>
                </div>
            </div>
            <div class="toolbar-section">
                <button class="action-btn" id="clear-canvas" title="Limpar">
                    <i class="fas fa-trash"></i>
                </button>
                <button class="action-btn confirm-btn" id="save-edits" title="Salvar">
                    <i class="fas fa-check"></i>
                </button>
            </div>
        `;
        
        // Adicionar CSS
        this.addToolbarStyles();
        
        return toolbar;
    }
    
    addToolbarStyles() {
        if (document.getElementById('mobile-editor-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'mobile-editor-styles';
        style.textContent = `
            .mobile-editor-toolbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
                margin-bottom: 15px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                flex-wrap: wrap;
                gap: 10px;
            }
            
            .toolbar-section {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .tool-btn, .action-btn {
                width: 44px;
                height: 44px;
                border: none;
                border-radius: 8px;
                background: white;
                color: #333;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .tool-btn:hover, .action-btn:hover {
                background: #e9ecef;
                transform: translateY(-1px);
            }
            
            .tool-btn.active {
                background: #20c1e8;
                color: white;
            }
            
            .confirm-btn {
                background: #28a745;
                color: white;
            }
            
            .confirm-btn:hover {
                background: #218838;
            }
            
            .color-picker {
                display: flex;
                gap: 6px;
            }
            
            .color-option {
                width: 32px;
                height: 32px;
                border-radius: 6px;
                cursor: pointer;
                border: 2px solid #ccc;
                transition: transform 0.2s;
            }
            
            .color-option:hover {
                transform: scale(1.1);
            }
            
            .color-option.active {
                border-color: #20c1e8;
                border-width: 3px;
            }
            
            @media (max-width: 480px) {
                .mobile-editor-toolbar {
                    padding: 10px;
                    gap: 8px;
                }
                
                .tool-btn, .action-btn {
                    width: 40px;
                    height: 40px;
                    font-size: 14px;
                }
                
                .color-option {
                    width: 28px;
                    height: 28px;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    attachToolbarEvents(toolbar) {
        // Ferramentas
        toolbar.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;
                this.selectTool(tool);
            });
        });
        
        // Cores
        toolbar.querySelectorAll('.color-option').forEach(color => {
            color.addEventListener('click', (e) => {
                const colorValue = e.currentTarget.dataset.color;
                this.selectColor(colorValue);
            });
        });
        
        // Ações
        toolbar.querySelector('#clear-canvas')?.addEventListener('click', () => this.clearCanvas());
        toolbar.querySelector('#save-edits')?.addEventListener('click', () => this.saveEdits());
    }
    
    selectTool(tool) {
        console.log('🔧 Ferramenta selecionada:', tool);
        this.currentTool = tool;
        this.selectedObject = null;
        
        // Atualizar visual dos botões
        document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelector(`[data-tool="${tool}"]`)?.classList.add('active');
        
        this.redraw();
    }
    
    selectColor(color) {
        console.log('🎨 Cor selecionada:', color);
        this.currentColor = color;
        
        // Atualizar visual das cores
        document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
        document.querySelector(`[data-color="${color}"]`)?.classList.add('active');
    }
    
    // === COORDENADAS PRECISAS ===
    getCoordinates(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }
    
    // === EVENTOS TOUCH ===
    handleTouchStart(e) {
        e.preventDefault();
        
        const touch = e.touches[0];
        const coords = this.getCoordinates(touch.clientX, touch.clientY);
        
        console.log(`👆 Touch em: (${Math.round(coords.x)}, ${Math.round(coords.y)})`);
        
        this.handleStart(coords.x, coords.y);
    }
    
    handleTouchMove(e) {
        e.preventDefault();
        
        if (!this.isDragging) return;
        
        const touch = e.touches[0];
        const coords = this.getCoordinates(touch.clientX, touch.clientY);
        
        this.handleMove(coords.x, coords.y);
    }
    
    handleTouchEnd(e) {
        e.preventDefault();
        this.handleEnd();
    }
    
    // === EVENTOS MOUSE ===
    handleMouseDown(e) {
        e.preventDefault();
        
        const coords = this.getCoordinates(e.clientX, e.clientY);
        this.handleStart(coords.x, coords.y);
    }
    
    handleMouseMove(e) {
        if (!this.isDragging) return;
        
        const coords = this.getCoordinates(e.clientX, e.clientY);
        this.handleMove(coords.x, coords.y);
    }
    
    handleMouseUp(e) {
        this.handleEnd();
    }
    
    // === LÓGICA DE INTERAÇÃO ===
    handleStart(x, y) {
        if (!this.currentTool) return;
        
        // Verificar se clicou em objeto existente
        const clickedObject = this.getObjectAt(x, y);
        
        if (clickedObject) {
            this.selectObject(clickedObject);
            this.startDragging(x, y);
        } else {
            this.createObject(x, y);
        }
    }
    
    handleMove(x, y) {
        if (!this.isDragging || !this.selectedObject) return;
        
        const deltaX = x - this.dragStart.x;
        const deltaY = y - this.dragStart.y;
        
        this.selectedObject.x = this.objectStart.x + deltaX;
        this.selectedObject.y = this.objectStart.y + deltaY;
        
        this.redraw();
    }
    
    handleEnd() {
        this.isDragging = false;
        this.canvas.style.cursor = 'crosshair';
    }
    
    createObject(x, y) {
        const object = {
            id: Date.now(),
            type: this.currentTool,
            x: x,
            y: y,
            width: 60,
            height: 60,
            color: this.currentColor,
            text: this.currentTool === 'text' ? 'Texto' : null,
            rotation: 0
        };
        
        this.objects.push(object);
        this.selectObject(object);
        
        console.log(`✨ Objeto ${this.currentTool} criado em (${Math.round(x)}, ${Math.round(y)})`);
        
        this.redraw();
    }
    
    selectObject(object) {
        this.selectedObject = object;
        this.redraw();
        console.log(`🎯 Objeto selecionado: ${object.type}`);
    }
    
    startDragging(x, y) {
        this.isDragging = true;
        this.dragStart = { x, y };
        this.objectStart = { x: this.selectedObject.x, y: this.selectedObject.y };
        this.canvas.style.cursor = 'move';
    }
    
    getObjectAt(x, y) {
        for (let i = this.objects.length - 1; i >= 0; i--) {
            const obj = this.objects[i];
            if (x >= obj.x && x <= obj.x + obj.width &&
                y >= obj.y && y <= obj.y + obj.height) {
                return obj;
            }
        }
        return null;
    }
    
    // === DESENHO ===
    redraw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Desenhar imagem base se existir
        if (this.image) {
            this.ctx.drawImage(this.image, 0, 0, this.canvas.width, this.canvas.height);
        }
        
        // Desenhar objetos
        this.objects.forEach(obj => {
            this.drawObject(obj);
        });
    }
    
    drawObject(obj) {
        this.ctx.save();
        this.ctx.strokeStyle = obj.color;
        this.ctx.fillStyle = obj.color;
        this.ctx.lineWidth = 3;
        
        const centerX = obj.x + obj.width / 2;
        const centerY = obj.y + obj.height / 2;
        
        this.ctx.translate(centerX, centerY);
        this.ctx.rotate(obj.rotation * Math.PI / 180);
        this.ctx.translate(-obj.width / 2, -obj.height / 2);
        
        switch (obj.type) {
            case 'brush':
                this.ctx.fillRect(0, 0, obj.width, obj.height);
                break;
                
            case 'circle':
                this.ctx.beginPath();
                this.ctx.arc(obj.width / 2, obj.height / 2, obj.width / 2, 0, 2 * Math.PI);
                this.ctx.stroke();
                break;
                
            case 'square':
                this.ctx.strokeRect(0, 0, obj.width, obj.height);
                break;
                
            case 'arrow':
                this.drawArrow(obj);
                break;
                
            case 'text':
                this.ctx.font = '16px Arial';
                this.ctx.fillText(obj.text || 'Texto', 0, obj.height / 2);
                break;
        }
        
        // Desenhar seleção
        if (obj === this.selectedObject) {
            this.ctx.strokeStyle = '#20c1e8';
            this.ctx.lineWidth = 2;
            this.ctx.setLineDash([5, 5]);
            this.ctx.strokeRect(-2, -2, obj.width + 4, obj.height + 4);
            this.ctx.setLineDash([]);
        }
        
        this.ctx.restore();
    }
    
    drawArrow(obj) {
        const headSize = 15;
        const x1 = 0;
        const y1 = obj.height / 2;
        const x2 = obj.width;
        const y2 = obj.height / 2;
        
        // Linha principal
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y1);
        this.ctx.lineTo(x2, y2);
        this.ctx.stroke();
        
        // Cabeça da seta
        this.ctx.beginPath();
        this.ctx.moveTo(x2, y2);
        this.ctx.lineTo(x2 - headSize, y2 - headSize / 2);
        this.ctx.moveTo(x2, y2);
        this.ctx.lineTo(x2 - headSize, y2 + headSize / 2);
        this.ctx.stroke();
    }
    
    // === AÇÕES ===
    loadImage(src) {
        const img = new Image();
        img.onload = () => {
            this.image = img;
            this.canvas.width = img.width;
            this.canvas.height = img.height;
            this.resizeCanvas();
            this.redraw();
            console.log('✅ Imagem carregada');
        };
        img.src = src;
    }
    
    clearCanvas() {
        if (confirm('Deseja limpar todas as anotações?')) {
            this.objects = [];
            this.selectedObject = null;
            this.redraw();
            console.log('🧹 Canvas limpo');
        }
    }
    
    saveEdits() {
        console.log('💾 Salvando edições...');
        
        // Aqui você pode implementar a lógica de salvamento
        // Por exemplo, converter canvas para base64 ou enviar dados via AJAX
        
        const imageData = this.canvas.toDataURL('image/png');
        console.log('✅ Edições salvas');
        
        // Mostrar feedback
        this.showSaveMessage();
        
        return imageData;
    }
    
    showSaveMessage() {
        const message = document.createElement('div');
        message.textContent = '✅ Edições salvas com sucesso!';
        message.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #28a745;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            z-index: 10000;
            font-weight: bold;
        `;
        
        document.body.appendChild(message);
        
        setTimeout(() => {
            message.remove();
        }, 2000);
    }
}

// Inicialização global
window.MobilePhotoEditor = MobilePhotoEditor;
console.log('🎨 Mobile Photo Editor carregado!');