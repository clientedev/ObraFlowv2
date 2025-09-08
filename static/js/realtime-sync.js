/**
 * SISTEMA DE SINCRONIZAÇÃO EM TEMPO REAL
 * Garante que o app mobile PWA tenha 100% dos dados do PostgreSQL
 */

class RealTimeSync {
    constructor() {
        this.syncInterval = null;
        this.lastSyncTimestamp = null;
        this.syncFrequency = 5000; // 5 segundos
        this.retryCount = 0;
        this.maxRetries = 3;
        this.isActive = false;
        
        // Dados em cache para comparação
        this.cachedData = {};
        
        this.init();
    }
    
    init() {
        console.log('🔄 REAL-TIME SYNC: Sistema iniciado');
        
        // Detectar se é PWA e ajustar frequência
        if (this.isPWAApp()) {
            this.syncFrequency = 3000; // PWA sincroniza mais frequentemente
            console.log('📱 PWA DETECTADO: Sincronização a cada 3s');
        }
        
        // Começar sincronização imediata
        this.startSync();
        
        // Escutar eventos de focus/blur para otimizar
        window.addEventListener('focus', () => {
            console.log('📱 APP FOCADO: Forçando sincronização');
            this.forceSyncNow();
        });
        
        window.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                console.log('📱 APP VISÍVEL: Forçando sincronização');
                this.forceSyncNow();
            }
        });
        
        // Verificar conectividade
        window.addEventListener('online', () => {
            console.log('🌐 CONECTADO: Iniciando sincronização');
            this.startSync();
        });
        
        window.addEventListener('offline', () => {
            console.log('❌ OFFLINE: Pausando sincronização');
            this.stopSync();
        });
    }
    
    isPWAApp() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true ||
               document.referrer.includes('android-app://');
    }
    
    startSync() {
        if (this.isActive) return;
        
        this.isActive = true;
        console.log(`🔄 SYNC ATIVO: Polling a cada ${this.syncFrequency}ms`);
        
        // Primeira sincronização imediata
        this.syncNow();
        
        // Polling contínuo
        this.syncInterval = setInterval(() => {
            this.syncNow();
        }, this.syncFrequency);
    }
    
    stopSync() {
        if (this.syncInterval) {
            clearInterval(this.syncInterval);
            this.syncInterval = null;
        }
        this.isActive = false;
        console.log('⏸️ SYNC PAUSADO');
    }
    
    async forceSyncNow() {
        this.stopSync();
        await this.syncNow();
        this.startSync();
    }
    
    async syncNow() {
        if (!navigator.onLine) {
            console.log('❌ OFFLINE: Sync cancelado');
            return;
        }
        
        try {
            // Adicionar timestamp anti-cache
            const timestamp = Date.now();
            const url = `/api/legendas?categoria=all&_t=${timestamp}&sync=realtime`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'If-None-Match': '*'
                },
                cache: 'no-store'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.legendas) {
                const currentCount = data.legendas.length;
                const lastCount = this.cachedData.count || 0;
                
                // Verificar se houve mudanças
                const dataChanged = this.hasDataChanged(data);
                
                if (dataChanged || currentCount !== lastCount) {
                    console.log(`🔄 DADOS ATUALIZADOS: ${currentCount} legendas (era ${lastCount})`);
                    this.updateUI(data);
                    this.cachedData = {
                        count: currentCount,
                        timestamp: data.timestamp,
                        hash: this.hashData(data.legendas)
                    };
                    
                    // Dispatch evento personalizado para outros componentes
                    window.dispatchEvent(new CustomEvent('realtime-sync-update', {
                        detail: { data: data, changed: true }
                    }));
                } else {
                    console.log(`✅ DADOS OK: ${currentCount} legendas (sem mudanças)`);
                }
                
                this.retryCount = 0; // Reset retry counter on success
            }
            
        } catch (error) {
            console.error('❌ ERRO SYNC:', error);
            this.handleSyncError(error);
        }
    }
    
    hasDataChanged(newData) {
        if (!this.cachedData.hash) return true;
        
        const newHash = this.hashData(newData.legendas);
        return newHash !== this.cachedData.hash;
    }
    
    hashData(data) {
        // Criar hash simples dos dados para detectar mudanças
        return btoa(JSON.stringify(data.map(item => ({ id: item.id, texto: item.texto })))).slice(0, 10);
    }
    
    updateUI(data) {
        // Atualizar interfaces que dependem de legendas
        this.updateLegendasSelects(data.legendas);
        this.updateLegendasCounters(data);
        this.showSyncNotification(data.legendas.length);
    }
    
    updateLegendasSelects(legendas) {
        // Atualizar todos os selects de legendas na página
        const selects = document.querySelectorAll('select[data-legendas], .legendas-select, #legendasSelect');
        
        selects.forEach(select => {
            if (select && typeof window.updateLegendasSelect === 'function') {
                window.updateLegendasSelect(select, legendas);
            }
        });
    }
    
    updateLegendasCounters(data) {
        // Atualizar contadores na interface
        const counters = document.querySelectorAll('[data-legenda-count]');
        counters.forEach(counter => {
            counter.textContent = data.total;
        });
        
        // Atualizar títulos de categorias
        const categories = {};
        data.legendas.forEach(legenda => {
            categories[legenda.categoria] = (categories[legenda.categoria] || 0) + 1;
        });
        
        Object.keys(categories).forEach(cat => {
            const catElements = document.querySelectorAll(`[data-category="${cat}"]`);
            catElements.forEach(el => {
                if (el.textContent.includes('(')) {
                    el.textContent = el.textContent.replace(/\(\d+\)/, `(${categories[cat]})`);
                }
            });
        });
    }
    
    showSyncNotification(count) {
        // Notificação removida - apenas log console para debug
        console.log(`🔄 REAL-TIME SYNC: ${count} legendas fresh do PostgreSQL`);
    }
    
    handleSyncError(error) {
        this.retryCount++;
        
        if (this.retryCount <= this.maxRetries) {
            console.log(`🔄 RETRY ${this.retryCount}/${this.maxRetries} em 2s`);
            setTimeout(() => this.syncNow(), 2000);
        } else {
            console.log('❌ MAX RETRIES atingido - pausando sync por 30s');
            this.stopSync();
            setTimeout(() => {
                this.retryCount = 0;
                this.startSync();
            }, 30000);
        }
    }
    
    // Método público para forçar sync
    static forceSyncNow() {
        if (window.realtimeSync) {
            window.realtimeSync.forceSyncNow();
        }
    }
    
    // Método público para verificar status
    static getStatus() {
        if (window.realtimeSync) {
            return {
                active: window.realtimeSync.isActive,
                lastSync: window.realtimeSync.lastSyncTimestamp,
                cachedCount: window.realtimeSync.cachedData.count || 0
            };
        }
        return null;
    }
}

// Iniciar automaticamente
document.addEventListener('DOMContentLoaded', function() {
    // Aguardar 1 segundo para não interferir no carregamento
    setTimeout(() => {
        window.realtimeSync = new RealTimeSync();
        
        // Expor funções globais
        window.forceSyncNow = RealTimeSync.forceSyncNow;
        window.getSyncStatus = RealTimeSync.getStatus;
        
        console.log('🔄 REAL-TIME SYNC: Sistema pronto');
    }, 1000);
});

// CSS para notificações
const syncStyle = document.createElement('style');
syncStyle.textContent = `
    .sync-notification {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 0.9;
        }
    }
`;
document.head.appendChild(syncStyle);