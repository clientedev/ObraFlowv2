/**
 * Sistema Profissional de Edição de Fotos para Touch
 * Compatível com relatórios normais e express
 */

class ProfessionalPhotoEditor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.originalImageData = null;
        this.actions = [];
        this.currentAction = [];
        this.isDrawing = false;
        this.currentTool = 'pen';
        this.currentColor = '#ff0000';
        this.currentSize = 3;
        this.startX = 0;
        this.startY = 0;
        this.previewLayer = null;
        
        // Touch-specific properties
        this.touchStartTime = 0;
        this.lastTouchPosition = null;
        this.touchSensitivity = 1;
        this.minTouchDistance = 2;
        
        this.initializeEditor();
    }
    
    initializeEditor() {
        // Configurar canvas para alta precisão
        this.canvas.style.touchAction = 'none';
        this.canvas.style.cursor = 'crosshair';
        
        // Event listeners unificados para mouse e touch
        this.addEventListeners();
        
        // Configurar preview layer
        this.createPreviewLayer();
        
        console.log('Editor profissional inicializado');
    }
    
    createPreviewLayer() {
        // Criar canvas de preview para visualização em tempo real
        this.previewLayer = document.createElement('canvas');
        this.previewLayer.width = this.canvas.width;
        this.previewLayer.height = this.canvas.height;
        this.previewLayer.style.position = 'absolute';
        this.previewLayer.style.top = this.canvas.offsetTop + 'px';
        this.previewLayer.style.left = this.canvas.offsetLeft + 'px';
        this.previewLayer.style.pointerEvents = 'none';
        this.previewLayer.style.opacity = '0.8';
        
        this.canvas.parentNode.appendChild(this.previewLayer);
        this.previewCtx = this.previewLayer.getContext('2d');
    }
    
    addEventListeners() {
        // Touch Events - Máxima Precisão
        this.canvas.addEventListener('touchstart', (e) => this.handleStart(e), { passive: false });
        this.canvas.addEventListener('touchmove', (e) => this.handleMove(e), { passive: false });
        this.canvas.addEventListener('touchend', (e) => this.handleEnd(e), { passive: false });
        
        // Mouse Events para desktop
        this.canvas.addEventListener('mousedown', (e) => this.handleStart(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleEnd(e));
        this.canvas.addEventListener('mouseleave', (e) => this.handleEnd(e));
        
        // Prevenir gestos indesejados
        this.canvas.addEventListener('gesturestart', e => e.preventDefault());
        this.canvas.addEventListener('gesturechange', e => e.preventDefault());
        this.canvas.addEventListener('gestureend', e => e.preventDefault());
    }
    
    getCoordinates(e) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        
        let clientX, clientY;
        
        if (e.touches && e.touches.length > 0) {
            // Touch event
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else if (e.changedTouches && e.changedTouches.length > 0) {
            // Touch end event
            clientX = e.changedTouches[0].clientX;
            clientY = e.changedTouches[0].clientY;
        } else {
            // Mouse event
            clientX = e.clientX;
            clientY = e.clientY;
        }
        
        // Calcular coordenadas precisas
        const x = (clientX - rect.left) * scaleX;
        const y = (clientY - rect.top) * scaleY;
        
        // Garantir que está dentro dos limites
        return [
            Math.max(0, Math.min(this.canvas.width, x)),
            Math.max(0, Math.min(this.canvas.height, y))
        ];
    }
    
    handleStart(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Verificar se é toque simples
        if (e.touches && e.touches.length > 1) return;
        
        this.isDrawing = true;
        this.touchStartTime = Date.now();
        
        const [x, y] = this.getCoordinates(e);
        this.startX = x;
        this.startY = y;
        this.lastTouchPosition = { x, y };
        
        if (this.currentTool === 'pen') {
            this.ctx.beginPath();
            this.ctx.moveTo(x, y);
            this.currentAction = [];
        }
        
        // Limpar preview
        this.clearPreview();
        
        console.log(`Iniciando ${this.currentTool} em (${x}, ${y})`);
    }
    
    handleMove(e) {
        if (!this.isDrawing) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        // Verificar se é toque simples
        if (e.touches && e.touches.length > 1) return;
        
        const [x, y] = this.getCoordinates(e);
        
        // Filtro de distância mínima para suavizar movimento
        if (this.lastTouchPosition) {
            const distance = Math.sqrt(
                Math.pow(x - this.lastTouchPosition.x, 2) + 
                Math.pow(y - this.lastTouchPosition.y, 2)
            );
            
            if (distance < this.minTouchDistance) return;
        }
        
        this.lastTouchPosition = { x, y };
        
        if (this.currentTool === 'pen') {
            this.drawPenStroke(x, y);
        } else {
            this.drawShapePreview(this.startX, this.startY, x, y);
        }
    }
    
    handleEnd(e) {
        if (!this.isDrawing) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        this.isDrawing = false;
        
        const [x, y] = this.getCoordinates(e);
        
        // Finalizar ação baseada na ferramenta
        this.finalizeAction(x, y);
        
        // Limpar preview
        this.clearPreview();
        
        console.log(`Finalizando ${this.currentTool}. Total de ações: ${this.actions.length}`);
    }
    
    drawPenStroke(x, y) {
        this.ctx.strokeStyle = this.currentColor;
        this.ctx.lineWidth = this.currentSize;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.lineTo(x, y);
        this.ctx.stroke();
        
        this.currentAction.push({
            tool: 'pen',
            x: x,
            y: y,
            color: this.currentColor,
            size: this.currentSize
        });
    }
    
    drawShapePreview(startX, startY, endX, endY) {
        // Limpar preview anterior
        this.clearPreview();
        
        // Configurar preview
        this.previewCtx.strokeStyle = this.currentColor;
        this.previewCtx.lineWidth = this.currentSize;
        this.previewCtx.lineCap = 'round';
        this.previewCtx.lineJoin = 'round';
        
        // Desenhar preview da forma
        if (this.currentTool === 'arrow') {
            this.drawArrowPreview(startX, startY, endX, endY);
        } else if (this.currentTool === 'circle') {
            this.drawCirclePreview(startX, startY, endX, endY);
        } else if (this.currentTool === 'rectangle') {
            this.drawRectanglePreview(startX, startY, endX, endY);
        }
    }
    
    drawArrowPreview(fromX, fromY, toX, toY) {
        const lineLength = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
        const isMobile = window.innerWidth <= 768;
        
        // Cabeça da seta otimizada para touch
        let headLength = Math.max(15, Math.min(35, lineLength * 0.25));
        if (isMobile) {
            headLength = Math.max(18, Math.min(40, lineLength * 0.3));
        }
        
        const angle = Math.atan2(toY - fromY, toX - fromX);
        
        this.previewCtx.beginPath();
        
        // Linha principal
        this.previewCtx.moveTo(fromX, fromY);
        this.previewCtx.lineTo(toX, toY);
        
        // Cabeça da seta
        const arrowAngle = Math.PI / 5; // 36 graus para melhor visibilidade
        this.previewCtx.lineTo(
            toX - headLength * Math.cos(angle - arrowAngle), 
            toY - headLength * Math.sin(angle - arrowAngle)
        );
        this.previewCtx.moveTo(toX, toY);
        this.previewCtx.lineTo(
            toX - headLength * Math.cos(angle + arrowAngle), 
            toY - headLength * Math.sin(angle + arrowAngle)
        );
        
        this.previewCtx.stroke();
    }
    
    drawCirclePreview(centerX, centerY, edgeX, edgeY) {
        const radius = Math.sqrt(Math.pow(edgeX - centerX, 2) + Math.pow(edgeY - centerY, 2));
        const minRadius = window.innerWidth <= 768 ? 10 : 8;
        const finalRadius = Math.max(minRadius, radius);
        
        this.previewCtx.beginPath();
        this.previewCtx.arc(centerX, centerY, finalRadius, 0, 2 * Math.PI);
        this.previewCtx.stroke();
    }
    
    drawRectanglePreview(startX, startY, endX, endY) {
        const width = endX - startX;
        const height = endY - startY;
        
        this.previewCtx.beginPath();
        this.previewCtx.rect(startX, startY, width, height);
        this.previewCtx.stroke();
    }
    
    finalizeAction(x, y) {
        if (this.currentTool === 'pen' && this.currentAction.length > 0) {
            this.actions.push([...this.currentAction]);
        } else if (this.currentTool !== 'pen') {
            // Desenhar forma final no canvas principal
            this.ctx.strokeStyle = this.currentColor;
            this.ctx.lineWidth = this.currentSize;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';
            
            const action = {
                tool: this.currentTool,
                color: this.currentColor,
                size: this.currentSize
            };
            
            if (this.currentTool === 'arrow') {
                this.drawArrowFinal(this.startX, this.startY, x, y);
                Object.assign(action, {
                    startX: this.startX,
                    startY: this.startY,
                    endX: x,
                    endY: y
                });
            } else if (this.currentTool === 'circle') {
                this.drawCircleFinal(this.startX, this.startY, x, y);
                Object.assign(action, {
                    centerX: this.startX,
                    centerY: this.startY,
                    radius: Math.sqrt(Math.pow(x - this.startX, 2) + Math.pow(y - this.startY, 2))
                });
            } else if (this.currentTool === 'rectangle') {
                this.drawRectangleFinal(this.startX, this.startY, x, y);
                Object.assign(action, {
                    startX: this.startX,
                    startY: this.startY,
                    endX: x,
                    endY: y
                });
            }
            
            this.actions.push([action]);
        }
    }
    
    drawArrowFinal(fromX, fromY, toX, toY) {
        const lineLength = Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2));
        const isMobile = window.innerWidth <= 768;
        
        let headLength = Math.max(15, Math.min(35, lineLength * 0.25));
        if (isMobile) {
            headLength = Math.max(18, Math.min(40, lineLength * 0.3));
        }
        
        const angle = Math.atan2(toY - fromY, toX - fromX);
        
        this.ctx.beginPath();
        this.ctx.moveTo(fromX, fromY);
        this.ctx.lineTo(toX, toY);
        
        const arrowAngle = Math.PI / 5;
        this.ctx.lineTo(
            toX - headLength * Math.cos(angle - arrowAngle), 
            toY - headLength * Math.sin(angle - arrowAngle)
        );
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(
            toX - headLength * Math.cos(angle + arrowAngle), 
            toY - headLength * Math.sin(angle + arrowAngle)
        );
        
        this.ctx.stroke();
    }
    
    drawCircleFinal(centerX, centerY, edgeX, edgeY) {
        const radius = Math.sqrt(Math.pow(edgeX - centerX, 2) + Math.pow(edgeY - centerY, 2));
        const minRadius = window.innerWidth <= 768 ? 10 : 8;
        const finalRadius = Math.max(minRadius, radius);
        
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, finalRadius, 0, 2 * Math.PI);
        this.ctx.stroke();
    }
    
    drawRectangleFinal(startX, startY, endX, endY) {
        const width = endX - startX;
        const height = endY - startY;
        
        this.ctx.beginPath();
        this.ctx.rect(startX, startY, width, height);
        this.ctx.stroke();
    }
    
    clearPreview() {
        this.previewCtx.clearRect(0, 0, this.previewLayer.width, this.previewLayer.height);
    }
    
    // Métodos públicos para controle
    setTool(tool) {
        this.currentTool = tool;
        console.log('Ferramenta alterada para:', tool);
    }
    
    setColor(color) {
        this.currentColor = color;
        console.log('Cor alterada para:', color);
    }
    
    setSize(size) {
        this.currentSize = parseInt(size);
        console.log('Tamanho alterado para:', size);
    }
    
    undo() {
        if (this.actions.length > 0) {
            this.actions.pop();
            this.redrawCanvas();
            console.log('Ação desfeita. Ações restantes:', this.actions.length);
        }
    }
    
    clear() {
        if (confirm('Tem certeza que deseja limpar todas as anotações?')) {
            this.actions = [];
            this.redrawCanvas();
            console.log('Canvas limpo');
        }
    }
    
    redrawCanvas() {
        if (!this.originalImageData) return;
        
        // Restaurar imagem original
        this.ctx.putImageData(this.originalImageData, 0, 0);
        
        // Redesenhar todas as ações
        this.actions.forEach(action => {
            if (action.length > 0) {
                const firstStep = action[0];
                
                this.ctx.strokeStyle = firstStep.color;
                this.ctx.lineWidth = firstStep.size;
                this.ctx.lineCap = 'round';
                this.ctx.lineJoin = 'round';
                
                if (firstStep.tool === 'pen') {
                    this.ctx.beginPath();
                    this.ctx.moveTo(firstStep.x, firstStep.y);
                    action.forEach(step => {
                        this.ctx.lineTo(step.x, step.y);
                    });
                    this.ctx.stroke();
                } else if (firstStep.tool === 'arrow') {
                    this.drawArrowFinal(firstStep.startX, firstStep.startY, firstStep.endX, firstStep.endY);
                } else if (firstStep.tool === 'circle') {
                    this.ctx.beginPath();
                    this.ctx.arc(firstStep.centerX, firstStep.centerY, firstStep.radius, 0, 2 * Math.PI);
                    this.ctx.stroke();
                } else if (firstStep.tool === 'rectangle') {
                    this.ctx.beginPath();
                    this.ctx.rect(firstStep.startX, firstStep.startY, 
                                firstStep.endX - firstStep.startX, 
                                firstStep.endY - firstStep.startY);
                    this.ctx.stroke();
                }
            }
        });
    }
    
    loadImage(imageElement) {
        this.canvas.width = imageElement.naturalWidth;
        this.canvas.height = imageElement.naturalHeight;
        
        // Atualizar preview layer
        this.previewLayer.width = this.canvas.width;
        this.previewLayer.height = this.canvas.height;
        
        this.ctx.drawImage(imageElement, 0, 0);
        this.originalImageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
        
        console.log('Imagem carregada:', this.canvas.width, 'x', this.canvas.height);
    }
    
    getImageData() {
        return this.canvas.toDataURL('image/jpeg', 0.9);
    }
}

// Variável global para instância do editor
let professionalEditor = null;

// Função para inicializar o editor profissional
function initializeProfessionalEditor() {
    if (professionalEditor) {
        professionalEditor = null;
    }
    
    professionalEditor = new ProfessionalPhotoEditor('photoCanvas');
    
    // Conectar controles da interface
    setupEditorControls();
    
    console.log('Editor profissional inicializado com sucesso');
}

function setupEditorControls() {
    // Ferramentas
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            professionalEditor.setTool(this.dataset.tool);
        });
    });
    
    // Cores
    document.getElementById('colorPicker')?.addEventListener('change', function() {
        professionalEditor.setColor(this.value);
    });
    
    document.querySelectorAll('.color-preset').forEach(preset => {
        preset.addEventListener('click', function() {
            const color = this.style.backgroundColor;
            const hex = rgbToHex(color);
            professionalEditor.setColor(hex);
            document.getElementById('colorPicker').value = hex;
        });
    });
    
    // Tamanho
    document.getElementById('brushSize')?.addEventListener('input', function() {
        professionalEditor.setSize(this.value);
    });
    
    // Ações
    document.getElementById('undoBtn')?.addEventListener('click', () => {
        professionalEditor.undo();
    });
    
    document.getElementById('clearBtn')?.addEventListener('click', () => {
        professionalEditor.clear();
    });
}

function rgbToHex(rgb) {
    const result = rgb.match(/\d+/g);
    if (result) {
        return '#' + result.map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
    }
    return rgb;
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('photoCanvas')) {
        initializeProfessionalEditor();
    }
});