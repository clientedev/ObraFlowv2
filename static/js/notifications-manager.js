class NotificationsManager {
    constructor() {
        this.notificacoes = [];
        this.drawer = null;
        this.badge = null;
        this.bell = null;
        this.notificationsList = null;
        this.unreadCountSpan = null;
        this.markAllReadBtn = null;
        this.refreshInterval = null;
        
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.drawer = document.getElementById('notificationsDrawer');
            this.badge = document.getElementById('notificationBadge');
            this.bell = document.getElementById('notificationBell');
            this.notificationsList = document.getElementById('notificationsList');
            this.unreadCountSpan = document.getElementById('unreadCount');
            this.markAllReadBtn = document.getElementById('markAllReadBtn');
            
            if (!this.bell) {
                console.debug('ℹ️ Sistema de notificações: aguardando login do usuário');
                return;
            }
            
            this.bell.addEventListener('click', (e) => {
                e.preventDefault();
                this.openDrawer();
            });
            
            if (this.markAllReadBtn) {
                this.markAllReadBtn.addEventListener('click', () => {
                    this.markAllAsRead();
                });
            }
            
            this.carregarNotificacoes();
            
            this.refreshInterval = setInterval(() => {
                this.carregarNotificacoes(true);
            }, 30000);
            
            console.log('✅ Notifications Manager inicializado');
        });
    }
    
    async carregarNotificacoes(silent = false) {
        try {
            const response = await fetch('/api/notificacoes', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.notificacoes = data.notificacoes;
                this.atualizarContador(data.nao_lidas);
                
                if (!silent) {
                    this.renderizarNotificacoes();
                }
                
                console.log(`✅ ${data.total} notificações carregadas (${data.nao_lidas} não lidas)`);
            } else {
                // Se falhar, zerar o contador
                this.atualizarContador(0);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar notificações:', error);
            // Em caso de erro, zerar o contador
            this.atualizarContador(0);
        }
    }
    
    atualizarContador(count) {
        if (!this.badge) return;
        
        if (count > 0) {
            this.badge.textContent = count > 99 ? '99+' : count;
            this.badge.style.display = 'inline-block';
        } else {
            this.badge.style.display = 'none';
        }
        
        if (this.unreadCountSpan) {
            this.unreadCountSpan.textContent = count;
        }
    }
    
    renderizarNotificacoes() {
        if (!this.notificationsList) return;
        
        if (this.notificacoes.length === 0) {
            this.notificationsList.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-bell-slash fa-3x mb-3 d-block"></i>
                    <p>Nenhuma notificação</p>
                </div>
            `;
            return;
        }
        
        this.notificationsList.innerHTML = '';
        
        this.notificacoes.forEach(notif => {
            const item = this.criarItemNotificacao(notif);
            this.notificationsList.appendChild(item);
        });
    }
    
    criarItemNotificacao(notif) {
        const div = document.createElement('div');
        div.className = `list-group-item list-group-item-action ${notif.status === 'nao_lida' ? 'bg-light' : ''}`;
        div.style.cursor = 'pointer';
        div.dataset.notifId = notif.id;
        
        const timeAgo = this.formatarTempo(notif.created_at);
        
        div.innerHTML = `
            <div class="d-flex w-100 justify-content-between align-items-start">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-1">
                        <span class="me-2" style="font-size: 1.2rem;">${notif.icone}</span>
                        <strong>${notif.titulo}</strong>
                        ${notif.status === 'nao_lida' ? '<span class="badge bg-primary ms-2" style="font-size: 0.65rem;">Nova</span>' : ''}
                    </div>
                    <p class="mb-1 small text-muted">${notif.mensagem}</p>
                    <small class="text-muted">
                        <i class="far fa-clock me-1"></i>${timeAgo}
                    </small>
                </div>
            </div>
        `;
        
        div.addEventListener('click', () => {
            this.marcarComoLida(notif.id);
            
            if (notif.link_destino) {
                window.location.href = notif.link_destino;
            }
        });
        
        return div;
    }
    
    formatarTempo(isoString) {
        const data = new Date(isoString);
        const agora = new Date();
        const diff = Math.floor((agora - data) / 1000);
        
        if (diff < 60) return 'Agora mesmo';
        if (diff < 3600) return `${Math.floor(diff / 60)} min atrás`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} h atrás`;
        if (diff < 604800) return `${Math.floor(diff / 86400)} dias atrás`;
        
        return data.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    async marcarComoLida(notifId) {
        try {
            const response = await fetch('/api/notificacoes/marcar-lida', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ notificacao_id: notifId })
            });
            
            if (response.ok) {
                await this.carregarNotificacoes();
            }
        } catch (error) {
            console.error('❌ Erro ao marcar notificação como lida:', error);
        }
    }
    
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notificacoes/marcar-todas-lidas', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                await this.carregarNotificacoes();
                console.log('✅ Todas as notificações marcadas como lidas');
            }
        } catch (error) {
            console.error('❌ Erro ao marcar todas como lidas:', error);
        }
    }
    
    openDrawer() {
        if (this.drawer) {
            const bsOffcanvas = new bootstrap.Offcanvas(this.drawer);
            bsOffcanvas.show();
            this.carregarNotificacoes();
        }
    }
    
    getCsrfToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

const notificationsManager = new NotificationsManager();
