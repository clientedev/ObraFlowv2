
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
                    'Pragma': 'no-cache',
                    'Accept': 'application/json'
                },
                timeout: 15000
            });
            
            if (!response.ok) {
                // Log detalhado do erro HTTP (APENAS NO CONSOLE)
                const responseText = await response.text();
                console.error(`❌ HTTP ${response.status}: ${responseText}`);
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && Array.isArray(data.legendas)) {
                this.cache.set(cacheKey, data.legendas);
                this.retryCount = 0;
                
                console.log(`✅ Legendas carregadas: ${data.total} itens (categoria: ${categoria}, fonte: ${data.fonte || 'N/A'})`);
                return data.legendas;
            } else {
                // Mesmo com erro, se tiver dados, usar
                if (Array.isArray(data.legendas) && data.legendas.length > 0) {
                    console.warn('⚠️ API com erro mas dados disponíveis');
                    this.cache.set(cacheKey, data.legendas);
                    return data.legendas;
                }
                throw new Error(data.error || 'Dados inválidos ou vazios');
            }
            
        } catch (error) {
            // APENAS LOGS NO CONSOLE - SEM ALERTAS VISUAIS
            console.error(`❌ Erro ao carregar legendas (tentativa ${this.retryCount + 1}/${this.maxRetries}):`, error);
            
            // Sistema de retry com backoff exponencial
            if (this.retryCount < this.maxRetries) {
                this.retryCount++;
                const delay = Math.pow(2, this.retryCount) * 1000; // 2s, 4s, 8s
                console.log(`🔄 Retry ${this.retryCount}/${this.maxRetries} em ${delay/1000}s...`);
                
                await new Promise(resolve => setTimeout(resolve, delay));
                return this.loadLegendas(categoria, forceRefresh);
            }
            
            // Fallback para cache
            if (this.cache.has(cacheKey)) {
                console.log('📋 Usando cache como fallback após falhas');
                return this.cache.get(cacheKey);
            }
            
            // Fallback final: dados estáticos básicos (SEM ALERTAS)
            console.warn('⚠️ Usando dados de fallback estáticos - legendas básicas');
            return [
                {id: 1, texto: 'Emboço bem-acabado', categoria: 'Acabamentos'},
                {id: 2, texto: 'Estrutura bem-acabada', categoria: 'Estrutural'},
                {id: 3, texto: 'Executado conforme projeto', categoria: 'Geral'}
            ];
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
            // APENAS LOG NO CONSOLE - SEM MENSAGEM DE ERRO VISÍVEL
            console.error('❌ Erro ao popular select:', error);
            
            // Manter select funcional com opção padrão
            selectElement.innerHTML = `<option value="">${placeholder}</option>`;
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
