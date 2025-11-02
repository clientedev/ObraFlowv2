/**
 * Sistema de Auto-Save para Relatórios
 * Implementa salvamento automático com debounce, tratamento de CSRF e feedback visual
 */

class ReportsAutoSave {
    constructor(options = {}) {
        // Configurações padrão
        this.reportId = options.reportId || null;
        this.csrfToken = options.csrfToken || null;
        this.debounceTime = options.debounceTime || 2500; // 2.5 segundos - otimizado
        this.retryDelay = options.retryDelay || 5000; // 5 segundos para retry
        this.maxRetries = options.maxRetries || 3;
        
        // Estado interno
        this.debounceTimer = null;
        this.isConnected = navigator.onLine;
        this.isSaving = false;
        this.retryCount = 0;
        this.lastSavedData = {};
        
        // Whitelist de campos para auto-save (deve coincidir com o backend)
        this.allowedFields = [
            'titulo', 'observacoes', 'latitude', 'longitude', 
            'endereco', 'checklist_data', 'last_edited_at',
            'descricao', 'categoria', 'local', 'observacoes_finais',
            'conteudo', 'lembrete_proxima_visita'
        ];
        
        this.init();
    }
    
    init() {
        if (!this.reportId) {
            console.warn('🚫 AutoSave: reportId não fornecido');
            return;
        }
        
        if (!this.csrfToken) {
            console.warn('🚫 AutoSave: csrfToken não fornecido');
        }
        
        // AutoSave iniciado silenciosamente
        
        // Configurar listeners de eventos
        this.setupEventListeners();
        this.setupNetworkListeners();
        this.setupStatusIndicator();
        
        // Carregar dados salvos localmente se houver
        this.loadFromLocalStorage();
    }
    
    setupEventListeners() {
        // Monitorar mudanças nos campos de formulário
        const formElements = document.querySelectorAll('input, textarea, select');
        
        formElements.forEach(element => {
            // Filtrar apenas campos permitidos
            if (this.allowedFields.includes(element.name)) {
                element.addEventListener('input', (e) => this.handleInputChange(e));
                element.addEventListener('change', (e) => this.handleInputChange(e));
            }
        });
        
        // Listener para mudanças no checklist (se existir)
        const checklistContainer = document.querySelector('[data-checklist]');
        if (checklistContainer) {
            checklistContainer.addEventListener('change', () => this.handleChecklistChange());
        }
    }
    
    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.isConnected = true;
            console.log('🔗 AutoSave: Conexão restaurada');
            this.retrySaveFromLocalStorage();
        });
        
        window.addEventListener('offline', () => {
            this.isConnected = false;
            console.log('📴 AutoSave: Conexão perdida - salvando localmente');
        });
    }
    
    setupStatusIndicator() {
        // Criar indicador de status se não existir
        if (!document.getElementById('autosave-status')) {
            const statusDiv = document.createElement('div');
            statusDiv.id = 'autosave-status';
            statusDiv.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1000;
                display: none;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(statusDiv);
        }
    }
    
    handleInputChange(event) {
        // Campo alterado - auto save ativado
        this.debouncedSave();
    }
    
    handleChecklistChange() {
        // Checklist alterado - auto save ativado
        this.debouncedSave();
    }
    
    debouncedSave() {
        // Cancelar timer anterior se existir
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Configurar novo timer
        this.debounceTimer = setTimeout(() => {
            this.performSave();
        }, this.debounceTime);
        
        // Mostrar indicador discreto apenas quando necessário
        console.log('🔄 AutoSave: Alterações detectadas, salvando em', this.debounceTime/1000, 's');
    }
    
    collectFormData() {
        const data = {};
        
        // Coletar dados dos campos permitidos - INCLUIR VALORES VAZIOS para permitir limpeza
        this.allowedFields.forEach(fieldName => {
            const element = document.querySelector(`[name="${fieldName}"]`);
            if (element) {
                // Enviar todos os valores, incluindo strings vazias, para permitir limpeza de campos
                data[fieldName] = element.value ? element.value.trim() : '';
            }
        });
        
        // Coletar dados do checklist se existir
        const checklistData = this.collectChecklistData();
        if (checklistData) {
            data.checklist_data = checklistData;
        }
        
        // Adicionar timestamp
        data.last_edited_at = new Date().toISOString();
        
        return data;
    }
    
    collectChecklistData() {
        const checklistItems = [];
        const checkboxes = document.querySelectorAll('input[type="checkbox"][data-checklist-item]');
        
        checkboxes.forEach(checkbox => {
            const item = {
                id: checkbox.dataset.checklistItem,
                completed: checkbox.checked,
                text: checkbox.dataset.checklistText || '',
                observations: ''
            };
            
            // Buscar observações relacionadas
            const obsField = document.querySelector(`[name="obs_${checkbox.name}"]`);
            if (obsField) {
                item.observations = obsField.value;
            }
            
            checklistItems.push(item);
        });
        
        return checklistItems.length > 0 ? JSON.stringify(checklistItems) : null;
    }
    
    async performSave() {
        if (this.isSaving) {
            console.log('⏸️ AutoSave: Já em progresso, aguardando...');
            return;
        }
        
        this.isSaving = true;
        
        const data = this.collectFormData();
        
        // Verificar se há mudanças
        if (JSON.stringify(data) === JSON.stringify(this.lastSavedData)) {
            this.isSaving = false;
            return;
        }
        
        try {
            if (this.isConnected) {
                await this.saveToServer(data);
            } else {
                this.saveToLocalStorage(data);
                console.log('💾 AutoSave: Salvo localmente (offline)');
            }
        } catch (error) {
            this.handleSaveError(data, error);
        } finally {
            this.isSaving = false;
        }
    }
    
    async saveToServer(data) {
        const url = `/reports/autosave/${this.reportId}`;
        
        const headers = {
            'Content-Type': 'application/json',
        };
        
        // Adicionar token CSRF se disponível
        if (this.csrfToken) {
            headers['X-CSRFToken'] = this.csrfToken;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
            
            // APENAS LOG - SEM MENSAGENS NA TELA
            console.error(`❌ AutoSave: Erro HTTP ${response.status}:`, errorData);
            
            // Não mostrar mensagens de erro na tela
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            this.lastSavedData = { ...data };
            this.retryCount = 0;
            this.clearLocalStorage();
            
            console.log('✅ AutoSave: Dados salvos com sucesso');
            
            // NÃO MOSTRAR STATUS VISUAL - apenas log
            this.hideStatus();
        } else {
            console.error('❌ AutoSave: Falha', result.error);
            throw new Error(result.error || 'Falha no auto-save');
        }
    }
    
    saveToLocalStorage(data) {
        try {
            const storageKey = `autosave_report_${this.reportId}`;
            const storageData = {
                data: data,
                timestamp: Date.now(),
                retryCount: this.retryCount
            };
            
            localStorage.setItem(storageKey, JSON.stringify(storageData));
            console.log('💾 AutoSave: Salvo no localStorage');
        } catch (error) {
            console.error('❌ AutoSave: Erro ao salvar no localStorage', error);
        }
    }
    
    loadFromLocalStorage() {
        try {
            const storageKey = `autosave_report_${this.reportId}`;
            const stored = localStorage.getItem(storageKey);
            
            if (stored) {
                const storageData = JSON.parse(stored);
                console.log('📂 AutoSave: Dados encontrados no localStorage');
                
                // Se há dados salvos localmente e estamos online, tentar enviar
                if (this.isConnected && storageData.data) {
                    this.retrySaveFromLocalStorage();
                }
            }
        } catch (error) {
            console.error('❌ AutoSave: Erro ao carregar do localStorage', error);
        }
    }
    
    async retrySaveFromLocalStorage() {
        const storageKey = `autosave_report_${this.reportId}`;
        const stored = localStorage.getItem(storageKey);
        
        if (!stored) return;
        
        try {
            const storageData = JSON.parse(stored);
            this.retryCount = storageData.retryCount || 0;
            
            console.log(`🔄 AutoSave: Tentando reenviar dados salvos localmente (tentativa ${this.retryCount + 1})`);
            await this.saveToServer(storageData.data);
        } catch (error) {
            console.error('❌ AutoSave: Falha ao reenviar dados locais', error);
            this.handleSaveError(JSON.parse(stored).data, error);
        }
    }
    
    handleSaveError(data, error) {
        this.retryCount++;
        
        // APENAS LOG - SEM MENSAGENS NA TELA
        console.error(`❌ AutoSave: Erro (tentativa ${this.retryCount}/${this.maxRetries})`, error);
        
        // Salvar localmente como backup
        this.saveToLocalStorage(data);
        
        if (this.retryCount < this.maxRetries) {
            // Implementar retry com backoff exponencial
            const backoffDelay = this.retryDelay * Math.pow(2, this.retryCount - 1);
            
            console.log(`🔄 AutoSave: Nova tentativa em ${Math.ceil(backoffDelay/1000)}s`);
            
            setTimeout(() => {
                this.performSave();
            }, backoffDelay);
        } else {
            console.error('❌ AutoSave: Máximo de tentativas atingido - dados salvos localmente');
        }
    }
    
    clearLocalStorage() {
        const storageKey = `autosave_report_${this.reportId}`;
        localStorage.removeItem(storageKey);
    }
    
    showStatus(message, type = 'info') {
        // MENSAGENS DE STATUS DESABILITADAS - APENAS LOGS
        // Não mostrar nada na tela, apenas logar no console
        console.log(`AutoSave [${type}]: ${message}`);
        return;
    }
    
    hideStatus() {
        const statusElement = document.getElementById('autosave-status');
        if (statusElement) {
            statusElement.style.display = 'none';
        }
    }
    
    // Método público para salvar manualmente
    forceSave() {
        console.log('🚀 AutoSave: Salvamento forçado');
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.performSave();
    }
    
    // Método público para limpar dados locais
    clearCache() {
        this.clearLocalStorage();
        console.log('🗑️ AutoSave: Cache local limpo');
    }
}

// Função de inicialização global
window.initAutoSave = function(reportId, csrfToken) {
    // Verificar se já foi inicializado
    if (window.autoSaveInstance) {
        console.warn('⚠️ AutoSave já foi inicializado');
        return window.autoSaveInstance;
    }
    
    window.autoSaveInstance = new ReportsAutoSave({
        reportId: reportId,
        csrfToken: csrfToken
    });
    
    return window.autoSaveInstance;
};

// Auto-inicialização se os dados estiverem disponíveis
document.addEventListener('DOMContentLoaded', function() {
    // Tentar obter dados do DOM
    const reportIdElement = document.querySelector('[data-report-id]');
    const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
    
    if (reportIdElement && csrfTokenElement) {
        const reportId = reportIdElement.dataset.reportId;
        const csrfToken = csrfTokenElement.getAttribute('content');
        
        if (reportId && csrfToken) {
            window.initAutoSave(reportId, csrfToken);
        }
    }
});

console.log('📱 AutoSave: Script carregado');