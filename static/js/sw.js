importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");

/**
 * ============================================================
 * ELP OBRAS — SERVICE WORKER AVANÇADO v3.1
 * ============================================================
 * Funcionalidades:
 * - Cache-First para módulo obras/relatórios (funciona 100% offline)
 * - Pre-carregamento pós-login de todas as páginas necessárias
 * - Interceptação de POST offline → IndexedDB → sync em background
 * - Estabilidade de rede (não troca de template em oscilações)
 * - Versionamento seguro de cache
 * - Push notifications (Integrado nativamente com OneSignal)
 * ============================================================
 */

const SW_VERSION = 'elp-v3.4'; // Bump para forçar atualização do SW e carregar o importScripts
const CACHE_CORE = `elp-core-${SW_VERSION}`;      // CSS, JS, fontes, ícones
const CACHE_OBRAS = `elp-obras-${SW_VERSION}`;     // Páginas HTML de obras/relatórios
const CACHE_PREFIXES = ['elp-core-', 'elp-obras-'];

// Assets estáticos para pre-cache no install
const PRECACHE_ASSETS = [
    '/static/css/style.css',
    '/static/css/mobile.css',
    '/static/css/mobile-accessibility.css',
    '/static/css/desktop-navbar-fix.css',
    '/static/js/main.js',
    '/static/js/mobile-utils.js',
    '/static/js/offline-manager.js',
    '/static/logo_elp_navbar.png',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/manifest.json',
    // CDNs externos
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
];

// Padrões de URL do módulo obras/relatórios (criticamente offline)
const OBRAS_PATTERNS = [
    /^\/projects(\/|$)/,
    /^\/reports(\/|$)/,
];

// Rotas de autenticação — NUNCA cachear (têm CSRF tokens vinculados à sessão)
const AUTH_ROUTES = [
    /^\/login/,
    /^\/logout/,
    /^\/register/,
    /^\/auth\//,
    /^\/first-login/,
    /^\/password-reset/,
    /^\/forgot-password/,
];

// Estabilidade de rede: evitar troca de template em oscilações
let networkFailCount = 0;
const NETWORK_FAIL_THRESHOLD = 2;   // falhas consecutivas para modo offline forçado
const FORCED_OFFLINE_DURATION = 30000; // 30s de espera após falhas
let forcedOfflineUntil = 0;

console.log(`🔧 SW ${SW_VERSION}: Iniciando...`);

// ============================================================
// INSTALL — pre-cache de assets críticos
// ============================================================
self.addEventListener('install', (event) => {
    console.log(`📦 SW ${SW_VERSION}: Instalando...`);

    event.waitUntil(
        caches.open(CACHE_CORE)
            .then(cache => {
                // Cache individual para não falhar tudo por um 404
                return Promise.allSettled(
                    PRECACHE_ASSETS.map(url =>
                        cache.add(url).catch(err =>
                            console.warn(`⚠️ SW: Não foi possível cachear ${url}:`, err)
                        )
                    )
                );
            })
            .then(() => {
                console.log(`✅ SW ${SW_VERSION}: Assets pré-cacheados`);
                return self.skipWaiting(); // Ativar imediatamente
            })
    );
});

// ============================================================
// ACTIVATE — limpar caches antigos e assumir controle
// ============================================================
self.addEventListener('activate', (event) => {
    console.log(`🚀 SW ${SW_VERSION}: Ativando...`);

    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        const isOurCache = CACHE_PREFIXES.some(prefix => cacheName.startsWith(prefix));
                        const isCurrentCache = (cacheName === CACHE_CORE || cacheName === CACHE_OBRAS);

                        if (isOurCache && !isCurrentCache) {
                            console.log(`🧹 SW: Removendo cache antigo: ${cacheName}`);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log(`✅ SW ${SW_VERSION}: Ativo e controlando todos os clientes`);
                return self.clients.claim(); // Controlar abas existentes imediatamente
            })
    );
});

// ============================================================
// FETCH — interceptação inteligente por tipo de requisição
// ============================================================
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    // Ignorar: extensões de browser, outras origens
    if (url.protocol.startsWith('chrome-extension')) return;

    // *** NUNCA CACHEAR ROTAS DE AUTENTICAÇÃO ***
    // Páginas de login/logout contêm CSRF tokens vinculados à sessão.
    // Cachear essas páginas causa erros de "CSRF token expirado".
    if (isAuthRoute(url.pathname)) {
        // Network-only para rotas de auth
        return;
    }

    // Interceptar POST de relatórios offline
    if (request.method === 'POST' && isObrasUrl(url.pathname)) {
        event.respondWith(handleOfflinePost(request, url));
        return;
    }

    // Ignorar outros não-GET
    if (request.method !== 'GET') return;

    // ---- GET requests ----

    // 1. Assets estáticos e CDNs → CacheFirst
    if (isStaticAsset(url)) {
        event.respondWith(cacheFirst(request, CACHE_CORE));
        return;
    }

    // 2. Módulo obras/relatórios → CacheFirst com revalidação em background
    if (request.mode === 'navigate' && isObrasUrl(url.pathname)) {
        event.respondWith(cacheFirstWithBgRevalidation(request));
        return;
    }

    // 3. Outras navegações → NetworkFirst com fallback de cache
    if (request.mode === 'navigate') {
        event.respondWith(networkFirstWithCacheFallback(request));
        return;
    }

    // 4. API de sync dados offline → Network only (sem cache)
    if (url.pathname.startsWith('/api/offline/')) {
        // Deixa o browser lidar normalmente
        return;
    }

    // 5. Imagens e outros recursos → StaleWhileRevalidate
    if (request.destination === 'image' || request.destination === 'font') {
        event.respondWith(staleWhileRevalidate(request, CACHE_CORE));
        return;
    }
});

// ============================================================
// ESTRATÉGIAS DE CACHE
// ============================================================

/**
 * CacheFirst: Serve do cache. Se não tiver, busca na rede e cacheia.
 */
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const urlWithoutSearch = request.url.split('?')[0];
    const cached = await cache.match(urlWithoutSearch) || await cache.match(request, { ignoreSearch: true });
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) cache.put(request, response.clone());
        return response;
    } catch (err) {
        console.warn(`⚠️ SW CacheFirst: sem rede e sem cache para ${request.url}`);
        return new Response('', { status: 503 });
    }
}

/**
 * CacheFirstWithBgRevalidation: Para páginas de obras.
 * Serve IMEDIATAMENTE do cache (zero latência offline).
 * Em background, atualiza o cache se tiver rede estável.
 */
async function cacheFirstWithBgRevalidation(request) {
    const cache = await caches.open(CACHE_OBRAS);
    const urlWithoutSearch = request.url.split('?')[0];
    const cached = await cache.match(urlWithoutSearch) || await cache.match(request, { ignoreSearch: true });

    const networkFetch = fetchAndCacheIfOk(request, cache);

    if (cached) {
        // Retorna cache imediatamente + atualiza em background
        if (isNetworkStable()) {
            networkFetch.catch(() => {}); // Bg update, sem esperar
        }
        return cached;
    }

    // Sem cache: depende da rede
    try {
        return await networkFetch;
    } catch (err) {
        recordNetworkFailure();
        console.warn(`⚠️ SW: Offline e sem cache para ${request.url}`);
        // Tentar servir a página de lista como fallback (evita tela de erro)
        const fallback = await cache.match('/projects', { ignoreSearch: true }) || await cache.match('/reports', { ignoreSearch: true });
        if (fallback) return fallback;
        return syntheticErrorResponse('Página ainda não disponível offline. Conecte-se à internet uma vez para baixá-la.');
    }
}

/**
 * NetworkFirst com fallback de cache.
 */
async function networkFirstWithCacheFallback(request) {
    const cache = await caches.open(CACHE_OBRAS);

    if (!isNetworkStable()) {
        // Rede instável: vai direto para cache
        const urlWithoutSearch = request.url.split('?')[0];
        const cached = await cache.match(urlWithoutSearch) || await cache.match(request, { ignoreSearch: true });
        if (cached) return cached;
    }

    try {
        const response = await fetch(request);
        recordNetworkSuccess();
        if (response.ok) cache.put(request, response.clone());
        return response;
    } catch (err) {
        recordNetworkFailure();
        const urlWithoutSearch = request.url.split('?')[0];
        const cached = await cache.match(urlWithoutSearch) || await cache.match(request, { ignoreSearch: true });
        if (cached) return cached;
        return syntheticErrorResponse('Você está offline e esta página não foi baixada.');
    }
}

/**
 * StaleWhileRevalidate: Retorna cache, mas atualiza no background.
 */
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const urlWithoutSearch = request.url.split('?')[0];
    const cached = await cache.match(urlWithoutSearch) || await cache.match(request, { ignoreSearch: true });

    const networkUpdate = fetch(request).then(response => {
        if (response.ok) cache.put(request, response.clone());
        return response;
    }).catch(() => null);

    return cached || networkUpdate;
}

// ============================================================
// INTERCEPTAÇÃO DE POST OFFLINE
// ============================================================

/**
 * Intercepta POST em páginas de obras quando offline.
 * Salva via IDB (via postMessage para o cliente) e retorna resposta sintética.
 */
async function handleOfflinePost(request, url) {
    // Se tivermos rede estável, deixa passar normalmente
    if (isNetworkStable()) {
        try {
            const response = await fetch(request);
            recordNetworkSuccess();
            return response;
        } catch (err) {
            recordNetworkFailure();
            // Cai para tratamento offline
        }
    }

    // Offline: capturar body do formulário
    try {
        const formDataText = await request.text();
        const offlineId = `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Notificar todos os clientes para salvar no IndexedDB
        const clients = await self.clients.matchAll({ type: 'window' });
        clients.forEach(client => {
            client.postMessage({
                type: 'SAVE_OFFLINE_FORM',
                payload: {
                    offlineId,
                    url: url.pathname,
                    method: 'POST',
                    formData: formDataText,
                    timestamp: Date.now(),
                }
            });
        });

        // Registrar background sync
        if (self.registration.sync) {
            try {
                await self.registration.sync.register('sync-offline-reports');
            } catch (e) {
                console.warn('⚠️ Background sync não disponível:', e);
            }
        }

        // Resposta sintética de sucesso — redireciona para lista
        return new Response(null, {
            status: 302,
            headers: {
                'Location': url.pathname.includes('/reports') ? '/reports' : '/projects',
                'X-Offline-Save': offlineId,
            }
        });

    } catch (err) {
        console.error('❌ SW: Erro ao capturar POST offline:', err);
        return new Response(JSON.stringify({ success: false, error: 'Erro offline' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// ============================================================
// BACKGROUND SYNC — enviar relatórios pendentes
// ============================================================
self.addEventListener('sync', (event) => {
    console.log(`🔄 SW: Background sync disparado: ${event.tag}`);

    if (event.tag === 'sync-offline-reports') {
        event.waitUntil(syncPendingReports());
    }
});

async function syncPendingReports() {
    const clients = await self.clients.matchAll({ type: 'window' });
    clients.forEach(client => {
        client.postMessage({ type: 'TRIGGER_SYNC_PENDING' });
    });
    console.log(`✅ SW: Solicitado sync de relatórios pendentes para ${clients.length} cliente(s)`);
}

// ============================================================
// CACHE WARMUP — pré-carregamento pós-login
// ============================================================
async function triggerCacheWarmup(csrfToken) {
    console.log('🔥 SW: Iniciando Cache Warmup pós-login...');

    try {
        // 1. Buscar lista de URLs a cachear
        const pagesResp = await fetch('/api/offline/pages', {
            credentials: 'include',
            headers: { 'X-CSRFToken': csrfToken || '' }
        });

        if (!pagesResp.ok) {
            console.warn('⚠️ SW: Não foi possível buscar lista de páginas offline');
            return;
        }

        const pagesData = await pagesResp.json();
        const urls = pagesData.urls || [];

        console.log(`📥 SW: Cache Warmup — ${urls.length} páginas para pre-cachear`);

        // 2. Cachear cada URL de forma sequencial (para não sobrecarregar)
        const cache = await caches.open(CACHE_OBRAS);
        let success = 0;
        let errors = 0;

        for (const url of urls) {
            // NUNCA cachear rotas de autenticação (evita erro CSRF)
            if (isAuthRoute(new URL(url, self.location.origin).pathname)) continue;
            
            try {
                const response = await fetch(url, { credentials: 'include' });
                if (response.ok && response.status !== 204) {
                    await cache.put(url, response);
                    success++;
                }
                // Pequena pausa para não travar o browser
                await new Promise(r => setTimeout(r, 50));
            } catch (err) {
                errors++;
                // Continua tentando as próximas
            }
        }

        console.log(`✅ SW: Cache Warmup concluído — ${success} ok, ${errors} erros`);

        // 3. Notificar clientes que o cache está pronto
        const clients = await self.clients.matchAll({ type: 'window' });
        clients.forEach(client => {
            client.postMessage({
                type: 'CACHE_WARMUP_COMPLETE',
                stats: { success, errors, total: urls.length }
            });
        });

    } catch (err) {
        console.error('❌ SW: Cache Warmup falhou:', err);
    }
}

// ============================================================
// MESSAGES — comunicação com a página
// ============================================================
self.addEventListener('message', (event) => {
    const { type, payload } = event.data || {};

    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'TRIGGER_CACHE_WARMUP':
            triggerCacheWarmup(payload?.csrfToken);
            break;

        case 'SYNC_PENDING':
            syncPendingReports();
            break;

        case 'CHECK_CACHE_STATUS':
            checkCacheStatus().then(status => {
                event.source?.postMessage({ type: 'CACHE_STATUS', status });
            });
            break;
    }
});

// ============================================================
// HELPERS
// ============================================================

function isObrasUrl(pathname) {
    return OBRAS_PATTERNS.some(pattern => pattern.test(pathname));
}

function isAuthRoute(pathname) {
    return AUTH_ROUTES.some(pattern => pattern.test(pathname));
}

function isStaticAsset(url) {
    return (
        url.pathname.startsWith('/static/') ||
        url.href.includes('cdn.jsdelivr.net') ||
        url.href.includes('cdnjs.cloudflare.com') ||
        url.href.includes('fonts.googleapis.com') ||
        url.href.includes('fonts.gstatic.com')
    );
}

function isNetworkStable() {
    if (Date.now() < forcedOfflineUntil) return false;
    return networkFailCount < NETWORK_FAIL_THRESHOLD;
}

function recordNetworkSuccess() {
    networkFailCount = 0;
    forcedOfflineUntil = 0;
}

function recordNetworkFailure() {
    networkFailCount++;
    if (networkFailCount >= NETWORK_FAIL_THRESHOLD) {
        forcedOfflineUntil = Date.now() + FORCED_OFFLINE_DURATION;
        console.warn(`⚠️ SW: ${networkFailCount} falhas consecutivas — modo cache forçado por ${FORCED_OFFLINE_DURATION / 1000}s`);
    }
}

async function fetchAndCacheIfOk(request, cache) {
    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
}

async function checkCacheStatus() {
    const obrasCacheKeys = await caches.open(CACHE_OBRAS).then(c => c.keys());
    const coreCacheKeys = await caches.open(CACHE_CORE).then(c => c.keys());
    return {
        obras_pages: obrasCacheKeys.length,
        core_assets: coreCacheKeys.length,
        version: SW_VERSION,
    };
}

function syntheticErrorResponse(message) {
    const html = `<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>ELP — Carregando...</title>
<meta http-equiv="refresh" content="5">
<style>body{display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:sans-serif;background:#f8f9fa;}
.box{text-align:center;padding:2rem;}</style></head>
<body><div class="box">
<p style="font-size:2rem">⏳</p>
<h2>Aguardando conexão...</h2>
<p>${message}</p>
<p><small>Esta página será recarregada automaticamente.</small></p>
</div></body></html>`;

    return new Response(html, {
        status: 200,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
}
