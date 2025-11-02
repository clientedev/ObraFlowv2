/**
 * AutoSave Completo e Silencioso (Logs Apenas no Console)
 * Sistema de salvamento automático do relatório de obras
 * Sem feedback visual - apenas logs no console
 */

class ReportsAutoSave {
    constructor(options = {}) {
        this.reportId = options.reportId || window.currentReportId || null;
        this.csrfToken = options.csrfToken || null;
        this.debounceTime = 2000; // 2 segundos conforme especificação
        this.isSaving = false;
        this.debounceTimer = null;
        this.isConnected = navigator.onLine;

        console.log('🕒 AutoSave: Iniciando sistema de autosave silencioso');
        
        if (!this.reportId) {
            console.log('📝 AutoSave: Sem reportId - será criado no primeiro salvamento');
        }

        this.init();
    }

    init() {
        console.log(`✅ AutoSave: Ativado para relatório ID ${this.reportId}`);
        this.startAutoSave();
        this.setupNetworkListeners();
    }

    startAutoSave() {
        const saveHandler = () => {
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => this.performSave(), this.debounceTime);
        };

        // Monitorar TODOS os campos do formulário
        document.querySelectorAll('input, textarea, select').forEach(el => {
            el.addEventListener('input', saveHandler);
            el.addEventListener('change', saveHandler);
        });

        console.log('🕒 AutoSave ativado para relatório atual.');
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

    collectFormData() {
        try {
            const data = {
                titulo: document.querySelector('#titulo_relatorio')?.value?.trim() || 
                        document.querySelector('#titulo')?.value?.trim() || "",
                numero: document.querySelector('#numero_relatorio')?.value?.trim() || 
                        document.querySelector('#numero')?.value?.trim() || "",
                data_relatorio: document.querySelector('#data_relatorio')?.value || null,
                observacoes_finais: document.querySelector('#observacoes')?.value?.trim() || "",
                lembrete_proxima_visita: document.querySelector('#lembrete')?.value?.trim() || null,
                conteudo: this.collectRichTextContent() || "",
                checklist_data: this.getChecklistData(),
                acompanhantes: this.getAcompanhantesData(),
                fotos: this.getImageData()
            };

            // Adicionar projeto_id como número inteiro
            const projetoIdStr = document.querySelector('#projeto_id')?.value?.trim();
            if (projetoIdStr) {
                data.projeto_id = parseInt(projetoIdStr, 10);
            }

            // Adicionar ID apenas se existir
            if (this.reportId) {
                data.id = parseInt(this.reportId, 10);
            }

            console.log('📦 AutoSave - Dados coletados:', data);
            return data;
        } catch (err) {
            console.error('❌ AutoSave: erro ao coletar dados do formulário:', err);
            return {};
        }
    }

    getChecklistData() {
        const items = Array.from(document.querySelectorAll('.checklist-item')).map(item => ({
            nome: item.querySelector('label')?.textContent?.trim() || '',
            status: item.querySelector('input[type="checkbox"]')?.checked || false,
            observacao: item.querySelector('textarea')?.value?.trim() || ''
        }));

        console.log(`📋 AutoSave - Checklist: ${items.length} itens coletados`);
        return items;
    }

    getImageData() {
        const images = window.attachedImages || [];
        const imageData = images.map((img, index) => ({
            nome: img.name || null,
            categoria: img.category || null,
            local: img.location || null,
            legenda: img.caption || null,
            titulo: img.title || null,
            tipo_servico: img.category || null,
            url: img.url || null,
            filename: img.filename || null,
            ordem: img.ordem !== undefined ? img.ordem : index
        }));

        console.log(`📸 AutoSave - Imagens: ${imageData.length} imagens coletadas`);
        return imageData;
    }

    collectRichTextContent() {
        const editor = document.querySelector('.ql-editor');
        return editor ? editor.innerHTML.trim() : '';
    }

    getAcompanhantesData() {
        try {
            // Verificar se existe variável global window.acompanhantes
            if (window.acompanhantes && Array.isArray(window.acompanhantes)) {
                console.log(`👥 AutoSave - Acompanhantes: ${window.acompanhantes.length} pessoas`);
                return window.acompanhantes;
            }
            
            // Tentar coletar do input hidden
            const acompanhantesInput = document.querySelector('#acompanhantes-data');
            if (acompanhantesInput && acompanhantesInput.value) {
                const acompanhantes = JSON.parse(acompanhantesInput.value);
                console.log(`👥 AutoSave - Acompanhantes: ${acompanhantes.length} pessoas`);
                return acompanhantes;
            }
        } catch (e) {
            console.error('❌ Erro ao coletar acompanhantes:', e);
        }
        return [];
    }

    async performSave() {
        if (this.isSaving) {
            console.log('⏸️ AutoSave: Salvamento já em progresso, aguardando...');
            return;
        }

        this.isSaving = true;
        const payload = this.collectFormData();

        try {
            const response = await fetch('/api/relatorios/autosave', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(this.csrfToken && { 'X-CSRFToken': this.csrfToken })
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                console.error('❌ AutoSave erro HTTP:', response.status, err);
                throw new Error(err.detail || err.error || 'Falha no autosave');
            }

            const result = await response.json();
            console.log('✅ AutoSave concluído com sucesso:', result);
            
            // Atualizar reportId se foi criado novo relatório
            if (result.relatorio_id && !this.reportId) {
                this.reportId = result.relatorio_id;
                window.currentReportId = result.relatorio_id;
                console.log(`📌 AutoSave: Novo relatório criado com ID ${this.reportId}`);
            }
            
            // Limpar localStorage após sucesso
            this.clearLocalStorage();

        } catch (error) {
            console.warn('⚠️ AutoSave falhou:', error.message);
            console.info('💾 Salvando temporariamente no localStorage...');
            this.saveToLocalStorage(payload);
        } finally {
            this.isSaving = false;
        }
    }

    saveToLocalStorage(payload) {
        try {
            localStorage.setItem('autosave_draft', JSON.stringify(payload));
            console.log('💾 AutoSave: Dados salvos no localStorage');
        } catch (error) {
            console.error('❌ Erro ao salvar no localStorage:', error);
        }
    }

    clearLocalStorage() {
        try {
            localStorage.removeItem('autosave_draft');
            console.log('🗑️ AutoSave: localStorage limpo');
        } catch (error) {
            console.error('❌ Erro ao limpar localStorage:', error);
        }
    }

    async retrySaveFromLocalStorage() {
        const stored = localStorage.getItem('autosave_draft');
        if (!stored) return;

        try {
            const payload = JSON.parse(stored);
            console.log('🔄 AutoSave: Tentando reenviar dados salvos localmente');
            
            const response = await fetch('/api/relatorios/autosave', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    ...(this.csrfToken && { 'X-CSRFToken': this.csrfToken })
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                console.log('✅ AutoSave: Dados locais reenviados com sucesso');
                this.clearLocalStorage();
            }
        } catch (error) {
            console.error('❌ Falha ao reenviar dados locais:', error);
        }
    }

    forceSave() {
        console.log('🚀 AutoSave: Salvamento forçado');
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        this.performSave();
    }
}

// Função de inicialização global
window.initAutoSave = function(reportId, csrfToken) {
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

console.log('📱 AutoSave: Script carregado e pronto');
