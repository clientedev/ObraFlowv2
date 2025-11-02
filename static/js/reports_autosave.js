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
        let timer;
        const saveHandler = () => {
            clearTimeout(timer);
            timer = setTimeout(() => this.performSave(), this.debounceTime);
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
        const data = {
            titulo: document.querySelector('#titulo_relatorio')?.value || null,
            numero: document.querySelector('#numero_relatorio')?.value || null,
            data_relatorio: document.querySelector('#data_relatorio')?.value || null,
            projeto_id: document.querySelector('#projeto_id')?.value || null,
            observacoes_finais: document.querySelector('#observacoes')?.value || null,
            lembrete_proxima_visita: document.querySelector('#lembrete')?.value || null,
            categoria: document.querySelector('#categoria')?.value || null,
            local: document.querySelector('#local')?.value || null,
            descricao: document.querySelector('#descricao')?.value || null,
            checklist_data: this.getChecklistData(),
            fotos: this.getImageData(),
        };

        // Adicionar ID apenas se existir
        if (this.reportId) {
            data.id = this.reportId;
        }

        console.log('📦 AutoSave - Dados coletados:', data);
        return data;
    }

    getChecklistData() {
        const items = Array.from(document.querySelectorAll('.checklist-item')).map(item => ({
            nome: item.querySelector('label')?.textContent?.trim() || '',
            status: item.querySelector('input[type="checkbox"]')?.checked || false,
            observacao: item.querySelector('textarea')?.value || ''
        }));

        console.log(`📋 AutoSave - Checklist: ${items.length} itens coletados`);
        return items.length > 0 ? items : null;
    }

    getImageData() {
        const images = window.attachedImages || [];
        const imageData = images.map(img => ({
            nome: img.name || null,
            legenda: img.caption || null,
            categoria: img.category || null,
            local: img.location || null
        }));

        console.log(`📸 AutoSave - Imagens: ${imageData.length} imagens coletadas`);
        return imageData.length > 0 ? imageData : null;
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
