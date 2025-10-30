# 🚂 Guia de Deploy no Railway - Sistema de Rastreamento de Obras

## 📋 Arquivos de Configuração Criados

Este projeto está **pronto para deploy no Railway** com os seguintes arquivos:

### 1. **start.sh** - Script de Inicialização
- ✅ Executa migrações Alembic automaticamente (`alembic upgrade head`)
- ✅ Inicia servidor Gunicorn com 4 workers
- ✅ Logs completos de migração e servidor

### 2. **Dockerfile** - Container de Produção
- ✅ Python 3.11-slim otimizado
- ✅ Dependências WeasyPrint (PDF) instaladas
- ✅ PostgreSQL client (libpq-dev) incluído
- ✅ Health check configurado

### 3. **railway.json** - Configuração Railway
- ✅ Build com Dockerfile
- ✅ Health check em `/health`
- ✅ Restart automático em caso de falha
- ✅ Timeout estendido para migrações

### 4. **Procfile** - Configuração Alternativa
- ✅ Gunicorn com 4 workers
- ✅ Timeout de 120 segundos

---

## 🚀 Como Fazer Deploy no Railway

### **Passo 1: Configurar Variáveis de Ambiente**

No painel do Railway, configure as seguintes variáveis:

#### **Obrigatórias:**
```bash
DATABASE_URL=postgresql://user:password@host:port/database
SESSION_SECRET=your-secret-key-here
```

#### **E-mail (Opcional - para envio de relatórios):**
```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu-email@gmail.com
MAIL_PASSWORD=sua-senha-de-app
MAIL_DEFAULT_SENDER=seu-email@gmail.com
MAIL_USE_TLS=true
```

#### **Criptografia (Opcional - para senhas de e-mail):**
```bash
EMAIL_PASSWORD_ENCRYPTION_KEY=<gere-com-comando-abaixo>
```

Para gerar a chave de criptografia:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### **Passo 2: Conectar Banco PostgreSQL**

O Railway detectará automaticamente o `DATABASE_URL` se você:

1. **Criar um serviço PostgreSQL** no Railway
2. O Railway automaticamente criará a variável `DATABASE_URL`
3. **Não é necessário configurar manualmente** se usar o PostgreSQL do Railway

---

### **Passo 3: Deploy**

1. **Conecte seu repositório GitHub** ao Railway
2. O Railway detectará o `Dockerfile` e fará o build automaticamente
3. Durante o deploy, o `start.sh` será executado:
   - ✅ Executará `alembic upgrade head` (migrações)
   - ✅ Criará tabelas automaticamente se não existirem
   - ✅ Criará usuário admin padrão
   - ✅ Iniciará servidor Gunicorn

---

## 🔧 Migração Atual do Alembic

**Versão atual:** `3d4ec2dfeefe` (HEAD)

**Última migração:** `add_fcm_token_to_users`

### Migrações incluídas:
1. ✅ Tabelas base (users, projetos, relatorios, etc.)
2. ✅ Sistema de notificações
3. ✅ Aprovadores globais e temporários
4. ✅ Checklist por obra
5. ✅ Campo `fcm_token` para push notifications
6. ✅ Metadados de imagens (hash, content_type, size)
7. ✅ Numeração customizada por projeto
8. ✅ Acompanhantes de relatórios (JSONB)

---

## 📊 Estrutura de Pastas

```
/app
├── migrations/          # Migrações Alembic
│   └── versions/       # Histórico de migrações
├── static/             # Arquivos estáticos (CSS, JS, imagens)
├── templates/          # Templates Jinja2
├── uploads/            # Upload de arquivos
├── app.py              # Configuração Flask
├── models.py           # Modelos SQLAlchemy
├── routes.py           # Rotas da aplicação
├── main.py             # Entry point
├── start.sh            # Script de inicialização
├── Dockerfile          # Container de produção
├── railway.json        # Configuração Railway
└── requirements.txt    # Dependências Python
```

---

## 🏥 Health Check

O Railway verificará a saúde da aplicação em:

- **URL:** `http://seu-app.railway.app/health`
- **Intervalo:** 30 segundos
- **Timeout:** 300 segundos
- **Retries:** 15 tentativas

**Certifique-se de ter uma rota `/health` no seu código!**

---

## 🔐 Credenciais Padrão

Após o primeiro deploy, use:

- **Usuário:** `admin`
- **Senha:** `admin123`

**⚠️ IMPORTANTE:** Altere a senha do admin imediatamente após o primeiro login!

---

## 🐛 Troubleshooting

### **Erro: "column users.fcm_token does not exist"**
- ✅ **JÁ CORRIGIDO!** O `start.sh` executa `alembic upgrade head` automaticamente

### **Erro: "Database connection failed"**
- Verifique se `DATABASE_URL` está configurado
- Teste a conexão: `psql $DATABASE_URL`

### **Erro: "Migration failed"**
- O `start.sh` continua mesmo se a migração falhar (tabelas podem já existir)
- Verifique logs: `railway logs`

### **Servidor não inicia**
- Verifique variável `PORT` (Railway define automaticamente)
- Logs: `railway logs --tail`

---

## 📝 Logs Úteis

Para ver logs em tempo real:

```bash
railway logs --tail
```

Procure por:
- `🚂 RAILWAY DEPLOYMENT - Starting...`
- `✅ Migrations completed successfully`
- `🚀 Starting Gunicorn server...`

---

## 🎯 Próximos Passos

1. ✅ Arquivos de deploy criados
2. ⬜ Configure variáveis de ambiente no Railway
3. ⬜ Conecte banco PostgreSQL
4. ⬜ Faça push para GitHub
5. ⬜ Deploy automático no Railway
6. ⬜ Altere senha do admin

---

## 🆘 Suporte

Em caso de problemas:

1. Verifique logs: `railway logs --tail`
2. Teste migração local: `alembic upgrade head`
3. Verifique variáveis de ambiente
4. Consulte documentação Railway: https://docs.railway.app

---

**✅ Sistema pronto para deploy no Railway com PostgreSQL!**
