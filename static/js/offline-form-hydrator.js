/**
 * ============================================================
 * OFFLINE FORM HYDRATOR v2.0
 * ============================================================
 * Motor de hidratação offline para o formulário de relatório.
 * Carrega TODOS os dados do projeto a partir do IndexedDB:
 *   - Número do relatório
 *   - Informações técnicas
 *   - Checklist da obra
 *   - Acompanhantes / funcionários
 *   - Categorias das fotos
 *   - Legendas pré-definidas
 *   - Lembrete anterior
 *
 * Também intercepta o submit offline e salva no IndexedDB
 * para sincronização posterior.
 * ============================================================
 */
(function () {
    'use strict';

    const HYDRATOR_VERSION = '2.0';

    // ============================================================
    // Helpers
    // ============================================================
    function log(msg, ...args) {
        console.log(`[Hydrator] ${msg}`, ...args);
    }
    function warn(msg, ...args) {
        console.warn(`[Hydrator] ⚠️ ${msg}`, ...args);
    }
    function err(msg, ...args) {
        console.error(`[Hydrator] ❌ ${msg}`, ...args);
    }

    /**
     * Verifica se o ELPOfflineManager já está pronto
     */
    function waitForOfflineManager(maxWaitMs = 5000) {
        return new Promise((resolve) => {
            if (window.ELPOfflineManager && typeof window.ELPOfflineManager.getProjects === 'function') {
                return resolve(window.ELPOfflineManager);
            }
            const start = Date.now();
            const interval = setInterval(() => {
                if (window.ELPOfflineManager && typeof window.ELPOfflineManager.getProjects === 'function') {
                    clearInterval(interval);
                    resolve(window.ELPOfflineManager);
                } else if (Date.now() - start > maxWaitMs) {
                    clearInterval(interval);
                    warn('ELPOfflineManager não disponível após timeout');
                    resolve(null);
                }
            }, 100);
        });
    }

    /**
     * Obtém o projeto_id da URL
     */
    function getProjetoIdFromURL() {
        return new URLSearchParams(window.location.search).get('projeto_id');
    }

    /**
     * Mostra uma notificação toast discreta
     */
    function showToast(message, type = 'info') {
        const colors = { info: '#0d6efd', success: '#198754', warning: '#ffc107', danger: '#dc3545' };
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: ${colors[type] || colors.info}; color: white; padding: 12px 24px;
            border-radius: 8px; z-index: 99999; font-size: 14px; font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); max-width: 90vw; text-align: center;
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    // ============================================================
    // HIDRATAÇÃO DO PROJETO
    // ============================================================
    async function hydratarProjeto(manager, projetoId) {
        if (!projetoId) { warn('Sem projeto_id para hidratar'); return; }

        log(`Buscando projeto ${projetoId} no IndexedDB...`);
        const projetos = await manager.getProjects();
        const projeto = projetos.find(p => String(p.id) === String(projetoId));

        if (!projeto) {
            warn(`Projeto ${projetoId} não encontrado no cache. Sync pode não ter rodado.`);
            return;
        }

        log(`✅ Projeto encontrado: "${projeto.nome}" — Iniciando hidratação completa`);

        // 1. SELECIONAR PROJETO NO SELECT (garante que o select tem a opção)
        const selectEl = document.getElementById('projeto_id');
        if (selectEl) {
            let optionFound = false;
            for (let i = 0; i < selectEl.options.length; i++) {
                if (String(selectEl.options[i].value) === String(projetoId)) {
                    selectEl.selectedIndex = i;
                    optionFound = true;
                    break;
                }
            }
            if (!optionFound) {
                const opt = document.createElement('option');
                opt.value = projetoId;
                opt.textContent = `${projeto.numero || ''} - ${projeto.nome}`;
                opt.selected = true;
                selectEl.appendChild(opt);
            }
            log('✅ Projeto selecionado no dropdown');
        }

        // 2. NÚMERO DO RELATÓRIO
        const numeroInput = document.getElementById('numero');
        if (numeroInput && projeto.next_numero) {
            numeroInput.value = projeto.next_numero;
            numeroInput.readOnly = false;
            log(`✅ Número do relatório: ${projeto.next_numero}`);
        } else {
            warn('Campo #numero não encontrado ou next_numero ausente');
        }

        // 3. INFORMAÇÕES TÉCNICAS
        if (projeto.technical_info && typeof projeto.technical_info === 'object') {
            Object.entries(projeto.technical_info).forEach(([key, value]) => {
                const field = document.getElementById(key);
                if (field && value) {
                    field.value = value;
                }
            });
            log('✅ Informações técnicas preenchidas');
        }

        // 4. CATEGORIAS DAS FOTOS
        if (projeto.categorias && projeto.categorias.length > 0) {
            window.currentProjectCategorias = projeto.categorias;
            log(`✅ ${projeto.categorias.length} categorias carregadas para fotos`);
            // Preencher dropdowns de categoria já existentes
            document.querySelectorAll('.categoria-select').forEach(sel => {
                const photoId = sel.dataset.photoId || sel.id.replace('category_', '');
                preencherCategoriasSelect(sel, projeto.categorias, photoId);
            });
        }

        // 5. CHECKLIST DA OBRA
        if (projeto.checklist_projeto && projeto.checklist_projeto.length > 0) {
            log(`✅ Carregando checklist: ${projeto.checklist_projeto.length} itens`);
            // Usar função do form_complete.html se disponível
            if (typeof window.carregarChecklist === 'function') {
                // Formato esperado: {id, texto, concluido}
                const items = projeto.checklist_projeto.map(item => ({
                    ...item,
                    concluido: false,
                    checked: false,
                    checked_in_this_report: false
                }));
                window.carregarChecklist(items);
                // Também popular o sistema dinâmico
                window._checklistItemsData = items.map(i => ({
                    id: i.id,
                    texto: i.texto,
                    concluido: false
                }));
                window._checklistCarregado = true;
            } else if (typeof window.carregarChecklistObra === 'function') {
                await window.carregarChecklistObra();
            } else {
                // Fallback: renderizar manualmente no container dinâmico
                renderizarChecklistManual(projeto.checklist_projeto);
            }
        } else {
            log('Projeto sem checklist personalizado');
            // Tentar carregar checklist padrão do IDB
            await hydratarChecklistPadrao(manager);
        }

        // 6. FUNCIONÁRIOS / ACOMPANHANTES
        if (projeto.funcionarios && projeto.funcionarios.length > 0) {
            window._offlineFuncionarios = projeto;
            log(`✅ ${projeto.funcionarios.length} funcionários disponíveis offline`);
            // Preencher o select de funcionários já aberto
            const selectFunc = document.getElementById('funcionario-select');
            if (selectFunc) {
                preencherSelectFuncionarios(selectFunc, projeto);
            }
        }

        // 7. LEMBRETE ANTERIOR
        if (projeto.lembrete_anterior) {
            const card = document.getElementById('lembrete-card');
            const titulo = document.getElementById('lembrete-titulo');
            const texto = document.getElementById('lembrete-texto');
            if (card && titulo && texto) {
                titulo.textContent = `⚠️ Lembrete anterior (${projeto.lembrete_anterior.numero || 'último'}):`;
                texto.textContent = projeto.lembrete_anterior.texto;
                card.style.display = 'block';
                log('✅ Lembrete anterior exibido');
            }
        }

        log('🎉 Hidratação do projeto completa!');
    }

    // ============================================================
    // CHECKLIST PADRÃO (fallback)
    // ============================================================
    async function hydratarChecklistPadrao(manager) {
        try {
            const checklist = await manager.getChecklist ? await manager.getChecklist() : [];
            if (checklist && checklist.length > 0) {
                if (typeof window.carregarChecklist === 'function') {
                    window.carregarChecklist(checklist.map(item => ({
                        ...item,
                        concluido: false,
                        checked: false
                    })));
                    window._checklistItemsData = checklist.map(i => ({ id: i.id, texto: i.texto, concluido: false }));
                    window._checklistCarregado = true;
                    log(`✅ Checklist padrão: ${checklist.length} itens`);
                }
            }
        } catch (e) {
            warn('Erro ao carregar checklist padrão:', e);
        }
    }

    // ============================================================
    // RENDERIZAR CHECKLIST MANUALMENTE
    // ============================================================
    function renderizarChecklistManual(items) {
        // Tentar o container dinâmico primeiro
        const containerDynamic = document.getElementById('checklistItemsDynamic');
        const containerStatic = document.getElementById('checklistItems');
        const container = containerDynamic || containerStatic;

        if (!container) { warn('Container de checklist não encontrado'); return; }

        const semItens = document.getElementById('checklistSemItens');
        if (semItens) semItens.classList.add('d-none');

        const badge = document.getElementById('checklistBadge');
        if (badge) {
            badge.textContent = `${items.length} item${items.length !== 1 ? 's' : ''}`;
            badge.className = 'badge ms-2 bg-primary';
        }

        window._checklistItemsData = [];
        let html = '';
        items.forEach((item, idx) => {
            const itemId = `cl_item_${item.id || idx}`;
            html += `
            <div class="d-flex align-items-start mb-3 p-2 rounded"
                 style="border: 1px solid #dee2e6; background: #fff;"
                 id="cl_row_${item.id || idx}">
                <input class="form-check-input me-3 mt-1 flex-shrink-0"
                       type="checkbox"
                       id="${itemId}"
                       data-item-id="${item.id || idx}"
                       onchange="onChecklistItemChange ? onChecklistItemChange(this, ${item.id || idx}) : null">
                <div class="flex-grow-1">
                    <label class="form-check-label fw-bold" for="${itemId}" style="cursor:pointer;">
                        ${idx + 1}. ${item.texto}
                    </label>
                </div>
            </div>`;
            window._checklistItemsData.push({ id: item.id || idx, texto: item.texto, concluido: false });
        });

        container.innerHTML = html;
        window._checklistCarregado = true;
        log(`✅ Checklist renderizado manualmente: ${items.length} itens`);
    }

    // ============================================================
    // PREENCHER SELECT DE CATEGORIAS DA FOTO
    // ============================================================
    function preencherCategoriasSelect(selectEl, categorias, photoId) {
        if (!selectEl || !categorias) return;
        let html = '<option value="">Sem categoria</option>';
        categorias.forEach(cat => {
            const nome = typeof cat === 'string' ? cat : (cat.nome_categoria || cat.nome || '');
            if (nome) html += `<option value="${nome}">${nome}</option>`;
        });
        selectEl.innerHTML = html;

        // Restaurar seleção anterior se existir
        if (photoId && window.mobilePhotoData) {
            const photoData = window.mobilePhotoData.find(p => String(p.id) === String(photoId) || p.id == photoId);
            if (photoData && photoData.category) selectEl.value = photoData.category;
        }
    }

    // ============================================================
    // PREENCHER SELECT DE FUNCIONÁRIOS
    // ============================================================
    function preencherSelectFuncionarios(selectEl, projeto) {
        const funcionarios = projeto.funcionarios || [];
        const emails = projeto.emails || [];

        if (funcionarios.length === 0) {
            selectEl.innerHTML = '<option value="">Nenhum funcionário cadastrado</option>';
            return;
        }

        let html = '';
        funcionarios.forEach(func => {
            let rawId = func.id;
            if (typeof rawId === 'string') rawId = rawId.replace('fp_', '').replace('ec_', '');
            const emailObj = emails.find(e => String(e.id) === String(rawId) || String(e.id) === String(func.id));
            const email = emailObj ? emailObj.email : '';
            const nome = func.nome_funcionario || 'Sem nome';
            const cargo = func.cargo || '';
            html += `<option value="${rawId}" data-nome="${nome}" data-cargo="${cargo}" data-email="${email}" data-id="${rawId}">${nome}${cargo ? ' – ' + cargo : ''}</option>`;
        });
        selectEl.innerHTML = html;

        if (typeof $ !== 'undefined' && $.fn && $.fn.select2) {
            $(selectEl).trigger('change');
        }
        log(`✅ ${funcionarios.length} funcionários carregados no select`);
    }

    // ============================================================
    // LEGENDAS
    // ============================================================
    async function hydratarLegendas(manager) {
        try {
            const legendas = await manager.getLegendas();
            if (legendas && legendas.length > 0) {
                window.predefinedLegendas = legendas;
                log(`✅ ${legendas.length} legendas carregadas do IDB`);
                if (typeof window.preencherDropdownLegendas === 'function') {
                    window.preencherDropdownLegendas();
                }
            } else {
                warn('Nenhuma legenda encontrada no IDB');
                window.predefinedLegendas = [];
            }
        } catch (e) {
            err('Erro ao carregar legendas:', e);
        }
    }

    // ============================================================
    // INTERCEPTAÇÃO DO SUBMIT OFFLINE
    // ============================================================
    function setupOfflineSubmitInterception(manager) {
        const form = document.getElementById('reportForm');
        if (!form) { warn('Formulário #reportForm não encontrado'); return; }

        form.addEventListener('submit', async function (e) {
            // Só interceptar se REALMENTE estiver offline
            if (navigator.onLine) return;

            e.preventDefault();
            e.stopImmediatePropagation();

            log('📴 Offline: Interceptando submit do formulário...');
            showToast('📴 Offline — Salvando relatório no dispositivo...', 'warning');

            try {
                const payload = await coletarPayloadCompleto();
                payload.offline_id = `offline_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
                payload.created_offline = true;
                payload.created_at = new Date().toISOString();

                await manager.savePendingReport(payload);

                log(`💾 Relatório salvo offline com ID: ${payload.offline_id}`);
                showToast('✅ Relatório salvo! Será enviado quando você tiver conexão.', 'success');

                // Redirecionar após 2s
                setTimeout(() => {
                    window.location.href = '/reports?offline_saved=1';
                }, 2200);

            } catch (error) {
                err('Erro ao salvar relatório offline:', error);
                showToast('❌ Erro ao salvar offline. Verifique o console.', 'danger');
            }
        }, true); // capture=true para rodar antes de outros listeners

        log('✅ Interceptação de submit offline configurada');
    }

    // ============================================================
    // COLETA COMPLETA DO PAYLOAD
    // ============================================================
    async function coletarPayloadCompleto() {
        const getValue = (selectors) => {
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.value && el.value.trim() !== '') return el.value.trim();
            }
            return '';
        };

        const projetoId = getValue(['#projeto_id', '[name="projeto_id"]']);
        const titulo = getValue(['#titulo_relatorio', '#titulo', '[name="titulo"]']);
        const numero = getValue(['#numero', '[name="numero"]', '#numero_relatorio']);
        const dataRelatorio = getValue(['#data_relatorio', '[name="data_relatorio"]']);
        const observacoes = getValue(['#conteudo', '[name="observacoes_finais"]', '#observacoes']);
        const lembrete = getValue(['#lembrete_proxima_visita', '#lembrete', '[name="lembrete_proxima_visita"]']);

        // Informações técnicas
        const techInfo = {};
        document.querySelectorAll('.technical-field').forEach(field => {
            if (field.name && field.value) techInfo[field.name] = field.value.trim();
        });

        // Checklist
        let checklistData = [];
        if (typeof window.getChecklistDataForAutosave === 'function') {
            const dynamic = window.getChecklistDataForAutosave();
            if (dynamic) checklistData = dynamic;
        }
        if (checklistData.length === 0 && window._checklistItemsData) {
            checklistData = window._checklistItemsData;
        }

        // Acompanhantes
        let acompanhantes = [];
        if (window.acompanhantes && Array.isArray(window.acompanhantes)) {
            acompanhantes = window.acompanhantes;
        } else {
            const hiddenField = document.getElementById('acompanhantes-data');
            if (hiddenField && hiddenField.value) {
                try { acompanhantes = JSON.parse(hiddenField.value); } catch (e) {}
            }
        }

        // Fotos — com base64 para armazenamento offline
        const fotos = await coletarFotosComBase64();

        const payload = {
            projeto_id: projetoId ? parseInt(projetoId) : null,
            titulo: titulo || `Relatório ${new Date().toLocaleDateString('pt-BR')}`,
            numero: numero,
            data_relatorio: dataRelatorio,
            observacoes_finais: observacoes,
            lembrete_proxima_visita: lembrete || null,
            technical_info: techInfo,
            checklist_data: checklistData,
            acompanhantes: acompanhantes,
            fotos: fotos,
            status: 'Rascunho'
        };

        log('📦 Payload coletado para salvar offline:', {
            projeto_id: payload.projeto_id,
            titulo: payload.titulo,
            numero: payload.numero,
            checklist: checklistData.length,
            acompanhantes: acompanhantes.length,
            fotos: fotos.length
        });

        return payload;
    }

    // ============================================================
    // FOTOS COM BASE64 PARA OFFLINE
    // ============================================================
    async function coletarFotosComBase64() {
        const imgs = window.mobilePhotoData || [];
        const resultado = [];

        for (const img of imgs) {
            const entry = {
                id: img.id,
                savedId: img.savedId || null,
                category: img.category || '',
                local: img.local || '',
                caption: img.manualCaption || img.predefinedCaption || img.caption || '',
                filename: img.name || img.filename || 'foto.jpg',
                previewUrl: img.previewUrl || null,
                isExisting: img.isExisting || false
            };

            // Se tiver blob (nova foto), converter para base64
            if (img.blob || img.file) {
                try {
                    const base64 = await blobToBase64(img.blob || img.file);
                    entry.base64 = base64;
                } catch (e) {
                    warn('Não foi possível converter foto para base64:', e);
                }
            }

            resultado.push(entry);
        }

        return resultado;
    }

    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            if (!blob) return resolve(null);
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error('Erro ao ler blob'));
            reader.readAsDataURL(blob);
        });
    }

    // ============================================================
    // OBSERVER PARA SELECTS CRIADOS DINAMICAMENTE (categorias de foto)
    // ============================================================
    function observarNovasFotos() {
        const photoContainer = document.getElementById('mobilePhotoCards');
        if (!photoContainer) return;

        const observer = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType !== 1) return;
                    // Preencher selects de categoria nas novas fotos adicionadas
                    node.querySelectorAll('.categoria-select').forEach(sel => {
                        const photoId = sel.dataset.photoId || sel.id.replace('category_', '');
                        if (window.currentProjectCategorias && window.currentProjectCategorias.length > 0) {
                            preencherCategoriasSelect(sel, window.currentProjectCategorias, photoId);
                        }
                    });
                    // Preencher selects de legenda
                    node.querySelectorAll('.caption-select').forEach(() => {
                        if (typeof window.preencherDropdownLegendas === 'function') {
                            window.preencherDropdownLegendas();
                        }
                    });
                });
            });
        });

        observer.observe(photoContainer, { childList: true, subtree: true });
        log('✅ Observer para novas fotos configurado');
    }

    // ============================================================
    // OVERRIDE DAS FUNÇÕES DE BUSCA DEPENDENTES DE REDE
    // ============================================================
    function patchNetworkFunctions(manager, projetoId) {
        // Quando `carregarFuncionariosParaAcompanhantes` for chamada,
        // e estivermos offline, usar dados do IDB
        const originalCarregarFunc = window.carregarFuncionariosParaAcompanhantes;
        window.carregarFuncionariosParaAcompanhantes = async function(pid) {
            if (navigator.onLine) {
                if (originalCarregarFunc) return originalCarregarFunc(pid);
                return;
            }
            const projetos = await manager.getProjects();
            const proj = projetos.find(p => String(p.id) === String(pid));
            const select = document.getElementById('funcionario-select');
            if (proj && select) {
                preencherSelectFuncionarios(select, proj);
            }
        };

        // Quando `populateCategorySelect` for chamada
        const originalPopulateCategory = window.populateCategorySelect;
        window.populateCategorySelect = function(photoId) {
            if (navigator.onLine) {
                if (originalPopulateCategory) return originalPopulateCategory(photoId);
                return;
            }
            const sel = document.getElementById(`category_${photoId}`);
            if (sel && window.currentProjectCategorias) {
                preencherCategoriasSelect(sel, window.currentProjectCategorias, photoId);
            }
        };

        log('✅ Funções de rede substituídas por versões offline-aware');
    }

    // ============================================================
    // SYNC AO VOLTAR ONLINE
    // ============================================================
    function setupOnlineSync(manager) {
        window.addEventListener('online', async () => {
            log('🔗 Conexão restaurada — iniciando sincronização de relatórios pendentes...');
            showToast('🔗 Conexão restaurada! Sincronizando relatórios...', 'info');

            try {
                await new Promise(r => setTimeout(r, 3000)); // Aguardar estabilização
                const result = await manager.syncPendingReports();
                if (result && result.synced > 0) {
                    showToast(`✅ ${result.synced} relatório(s) sincronizado(s) com sucesso!`, 'success');
                    log(`✅ ${result.synced} relatório(s) sincronizados`);
                }
            } catch (e) {
                err('Erro ao sincronizar relatórios pendentes:', e);
            }
        });
    }

    // ============================================================
    // ENTRADA PRINCIPAL
    // ============================================================
    async function init() {
        log(`Inicializando versão ${HYDRATOR_VERSION}...`);

        // Aguardar DOM
        await new Promise(resolve => {
            if (document.readyState !== 'loading') return resolve();
            document.addEventListener('DOMContentLoaded', resolve);
        });

        // Verificar se estamos numa página de formulário de relatório
        if (!document.getElementById('reportForm') && !document.getElementById('projeto_id')) {
            log('Não é página de formulário de relatório. Hydrator inativo.');
            return;
        }

        // Aguardar ELPOfflineManager
        const manager = await waitForOfflineManager();
        if (!manager) {
            warn('Hydrator não pode inicialidar: ELPOfflineManager indisponível.');
            return;
        }

        const projetoId = getProjetoIdFromURL();

        // Configurar sync online e intercept de submit
        setupOnlineSync(manager);
        setupOfflineSubmitInterception(manager);
        observarNovasFotos();

        // Carregar legendas (online ou offline)
        if (!navigator.onLine) {
            await hydratarLegendas(manager);
        }

        // Se estiver offline, fazer hidratação completa do projeto
        if (!navigator.onLine && projetoId) {
            log('📴 Modo OFFLINE — Iniciando hidratação completa...');
            patchNetworkFunctions(manager, projetoId);
            await hydratarProjeto(manager, projetoId);
        } else if (navigator.onLine && projetoId) {
            // Online: ainda assim carregar categorias do cache como backup
            try {
                const projetos = await manager.getProjects();
                const projeto = projetos.find(p => String(p.id) === String(projetoId));
                if (projeto && projeto.categorias) {
                    window.currentProjectCategorias = projeto.categorias;
                    log(`✅ [Online] Categorias cacheadas: ${projeto.categorias.length} itens`);
                }
            } catch (e) { /* silencioso */ }

            // Configurar patch mesmo online para quando ficar offline
            patchNetworkFunctions(manager, projetoId);
        }

        // Listener para quando o projeto é trocado no select
        const selectEl = document.getElementById('projeto_id');
        if (selectEl) {
            selectEl.addEventListener('change', async function() {
                const newProjetoId = this.value;
                if (!navigator.onLine && newProjetoId) {
                    log(`🔄 Projeto alterado para ${newProjetoId} — re-hidratando...`);
                    await hydratarProjeto(manager, newProjetoId);
                    await hydratarLegendas(manager);
                }
            });
        }

        log('✅ Offline Form Hydrator inicializado com sucesso!');
    }

    // Inicializar
    init().catch(e => console.error('[Hydrator] Erro fatal na inicialização:', e));

    // Expor API para debugging
    window.ELPFormHydrator = {
        version: HYDRATOR_VERSION,
        hydratarProjeto,
        hydratarLegendas,
        coletarPayloadCompleto,
        showToast
    };

})();
