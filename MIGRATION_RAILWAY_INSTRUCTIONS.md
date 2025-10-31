# 🚀 Instruções para Executar Migration no Railway

## ✅ Migration Criada com Sucesso

Foi criada a migration Alembic: `cc5ad1eaca6b_add_notification_email_push_columns.py`

Esta migration adiciona as seguintes colunas à tabela `notificacoes` no banco de dados:
- `email_enviado` (Boolean)
- `email_sucesso` (Boolean)
- `email_erro` (Text)
- `push_enviado` (Boolean)
- `push_sucesso` (Boolean)
- `push_erro` (Text)

## 📋 Como Executar no Railway

### Opção 1: Via Railway CLI (RECOMENDADO)

1. **Instale o Railway CLI** (se ainda não tiver):
   ```bash
   npm install -g @railway/cli
   ```

2. **Faça login no Railway**:
   ```bash
   railway login
   ```

3. **Conecte ao seu projeto**:
   ```bash
   railway link
   ```

4. **Execute a migration**:
   ```bash
   railway run flask db upgrade
   ```

5. **Verifique a versão atual**:
   ```bash
   railway run flask db current
   ```
   - Deve mostrar: `cc5ad1eaca6b`

### Opção 2: Via Deploy no Railway

1. **Faça commit das mudanças**:
   ```bash
   git add migrations/
   git commit -m "Add notification email and push columns migration"
   git push
   ```

2. **No Railway Dashboard**:
   - O Railway vai fazer deploy automaticamente
   - As migrations são executadas durante o deploy

3. **Adicione comando de migration** ao deploy (se necessário):
   - Vá para Settings > Deploy
   - Adicione Build Command: `flask db upgrade`

### Opção 3: Executar Manualmente via psql

Se você tiver acesso direto ao banco de dados Railway:

```bash
# Obtenha a connection string no Railway Dashboard
# Vá para PostgreSQL > Connect > Connection String

# Execute:
psql "sua_connection_string_aqui"
```

Então execute os comandos SQL manualmente (arquivo `migrations/fix_railway_notificacoes.sql`).

## ✅ Verificação Pós-Migration

Após executar a migration, verifique se funcionou:

```bash
# Via Railway CLI
railway run flask db current

# Deve mostrar:
# cc5ad1eaca6b (HEAD)
```

Ou consulte diretamente o banco:
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'notificacoes' 
ORDER BY ordinal_position;
```

Você deve ver 19 colunas no total.

## 🔍 Status das Migrations

**Development (Replit)**: ✅ Migration `cc5ad1eaca6b` já executada
**Production (Railway)**: ⏳ Aguardando execução

## ⚠️ Importante

- Esta migration é **idempotente** - verifica se as colunas já existem antes de adicionar
- É **segura** - não afeta dados existentes
- Pode ser executada **múltiplas vezes** sem causar erros

## 🎯 Resultado Esperado

Após executar a migration no Railway:
- ✅ Erro `column notificacoes.email_enviado does not exist` será resolvido
- ✅ Sistema de notificações funcionará corretamente
- ✅ Envio de emails e push notifications funcionará

## 📞 Em Caso de Problemas

Se encontrar erros, verifique:
1. Versão do Alembic instalada no Railway
2. Permissões do banco de dados
3. Logs do Railway para detalhes do erro

Para reverter a migration (se necessário):
```bash
railway run flask db downgrade
```
