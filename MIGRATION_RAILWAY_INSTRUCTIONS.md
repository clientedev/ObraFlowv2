# Instruções para Corrigir o Banco de Dados no Railway

## Problema
O banco de dados de produção no Railway está com a tabela `notificacoes` desatualizada, faltando as seguintes colunas:
- `email_enviado`
- `email_sucesso`
- `email_erro`
- `push_enviado`
- `push_sucesso`
- `push_erro`

## Solução

### Opção 1: Executar via Railway Dashboard (RECOMENDADO)

1. Acesse o dashboard do Railway: https://railway.app
2. Selecione seu projeto
3. Clique no serviço do PostgreSQL
4. Vá para a aba "Query"
5. Cole o conteúdo do arquivo `migrations/fix_railway_notificacoes.sql`
6. Execute o script
7. Verifique se todas as colunas foram adicionadas

### Opção 2: Executar via CLI do Railway

```bash
# 1. Instale o Railway CLI se ainda não tiver
npm install -g @railway/cli

# 2. Faça login
railway login

# 3. Link com seu projeto
railway link

# 4. Execute a migration
railway run psql -f migrations/fix_railway_notificacoes.sql
```

### Opção 3: Usar psql diretamente

Se você tiver as credenciais do banco Railway:

```bash
psql "postgresql://usuario:senha@host:porta/database" -f migrations/fix_railway_notificacoes.sql
```

## Verificação

Após executar a migration, execute esta query para verificar:

```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'notificacoes' 
ORDER BY ordinal_position;
```

Você deve ver 19 colunas no total, incluindo todas as colunas de email e push.

## Observações Importantes

- ⚠️ Este script é **idempotente** - pode ser executado múltiplas vezes sem causar erros
- ✅ Ele verifica se cada coluna já existe antes de tentar adicioná-la
- 🔒 Não afeta dados existentes na tabela
- 📝 As novas colunas terão valores padrão para registros existentes:
  - `email_enviado`: `FALSE`
  - `push_enviado`: `FALSE`
  - Outras colunas: `NULL`

## Próximos Passos

Depois de executar a migration no Railway:
1. Reinicie o servidor no Railway (se necessário)
2. Teste o sistema de notificações
3. Verifique se não há mais erros relacionados a `email_enviado`
