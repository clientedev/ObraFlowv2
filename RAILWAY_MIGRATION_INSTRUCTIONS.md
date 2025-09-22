# 🚂 Instruções para Migração no Railway

Este documento contém as instruções completas para executar as migrações Alembic no ambiente Railway, especificamente para adicionar suporte a armazenamento de imagens em PostgreSQL via campos BYTEA.

## 📋 Resumo das Migrações

As seguintes migrações serão aplicadas:
1. **001** → **42776d8c4e78**: Add ChecklistObra and ProjetoChecklistConfig models
2. **42776d8c4e78** → **add_updated_at_relatorios**: Add updated_at to relatorios table
3. **add_updated_at_relatorios** → **add_numero_ordem_legendas**: Add numero_ordem to legendas
4. **add_numero_ordem_legendas** → **add_imagem_fotos_tables**: **[PRINCIPAL]** Add campos BYTEA para imagens

## 🎯 Migração Principal: Campos BYTEA para Imagens

A migração `add_imagem_fotos_tables` adiciona:
- `imagem` (BYTEA) na tabela `fotos_relatorio`
- `imagem` (BYTEA) na tabela `fotos_relatorios_express`

Isso permite armazenar imagens diretamente no PostgreSQL em vez de apenas filenames.

## 🛠️ Comandos para Railway

### Método 1: Via Railway CLI (Recomendado)

```bash
# 1. Fazer login no Railway
railway login

# 2. Conectar ao projeto
railway link [YOUR_PROJECT_ID]

# 3. Executar migrações via shell Railway
railway shell

# 4. Dentro do shell Railway, executar:
alembic upgrade head

# 5. Verificar se a migração foi aplicada
alembic current
alembic history --verbose
```

### Método 2: Via Railway Web Interface

1. **Acesse o Railway Dashboard**
2. **Navegue até seu projeto**
3. **Vá em "Deployments" → "Console"**
4. **Execute os comandos:**

```bash
alembic upgrade head
```

### Método 3: Via Variables de Ambiente

Adicione no Railway a variável de ambiente:
```
RAILWAY_RUN_MIGRATIONS=true
```

E modifique o script de inicialização para executar as migrações automaticamente.

## 🔍 Verificação da Migração

Após executar as migrações, verifique se funcionou:

```sql
-- Verificar se as colunas BYTEA foram criadas
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name IN ('fotos_relatorio', 'fotos_relatorios_express') 
AND column_name = 'imagem';
```

Resultado esperado:
```
column_name | data_type | is_nullable
------------|-----------|------------
imagem      | bytea     | YES
imagem      | bytea     | YES
```

## ⚠️ Pontos Importantes

1. **Backup**: As migrações são seguras (só adicionam colunas), mas sempre faça backup antes
2. **Downtime**: Estas migrações são rápidas e não causam downtime significativo
3. **Compatibilidade**: O sistema já está preparado para usar tanto filesystem quanto database
4. **Rollback**: Se necessário, use `alembic downgrade [revision]`

## 🐛 Troubleshooting

### Error: "alembic_version table doesn't exist"
```bash
# Inicializar Alembic no banco
alembic stamp head
```

### Error: "revision not found"
```bash
# Verificar se todas as migrações estão no diretório
ls -la migrations/versions/
```

### Error: "database connection failed"
```bash
# Verificar se DATABASE_URL está configurado
echo $DATABASE_URL
```

## 📈 Benefícios Após a Migração

1. **Imagens no Banco**: Dados binários salvos diretamente no PostgreSQL
2. **Backup Simplificado**: Imagens incluídas no backup do banco
3. **Consistência**: Não há risco de dessincronia entre filesystem e database
4. **Escalabilidade**: Funciona melhor em ambientes multi-instância
5. **Fallback**: Sistema mantém compatibilidade com filesystem

## 🔧 Configuração de Ambiente

Certifique-se de que estas variáveis estão configuradas no Railway:

```env
DATABASE_URL=postgresql://...
FLASK_ENV=production
FLASK_APP=main.py
```

## ✅ Validação Final

Após a migração, teste:
1. **Upload de fotos** em relatórios
2. **Visualização de imagens** via `/imagens/<id>`
3. **Sistema de fallback** (imagens antigas no filesystem)
4. **Performance** das consultas de imagem

---

**Data de Criação**: 2025-09-22  
**Última Atualização**: 2025-09-22  
**Versão**: 1.0