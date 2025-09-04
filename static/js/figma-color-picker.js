/**
 * Color Picker Modal Profissional - Estilo Figma
 * Sistema de seleção de cor com gradient, hue e alpha
 */

class FigmaColorPicker {
    constructor(onColorSelect) {
        this.onColorSelect = onColorSelect;
        this.currentColor = { h: 0, s: 100, l: 50, a: 1 };
        this.isVisible = false;
        
        // Cores pré-definidas
        this.presetColors = [
            '#ff0000', '#ff8000', '#ffff00', '#80ff00',
            '#00ff00', '#00ff80', '#00ffff', '#0080ff',
            '#0000ff', '#8000ff', '#ff00ff', '#ff0080',
            '#ffffff', '#cccccc', '#999999', '#666666',
            '#333333', '#000000', '#8b4513', '#a0522d'
        ];
        
        this.createElement();
        this.attachEvents();
    }
    
    createElement() {
        // Criar modal
        this.modal = document.createElement('div');
        this.modal.className = 'figma-color-modal';
        
        this.modal.innerHTML = `
            <div class="figma-color-picker">
                <div class="color-picker-header">
                    <h3 class="color-picker-title">Selecionar Cor</h3>
                    <button class="color-picker-close" type="button">&times;</button>
                </div>
                
                <div class="color-gradient" id="colorGradient"></div>
                
                <div class="hue-slider" id="hueSlider"></div>
                
                <div class="alpha-slider" id="alphaSlider"></div>
                
                <div class="color-preview">
                    <div class="color-preview-item" id="currentColor">Atual</div>
                    <div class="color-preview-item" id="newColor">Nova</div>
                </div>
                
                <div class="color-presets">
                    <h4>Cores Rápidas</h4>
                    <div class="preset-colors" id="presetColors"></div>
                </div>
                
                <div class="color-picker-actions">
                    <button class="color-action-btn" id="cancelColor">Cancelar</button>
                    <button class="color-action-btn primary" id="selectColor">Selecionar</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Criar cores preset
        this.createPresetColors();
        
        // Elementos principais
        this.gradient = this.modal.querySelector('#colorGradient');
        this.hueSlider = this.modal.querySelector('#hueSlider');
        this.alphaSlider = this.modal.querySelector('#alphaSlider');
        this.currentColorPreview = this.modal.querySelector('#currentColor');
        this.newColorPreview = this.modal.querySelector('#newColor');
    }
    
    createPresetColors() {
        const container = this.modal.querySelector('#presetColors');
        
        this.presetColors.forEach(color => {
            const colorDiv = document.createElement('div');
            colorDiv.className = 'preset-color';
            colorDiv.style.backgroundColor = color;
            colorDiv.dataset.color = color;
            
            colorDiv.addEventListener('click', () => {
                this.setColorFromHex(color);
                this.updatePreview();
            });
            
            container.appendChild(colorDiv);
        });
    }
    
    attachEvents() {
        const closeBtn = this.modal.querySelector('.color-picker-close');
        const cancelBtn = this.modal.querySelector('#cancelColor');
        const selectBtn = this.modal.querySelector('#selectColor');
        
        // Fechar modal
        [closeBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => this.hide());
        });
        
        // Selecionar cor
        selectBtn.addEventListener('click', () => {
            this.selectCurrentColor();
        });
        
        // Clique fora para fechar
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });
        
        // Eventos de touch/mouse
        this.attachSliderEvents();
    }
    
    attachSliderEvents() {
        // Gradient picker
        this.attachPointerEvents(this.gradient, (x, y) => {
            const rect = this.gradient.getBoundingClientRect();
            const s = Math.round((x / rect.width) * 100);
            const l = Math.round(100 - (y / rect.height) * 100);
            
            this.currentColor.s = Math.max(0, Math.min(100, s));
            this.currentColor.l = Math.max(0, Math.min(100, l));
            
            this.updateGradientPosition();
            this.updatePreview();
        });
        
        // Hue slider
        this.attachPointerEvents(this.hueSlider, (x) => {
            const rect = this.hueSlider.getBoundingClientRect();
            const h = Math.round((x / rect.width) * 360);
            
            this.currentColor.h = Math.max(0, Math.min(360, h));
            
            this.updateHuePosition();
            this.updateGradientBackground();
            this.updatePreview();
        });
        
        // Alpha slider
        this.attachPointerEvents(this.alphaSlider, (x) => {
            const rect = this.alphaSlider.getBoundingClientRect();
            const a = x / rect.width;
            
            this.currentColor.a = Math.max(0, Math.min(1, a));
            
            this.updateAlphaPosition();
            this.updatePreview();
        });
    }
    
    attachPointerEvents(element, callback) {
        let isPointerDown = false;
        
        const handleStart = (e) => {
            e.preventDefault();
            isPointerDown = true;
            
            const rect = element.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            callback(
                clientX - rect.left,
                clientY - rect.top
            );
        };
        
        const handleMove = (e) => {
            if (!isPointerDown) return;
            e.preventDefault();
            
            const rect = element.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            callback(
                Math.max(0, Math.min(rect.width, clientX - rect.left)),
                Math.max(0, Math.min(rect.height, clientY - rect.top))
            );
        };
        
        const handleEnd = () => {
            isPointerDown = false;
        };
        
        // Mouse events
        element.addEventListener('mousedown', handleStart);
        document.addEventListener('mousemove', handleMove);
        document.addEventListener('mouseup', handleEnd);
        
        // Touch events
        element.addEventListener('touchstart', handleStart, { passive: false });
        document.addEventListener('touchmove', handleMove, { passive: false });
        document.addEventListener('touchend', handleEnd);
    }
    
    show(currentColor = '#ff0000') {
        this.setColorFromHex(currentColor);
        this.originalColor = currentColor;
        
        this.updateGradientBackground();
        this.updatePositions();
        this.updatePreview();
        
        this.isVisible = true;
        this.modal.classList.add('show');
        
        // Focar no modal para acessibilidade
        this.modal.focus();
    }
    
    hide() {
        this.isVisible = false;
        this.modal.classList.remove('show');
    }
    
    selectCurrentColor() {
        const colorHex = this.hslToHex(this.currentColor);
        if (this.onColorSelect) {
            this.onColorSelect(colorHex);
        }
        this.hide();
    }
    
    setColorFromHex(hex) {
        const hsl = this.hexToHsl(hex);
        this.currentColor = { ...hsl, a: 1 };
    }
    
    updateGradientBackground() {
        const hue = this.currentColor.h;
        this.gradient.style.background = `
            linear-gradient(to bottom, transparent, black),
            linear-gradient(to right, white, hsl(${hue}, 100%, 50%))
        `;
    }
    
    updatePositions() {
        this.updateGradientPosition();
        this.updateHuePosition();
        this.updateAlphaPosition();
    }
    
    updateGradientPosition() {
        const x = (this.currentColor.s / 100) * 100;
        const y = (1 - this.currentColor.l / 100) * 100;
        
        this.gradient.style.setProperty('--picker-x', `${x}%`);
        this.gradient.style.setProperty('--picker-y', `${y}%`);
    }
    
    updateHuePosition() {
        const position = (this.currentColor.h / 360) * 100;
        this.hueSlider.style.setProperty('--hue-position', `${position}%`);
    }
    
    updateAlphaPosition() {
        const position = this.currentColor.a * 100;
        this.alphaSlider.style.setProperty('--alpha-position', `${position}%`);
    }
    
    updatePreview() {
        const currentHex = this.hslToHex(this.currentColor);
        const currentRgba = this.hslToRgba(this.currentColor);
        
        this.newColorPreview.style.backgroundColor = currentRgba;
        this.currentColorPreview.style.backgroundColor = this.originalColor || currentHex;
        
        // Atualizar alpha slider background
        const rgbColor = this.hslToRgb(this.currentColor);
        this.alphaSlider.style.setProperty(
            '--current-color-rgb', 
            `rgb(${rgbColor.r}, ${rgbColor.g}, ${rgbColor.b})`
        );
    }
    
    // Utility functions para conversão de cores
    hexToHsl(hex) {
        const r = parseInt(hex.slice(1, 3), 16) / 255;
        const g = parseInt(hex.slice(3, 5), 16) / 255;
        const b = parseInt(hex.slice(5, 7), 16) / 255;
        
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        let h, s, l = (max + min) / 2;
        
        if (max === min) {
            h = s = 0;
        } else {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            
            switch (max) {
                case r: h = (g - b) / d + (g < b ? 6 : 0); break;
                case g: h = (b - r) / d + 2; break;
                case b: h = (r - g) / d + 4; break;
            }
            h /= 6;
        }
        
        return {
            h: Math.round(h * 360),
            s: Math.round(s * 100),
            l: Math.round(l * 100)
        };
    }
    
    hslToHex(hsl) {
        const { h, s, l } = hsl;
        const c = (1 - Math.abs(2 * l / 100 - 1)) * s / 100;
        const x = c * (1 - Math.abs((h / 60) % 2 - 1));
        const m = l / 100 - c / 2;
        let r, g, b;
        
        if (0 <= h && h < 60) {
            r = c; g = x; b = 0;
        } else if (60 <= h && h < 120) {
            r = x; g = c; b = 0;
        } else if (120 <= h && h < 180) {
            r = 0; g = c; b = x;
        } else if (180 <= h && h < 240) {
            r = 0; g = x; b = c;
        } else if (240 <= h && h < 300) {
            r = x; g = 0; b = c;
        } else if (300 <= h && h < 360) {
            r = c; g = 0; b = x;
        }
        
        r = Math.round((r + m) * 255);
        g = Math.round((g + m) * 255);
        b = Math.round((b + m) * 255);
        
        return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
    }
    
    hslToRgb(hsl) {
        const { h, s, l } = hsl;
        const c = (1 - Math.abs(2 * l / 100 - 1)) * s / 100;
        const x = c * (1 - Math.abs((h / 60) % 2 - 1));
        const m = l / 100 - c / 2;
        let r, g, b;
        
        if (0 <= h && h < 60) {
            r = c; g = x; b = 0;
        } else if (60 <= h && h < 120) {
            r = x; g = c; b = 0;
        } else if (120 <= h && h < 180) {
            r = 0; g = c; b = x;
        } else if (180 <= h && h < 240) {
            r = 0; g = x; b = c;
        } else if (240 <= h && h < 300) {
            r = x; g = 0; b = c;
        } else if (300 <= h && h < 360) {
            r = c; g = 0; b = x;
        }
        
        return {
            r: Math.round((r + m) * 255),
            g: Math.round((g + m) * 255),
            b: Math.round((b + m) * 255)
        };
    }
    
    hslToRgba(hsl) {
        const rgb = this.hslToRgb(hsl);
        return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${hsl.a})`;
    }
}

// Export para uso global
window.FigmaColorPicker = FigmaColorPicker;