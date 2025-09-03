/**
 * Sistema de Scroll Horizontal Perfeito para Mobile
 * Otimizado especificamente para tabelas em dispositivos touch
 */

class PerfectHorizontalScroll {
    constructor() {
        this.tables = [];
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupScrollSystem());
        } else {
            this.setupScrollSystem();
        }
    }

    setupScrollSystem() {
        // Encontrar todas as tabelas responsivas
        const containers = document.querySelectorAll('.table-responsive');
        
        containers.forEach(container => {
            this.enhanceTableScroll(container);
        });

        console.log(`Sistema de scroll horizontal configurado para ${containers.length} tabelas`);
    }

    enhanceTableScroll(container) {
        const table = container.querySelector('table');
        if (!table) return;

        // Garantir que a tabela seja scrollável
        this.setupTableScrollability(container, table);
        
        // Configurar eventos touch otimizados
        this.setupTouchEvents(container);
        
        // Adicionar indicadores visuais
        this.addScrollIndicators(container);
        
        // Adicionar ao sistema
        this.tables.push({
            container,
            table,
            isScrolling: false,
            lastScrollLeft: 0
        });
    }

    setupTableScrollability(container, table) {
        // Configurar CSS para scroll horizontal perfeito
        container.style.overflowX = 'auto';
        container.style.overflowY = 'visible';
        container.style.WebkitOverflowScrolling = 'touch';
        container.style.touchAction = 'pan-x pan-y';
        container.style.scrollBehavior = 'smooth';
        
        // Garantir largura mínima da tabela
        const minWidth = this.calculateMinTableWidth(table);
        table.style.minWidth = minWidth + 'px';
        table.style.width = 'max-content';
        
        // Configurar células para não quebrar
        const cells = table.querySelectorAll('th, td');
        cells.forEach(cell => {
            cell.style.whiteSpace = 'nowrap';
            cell.style.minWidth = '120px';
            cell.style.padding = '12px 8px';
        });
    }

    calculateMinTableWidth(table) {
        const headers = table.querySelectorAll('thead th');
        let totalWidth = 0;
        
        headers.forEach(header => {
            // Estimar largura baseada no conteúdo
            const text = header.textContent || header.innerText;
            let width = Math.max(120, text.length * 8 + 40); // Base + padding
            
            // Ajustes específicos por tipo de coluna
            if (text.toLowerCase().includes('ações')) {
                width = Math.max(width, 160);
            } else if (text.toLowerCase().includes('status')) {
                width = Math.max(width, 130);
            } else if (text.toLowerCase().includes('data')) {
                width = Math.max(width, 110);
            }
            
            totalWidth += width;
        });
        
        // Adicionar margem de segurança
        return Math.max(totalWidth, window.innerWidth + 200);
    }

    setupTouchEvents(container) {
        let touchState = {
            isScrolling: false,
            startX: 0,
            scrollLeft: 0,
            lastMoveTime: 0,
            velocity: 0
        };

        // Touch Start - Inicializar scroll
        const handleTouchStart = (e) => {
            // Permitir apenas toque único
            if (e.touches.length !== 1) return;
            
            const touch = e.touches[0];
            touchState.isScrolling = true;
            touchState.startX = touch.clientX;
            touchState.scrollLeft = container.scrollLeft;
            touchState.lastMoveTime = Date.now();
            touchState.velocity = 0;
            
            // Parar animações de scroll suave durante o toque
            container.style.scrollBehavior = 'auto';
            
            // Adicionar classe para feedback visual
            container.classList.add('touch-scrolling');
        };

        // Touch Move - Processar scroll
        const handleTouchMove = (e) => {
            if (!touchState.isScrolling || e.touches.length !== 1) return;
            
            // Prevenir comportamento padrão apenas se estiver scrollando horizontalmente
            const touch = e.touches[0];
            const deltaX = touch.clientX - touchState.startX;
            const deltaY = Math.abs(touch.clientY - (e.touches[0].clientY || 0));
            
            // Se movimento horizontal é maior que vertical, prevenir scroll da página
            if (Math.abs(deltaX) > deltaY) {
                e.preventDefault();
            }
            
            // Calcular velocidade para momentum
            const currentTime = Date.now();
            const timeDelta = currentTime - touchState.lastMoveTime;
            if (timeDelta > 0) {
                touchState.velocity = deltaX / timeDelta;
            }
            touchState.lastMoveTime = currentTime;
            
            // Aplicar scroll com precisão
            const newScrollLeft = touchState.scrollLeft - deltaX;
            container.scrollLeft = Math.max(0, Math.min(
                container.scrollWidth - container.clientWidth, 
                newScrollLeft
            ));
        };

        // Touch End - Finalizar scroll com momentum
        const handleTouchEnd = (e) => {
            if (!touchState.isScrolling) return;
            
            touchState.isScrolling = false;
            container.classList.remove('touch-scrolling');
            
            // Restaurar scroll behavior
            setTimeout(() => {
                container.style.scrollBehavior = 'smooth';
            }, 100);
            
            // Aplicar momentum se a velocidade for significativa
            if (Math.abs(touchState.velocity) > 0.5) {
                this.applyMomentum(container, touchState.velocity);
            }
            
            // Reset do estado
            touchState = {
                isScrolling: false,
                startX: 0,
                scrollLeft: 0,
                lastMoveTime: 0,
                velocity: 0
            };
        };

        // Mouse events para desktop (mantém compatibilidade)
        const handleMouseDown = (e) => {
            if (window.innerWidth > 768) { // Apenas desktop
                touchState.isScrolling = true;
                touchState.startX = e.clientX;
                touchState.scrollLeft = container.scrollLeft;
                container.style.cursor = 'grabbing';
                container.style.scrollBehavior = 'auto';
            }
        };

        const handleMouseMove = (e) => {
            if (!touchState.isScrolling || window.innerWidth <= 768) return;
            
            e.preventDefault();
            const deltaX = e.clientX - touchState.startX;
            container.scrollLeft = touchState.scrollLeft - deltaX;
        };

        const handleMouseUp = () => {
            if (window.innerWidth > 768) {
                touchState.isScrolling = false;
                container.style.cursor = 'grab';
                container.style.scrollBehavior = 'smooth';
            }
        };

        // Adicionar listeners
        container.addEventListener('touchstart', handleTouchStart, { passive: true });
        container.addEventListener('touchmove', handleTouchMove, { passive: false });
        container.addEventListener('touchend', handleTouchEnd, { passive: true });
        
        container.addEventListener('mousedown', handleMouseDown);
        container.addEventListener('mousemove', handleMouseMove);
        container.addEventListener('mouseup', handleMouseUp);
        container.addEventListener('mouseleave', handleMouseUp);

        // Scroll listener para indicadores
        container.addEventListener('scroll', () => {
            this.updateScrollIndicators(container);
        }, { passive: true });
    }

    applyMomentum(container, velocity) {
        // Aplicar momentum scroll baseado na velocidade
        const momentumDistance = velocity * 100; // Ajustar multiplicador conforme necessário
        const currentScrollLeft = container.scrollLeft;
        const targetScrollLeft = Math.max(0, Math.min(
            container.scrollWidth - container.clientWidth,
            currentScrollLeft - momentumDistance
        ));

        // Usar animação suave para o momentum
        container.style.scrollBehavior = 'smooth';
        container.scrollLeft = targetScrollLeft;
    }

    addScrollIndicators(container) {
        // Criar indicador de scroll lateral
        const indicator = document.createElement('div');
        indicator.className = 'scroll-indicator';
        indicator.innerHTML = `
            <div class="scroll-hint">
                <i class="fas fa-arrow-right"></i>
                <span>Arraste para ver mais</span>
            </div>
        `;
        
        container.style.position = 'relative';
        container.appendChild(indicator);

        // Esconder indicador após primeiro scroll
        const hideIndicator = () => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.remove();
                }
            }, 300);
            container.removeEventListener('scroll', hideIndicator);
        };

        container.addEventListener('scroll', hideIndicator, { once: true });

        // Auto esconder após 5 segundos
        setTimeout(() => {
            if (indicator.parentNode) {
                hideIndicator();
            }
        }, 5000);
    }

    updateScrollIndicators(container) {
        const scrollLeft = container.scrollLeft;
        const maxScroll = container.scrollWidth - container.clientWidth;
        const scrollPercentage = maxScroll > 0 ? (scrollLeft / maxScroll) * 100 : 0;

        // Atualizar shadow indicators se existirem
        if (scrollPercentage > 5) {
            container.classList.add('scrolled-left');
        } else {
            container.classList.remove('scrolled-left');
        }

        if (scrollPercentage < 95) {
            container.classList.add('scrolled-right');
        } else {
            container.classList.remove('scrolled-right');
        }
    }

    // Método para adicionar novas tabelas dinamicamente
    addTable(container) {
        this.enhanceTableScroll(container);
    }

    // Método para atualizar todas as tabelas
    refresh() {
        this.tables = [];
        this.setupScrollSystem();
    }
}

// CSS inline para indicadores
const scrollIndicatorStyles = `
<style>
.scroll-indicator {
    position: absolute;
    top: 50%;
    right: 20px;
    transform: translateY(-50%);
    background: rgba(32, 193, 232, 0.9);
    color: white;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    pointer-events: none;
    z-index: 10;
    transition: opacity 0.3s ease;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.scroll-hint {
    display: flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
}

.scroll-hint i {
    animation: scrollPulse 2s infinite;
}

@keyframes scrollPulse {
    0%, 100% { transform: translateX(0); }
    50% { transform: translateX(5px); }
}

.touch-scrolling {
    scroll-behavior: auto !important;
}

.table-responsive {
    position: relative;
}

.table-responsive::before,
.table-responsive::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 20px;
    pointer-events: none;
    z-index: 5;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.table-responsive::before {
    left: 0;
    background: linear-gradient(to right, rgba(255,255,255,0.8), transparent);
}

.table-responsive::after {
    right: 0;
    background: linear-gradient(to left, rgba(255,255,255,0.8), transparent);
}

.table-responsive.scrolled-left::before {
    opacity: 1;
}

.table-responsive.scrolled-right::after {
    opacity: 1;
}

/* Scrollbar customizada */
.table-responsive::-webkit-scrollbar {
    height: 8px;
}

.table-responsive::-webkit-scrollbar-track {
    background: #f1f3f4;
    border-radius: 4px;
}

.table-responsive::-webkit-scrollbar-thumb {
    background: #20c1e8;
    border-radius: 4px;
}

.table-responsive::-webkit-scrollbar-thumb:hover {
    background: #17a2b8;
}

@media (max-width: 768px) {
    .scroll-indicator {
        right: 10px;
        padding: 6px 10px;
        font-size: 12px;
    }
    
    .table-responsive::-webkit-scrollbar {
        height: 6px;
    }
}
</style>
`;

// Inserir CSS
document.head.insertAdjacentHTML('beforeend', scrollIndicatorStyles);

// Inicializar sistema globalmente
window.PerfectHorizontalScroll = new PerfectHorizontalScroll();

// Expor métodos globais
window.addPerfectScroll = (container) => window.PerfectHorizontalScroll.addTable(container);
window.refreshPerfectScroll = () => window.PerfectHorizontalScroll.refresh();