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
        // IMPORTANTE: Todos os campos do formulário devem estar aqui para disparar autosave
        this.allowedFields = [
            'titulo', 'observacoes', 'latitude', 'longitude',
            'endereco', 'checklist_data', 'last_edited_at',
            'descricao', 'categoria', 'local', 'observacoes_finais',
            'conteudo', 'lembrete_proxima_visita', 'numero', 'data_relatorio',
            'projeto_id', 'status'
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
            if (this.allowedFields.includes(element.name) || element.id && this.allowedFields.includes(element.id)) {
                element.addEventListener('input', (e) => this.handleInputChange(e));
                element.addEventListener('change', (e) => this.handleInputChange(e));
            }
        });

        // Listener para mudanças no checklist (se existir)
        const checklistContainer = document.querySelector('[data-checklist]');
        if (checklistContainer) {
            checklistContainer.addEventListener('change', () => this.handleChecklistChange());
        }

        // Listener para mudanças em acompanhantes (múltiplos formatos)
        const acompanhantesFields = document.querySelectorAll('[name^="acompanhante_"]');
        acompanhantesFields.forEach(field => {
            field.addEventListener('input', (e) => this.handleInputChange(e));
            field.addEventListener('change', (e) => this.handleInputChange(e));
        });

        // Listener para container de acompanhantes
        const acompanhantesContainer = document.querySelector('[data-acompanhantes-list]');
        if (acompanhantesContainer) {
            acompanhantesContainer.addEventListener('input', () => this.debouncedSave());
            acompanhantesContainer.addEventListener('change', () => this.debouncedSave());
        }

        // Listener para upload de imagens
        const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
        imageInputs.forEach(input => {
            input.addEventListener('change', (e) => this.handleImageUpload(e));
        });

        // Listeners específicos para campos que podem não ter name attribute
        const specificFields = ['numero', 'data_relatorio', 'projeto_id', 'status'];
        specificFields.forEach(fieldId => {
            const element = document.getElementById(fieldId);
            if (element) {
                element.addEventListener('input', (e) => this.handleInputChange(e));
                element.addEventListener('change', (e) => this.handleInputChange(e));
            }
        });

        // Listener para mudanças em metadados de imagens
        const imagemMetadataFields = document.querySelectorAll('[data-imagem-id] [data-field]');
        imagemMetadataFields.forEach(field => {
            field.addEventListener('input', () => this.debouncedSave());
            field.addEventListener('change', () => this.debouncedSave());
        });
    }

    handleImageUpload(event) {
        console.log('📸 AutoSave: Upload de imagem detectado');
        // As imagens serão enviadas separadamente após upload
        // O sistema deve apenas registrar que houve mudança
        this.debouncedSave();
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

        // Mostrar indicador de que está aguardando para salvar
        this.showStatus('Salvando...', 'info');
        console.log('🔄 AutoSave: Alterações detectadas, salvando em', this.debounceTime/1000, 's');
    }

    collectFormData() {
        const data = {};

        // Lista COMPLETA de campos do formulário conforme especificação
        const fields = [
            'titulo', 'descricao', 'categoria', 'local',
            'observacoes_finais', 'conteudo', 'status',
            'endereco', 'observacoes', 'numero', 'data_relatorio'
        ];

        fields.forEach(field => {
            const element = document.getElementById(field) || document.querySelector(`[name="${field}"]`);
            if (element) {
                // Enviar SEMPRE o valor, mesmo se vazio (permite limpeza de campos)
                data[field] = element.value !== undefined ? element.value : null;
                console.log(`📝 AutoSave: Campo '${field}' coletado: '${String(data[field]).substring(0, 50)}'`);
            }
        });

        // Projeto vinculado
        const projetoElement = document.getElementById('projeto_id') || document.querySelector('[name="projeto_id"]');
        if (projetoElement && projetoElement.value) {
            data.projeto_id = parseInt(projetoElement.value);
        }

        // Lembrete próxima visita
        const lembreteElement = document.getElementById('lembrete_proxima_visita');
        if (lembreteElement) {
            data.lembrete_proxima_visita = lembreteElement.value || null;
        }

        // Acompanhantes (enviar como array, não como string JSON)
        const acompanhantesData = this.getAcompanhantesData();
        if (acompanhantesData) {
            data.acompanhantes = acompanhantesData;
        }

        // Coordenadas GPS
        const latElement = document.getElementById('latitude') || document.querySelector('[name="latitude"]');
        if (latElement && latElement.value) {
            data.latitude = parseFloat(latElement.value);
        }

        const lonElement = document.getElementById('longitude') || document.querySelector('[name="longitude"]');
        if (lonElement && lonElement.value) {
            data.longitude = parseFloat(lonElement.value);
        }

        // Checklist data (se existir) - CORRIGIDO: usar collectChecklistData()
        // Enviar como array/objeto, não como string JSON (backend faz a conversão)
        const checklistData = this.collectChecklistData();
        if (checklistData) {
            // collectChecklistData() retorna JSON string, precisamos parsear de volta
            try {
                data.checklist_data = JSON.parse(checklistData);
            } catch (e) {
                data.checklist_data = checklistData;
            }
        }

        // Imagens (metadados e exclusões)
        const imagensData = this.getImagenesData();
        if (imagensData) {
            data.fotos = imagensData;
        }

        // Timestamp de última edição
        data.last_edited_at = new Date().toISOString();

        console.log(`📦 AutoSave: ${Object.keys(data).length} campos coletados para envio`);

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

    getAcompanhantesData() {
        const acompanhantes = [];
        
        // Buscar campos de acompanhantes (múltiplas abordagens)
        // 1. Campos individuais com pattern acompanhante_nome_X, acompanhante_funcao_X
        let index = 0;
        while (true) {
            const nomeElement = document.getElementById(`acompanhante_nome_${index}`) || 
                               document.querySelector(`[name="acompanhante_nome_${index}"]`);
            const funcaoElement = document.getElementById(`acompanhante_funcao_${index}`) || 
                                 document.querySelector(`[name="acompanhante_funcao_${index}"]`);
            
            if (!nomeElement && index > 0) break; // Parar quando não houver mais campos
            
            if (nomeElement || funcaoElement) {
                const nome = nomeElement ? nomeElement.value : '';
                const funcao = funcaoElement ? funcaoElement.value : '';
                
                // Só adicionar se pelo menos um campo estiver preenchido
                if (nome || funcao) {
                    acompanhantes.push({
                        nome: nome,
                        funcao: funcao
                    });
                }
            }
            index++;
        }

        // 2. Lista de acompanhantes em container específico
        const acompanhantesContainer = document.querySelector('[data-acompanhantes-list]');
        if (acompanhantesContainer && acompanhantes.length === 0) {
            const items = acompanhantesContainer.querySelectorAll('[data-acompanhante-item]');
            items.forEach(item => {
                const nome = item.querySelector('[data-field="nome"]')?.value || 
                            item.querySelector('.acompanhante-nome')?.value || '';
                const funcao = item.querySelector('[data-field="funcao"]')?.value || 
                              item.querySelector('.acompanhante-funcao')?.value || '';
                
                if (nome || funcao) {
                    acompanhantes.push({ nome, funcao });
                }
            });
        }

        return acompanhantes.length > 0 ? acompanhantes : null;
    }

    getImagenesData() {
        const imagens = [];
        
        // Buscar imagens já carregadas no relatório
        const imagemElements = document.querySelectorAll('[data-imagem-id]');
        imagemElements.forEach(imgElement => {
            const id = imgElement.dataset.imagemId;
            const legenda = imgElement.querySelector('[data-field="legenda"]')?.value || 
                           imgElement.dataset.legenda || '';
            const categoria = imgElement.querySelector('[data-field="categoria"]')?.value || 
                             imgElement.dataset.categoria || '';
            const local = imgElement.querySelector('[data-field="local"]')?.value || 
                         imgElement.dataset.local || '';
            const titulo = imgElement.querySelector('[data-field="titulo"]')?.value || 
                          imgElement.dataset.titulo || '';
            const ordem = imgElement.dataset.ordem || imagens.length;
            
            imagens.push({
                id: parseInt(id),
                legenda: legenda,
                categoria: categoria,
                local: local,
                titulo: titulo,
                ordem: parseInt(ordem)
            });
        });

        // Buscar imagens marcadas para exclusão
        const imagensParaExcluir = document.querySelectorAll('[data-imagem-deletar="true"]');
        imagensParaExcluir.forEach(imgElement => {
            const id = imgElement.dataset.imagemId;
            if (id) {
                imagens.push({
                    id: parseInt(id),
                    deletar: true
                });
            }
        });

        return imagens.length > 0 ? imagens : null;
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
        const url = `/api/relatorios/autosave`;

        const headers = {
            'Content-Type': 'application/json',
        };

        // Adicionar token CSRF se disponível
        if (this.csrfToken) {
            headers['X-CSRFToken'] = this.csrfToken;
        }

        // Adicionar ID do relatório ao payload
        const payload = {
            ...data,
            id: this.reportId
        };

        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
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

            // Mostrar feedback de sucesso
            this.showStatus('✓ Alterações salvas automaticamente', 'success');
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

        console.error(`❌ AutoSave: Erro (tentativa ${this.retryCount}/${this.maxRetries})`, error);

        // Salvar localmente como backup
        this.saveToLocalStorage(data);

        if (this.retryCount < this.maxRetries) {
            // Implementar retry com backoff exponencial
            const backoffDelay = this.retryDelay * Math.pow(2, this.retryCount - 1);

            console.log(`🔄 AutoSave: Nova tentativa em ${Math.ceil(backoffDelay/1000)}s`);
            this.showStatus(`Tentando salvar novamente (${this.retryCount}/${this.maxRetries})...`, 'warning');

            setTimeout(() => {
                this.performSave();
            }, backoffDelay);
        } else {
            console.error('❌ AutoSave: Máximo de tentativas atingido - dados salvos localmente');
            this.showStatus('Erro ao salvar. Dados salvos localmente.', 'error');
        }
    }

    clearLocalStorage() {
        const storageKey = `autosave_report_${this.reportId}`;
        localStorage.removeItem(storageKey);
    }

    showStatus(message, type = 'info') {
        // Exibir feedback visual conforme especificação
        const statusElement = document.getElementById('autosave-status');
        if (!statusElement) return;

        // Cores conforme tipo
        const colors = {
            info: '#2196F3',
            success: '#4CAF50',
            error: '#f44336',
            warning: '#ff9800'
        };

        statusElement.style.backgroundColor = colors[type] || colors.info;
        statusElement.style.color = 'white';
        statusElement.textContent = message;
        statusElement.style.display = 'block';

        // Log também no console
        console.log(`AutoSave [${type}]: ${message}`);

        // Auto-ocultar após 3 segundos (exceto erros)
        if (type !== 'error') {
            setTimeout(() => {
                this.hideStatus();
            }, 3000);
        }
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