/**
 * Sistema de Tabelas Mobile-First
 * Gerencia rolagem horizontal, modo cards e funcionalidades touch
 */

class MobileTableManager {
    constructor() {
        this.tables = [];
        this.isTouch = 'ontouchstart' in window;
        this.init();
    }

    init() {
        // Aguardar o DOM carregar
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupTables());
        } else {
            this.setupTables();
        }
    }

    setupTables() {
        // Encontrar todas as tabelas responsivas
        const containers = document.querySelectorAll('.table-responsive');
        
        containers.forEach(container => {
            this.enhanceTable(container);
        });

        // Adicionar listener para redimensionamento
        window.addEventListener('resize', () => this.handleResize());
        
        // Setup inicial baseado no tamanho da tela
        this.handleResize();
    }

    enhanceTable(container) {
        const table = container.querySelector('table');
        if (!table) return;

        // Adicionar classes do sistema mobile
        container.classList.add('mobile-table-container');
        table.classList.add('mobile-table');

        // Configurar scroll horizontal
        this.setupHorizontalScroll(container);
        
        // Criar versão em cards para mobile
        this.createCardVersion(container, table);
        
        // Adicionar toggle se necessário
        this.addViewToggle(container);

        this.tables.push({
            container,
            table,
            hasScrolled: false
        });
    }

    setupHorizontalScroll(container) {
        let isScrolling = false;
        let startX = 0;
        let scrollLeft = 0;

        // Touch events para scroll horizontal
        container.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                isScrolling = true;
                startX = e.touches[0].pageX - container.offsetLeft;
                scrollLeft = container.scrollLeft;
            }
        }, { passive: true });

        container.addEventListener('touchmove', (e) => {
            if (!isScrolling || e.touches.length !== 1) return;
            
            e.preventDefault();
            const x = e.touches[0].pageX - container.offsetLeft;
            const walk = (x - startX) * 2; // Multiplicador para velocidade
            container.scrollLeft = scrollLeft - walk;
        }, { passive: false });

        container.addEventListener('touchend', () => {
            isScrolling = false;
        }, { passive: true });

        // Marcar como scrolled após primeiro scroll
        container.addEventListener('scroll', () => {
            if (container.scrollLeft > 0) {
                container.classList.add('scrolled');
                // Armazenar estado
                const tableData = this.tables.find(t => t.container === container);
                if (tableData) {
                    tableData.hasScrolled = true;
                }
            }
        }, { passive: true });

        // Mouse drag em desktop
        if (!this.isTouch) {
            container.addEventListener('mousedown', (e) => {
                isScrolling = true;
                container.style.cursor = 'grabbing';
                startX = e.pageX - container.offsetLeft;
                scrollLeft = container.scrollLeft;
            });

            container.addEventListener('mouseleave', () => {
                isScrolling = false;
                container.style.cursor = 'grab';
            });

            container.addEventListener('mouseup', () => {
                isScrolling = false;
                container.style.cursor = 'grab';
            });

            container.addEventListener('mousemove', (e) => {
                if (!isScrolling) return;
                e.preventDefault();
                const x = e.pageX - container.offsetLeft;
                const walk = (x - startX) * 2;
                container.scrollLeft = scrollLeft - walk;
            });
        }
    }

    createCardVersion(container, table) {
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const rows = Array.from(table.querySelectorAll('tbody tr'));
        
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'table-cards';
        cardsContainer.style.display = 'none';

        rows.forEach((row, index) => {
            const cells = Array.from(row.querySelectorAll('td'));
            const card = this.createCard(headers, cells, index);
            cardsContainer.appendChild(card);
        });

        container.appendChild(cardsContainer);
    }

    createCard(headers, cells, index) {
        const card = document.createElement('div');
        card.className = 'table-card';

        // Header do card (primeira coluna geralmente é o identificador)
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        
        const title = document.createElement('h4');
        title.className = 'card-title';
        title.textContent = cells[0]?.textContent?.trim() || `Item ${index + 1}`;
        
        cardHeader.appendChild(title);
        card.appendChild(cardHeader);

        // Campos do card (pular primeira coluna que já é o título)
        headers.slice(1).forEach((header, i) => {
            const cell = cells[i + 1];
            if (!cell) return;

            const field = document.createElement('div');
            field.className = 'card-field';

            const label = document.createElement('span');
            label.className = 'field-label';
            label.textContent = header;

            const value = document.createElement('span');
            value.className = 'field-value';
            
            // Preservar HTML especial como badges e botões
            if (cell.querySelector('.status-badge, .btn, .action-btn')) {
                value.innerHTML = cell.innerHTML;
            } else {
                value.textContent = cell.textContent.trim();
            }

            field.appendChild(label);
            field.appendChild(value);
            card.appendChild(field);
        });

        // Ações do card (última coluna se contém botões)
        const lastCell = cells[cells.length - 1];
        if (lastCell && lastCell.querySelector('.btn, .action-btn, .action-buttons')) {
            const actions = document.createElement('div');
            actions.className = 'card-actions';
            actions.innerHTML = lastCell.innerHTML;
            card.appendChild(actions);
        }

        return card;
    }

    addViewToggle(container) {
        // Criar toggle apenas para telas pequenas
        const toggle = document.createElement('div');
        toggle.className = 'table-view-toggle';
        toggle.innerHTML = `
            <span style="font-size: var(--text-xs); color: #6c757d;">Visualização:</span>
            <button type="button" class="toggle-btn active" data-view="table">
                <i class="fas fa-table"></i> Tabela
            </button>
            <button type="button" class="toggle-btn" data-view="cards">
                <i class="fas fa-th-large"></i> Cards
            </button>
        `;

        container.parentNode.insertBefore(toggle, container);

        // Event listeners
        const buttons = toggle.querySelectorAll('.toggle-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.getAttribute('data-view');
                this.switchView(container, view);
                
                // Atualizar estado dos botões
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    }

    switchView(container, view) {
        const table = container.querySelector('.mobile-table');
        const cards = container.querySelector('.table-cards');

        if (view === 'cards') {
            table.style.display = 'none';
            cards.style.display = 'block';
            container.classList.add('card-mode');
        } else {
            table.style.display = 'table';
            cards.style.display = 'none';
            container.classList.remove('card-mode');
        }
    }

    handleResize() {
        const isNarrow = window.innerWidth <= 480;
        
        this.tables.forEach(({ container }) => {
            const toggle = container.parentNode.querySelector('.table-view-toggle');
            
            if (isNarrow) {
                // Mostrar toggle em telas estreitas
                if (toggle) {
                    toggle.classList.remove('hidden');
                }
                
                // Auto switch para cards se ainda não teve interação
                const activeToggle = toggle?.querySelector('.toggle-btn.active');
                if (!activeToggle || activeToggle.getAttribute('data-view') === 'table') {
                    this.switchView(container, 'cards');
                    if (toggle) {
                        toggle.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
                        toggle.querySelector('[data-view="cards"]').classList.add('active');
                    }
                }
            } else {
                // Esconder toggle e forçar modo tabela em telas maiores
                if (toggle) {
                    toggle.classList.add('hidden');
                }
                this.switchView(container, 'table');
            }
        });
    }

    // Método público para atualizar tabelas dinamicamente
    refresh() {
        this.tables = [];
        this.setupTables();
    }

    // Método para adicionar nova tabela dinamicamente
    addTable(container) {
        this.enhanceTable(container);
    }
}

// Inicializar sistema globalmente
window.MobileTableManager = new MobileTableManager();

// Expor métodos globais para uso em outras páginas
window.refreshMobileTables = () => window.MobileTableManager.refresh();
window.addMobileTable = (container) => window.MobileTableManager.addTable(container);