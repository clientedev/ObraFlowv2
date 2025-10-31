# 🚀 Instruções para Aplicar Migration no Railway

## Problema Identificado
A coluna `link_destino` não existe na tabela `notificacoes` do banco de dados PostgreSQL de produção no Railway, causando erro 500 no endpoint `/api/notificacoes`.

## Solução: Migration Criada
Foi criada a migration `20251031_1420_add_link_destino_to_notificacoes.py` que adiciona a coluna faltante.

---

## 📋 Opção 1: Aplicar via Railway CLI (Recomendado)

### Pré-requisitos
- Railway CLI instalado: `npm install -g @railway/cli`
- Estar logado: `railway login`

### Passos:

1. **Conectar ao projeto Railway:**
   ```bash
   railway link
   ```

2. **Executar a migration:**
   ```bash
   railway run alembic upgrade head
   ```

3. **Verificar se a migration foi aplicada:**
   ```bash
   railway run alembic current
   ```
   
   Deve mostrar: `20251031_1420` (head)

---

## 📋 Opção 2: Aplicar via Deploy Automático

### Modificar o Procfile ou script de inicialização

Se você usa Procfile, adicione o comando de migration antes de iniciar o servidor:

```procfile
release: alembic upgrade head
web: gunicorn --bind=0.0.0.0:$PORT --reuse-port main:app
```

Ou se usa `start.sh`, adicione no início:

```bash
#!/bin/bash
echo "🔄 Aplicando migrations do banco de dados..."
alembic upgrade head

echo "🚀 Iniciando servidor..."
gunicorn --bind=0.0.0.0:$PORT --reuse-port main:app
```

Depois faça o commit e push:
```bash
git add .
git commit -m "feat: add link_destino column migration"
git push
```

O Railway aplicará automaticamente a migration no próximo deploy.

---

## 📋 Opção 3: SQL Direto (Solução Rápida)

Se você tem acesso direto ao banco de dados PostgreSQL do Railway:

```sql
-- Verificar se a coluna já existe
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'notificacoes' AND column_name = 'link_destino';

-- Se não existir, adicionar a coluna
ALTER TABLE notificacoes 
ADD COLUMN IF NOT EXISTS link_destino VARCHAR(255);

-- Verificar que foi adicionada
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'notificacoes' AND column_name = 'link_destino';
```

**⚠️ Atenção:** Mesmo aplicando via SQL direto, execute `alembic stamp head` depois para manter o histórico de migrations sincronizado.

---

## ✅ Verificação Final

Após aplicar a migration, teste o endpoint:

```bash
curl https://elpconsultoria.pro/api/notificacoes \
  -H "Cookie: session=SEU_SESSION_ID" \
  -H "Accept: application/json"
```

**Resultado esperado:** HTTP 200 OK com lista de notificações.

---

## 🔍 Troubleshooting

### Erro: "Target database is not up to date"
```bash
alembic stamp head
alembic upgrade head
```

### Erro: "Multiple heads detected"
```bash
alembic heads
alembic merge heads -m "merge migrations"
alembic upgrade head
```

### Verificar todas as migrations aplicadas:
```bash
alembic history
```

### Reverter esta migration (se necessário):
```bash
alembic downgrade -1
```

---

## 📝 Notas Importantes

1. **Backup**: O Railway faz backup automático, mas é sempre bom ter cautela
2. **Downtime**: A migration é rápida (< 1 segundo) e não causa downtime
3. **Reversível**: A migration tem função `downgrade()` caso precise reverter
4. **Idempotente**: A migration verifica se a coluna já existe antes de adicionar

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do Railway: `railway logs`
2. Verifique o estado das migrations: `railway run alembic current`
3. Consulte a documentação do Alembic: https://alembic.sqlalchemy.org/
