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
                fotos: [] // Será preenchido na versão async
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
    
    async collectFormDataAsync() {
        try {
            // Coletar checklist e acompanhantes ANTES de serializar
            const checklistData = this.getChecklistData();
            const acompanhantesData = this.getAcompanhantesData();
            
            const data = {
                titulo: document.querySelector('#titulo_relatorio')?.value?.trim() || 
                        document.querySelector('#titulo')?.value?.trim() || "",
                numero: document.querySelector('#numero_relatorio')?.value?.trim() || 
                        document.querySelector('#numero')?.value?.trim() || "",
                data_relatorio: document.querySelector('#data_relatorio')?.value || null,
                observacoes_finais: document.querySelector('#observacoes')?.value?.trim() || "",
                lembrete_proxima_visita: document.querySelector('#lembrete_proxima_visita')?.value?.trim() || null,
                conteudo: this.collectRichTextContent() || "",
                // ENVIAR COMO ARRAY - backend irá converter para JSON
                checklist_data: checklistData,
                acompanhantes: acompanhantesData,
                fotos: await this.getImageData(), // Aguardar upload das imagens
                categoria: document.querySelector('#categoria')?.value?.trim() || null,
                local: document.querySelector('#local')?.value?.trim() || null
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

            console.log('📦 AutoSave - Dados coletados (com imagens):', data);
            console.log('📸 AutoSave - Total de fotos:', data.fotos?.length || 0);
            console.log('👥 AutoSave - Acompanhantes:', acompanhantesData.length, 'pessoas');
            console.log('✅ AutoSave - Checklist:', checklistData.length, 'itens');
            return data;
        } catch (err) {
            console.error('❌ AutoSave: erro ao coletar dados do formulário:', err);
            return {};
        }
    }

    getChecklistData() {
        const checklistData = [];
        
        // Coletar itens do checklist EXATAMENTE como o botão concluir faz
        document.querySelectorAll('.checklist-item').forEach(item => {
            const checkbox = item.querySelector('.form-check-input[type="checkbox"]');
            const label = item.querySelector('.form-check-label');
            const customInput = item.querySelector('input[type="text"]');
            const textarea = item.querySelector('textarea');
            
            if (checkbox) {
                const itemText = label ? label.textContent.trim() : (customInput ? customInput.value : '');
                if (itemText) {
                    checklistData.push({
                        item: itemText,
                        completed: checkbox.checked,
                        observations: textarea ? textarea.value : ''
                    });
                }
            }
        });

        console.log(`📋 AutoSave - Checklist: ${checklistData.length} itens coletados`, checklistData);
        return checklistData;
    }

    async getImageData() {
        // Coletar imagens do mobilePhotoData (sistema mobile-first)
        const mobilePhotos = window.mobilePhotoData || [];
        const imageData = [];
        
        console.log(`📸 AutoSave - Processando ${mobilePhotos.length} imagens do sistema mobile-first...`);
        
        for (let i = 0; i < mobilePhotos.length; i++) {
            const photo = mobilePhotos[i];
            
            console.log(`📸 Imagem ${i}:`, {
                savedId: photo.savedId,
                hasFile: !!photo.file,
                category: photo.category,
                manualCaption: photo.manualCaption,
                predefinedCaption: photo.predefinedCaption
            });
            
            // Se já tem ID, é uma imagem já salva - apenas metadados
            if (photo.savedId) {
                imageData.push({
                    id: photo.savedId,
                    legenda: photo.manualCaption || photo.predefinedCaption || '',
                    categoria: photo.category || null,
                    local: photo.local || null,
                    titulo: photo.manualCaption || photo.predefinedCaption || null,
                    tipo_servico: photo.category || null,
                    ordem: i
                });
                console.log(`📌 AutoSave - Imagem já salva: ID ${photo.savedId}, legenda: "${photo.manualCaption || photo.predefinedCaption}"`);
                continue;
            }
            
            // Se tem arquivo, fazer upload temporário
            if (photo.file) {
                try {
                    console.log(`📤 AutoSave - Iniciando upload da imagem ${i}...`);
                    const tempUploadResult = await this.uploadImageTemp(photo.file);
                    
                    if (tempUploadResult && tempUploadResult.temp_id) {
                        // Armazenar temp_id para posterior associação
                        photo.temp_id = tempUploadResult.temp_id;
                        
                        const imgData = {
                            temp_id: tempUploadResult.temp_id,
                            extension: tempUploadResult.filename.split('.').pop(),
                            legenda: photo.manualCaption || photo.predefinedCaption || '',
                            categoria: photo.category || null,
                            local: photo.local || null,
                            titulo: photo.manualCaption || photo.predefinedCaption || null,
                            tipo_servico: photo.category || null,
                            ordem: i
                        };
                        
                        imageData.push(imgData);
                        console.log(`✅ AutoSave - Upload temporário: ${tempUploadResult.temp_id}`, imgData);
                    }
                } catch (error) {
                    console.error(`❌ AutoSave - Erro no upload da imagem ${i}:`, error);
                }
            } else {
                console.warn(`⚠️ AutoSave - Imagem ${i} sem arquivo e sem savedId`);
            }
        }
        
        console.log(`📸 AutoSave - TOTAL: ${imageData.length} imagens preparadas para salvamento`);
        console.log(`📸 AutoSave - Detalhes:`, imageData);
        return imageData;
    }
    
    async uploadImageTemp(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/uploads/temp', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload falhou: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                return result;
            } else {
                throw new Error(result.error || 'Erro no upload');
            }
        } catch (error) {
            console.error('❌ Erro no upload temporário:', error);
            throw error;
        }
    }

    collectRichTextContent() {
        const editor = document.querySelector('.ql-editor');
        return editor ? editor.innerHTML.trim() : '';
    }

    getAcompanhantesData() {
        try {
            // Verificar se existe variável global window.acompanhantes
            if (window.acompanhantes && Array.isArray(window.acompanhantes)) {
                console.log(`👥 AutoSave - Acompanhantes (global): ${window.acompanhantes.length} pessoas`, window.acompanhantes);
                return window.acompanhantes;
            }
            
            // Tentar coletar do input hidden
            const acompanhantesInput = document.querySelector('#acompanhantes-data');
            if (acompanhantesInput && acompanhantesInput.value) {
                try {
                    const acompanhantes = JSON.parse(acompanhantesInput.value);
                    console.log(`👥 AutoSave - Acompanhantes (input): ${acompanhantes.length} pessoas`, acompanhantes);
                    return acompanhantes;
                } catch (parseError) {
                    console.warn('⚠️ Erro ao parsear acompanhantes do input:', parseError);
                    console.log('   Valor do input:', acompanhantesInput.value);
                }
            }
            
            console.log('👥 AutoSave - Nenhum acompanhante encontrado');
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
        
        // Coletar dados do formulário de forma assíncrona (aguardar upload de imagens)
        const payload = await this.collectFormDataAsync();

        try {
            console.log('📤 AutoSave: Enviando dados...', payload);
            
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
                
                // Atualizar campo hidden se existir
                const reportIdInput = document.querySelector('input[name="report_id"]');
                if (reportIdInput) {
                    reportIdInput.value = this.reportId;
                }
            }
            
            // Mapear temp_ids para IDs reais das imagens salvas
            if (result.imagens && Array.isArray(result.imagens) && window.mobilePhotoData) {
                console.log(`📸 AutoSave: Mapeando ${result.imagens.length} imagens salvas`);
                result.imagens.forEach(img => {
                    if (img.temp_id) {
                        // Encontrar foto correspondente no mobilePhotoData
                        const photo = window.mobilePhotoData.find(p => p.temp_id === img.temp_id);
                        if (photo) {
                            photo.savedId = img.id;
                            console.log(`📸 AutoSave: Imagem ${img.temp_id} → ID ${img.id} (legenda: "${img.legenda}")`);
                        }
                    }
                });
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
