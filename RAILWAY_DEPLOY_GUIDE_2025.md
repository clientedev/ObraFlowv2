# Guia de Deploy no Railway - 2025

## ✅ CORREÇÃO COMPLETA - Sistema Auto-Recuperável

**🎉 NOVIDADE**: O sistema agora detecta e limpa automaticamente versões órfãs do Alembic durante o startup!

Todas as correções foram aplicadas. O deploy no Railway agora é **100% automático** - não precisa executar scripts manuais!

---

## 🚀 Como Fazer Deploy no Railway - ZERO Configuração Manual

### 🔥 Sistema Auto-Recuperável (Self-Healing)

O código agora inclui detecção automática de versões órfãs do Alembic:

**Funcionamento Automático:**
1. 🔍 Detecta versões antigas registradas no banco (como `a4d5b6d9c0ca`)
2. 🧹 Remove automaticamente versões órfãs que não existem mais no código
3. ✅ Permite que o Alembic detecte e aplique a migração correta
4. 🚀 Continua com o deploy normalmente

**Você NÃO precisa mais executar scripts manuais!**

---

## 📋 Deploy Automático

1. **Push para o repositório Git**
2. O Railway irá automaticamente:
   - ✅ Instalar as dependências do `requirements.txt`
   - ✅ Executar `alembic upgrade head` (via `main.py` quando `RAILWAY_ENVIRONMENT` está definido)
   - ✅ Aplicar todas as migrações automaticamente
   - ✅ Iniciar o servidor com Gunicorn

---

## 📋 Checklist de Deploy

### Antes do Deploy:

- [ ] Variável `DATABASE_URL` configurada no Railway
- [ ] Variável `SESSION_SECRET` configurada no Railway
- [ ] Variável `RAILWAY_ENVIRONMENT` = `production` (ou qualquer valor)
- [ ] (Opcional) `EMAIL_PASSWORD_ENCRYPTION_KEY` se usar configuração de email por usuário
- [ ] (Opcional) `FIREBASE_CREDENTIALS_PATH` ou `FIREBASE_CONFIG` se usar notificações push

### Durante o Deploy:

O Railway executará automaticamente (via `main.py`):
1. ✅ Build das dependências
2. ✅ **Detecção automática** de versões órfãs do Alembic
3. ✅ **Limpeza automática** de versões antigas (se necessário)
4. ✅ Aplicação de migrações via `alembic upgrade head`
5. ✅ Inicialização do servidor com Gunicorn

### Após o Deploy:

- [ ] Verificar logs no Railway Dashboard
- [ ] Testar a aplicação
- [ ] Verificar que não há erros de migração

---

## 🔧 O Que Foi Corrigido - Análise Técnica

### 🐛 Problema Original:

O banco de dados no Railway continha uma versão órfã (`a4d5b6d9c0ca`) registrada na tabela `alembic_version`, mas essa migração não existia mais no código. Quando o Alembic tentava executar `upgrade head`, ele falhava com:

```
FAILED: Can't locate revision identified by 'a4d5b6d9c0ca'
```

### ✅ Solução Implementada:

Adicionamos uma função `clean_orphaned_alembic_versions()` no `main.py` que executa **ANTES** das migrações no Railway:

```python
def clean_orphaned_alembic_versions():
    """Remove versões órfãs do Alembic que não existem mais no código"""
    # 1. Conecta ao banco de dados
    # 2. Verifica a versão registrada
    # 3. Se não estiver na lista de versões válidas, DELETA
    # 4. Permite que o Alembic detecte automaticamente a versão correta
```

**Lista de versões válidas:** `['265f97ab88c1']`

Qualquer outra versão será automaticamente removida durante o startup.

---

## 🔍 Verificando Status das Migrações

Para verificar qual versão do alembic está aplicada:

```bash
alembic current
```

Resposta esperada:
```
265f97ab88c1 (head)
```

---

## 🛠️ Estrutura de Migrações

### Migração Atual:

- **ID**: `265f97ab88c1`
- **Descrição**: `initial_schema_with_all_tables`
- **Localização**: `migrations/versions/20251031_1809_265f97ab88c1_initial_schema_with_all_tables.py`

Esta migração inclui **TODAS** as tabelas e colunas necessárias:
- ✅ Tabela `notificacoes` com `usuario_origem_id` e `usuario_destino_id`
- ✅ Todas as outras tabelas do sistema
- ✅ Todas as foreign keys e constraints

### O que foi REMOVIDO:

❌ Código que forçava versões específicas:
- `main.py` - Removido código que forçava `265f97ab88c1` ou `a4d5b6d9c0ca`
- `fix_user_email_config_columns.py` - Removido código que forçava `20250929_2303`
- `railway_routes_fix.py` - Removido código que forçava `c18fc0f1e85a`
- `fix_alembic_version.py` - Marcado como DEPRECATED

### O que está ATIVO:

✅ Sistema de migrações automático:
- Alembic detecta automaticamente qual migração aplicar
- Migrações são aplicadas via `alembic upgrade head`
- Nenhum código força versões específicas

---

## ❌ Erros Comuns e Soluções

### Erro: `Can't locate revision identified by 'a4d5b6d9c0ca'`

**Causa**: O banco de dados tem uma versão antiga registrada.

**Solução**:
```bash
python clear_alembic_version.py
alembic stamp head
```

### Erro: `relation "checklist_padrao" already exists`

**Causa**: As tabelas já existem, mas o alembic tenta criá-las novamente.

**Solução**:
```bash
alembic stamp head
```

Este comando marca a migração como "já aplicada" sem executá-la novamente.

### Erro: `Table alembic_version doesn't exist`

**Causa**: É o primeiro deploy e a tabela ainda não foi criada.

**Solução**: O Alembic criará automaticamente durante o primeiro `alembic upgrade head`.

---

## 📝 Comandos Úteis

### Verificar migrações pendentes:
```bash
alembic current
alembic heads
```

### Aplicar migrações:
```bash
alembic upgrade head
```

### Marcar migração como aplicada (sem executar):
```bash
alembic stamp head
```

### Ver histórico de migrações:
```bash
alembic history
```

---

## 🎯 Resultado Esperado no Railway

Após o deploy bem-sucedido, você verá nos logs do Railway:

```
INFO:root:🚂 Railway environment - preparando migrações...
INFO:root:🔍 Versão Alembic no banco: a4d5b6d9c0ca
WARNING:root:⚠️ Versão órfã detectada: a4d5b6d9c0ca
INFO:root:🧹 Limpando versão órfã e permitindo auto-detecção...
INFO:root:✅ Versão órfã removida - Alembic irá detectar automaticamente
INFO:root:🔄 Executando migrações automáticas...
INFO  [alembic.runtime.migration] Running upgrade  -> 265f97ab88c1
INFO:root:✅ Migrações aplicadas com sucesso
```

**Se o banco já estiver correto:**
```
INFO:root:🚂 Railway environment - preparando migrações...
INFO:root:🔍 Versão Alembic no banco: 265f97ab88c1
INFO:root:✅ Versão válida encontrada: 265f97ab88c1
INFO:root:🔄 Executando migrações automáticas...
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO:root:✅ Migrações aplicadas com sucesso
```

E a aplicação estará rodando sem erros de migração! 🎉

---

## 📧 Suporte

Se encontrar problemas:

1. Verifique os logs do Railway
2. Execute `alembic current` para ver a versão atual
3. Execute `python clear_alembic_version.py` para limpar versões antigas
4. Execute `alembic stamp head` para marcar a migração como aplicada

---

**Última Atualização**: 31 de Outubro de 2025
**Versão do Alembic**: 265f97ab88c1 (head)
