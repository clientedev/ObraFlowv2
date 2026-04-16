/**
 * ============================================================
 * ELP OFFLINE MANAGER v2.0 — SYNC RESILIENTE
 * ============================================================
 * Gerencia dados offline usando IndexedDB:
 * - Armazena projetos, relatórios, legendas localmente
 * - Intercepta formulários de relatório quando offline
 * - Sincroniza dados pendentes quando volta online
 * - RESILIÊNCIA: sincroniza pendentes em TODA carga de página
 * - Banner visual persistente mostrando status de sync
 * - Retry com backoff exponencial
 * - Lock anti-duplicação (multi-tab safe)
 * ============================================================
 */

(function () {
    'use strict';

    const DB_NAME = 'elp-offline-db';
    const DB_VERSION = 2;
    let db = null;

    // Constantes de sync
    const SYNC_LOCK_KEY = 'elp_sync_lock';
    const SYNC_LOCK_TTL = 60000; // 60s — se uma aba travou, outra pode assumir
    const MAX_RETRIES = 5;
    const BASE_DELAY = 2000; // 2s

    // ============================================================
    // IndexedDB — inicialização
    // ============================================================
    function initDB() {
        return new Promise((resolve, reject) => {
            if (db) return resolve(db);

            const req = indexedDB.open(DB_NAME, DB_VERSION);

            req.onupgradeneeded = (event) => {
                const database = event.target.result;

                // Store de projetos
                if (!database.objectStoreNames.contains('projects')) {
                    database.createObjectStore('projects', { keyPath: 'id' });
                }

                // Store de relatórios
                if (!database.objectStoreNames.contains('reports')) {
                    const store = database.createObjectStore('reports', { keyPath: 'id' });
                    store.createIndex('projeto_id', 'projeto_id', { unique: false });
                }

                // Store de relatórios pendentes de sincronização
                if (!database.objectStoreNames.contains('pending_sync')) {
                    const store = database.createObjectStore('pending_sync', {
                        keyPath: 'offline_id'
                    });
                    store.createIndex('created_at', 'created_at', { unique: false });
                    store.createIndex('status', 'status', { unique: false });
                }

                // Store de legendas
                if (!database.objectStoreNames.contains('legendas')) {
                    database.createObjectStore('legendas', { keyPath: 'id' });
                }

                // Store de checklist padrão
                if (!database.objectStoreNames.contains('checklist')) {
                    database.createObjectStore('checklist', { keyPath: 'id' });
                }

                // Store de metadados (última sincronização, versão, etc.)
                if (!database.objectStoreNames.contains('meta')) {
                    database.createObjectStore('meta', { keyPath: 'key' });
                }

                console.log('✅ IndexedDB: Banco criado/atualizado com sucesso');
            };

            req.onsuccess = (event) => {
                db = event.target.result;
                console.log('✅ IndexedDB: Conectado ao elp-offline-db');
                resolve(db);
            };

            req.onerror = (event) => {
                console.error('❌ IndexedDB: Erro ao abrir banco:', event.target.error);
                reject(event.target.error);
            };
        });
    }

    // ============================================================
    // Operações de banco de dados
    // ============================================================
    function dbPut(storeName, data) {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            if (Array.isArray(data)) {
                data.forEach(item => store.put(item));
            } else {
                store.put(data);
            }
            tx.oncomplete = () => resolve(true);
            tx.onerror = (e) => reject(e.target.error);
        });
    }

    function dbGetAll(storeName) {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const req = store.getAll();
            req.onsuccess = () => resolve(req.result);
            req.onerror = (e) => reject(e.target.error);
        });
    }

    function dbGet(storeName, key) {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const req = store.get(key);
            req.onsuccess = () => resolve(req.result);
            req.onerror = (e) => reject(e.target.error);
        });
    }

    function dbDelete(storeName, key) {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const req = store.delete(key);
            req.onsuccess = () => resolve(true);
            req.onerror = (e) => reject(e.target.error);
        });
    }

    function dbClear(storeName) {
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const req = store.clear();
            req.onsuccess = () => resolve(true);
            req.onerror = (e) => reject(e.target.error);
        });
    }

    // ============================================================
    // LOCK DISTRIBUÍDA — evita sync duplicado entre abas
    // ============================================================
    function acquireSyncLock() {
        const now = Date.now();
        const existing = localStorage.getItem(SYNC_LOCK_KEY);
        if (existing) {
            const lockTime = parseInt(existing, 10);
            if (now - lockTime < SYNC_LOCK_TTL) {
                // Outra aba está sincronizando
                return false;
            }
        }
        localStorage.setItem(SYNC_LOCK_KEY, now.toString());
        return true;
    }

    function releaseSyncLock() {
        localStorage.removeItem(SYNC_LOCK_KEY);
    }

    // ============================================================
    // BANNER DE SINCRONIZAÇÃO VISUAL
    // ============================================================
    let syncBanner = null;

    function showSyncBanner(message, type = 'syncing') {
        removeSyncBanner();

        syncBanner = document.createElement('div');
        syncBanner.id = 'elp-sync-banner';

        const colors = {
            syncing: 'linear-gradient(135deg, #0d6efd 0%, #0a58ca 100%)',
            success: 'linear-gradient(135deg, #198754 0%, #146c43 100%)',
            error: 'linear-gradient(135deg, #dc3545 0%, #b02a37 100%)',
            pending: 'linear-gradient(135deg, #fd7e14 0%, #e06100 100%)'
        };

        const icons = {
            syncing: '<i class="fas fa-sync-alt fa-spin me-2"></i>',
            success: '<i class="fas fa-check-circle me-2"></i>',
            error: '<i class="fas fa-exclamation-triangle me-2"></i>',
            pending: '<i class="fas fa-cloud-upload-alt me-2"></i>'
        };

        syncBanner.style.cssText = `
            position: fixed; top: 0; left: 0; right: 0; z-index: 99999;
            background: ${colors[type] || colors.syncing};
            color: white; padding: 10px 20px; font-size: 14px; font-weight: 600;
            text-align: center; box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            display: flex; align-items: center; justify-content: center;
            animation: slideDown 0.3s ease-out;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        `;

        syncBanner.innerHTML = `${icons[type] || ''}${message}`;

        // Adicionar animation CSS se não existir
        if (!document.getElementById('elp-sync-animations')) {
            const style = document.createElement('style');
            style.id = 'elp-sync-animations';
            style.textContent = `
                @keyframes slideDown {
                    from { transform: translateY(-100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                @keyframes slideUp {
                    from { transform: translateY(0); opacity: 1; }
                    to { transform: translateY(-100%); opacity: 0; }
                }
                #elp-sync-banner.closing {
                    animation: slideUp 0.3s ease-in forwards;
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(syncBanner);

        // Empurrar conteúdo para baixo
        document.body.style.marginTop = syncBanner.offsetHeight + 'px';
    }

    function removeSyncBanner(delay = 0) {
        if (delay > 0) {
            setTimeout(() => removeSyncBanner(0), delay);
            return;
        }
        const existing = document.getElementById('elp-sync-banner');
        if (existing) {
            existing.classList.add('closing');
            setTimeout(() => {
                existing.remove();
                document.body.style.marginTop = '';
            }, 300);
        }
        syncBanner = null;
    }

    // ============================================================
    // Sync de dados do servidor → IndexedDB
    // ============================================================
    async function populateFromServer() {
        try {
            console.log('📥 OfflineManager: Buscando dados do servidor...');

            const response = await fetch('/api/offline/sync-data', {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            });

            if (!response.ok) {
                if (response.status === 302 || response.status === 401) {
                    console.log('ℹ️ OfflineManager: Usuário não autenticado, sync ignorado');
                    return;
                }
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Resposta inválida da API');
            }

            await initDB();

            // Popular cada store
            if (data.projetos?.length) {
                await dbClear('projects');
                await dbPut('projects', data.projetos);
                console.log(`✅ IndexedDB: ${data.projetos.length} projetos armazenados`);
            }

            if (data.relatorios?.length) {
                await dbClear('reports');
                await dbPut('reports', data.relatorios);
                console.log(`✅ IndexedDB: ${data.relatorios.length} relatórios armazenados`);
            }

            if (data.legendas?.length) {
                await dbClear('legendas');
                await dbPut('legendas', data.legendas);
                console.log(`✅ IndexedDB: ${data.legendas.length} legendas armazenadas`);
            }

            if (data.checklist?.length) {
                await dbClear('checklist');
                await dbPut('checklist', data.checklist);
                console.log(`✅ IndexedDB: ${data.checklist.length} itens de checklist armazenados`);
            }

            // Salvar metadata
            await dbPut('meta', {
                key: 'last_sync',
                value: data.synced_at || new Date().toISOString()
            });

            await dbPut('meta', {
                key: 'user',
                value: data.user || null
            });

            console.log('✅ OfflineManager: Dados sincronizados com sucesso!');

        } catch (err) {
            console.error('❌ OfflineManager: Falha ao popular dados offline:', err);
        }
    }

    // ============================================================
    // Salvar relatório pendente de sincronização
    // ============================================================
    async function savePendingReport(payload) {
        await initDB();

        const record = {
            offline_id: payload.offline_id || `offline_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
            tipo: 'relatorio',
            payload: payload,
            created_at: new Date().toISOString(),
            status: 'pending',
            retry_count: 0,
            last_error: null
        };

        await dbPut('pending_sync', record);
        console.log(`💾 IndexedDB: Relatório offline salvo como ${record.offline_id}`);

        // Notificar SW para registrar background sync
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SYNC_PENDING' });
        }

        // Mostrar banner imediatamente
        showSyncBanner('📴 Relatório salvo localmente. Será sincronizado quando houver conexão.', 'pending');

        return record.offline_id;
    }

    // ============================================================
    // SYNC RESILIENTE — sincronizar relatórios pendentes
    // ============================================================
    async function syncPendingReports() {
        await initDB();
        const pending = await dbGetAll('pending_sync');

        if (!pending || pending.length === 0) {
            console.log('ℹ️ OfflineManager: Nenhum relatório pendente');
            removeSyncBanner();
            return { synced: 0, errors: 0 };
        }

        // Verificar conexão real
        if (!navigator.onLine) {
            console.log('📵 OfflineManager: Offline — sync adiado');
            showSyncBanner(`📵 ${pending.length} relatório(s) aguardando conexão para sincronizar`, 'pending');
            return { synced: 0, errors: 0 };
        }

        // Tentar adquirir lock (evita sync duplicado entre abas)
        if (!acquireSyncLock()) {
            console.log('🔒 OfflineManager: Outra aba está sincronizando, aguardando...');
            return { synced: 0, errors: 0 };
        }

        console.log(`🔄 OfflineManager: Sincronizando ${pending.length} relatório(s) pendente(s)...`);
        showSyncBanner(`🔄 Sincronizando ${pending.length} relatório(s)...`, 'syncing');

        let synced = 0;
        let errors = 0;

        for (const record of pending) {
            // Pular itens já em progresso de sync (proteção contra re-entry)
            if (record.status === 'syncing') {
                // Se ficou travado em 'syncing' por mais de 2 minutos, resetar
                const statusAge = Date.now() - (record.sync_started_at || 0);
                if (statusAge < 120000) {
                    console.log(`⏳ ${record.offline_id}: Sync em progresso por outra instância, pulando`);
                    continue;
                }
            }

            // Marcar como 'syncing' com timestamp antes de enviar
            record.status = 'syncing';
            record.sync_started_at = Date.now();
            await dbPut('pending_sync', record);

            const retryCount = record.retry_count || 0;
            if (retryCount >= MAX_RETRIES) {
                console.error(`❌ ${record.offline_id}: Max retries (${MAX_RETRIES}) atingido`);
                record.status = 'failed';
                await dbPut('pending_sync', record);
                errors++;
                continue;
            }

            try {
                showSyncBanner(
                    `🔄 Sincronizando relatório ${synced + 1}/${pending.length}...`,
                    'syncing'
                );

                const response = await fetch('/api/offline/save-report', {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        offline_id: record.offline_id,
                        ...record.payload
                    })
                });

                const result = await response.json();

                if (result.success) {
                    // SUCESSO: remover do IndexedDB
                    await dbDelete('pending_sync', record.offline_id);
                    synced++;
                    console.log(`✅ Relatório ${record.offline_id} sincronizado → id=${result.relatorio_id}`);
                } else {
                    // Erro do servidor (mas resposta válida)
                    record.status = 'pending';
                    record.retry_count = retryCount + 1;
                    record.last_error = result.error || 'Erro desconhecido';
                    await dbPut('pending_sync', record);
                    errors++;
                    console.warn(`⚠️ Falha ao sincronizar ${record.offline_id}:`, result.error);
                }

            } catch (err) {
                // Erro de rede (fetch falhou) — manter no IDB para próxima tentativa
                record.status = 'pending';
                record.retry_count = retryCount + 1;
                record.last_error = err.message;
                await dbPut('pending_sync', record);
                errors++;
                console.warn(`⚠️ Erro de rede ao sincronizar ${record.offline_id}:`, err.message);

                // Se perdeu conexão, parar de tentar
                if (!navigator.onLine) {
                    showSyncBanner(
                        `📵 Conexão perdida. ${synced} sincronizado(s), ${pending.length - synced} pendente(s)`,
                        'pending'
                    );
                    releaseSyncLock();
                    return { synced, errors };
                }

                // Esperar delay exponencial antes da próxima tentativa
                const delay = Math.min(BASE_DELAY * Math.pow(2, retryCount), 30000);
                console.log(`⏳ Aguardando ${delay}ms antes de próxima tentativa...`);
                await new Promise(r => setTimeout(r, delay));
            }
        }

        releaseSyncLock();

        console.log(`✅ OfflineManager: Sync concluído — ${synced} ok, ${errors} erros`);

        if (synced > 0 && errors === 0) {
            showSyncBanner(
                `✅ ${synced} relatório(s) sincronizado(s) com sucesso!`,
                'success'
            );
            removeSyncBanner(4000);
        } else if (synced > 0 && errors > 0) {
            showSyncBanner(
                `⚠️ ${synced} sincronizado(s), ${errors} com erro(s). Tentará novamente.`,
                'error'
            );
            removeSyncBanner(6000);
        } else if (errors > 0) {
            showSyncBanner(
                `❌ Falha ao sincronizar ${errors} relatório(s). Nova tentativa em breve.`,
                'error'
            );
            removeSyncBanner(6000);
        } else {
            removeSyncBanner();
        }

        if (synced > 0) {
            // Notificar página silenciosamente
            window.dispatchEvent(new CustomEvent('elp:reports-synced', {
                detail: { synced, errors }
            }));
        }

        return { synced, errors };
    }

    // ============================================================
    // SYNC AUTOMÁTICO AO CARREGAR PÁGINA (core da resiliência)
    // ============================================================
    async function autoSyncOnPageLoad() {
        await initDB();

        // Verificar se há pendentes
        const pending = await dbGetAll('pending_sync');
        const realPending = (pending || []).filter(
            r => r.status === 'pending' || r.status === 'syncing'
        );

        if (realPending.length === 0) return;

        console.log(`🔄 OfflineManager [auto]: ${realPending.length} relatório(s) pendente(s) detectado(s)`);

        if (navigator.onLine) {
            // Estamos online: sincronizar imediatamente
            showSyncBanner(
                `🔄 Sincronizando ${realPending.length} relatório(s) pendente(s)...`,
                'syncing'
            );
            // Pequeno delay para não atrapalhar o carregamento da página
            setTimeout(async () => {
                await syncPendingReports();
                // Após sincronizar, atualizar dados locais
                await populateFromServer();
            }, 1500);
        } else {
            // Offline: mostrar banner informativo
            showSyncBanner(
                `📵 ${realPending.length} relatório(s) aguardando conexão para sincronizar`,
                'pending'
            );
        }
    }

    // ============================================================
    // Interceptação de formulários de relatório offline
    // ============================================================
    function interceptReportForms() {
        document.addEventListener('submit', async function (event) {
            // Apenas formulários de criação de relatório
            const form = event.target;
            if (!form || !isReportForm(form)) return;

            // Se estiver online, deixa submeter normalmente
            if (navigator.onLine) return;

            // Offline: interceptar
            event.preventDefault();
            event.stopPropagation();

            console.log('📋 OfflineManager: Formulário de relatório interceptado (modo offline)');

            try {
                const formData = new FormData(form);
                const payload = {};

                for (const [key, value] of formData.entries()) {
                    if (key === 'csrf_token' || key === '_token') continue;
                    payload[key] = value;
                }

                const offlineId = await savePendingReport(payload);

                showOfflineSuccess(offlineId);

            } catch (err) {
                console.error('❌ OfflineManager: Erro ao salvar formulário offline:', err);
                showOfflineError();
            }
        }, true);
    }

    function isReportForm(form) {
        // Se o hidratador especializado estiver presente, deixa ele cuidar do formulário
        if (document.getElementById('reportForm') && window.ELPFormHydrator) return false;

        const action = form.action || '';
        const id = form.id || '';
        const cls = form.className || '';

        return (
            action.includes('/reports') ||
            action.includes('/relatorios') ||
            id.includes('report') ||
            id.includes('relatorio') ||
            cls.includes('report-form') ||
            form.querySelector('[name="titulo"]') !== null
        );
    }

    function showOfflineSuccess(offlineId) {
        // Toast de sucesso sem reload
        showSyncBanner('✅ Relatório salvo localmente! Será sincronizado ao reconectar.', 'pending');

        // Navegar para lista de relatórios após breve delay
        setTimeout(() => {
            window.location.href = '/reports';
        }, 2000);
    }

    function showOfflineError() {
        showSyncBanner('❌ Erro ao salvar offline. Tente novamente.', 'error');
        removeSyncBanner(5000);
    }

    // ============================================================
    // Monitoramento de conexão estável
    // ============================================================
    function setupConnectionMonitor() {
        let syncTimer = null;

        window.addEventListener('online', () => {
            console.log('🌐 OfflineManager: Conexão restabelecida, aguardando estabilidade...');

            // Aguardar 3s de estabilidade antes de sincronizar
            clearTimeout(syncTimer);
            syncTimer = setTimeout(async () => {
                console.log('🔄 OfflineManager: Iniciando sincronização automática...');
                const result = await syncPendingReports();
                if (result.synced > 0) {
                    await populateFromServer(); // Atualizar dados locais somente após sync com sucesso
                }
            }, 3000);
        });

        window.addEventListener('offline', () => {
            console.log('📵 OfflineManager: Conexão perdida — modo cache ativo');
            clearTimeout(syncTimer);

            // Checar se tem pendentes e mostrar banner
            initDB().then(() => dbGetAll('pending_sync')).then(pending => {
                const realPending = (pending || []).filter(r => r.status !== 'failed');
                if (realPending.length > 0) {
                    showSyncBanner(
                        `📵 Sem conexão. ${realPending.length} relatório(s) serão sincronizados quando reconectar.`,
                        'pending'
                    );
                }
            });
        });
    }

    // ============================================================
    // Listener de mensagens do Service Worker
    // ============================================================
    function setupSWMessageListener() {
        if (!('serviceWorker' in navigator)) return;

        navigator.serviceWorker.addEventListener('message', async (event) => {
            const { type, payload } = event.data || {};

            switch (type) {
                case 'SAVE_OFFLINE_FORM':
                    // SW nos pediu para salvar um formulário no IDB
                    if (payload) {
                        await initDB();
                        await savePendingReport(payload);
                    }
                    break;

                case 'TRIGGER_SYNC_PENDING':
                    // SW quer sincronizar pendentes (background sync)
                    await syncPendingReports();
                    break;

                case 'CACHE_WARMUP_COMPLETE':
                    console.log(`✅ OfflineManager: Cache Warmup concluído`, payload);
                    break;
            }
        });
    }

    // ============================================================
    // Registro do Service Worker + trigger pós-login
    // ============================================================
    async function registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('⚠️ OfflineManager: Service Workers não suportados neste browser');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/',
                updateViaCache: 'none' // Nunca usar cache do browser para o SW
            });

            console.log(`✅ OfflineManager: Service Worker registrado (scope: ${registration.scope})`);

            // Verificar atualizações periodicamente
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                if (newWorker) {
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            console.log('🔄 SW: Nova versão disponível, atualizando...');
                            newWorker.postMessage({ type: 'SKIP_WAITING' });
                        }
                    });
                }
            });

            // Quando o SW assumir controle (após reload ou claim)
            navigator.serviceWorker.addEventListener('controllerchange', () => {
                console.log('✅ SW: Novo Service Worker assumiu controle');
            });

            return registration;
        } catch (err) {
            if (!navigator.onLine) {
                console.warn('⚠️ OfflineManager: Service Worker não pôde ser atualizado (offline):', err.message);
            } else {
                console.error('❌ OfflineManager: Falha ao registrar Service Worker:', err);
            }
        }
    }

    // ============================================================
    // Trigger de Cache Warmup pós-login
    // ============================================================
    async function triggerCacheWarmupIfLoggedIn() {
        // Verificar se usuário está logado via variável global injetada pelo servidor
        const isLoggedIn = window.ELP_USER_LOGGED_IN === true;
        if (!isLoggedIn) return;

        // Removido o timeout de 2h para forçar o cache a ser populado sempre
        // Isso garante que se o usuário testar offline, o IndexedDB já tem os dados.
        await initDB();
        const projects = await dbGetAll('projects');
        if (projects && projects.length === 0) {
            console.log('🔥 OfflineManager: IDB vazio, forçando warmup imediato...');
        }

        if (!navigator.onLine) {
            console.log('ℹ️ OfflineManager: Offline, warmup adiado');
            return;
        }

        console.log('🔥 OfflineManager: Disparando Cache Warmup pós-login...');

        // Aguardar SW estar pronto
        if (navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'TRIGGER_CACHE_WARMUP',
                payload: { csrfToken: getCSRFToken() }
            });
        } else {
            // SW ainda não controlando — aguardar
            navigator.serviceWorker.ready.then(registration => {
                if (registration.active) {
                    registration.active.postMessage({
                        type: 'TRIGGER_CACHE_WARMUP',
                        payload: { csrfToken: getCSRFToken() }
                    });
                }
            });
        }

        // Popular IndexedDB em paralelo
        await populateFromServer();

        localStorage.setItem('elp_last_warmup', Date.now().toString());
    }

    // ============================================================
    // Helper: CSRF Token
    // ============================================================
    function getCSRFToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.content : '';
    }

    // ============================================================
    // VERIFICAÇÃO PERIÓDICA DE PENDENTES
    // ============================================================
    function setupPeriodicCheck() {
        // A cada 30 segundos, verificar se há pendentes e estamos online
        setInterval(async () => {
            if (!navigator.onLine) return;
            try {
                await initDB();
                const pending = await dbGetAll('pending_sync');
                const realPending = (pending || []).filter(
                    r => r.status === 'pending'
                );
                if (realPending.length > 0) {
                    console.log(`🔄 OfflineManager [periodic]: ${realPending.length} pendente(s) encontrado(s)`);
                    await syncPendingReports();
                }
            } catch (e) {
                // Silencioso
            }
        }, 30000);
    }

    // ============================================================
    // API pública
    // ============================================================
    const ELPOfflineManager = {
        init: async function () {
            await initDB();
            setupSWMessageListener();
            setupConnectionMonitor();
            interceptReportForms();

            // Registrar SW e disparar warmup após tudo pronto
            await registerServiceWorker();

            // *** CORE DA RESILIÊNCIA ***
            // Verificar e sincronizar pendentes ao carregar QUALQUER página
            await autoSyncOnPageLoad();

            // Verificação periódica a cada 30s
            setupPeriodicCheck();

            // Disparar warmup sem delay longo para garantir que o cache seja populado
            // antes do usuário acidentalmente (ou de propósito para testar) ficar offline
            setTimeout(async () => {
                await triggerCacheWarmupIfLoggedIn();
            }, 50);

            console.log('✅ OfflineManager v2.0: Inicializado com sync resiliente');
        },
        savePendingReport,
        syncPendingReports,
        populateFromServer,
        getProjects: () => initDB().then(() => dbGetAll('projects')),
        getReports: () => initDB().then(() => dbGetAll('reports')),
        getPendingSync: () => initDB().then(() => dbGetAll('pending_sync')),
        getLegendas: () => initDB().then(() => dbGetAll('legendas')),
        getChecklist: () => initDB().then(() => dbGetAll('checklist')),
        triggerWarmup: triggerCacheWarmupIfLoggedIn,
        showSyncBanner,
        removeSyncBanner,
    };

    window.ELPOfflineManager = ELPOfflineManager;

    // Auto-inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.ELPOfflineManager.init());
    } else {
        // DOM já carregado
        setTimeout(() => window.ELPOfflineManager.init(), 0);
    }

})();
