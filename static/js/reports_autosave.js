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

        // Verificar se há parâmetro edit na URL
        const urlParams = new URLSearchParams(window.location.search);
        const editParam = urlParams.get('edit');
        if (editParam && !this.reportId) {
            this.reportId = parseInt(editParam, 10);
            console.log(`📥 AutoSave: ID do relatório capturado da URL: ${this.reportId}`);
        }

        if (!this.reportId) {
            console.log('📝 AutoSave: Sem reportId - será criado no primeiro salvamento');
        }

        this.init();
    }

    init() {
        console.log(`✅ AutoSave: Ativado para relatório ID ${this.reportId}`);
        console.log(`🔑 AutoSave: CSRF Token presente: ${!!this.csrfToken}`);
        console.log(`⏱️ AutoSave: Debounce configurado para ${this.debounceTime}ms`);

        // Se há reportId, carregar os dados do relatório primeiro
        if (this.reportId) {
            this.loadReportData();
        }

        this.startAutoSave();
        this.setupNetworkListeners();
    }

    /**
     * Carrega os dados do relatório existente
     */
    async loadReportData() {
        try {
            console.log(`📥 Carregando relatório ID: ${this.reportId}`);

            const response = await fetch(`/api/relatorios/${this.reportId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Erro ao carregar relatório: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                console.log('✅ Dados do relatório carregados:', data);

                // Preencher formulário com dados carregados
                this.populateForm(data.relatorio);

                // Selecionar projeto se disponível
                if (data.projeto) {
                    this.selectProjeto(data.projeto);
                }

                // Carregar imagens com categoria e local
                if (data.imagens && data.imagens.length > 0) {
                    this.loadImages(data.imagens);
                }

                // Preencher checklist
                if (data.checklist && data.checklist.length > 0) {
                    this.preencherChecklist(data.checklist);
                }

                // Preencher acompanhantes
                if (data.acompanhantes && data.acompanhantes.length > 0) {
                    this.preencherAcompanhantes(data.acompanhantes);
                }

                console.log('✅ Relatório carregado e pré-preenchido com sucesso');
            }

        } catch (error) {
            console.error('❌ Erro ao carregar relatório:', error);
        }
    }

    /**
     * Preenche o formulário com dados do relatório
     */
    populateForm(relatorio) {
        console.log('📝 Preenchendo formulário com dados do relatório');

        // Preencher campos básicos
        if (relatorio.titulo) {
            const titulo = document.getElementById('titulo') || document.getElementById('titulo_relatorio');
            if (titulo) titulo.value = relatorio.titulo;
        }

        if (relatorio.numero) {
            const numero = document.getElementById('numero') || document.getElementById('numero_relatorio');
            if (numero) numero.value = relatorio.numero;
        }

        if (relatorio.data_relatorio) {
            const data = document.getElementById('data_relatorio');
            if (data) data.value = relatorio.data_relatorio.split('T')[0];
        }

        if (relatorio.observacoes_finais) {
            const obs = document.getElementById('observacoes') || document.querySelector('[name="observacoes_finais"]');
            if (obs) obs.value = relatorio.observacoes_finais;
        }

        if (relatorio.conteudo) {
            const conteudo = document.getElementById('conteudo');
            if (conteudo) conteudo.value = relatorio.conteudo;
        }

        if (relatorio.lembrete_proxima_visita) {
            const lembrete = document.getElementById('lembrete_proxima_visita') || document.getElementById('lembrete');
            if (lembrete) {
                const date = new Date(relatorio.lembrete_proxima_visita);
                lembrete.value = date.toISOString().slice(0, 16);
            }
        }

        if (relatorio.categoria) {
            const categoria = document.getElementById('categoria');
            if (categoria) categoria.value = relatorio.categoria;
        }

        if (relatorio.local) {
            const local = document.getElementById('local');
            if (local) local.value = relatorio.local;
        }

        console.log('✅ Formulário preenchido');
    }

    /**
     * Seleciona o projeto no campo de seleção
     */
    selectProjeto(projeto) {
        if (!projeto) return;

        console.log('🏢 Selecionando projeto:', projeto.nome);
        const projetoSelect = document.getElementById('projeto_id') || document.querySelector('select[name="projeto_id"]');
        if (projetoSelect) {
            let optionExists = false;
            for (let i = 0; i < projetoSelect.options.length; i++) {
                if (projetoSelect.options[i].value == projeto.id) {
                    projetoSelect.selectedIndex = i;
                    optionExists = true;
                    break;
                }
            }

            if (!optionExists) {
                const option = new Option(projeto.nome, projeto.id, true, true);
                projetoSelect.appendChild(option);
            }

            // Disparar evento change para carregar dados do projeto
            projetoSelect.dispatchEvent(new Event('change'));
            console.log(`✅ Projeto selecionado: ${projeto.nome}`);
        }
    }

    /**
     * Carrega e exibe imagens do relatório
     */
    loadImages(imagens) {
        console.log(`📸 Carregando ${imagens.length} imagens`);

        // Tentar encontrar o container de imagens
        const container = document.getElementById('imagens-container') || 
                         document.getElementById('photos-container') ||
                         document.querySelector('.photos-container');

        if (!container) {
            console.warn('⚠️ Container de imagens não encontrado');
            return;
        }

        container.innerHTML = '';

        imagens.forEach((img, index) => {
            const card = document.createElement('div');
            card.className = 'mobile-photo-card';
            card.innerHTML = `
                <img src="${img.path || img.url}" alt="${img.caption || img.legenda || 'Foto'}" 
                     class="photo-card-image">
                <div class="photo-card-content">
                    <input type="text" class="caption-input" placeholder="Legenda" 
                           value="${img.caption || img.legenda || ''}" 
                           data-image-id="${img.id}">
                    <input type="text" class="caption-input" placeholder="Categoria" 
                           value="${img.category || img.tipo_servico || ''}"
                           data-image-id="${img.id}">
                    <input type="text" class="caption-input" placeholder="Local" 
                           value="${img.local || ''}"
                           data-image-id="${img.id}">
                </div>
            `;
            container.appendChild(card);
        });

        console.log(`✅ ${imagens.length} imagens carregadas e exibidas`);
    }

    /**
     * Preenche o checklist com os dados carregados
     */
    preencherChecklist(checklist) {
        console.log(`📋 Preenchendo checklist com ${checklist.length} itens`);

        if (!Array.isArray(checklist)) {
            console.warn('⚠️ Checklist não é um array:', checklist);
            return;
        }

        checklist.forEach(item => {
            const pergunta = item.item || item.pergunta || item.texto;
            const concluido = item.completed || item.concluido || item.resposta;

            // Tentar encontrar o checkbox correspondente
            const checkboxes = document.querySelectorAll('.checklist-item .form-check-input[type="checkbox"]');
            checkboxes.forEach(checkbox => {
                const label = checkbox.closest('.checklist-item')?.querySelector('.form-check-label');
                if (label && label.textContent.trim().includes(pergunta)) {
                    checkbox.checked = concluido;
                }
            });
        });

        console.log(`✅ ${checklist.length} itens de checklist preenchidos`);
    }

    /**
     * Preenche os acompanhantes com os dados carregados
     */
    preencherAcompanhantes(acompanhantesData) {
        console.log(`👥 Preenchendo ${acompanhantesData.length} acompanhantes`);

        if (!Array.isArray(acompanhantesData)) {
            console.warn('⚠️ Acompanhantes não é um array:', acompanhantesData);
            return;
        }

        // Usar a variável global acompanhantes se existir
        if (typeof window.acompanhantes !== 'undefined') {
            window.acompanhantes = acompanhantesData;

            // Atualizar visualização se a função existir
            if (typeof window.atualizarListaAcompanhantes === 'function') {
                window.atualizarListaAcompanhantes();
            }

            // Atualizar campo hidden
            const hiddenField = document.getElementById('acompanhantes-data');
            if (hiddenField) {
                hiddenField.value = JSON.stringify(acompanhantesData);
            }

            console.log(`✅ ${acompanhantesData.length} acompanhantes carregados`);
        }
    }

    startAutoSave() {
        const saveHandler = () => {
            console.log('📝 AutoSave: Campo modificado - iniciando debounce de 2s');
            clearTimeout(this.debounceTimer);
            this.debounceTimer = setTimeout(() => this.performSave(), this.debounceTime);
        };

        // Monitorar TODOS os campos do formulário
        const formElements = document.querySelectorAll('input, textarea, select');
        formElements.forEach(el => {
            el.addEventListener('input', saveHandler);
            el.addEventListener('change', saveHandler);
        });

        console.log(`🕒 AutoSave: Monitorando ${formElements.length} campos do formulário`);
    }

    /**
     * Public method to trigger autosave from external code
     * Used when photo fields (categoria, local, legenda) are updated
     */
    triggerSave() {
        console.log('📝 AutoSave: Triggered externally - iniciando debounce de 2s');
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.performSave(), this.debounceTime);
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
                // Observações Gerais: ler do #conteudo e salvar em observacoes_finais
                observacoes_finais: document.querySelector('#conteudo')?.value?.trim() || 
                                   document.querySelector('#observacoes')?.value?.trim() || "",
                lembrete_proxima_visita: document.querySelector('#lembrete')?.value?.trim() || null,
                conteudo: this.collectRichTextContent() || "",
                checklist_data: this.getChecklistData(),
                acompanhantes: this.getAcompanhantesData(),
                fotos: [] // Será preenchido na versão async
            };

            // Adicionar projeto_id como número inteiro - buscar em múltiplos locais
            const projetoIdStr = 
                document.querySelector('[name="projeto_id"]')?.value?.trim() ||
                document.querySelector('#projeto_id')?.value?.trim() ||
                document.querySelector('[data-project-id]')?.getAttribute('data-project-id') ||
                (window.currentProjetoId ? String(window.currentProjetoId) : null);

            if (projetoIdStr) {
                data.projeto_id = parseInt(projetoIdStr, 10);
                console.log('✅ AutoSave - projeto_id encontrado:', data.projeto_id);
            } else {
                console.warn('⚠️ AutoSave - projeto_id NÃO encontrado! AutoSave pode falhar.');
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
                // Observações Gerais: ler do #conteudo e salvar em observacoes_finais
                observacoes_finais: document.querySelector('#conteudo')?.value?.trim() || 
                                   document.querySelector('#observacoes')?.value?.trim() || "",
                lembrete_proxima_visita: document.querySelector('#lembrete_proxima_visita')?.value?.trim() || null,
                conteudo: this.collectRichTextContent() || "",
                // ENVIAR COMO ARRAY - backend irá converter para JSON
                checklist_data: checklistData,
                acompanhantes: acompanhantesData,
                fotos: await this.getImageData(), // Aguardar upload das imagens
                categoria: document.querySelector('#categoria')?.value?.trim() || null,
                local: document.querySelector('#local')?.value?.trim() || null
            };

            // Adicionar projeto_id como número inteiro - buscar em múltiplos locais
            const projetoIdStr = 
                document.querySelector('[name="projeto_id"]')?.value?.trim() ||
                document.querySelector('#projeto_id')?.value?.trim() ||
                document.querySelector('[data-project-id]')?.getAttribute('data-project-id') ||
                (window.currentProjetoId ? String(window.currentProjetoId) : null);

            if (projetoIdStr) {
                data.projeto_id = parseInt(projetoIdStr, 10);
                console.log('✅ AutoSave - projeto_id encontrado:', data.projeto_id);
            } else {
                console.warn('⚠️ AutoSave - projeto_id NÃO encontrado! AutoSave pode falhar.');
                console.warn('   Tentou buscar em: [name="projeto_id"], #projeto_id, [data-project-id], window.currentProjetoId');
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

        // Coletar itens do checklist EXATAMENTE como o botão concluir faz (linhas 1521-1542 de form_complete.html)
        document.querySelectorAll('.checklist-item').forEach(item => {
            const checkbox = item.querySelector('.form-check-input[type="checkbox"]');
            const label = item.querySelector('.form-check-label');
            const customInput = item.querySelector('input[type="text"]');
            const textarea = item.querySelector('textarea');

            if (checkbox) {
                const itemText = label ? label.textContent.trim() : (customInput ? customInput.value : '');
                if (itemText) {
                    checklistData.push({
                        texto: itemText,
                        concluido: checkbox.checked,
                        observacao: textarea ? textarea.value : ''
                    });
                }
            }
        });

        console.log(`📋 AutoSave - Checklist: ${checklistData.length} itens coletados`, checklistData);
        return checklistData;
    }

    /**
     * Função de coleta de imagens conforme especificação técnica
     * Garante que todas as imagens sejam processadas com metadados completos
     */
    async getImageData() {
        const imgs = window.mobilePhotoData || [];
        const uploaded = [];

        for (let i = 0; i < imgs.length; i++) {
            const img = imgs[i];
            console.log(`📸 Imagem ${i}:`, img);

            // Se a imagem já foi salva no banco, apenas incluir seus metadados
            if (img.savedId && img.savedId > 0) {
                uploaded.push({
                    id: img.savedId,
                    filename: img.name || img.filename,
                    category: img.category || "em branco",
                    local: img.local || "em branco",
                    caption: img.manualCaption || img.predefinedCaption || img.caption || "em branco",
                    ordem: i
                });
                console.log(`📌 AutoSave - Imagem já salva no banco: ID ${img.savedId}`);
                continue;
            }

            // Validar se tem blob/file antes de tentar upload
            if (!img || !img.blob) {
                console.warn("⚠️ Imagem inválida ou blob ausente:", img);
                continue; // ignora sem travar
            }

            try {
                // Forçar "em branco" no objeto antes do upload para garantir persistência
                img.category = img.category || "em branco";
                img.local = img.local || "em branco";
                img.caption = img.manualCaption || img.predefinedCaption || img.caption || "em branco";

                const tempId = await this.uploadImageTemp(img);
                if (tempId) {
                    uploaded.push({
                        temp_id: tempId,
                        filename: img.name || img.filename,
                        category: img.category,
                        local: img.local,
                        caption: img.caption,
                        ordem: i
                    });
                }
            } catch (err) {
                console.error(`❌ Falha ao enviar imagem ${i}:`, err);
            }
        }

        console.log(`📸 AutoSave - Total de ${uploaded.length} imagens enviadas`);
        return uploaded;
    }

    /**
     * Faz upload da imagem temporária com multipart/form-data
     * Retorna o ID temporário salvo no backend
     */
    async uploadImageTemp(image) {
        try {
            if (!image || !image.blob) {
                console.warn("⚠️ Imagem inválida ou blob ausente:", image);
                return null;
            }

            // 🔒 Define valores padrão se estiverem vazios
            const category = image.category || "em branco";
            const local = image.local || "em branco";
            const caption = image.manualCaption || image.predefinedCaption || image.caption || "em branco";
            
            console.log("📤 AutoSave - Preparando upload da imagem:", image.name || image.filename);

            const formData = new FormData();
            formData.append("file", image.blob, image.name || image.filename || "imagem.jpg");
            formData.append("category", category);
            formData.append("local", local);
            formData.append("caption", caption);

            // 🔐 Inclui CSRF token se necessário
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
            const headers = csrfToken ? { "X-CSRFToken": csrfToken } : {};

            const response = await fetch("/api/uploads/temp", {
                method: "POST",
                headers,
                body: formData,
                credentials: "include", // 🔐 importante para cookies de sessão
            });

            if (!response.ok) {
                const msg = await response.text();
                console.error("❌ Erro HTTP no upload:", response.status, msg);
                throw new Error(`Upload falhou: ${response.status}`);
            }

            const data = await response.json();
            console.log("✅ Upload temporário bem-sucedido:", data);

            return data.temp_id || data.id || null;
        } catch (err) {
            console.error("❌ Erro no upload temporário:", err);
            throw err;
        }
    }

    collectRichTextContent() {
        // Primeiro, tentar o editor Quill (se existir)
        const editor = document.querySelector('.ql-editor');
        if (editor) {
            return editor.innerHTML.trim();
        }
        
        // Fallback: ler do textarea #conteudo diretamente
        const conteudoTextarea = document.querySelector('#conteudo');
        if (conteudoTextarea) {
            return conteudoTextarea.value?.trim() || '';
        }
        
        return '';
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

        // Evita salvar se existir imagem sem legenda (DESATIVADO: Permitir salvar sem legenda)
        /*
        const pendingImages = (window.mobilePhotoData || []).filter(
            img => img.blob && (!img.caption || img.caption.trim() === "") && 
                   (!img.manualCaption || img.manualCaption.trim() === "") &&
                   (!img.predefinedCaption || img.predefinedCaption.trim() === "")
        );

        if (pendingImages.length > 0) {
            console.warn("⏸️ AutoSave adiado: há imagens sem legenda.");
            return;
        }
        */

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
                console.error('❌ AutoSave erro HTTP:', response.status);
                console.error('   Mensagem do servidor:', err.error || err.detail || 'Sem mensagem');
                console.error('   Detalhes completos:', err);
                throw new Error(err.error || err.detail || `Falha no autosave (HTTP ${response.status})`);
            }

            const result = await response.json();
            console.log('✅ AutoSave concluído com sucesso:', result);

            // Atualizar reportId se foi criado novo relatório
                if (result.relatorio_id) {
                    if (!this.reportId) {
                        console.log(`📌 AutoSave: Novo relatório criado com ID ${result.relatorio_id}`);
                    }
                    this.reportId = result.relatorio_id;
                    window.currentReportId = result.relatorio_id;

                    // Atualizar TODOS os campos hidden possíveis
                    const reportIdInputs = [
                        document.querySelector('input[name="report_id"]'),
                        document.getElementById('relatorio_id'),
                        document.querySelector('input[name="relatorio_id"]')
                    ];

                    reportIdInputs.forEach(input => {
                        if (input) {
                            input.value = this.reportId;
                        }
                    });
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
                        } else {
                            console.warn(`⚠️ AutoSave: Não foi possível encontrar foto com temp_id ${img.temp_id} no mobilePhotoData`);
                        }
                    }
                });
            } else {
                console.warn(`⚠️ AutoSave: Nenhuma imagem retornada no resultado ou mobilePhotoData vazio`);
            }

            // VALIDAÇÃO FINAL: Confirmar total de imagens
            console.log(`✅ AutoSave FINAL: ${result.imagens?.length || 0} imagens processadas`);
            console.log(`📊 mobilePhotoData após salvamento:`, window.mobilePhotoData?.map(p => ({
                savedId: p.savedId,
                temp_id: p.temp_id,
                legenda: p.manualCaption || p.predefinedCaption
            })));

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