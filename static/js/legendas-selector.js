
/**
 * Sistema de Seleção de Legendas Pré-definidas
 * Para uso em formulários de relatórios
 */

class LegendasSelector {
    constructor(options = {}) {
        this.apiUrl = options.apiUrl || '/api/legendas';
        this.cache = new Map();
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    init() {
        console.log('🏷️ LegendasSelector: Inicializando sistema de legendas');
        this.loadLegendas();
        this.setupEventListeners();
    }
    
    async loadLegendas(categoria = 'all', forceRefresh = false) {
        const cacheKey = `legendas_${categoria}`;
        
        // Verificar cache se não for refresh forçado
        if (!forceRefresh && this.cache.has(cacheKey)) {
            console.log(`📋 Cache HIT para categoria: ${categoria}`);
            return this.cache.get(cacheKey);
        }
        
        try {
            const url = `${this.apiUrl}?categoria=${categoria}&_t=${Date.now()}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.legendas) {
                this.cache.set(cacheKey, data.legendas);
                this.retryCount = 0;
                
                console.log(`✅ Legendas carregadas: ${data.total} itens (categoria: ${categoria})`);
                return data.legendas;
            } else {
                throw new Error(data.error || 'Dados inválidos');
            }
            
        } catch (error) {
            console.error(`❌ Erro ao carregar legendas:`, error);
            
            // Sistema de retry
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                console.log(`🔄 Retry ${this.retryCount}/${this.maxRetries} em 2s...`);
                
                await new Promise(resolve => setTimeout(resolve, 2000));
                return this.loadLegendas(categoria, forceRefresh);
            }
            
            // Fallback para cache ou dados vazios
            if (this.cache.has(cacheKey)) {
                console.log('📋 Usando cache como fallback');
                return this.cache.get(cacheKey);
            }
            
            return [];
        }
    }
    
    async populateSelect(selectElement, categoria = 'all', placeholder = 'Selecione uma legenda...') {
        if (!selectElement) {
            console.warn('❌ Elemento select não encontrado');
            return;
        }
        
        // Mostrar loading
        selectElement.innerHTML = '<option value="">Carregando legendas...</option>';
        selectElement.disabled = true;
        
        try {
            const legendas = await this.loadLegendas(categoria);
            
            // Limpar select
            selectElement.innerHTML = '';
            
            // Adicionar placeholder
            const placeholderOption = document.createElement('option');
            placeholderOption.value = '';
            placeholderOption.textContent = placeholder;
            selectElement.appendChild(placeholderOption);
            
            // Agrupar por categoria
            const categorias = {};
            legendas.forEach(legenda => {
                if (!categorias[legenda.categoria]) {
                    categorias[legenda.categoria] = [];
                }
                categorias[legenda.categoria].push(legenda);
            });
            
            // Adicionar opções agrupadas
            Object.keys(categorias).sort().forEach(cat => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = `${cat} (${categorias[cat].length})`;
                
                categorias[cat].forEach(legenda => {
                    const option = document.createElement('option');
                    option.value = legenda.texto;
                    option.textContent = legenda.texto;
                    option.dataset.categoria = legenda.categoria;
                    option.dataset.id = legenda.id;
                    
                    optgroup.appendChild(option);
                });
                
                selectElement.appendChild(optgroup);
            });
            
            selectElement.disabled = false;
            console.log(`✅ Select populado com ${legendas.length} legendas`);
            
        } catch (error) {
            console.error('❌ Erro ao popular select:', error);
            selectElement.innerHTML = '<option value="">Erro ao carregar legendas</option>';
            selectElement.disabled = false;
        }
    }
    
    setupEventListeners() {
        // Auto-setup em elementos com classe específica
        document.addEventListener('DOMContentLoaded', () => {
            const selects = document.querySelectorAll('.legendas-select, select[data-legendas]');
            
            selects.forEach(select => {
                const categoria = select.dataset.categoria || 'all';
                const placeholder = select.dataset.placeholder || 'Selecione uma legenda...';
                
                this.populateSelect(select, categoria, placeholder);
            });
        });
        
        // Refresh quando a página voltar a ficar visível
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('🔄 Página visível novamente - refreshing legendas');
                this.clearCache();
            }
        });
    }
    
    clearCache() {
        this.cache.clear();
        console.log('🧹 Cache de legendas limpo');
    }
    
    // Método para integração com outros sistemas
    async search(termo, categoria = 'all') {
        const legendas = await this.loadLegendas(categoria);
        
        if (!termo || termo.trim() === '') {
            return legendas;
        }
        
        const termoLower = termo.toLowerCase();
        return legendas.filter(legenda => 
            legenda.texto.toLowerCase().includes(termoLower)
        );
    }
}

// Instância global
window.LegendasSelector = LegendasSelector;
window.legendasSelector = new LegendasSelector();

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LegendasSelector;
}
