/**
 * ============================================================
 * ELP OFFLINE MANAGER v1.0
 * ============================================================
 * Gerencia dados offline usando IndexedDB:
 * - Armazena projetos, relatórios, legendas localmente
 * - Intercepta formulários de relatório quando offline
 * - Sincroniza dados pendentes quando volta online
 * - Monitora estabilidade da conexão
 * ============================================================
 */

(function () {
    'use strict';

    const DB_NAME = 'elp-offline-db';
    const DB_VERSION = 1;
    let db = null;

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
            const req = Array.isArray(data)
                ? data.map(item => store.put(item))
                : [store.put(data)];

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
            status: 'pending'
        };

        await dbPut('pending_sync', record);
        console.log(`💾 IndexedDB: Relatório offline salvo como ${record.offline_id}`);

        // Notificar SW para registrar background sync
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({ type: 'SYNC_PENDING' });
        }

        return record.offline_id;
    }

    // ============================================================
    // Sincronizar relatórios pendentes com servidor
    // ============================================================
    async function syncPendingReports() {
        await initDB();
        const pending = await dbGetAll('pending_sync');

        if (!pending || pending.length === 0) {
            console.log('ℹ️ OfflineManager: Nenhum relatório pendente');
            return { synced: 0, errors: 0 };
        }

        console.log(`🔄 OfflineManager: Sincronizando ${pending.length} relatório(s) pendente(s)...`);

        let synced = 0;
        let errors = 0;

        for (const record of pending) {
            try {
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
                    await dbDelete('pending_sync', record.offline_id);
                    synced++;
                    console.log(`✅ Relatório ${record.offline_id} sincronizado → id=${result.relatorio_id}`);
                } else {
                    errors++;
                    console.warn(`⚠️ Falha ao sincronizar ${record.offline_id}:`, result.error);
                }

            } catch (err) {
                errors++;
                console.warn(`⚠️ Erro de rede ao sincronizar ${record.offline_id}:`, err);
            }
        }

        console.log(`✅ OfflineManager: Sync concluído — ${synced} ok, ${errors} erros`);

        if (synced > 0) {
            // Notificar página silenciosamente (sem reload)
            window.dispatchEvent(new CustomEvent('elp:reports-synced', {
                detail: { synced, errors }
            }));
        }

        return { synced, errors };
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
        const msg = 'Relatório salvo localmente. Será sincronizado quando houver conexão.';
        if (typeof showToast === 'function') {
            showToast(msg, 'warning', 6000);
        } else {
            console.log('✅ ' + msg);
            alert(msg);
        }

        // Navegar para lista de relatórios após breve delay
        setTimeout(() => {
            window.location.href = '/reports';
        }, 2000);
    }

    function showOfflineError() {
        const msg = 'Erro ao salvar offline. Tente novamente.';
        if (typeof showToast === 'function') {
            showToast(msg, 'error', 6000);
        } else {
            alert(msg);
        }
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
                await syncPendingReports();
                await populateFromServer(); // Atualizar dados locais
            }, 3000);
        });

        window.addEventListener('offline', () => {
            console.log('📵 OfflineManager: Conexão perdida — modo cache ativo');
            clearTimeout(syncTimer);
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
            console.error('❌ OfflineManager: Falha ao registrar Service Worker:', err);
        }
    }

    // ============================================================
    // Trigger de Cache Warmup pós-login
    // ============================================================
    async function triggerCacheWarmupIfLoggedIn() {
        // Verificar se usuário está logado via variável global injetada pelo servidor
        const isLoggedIn = window.ELP_USER_LOGGED_IN === true;
        if (!isLoggedIn) return;

        // Verificar se já fez warmup recentemente (últimas 2h)
        const lastWarmup = localStorage.getItem('elp_last_warmup');
        const TWO_HOURS = 2 * 60 * 60 * 1000;

        if (lastWarmup && (Date.now() - parseInt(lastWarmup)) < TWO_HOURS) {
            console.log('ℹ️ OfflineManager: Cache ainda recente, warmup ignorado');
            return;
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
    // API pública
    // ============================================================
    window.ELPOfflineManager = {
        init: async function () {
            await initDB();
            setupSWMessageListener();
            setupConnectionMonitor();
            interceptReportForms();

            // Registrar SW e disparar warmup após tudo pronto
            await registerServiceWorker();

            // Pequeno delay para o SW ficar pronto
            setTimeout(async () => {
                await triggerCacheWarmupIfLoggedIn();
            }, 1500);

            console.log('✅ OfflineManager: Inicializado completamente');
        },
        savePendingReport,
        syncPendingReports,
        populateFromServer,
        getProjects: () => initDB().then(() => dbGetAll('projects')),
        getReports: () => initDB().then(() => dbGetAll('reports')),
        getPendingSync: () => initDB().then(() => dbGetAll('pending_sync')),
        getLegendas: () => initDB().then(() => dbGetAll('legendas')),
        triggerWarmup: triggerCacheWarmupIfLoggedIn,
    };

    // Auto-inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => window.ELPOfflineManager.init());
    } else {
        // DOM já carregado
        setTimeout(() => window.ELPOfflineManager.init(), 0);
    }

})();
