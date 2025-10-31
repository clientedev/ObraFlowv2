# Guia de Deploy no Railway - 2025

## ✅ CORREÇÃO COMPLETA - Migrações Alembic Automatizadas

Todas as correções foram aplicadas. O sistema agora gerencia as migrações automaticamente sem forçar versões específicas.

---

## 🚀 Como Fazer Deploy no Railway

### 1. **Limpar Versões Antigas do Alembic (UMA VEZ APENAS)**

Se você já tem uma aplicação rodando no Railway com versões antigas do alembic, execute este comando **UMA VEZ** no terminal do Railway:

```bash
python clear_alembic_version.py
```

Este script irá:
- ✅ Limpar a tabela `alembic_version`
- ✅ Permitir que o Alembic detecte automaticamente a migração correta

### 2. **Deploy Automático**

Após limpar as versões antigas, o deploy no Railway será **totalmente automático**:

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
- [ ] (Opcional) `EMAIL_PASSWORD_ENCRYPTION_KEY` se usar configuração de email por usuário
- [ ] (Opcional) `FIREBASE_CREDENTIALS_PATH` ou `FIREBASE_CONFIG` se usar notificações push

### Durante o Deploy:

O Railway executará automaticamente:
1. ✅ Build das dependências
2. ✅ Limpeza de versões antigas do alembic (se necessário)
3. ✅ Aplicação de migrações via `alembic upgrade head`
4. ✅ Inicialização do servidor

### Após o Deploy:

- [ ] Verificar logs no Railway Dashboard
- [ ] Testar a aplicação
- [ ] Verificar que não há erros de migração

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

## 🎯 Resultado Esperado

Após o deploy bem-sucedido, você verá nos logs do Railway:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 265f97ab88c1
✅ Migrações aplicadas com sucesso
```

E a aplicação estará rodando sem erros de migração!

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
