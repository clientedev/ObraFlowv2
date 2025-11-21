# Correção Completa do Sistema de Geração de PDF
## Data: 21 de Novembro de 2025

## Problemas Identificados e Soluções

### 1. ✅ Imagens Não Carregando no PDF

**Problema**: As imagens apareciam como "Foto não disponível" no PDF gerado.

**Causa Raiz**: 
- Para relatórios normais: O processamento estava correto, mas faltavam logs para debug
- Para relatórios express: O campo `imagem` (BYTEA do PostgreSQL) não estava sendo copiado para o objeto MockFoto

**Solução Implementada**:

**Arquivo**: `pdf_generator_weasy.py` (linhas 139-205)
- ✅ Adicionado logging detalhado em cada etapa do processamento de imagens
- ✅ Melhorado tratamento de tipos (memoryview vs bytes)
- ✅ Verificação explícita de existência de arquivo no filesystem
- ✅ Mensagens de erro específicas quando imagem não é encontrada

```python
# Logs adicionados:
print(f"🔍 Processando foto {foto.ordem}: filename={foto.filename}")
print(f"✅ Foto {foto.ordem} carregada do PostgreSQL (memoryview): {len(image_bytes)} bytes")
print(f"❌ ERRO: Foto {foto.ordem} NÃO CARREGADA - não encontrada no PostgreSQL nem no filesystem")
```

**Arquivo**: `pdf_generator_express.py` (linha 155)
- ✅ Adicionado campo `imagem` ao MockFoto para copiar os bytes do PostgreSQL

```python
class MockFoto:
    def __init__(self, foto_express):
        self.filename = foto_express.filename
        self.imagem = getattr(foto_express, 'imagem', None)  # CRÍTICO!
```

---

### 2. ✅ Logo Muito Pequeno

**Problema**: O logo da ELP estava aparecendo muito pequeno no cabeçalho do PDF (100px x 35px).

**Solução**: Aumentado em 50% o tamanho do logo.

**Arquivo**: `pdf_generator_weasy.py` (linhas 374-377)

**Antes**:
```css
.logo-container {
    width: 100px;
    height: 35px;
    flex-shrink: 0;
}
```

**Depois**:
```css
.logo-container {
    width: 150px;
    height: 55px;
    flex-shrink: 0;
}
```

**Resultado**: Logo agora 50% maior e mais visível no PDF.

---

### 3. ✅ Horário Incorreto (Timezone Errado)

**Problema**: O PDF mostrava horário UTC ao invés do horário do Brasil (Brasília/São Paulo).

**Solução**: Implementado timezone correto usando pytz.

**Arquivo**: `pdf_generator_weasy.py` (linhas 11, 119-135)

**Dependência Adicionada**: `pytz` (instalado via packager_tool)

**Código Implementado**:
```python
import pytz

# Usar timezone do Brasil (São Paulo)
brazil_tz = pytz.timezone('America/Sao_Paulo')
utc_tz = pytz.UTC
now_brazil = datetime.now(brazil_tz)

# Helper para converter datetime naive (UTC) para Brazil timezone
def to_brazil_tz(dt):
    """Converte datetime para timezone do Brasil, tratando naive datetimes como UTC"""
    if dt is None:
        return now_brazil
    # Se datetime é naive (sem timezone), assumir que é UTC
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt = utc_tz.localize(dt)
    # Converter para timezone do Brasil
    return dt.astimezone(brazil_tz)

data = {
    'data_atual': now_brazil.strftime('%d/%m/%Y %H:%M'),
    'data_relatorio': to_brazil_tz(relatorio.data_relatorio).strftime('%d/%m/%Y %H:%M'),
}
```

**Nota Importante**: A função `to_brazil_tz()` trata corretamente datetimes "naive" (sem timezone) do PostgreSQL/SQLAlchemy, assumindo que são UTC e convertendo para o horário do Brasil.

**Resultado**: 
- Datas/horas agora exibidas em UTC-3 (horário de Brasília)
- Tanto para data atual quanto para data do relatório

---

### 4. ✅ Campo "Empresa" Mostrando Informação Errada

**Problema**: No relatório normal, o campo "Empresa" mostrava o nome do responsável ao invés do nome da empresa/obra.

**Solução**: Corrigido para usar `projeto.nome` (nome da obra/empresa).

**Arquivo**: `pdf_generator_weasy.py` (linha 127)

**Antes**:
```python
'empresa': projeto.responsavel.nome_completo if projeto.responsavel else "ELP Consultoria",
```

**Depois**:
```python
'empresa': projeto.nome if projeto else "ELP Consultoria",
```

**Nota**: Para relatórios express, o campo já estava correto usando `empresa_nome` (linha 70 de `pdf_generator_express.py`).

---

### 5. ✅ Legendas das Imagens

**Problema**: Garantir que as legendas carreguem corretamente de ambos os campos (legenda ou descrição).

**Solução**: Implementada prioridade: `descricao` > `legenda` > `"Foto {ordem}"`.

**Arquivo**: `pdf_generator_weasy.py` (linhas 190-195)

```python
# Criar legenda completa - PRIORIDADE: descricao > legenda
legenda_completa = f"Foto {foto.ordem}"
if hasattr(foto, 'descricao') and foto.descricao:
    legenda_completa = foto.descricao
elif hasattr(foto, 'legenda') and foto.legenda:
    legenda_completa = foto.legenda

print(f"📝 Foto {foto.ordem} - Legenda: {legenda_completa}")
```

**Arquivo**: `pdf_generator_express.py` (linhas 156-163)

Para relatórios express, as legendas são compostas automaticamente:
```python
base_descricao = f"Foto {foto_express.ordem}"
if foto_express.legenda:
    base_descricao += f" - {foto_express.legenda}"

self.descricao = base_descricao
```

---

## Arquivos Modificados

### 1. `pdf_generator_weasy.py`
- ✅ Adicionado import `pytz`
- ✅ Implementado timezone do Brasil (America/Sao_Paulo)
- ✅ Corrigido campo empresa (projeto.nome)
- ✅ Aumentado tamanho do logo (CSS)
- ✅ Melhorado processamento de imagens com logs detalhados
- ✅ Corrigida prioridade de legendas (descricao > legenda)

### 2. `pdf_generator_express.py`
- ✅ Adicionado campo `imagem` ao MockFoto
- ✅ Mantido uso correto de `empresa_nome`

### 3. Dependências
- ✅ Instalado `pytz==2025.2` via packager_tool

---

## Resultados Esperados

### Para Relatórios Normais:
✅ **Imagens**: Carregam do PostgreSQL (BYTEA) ou filesystem com logs detalhados  
✅ **Logo**: 150px x 55px (50% maior)  
✅ **Timezone**: Horário de Brasília (UTC-3)  
✅ **Campo Empresa**: Nome da obra/projeto  
✅ **Legendas**: Prioridade descricao > legenda > padrão  

### Para Relatórios Express:
✅ **Imagens**: Campo `imagem` copiado corretamente do PostgreSQL  
✅ **Logo**: 150px x 55px (herda CSS do WeasyPrint)  
✅ **Timezone**: Horário de Brasília (herda do WeasyPrint)  
✅ **Campo Empresa**: `empresa_nome` (já estava correto)  
✅ **Legendas**: Compostas com número + legenda pré-definida  

---

## Testes Recomendados

### Teste 1: Relatório Normal com Fotos
1. Criar/abrir relatório normal finalizado
2. Gerar PDF
3. Verificar:
   - ✅ Imagens aparecem (não "Foto não disponível")
   - ✅ Logo aparece maior
   - ✅ Horário está em Brasília
   - ✅ Campo Empresa mostra nome da obra
   - ✅ Legendas aparecem corretamente

### Teste 2: Relatório Express com Fotos
1. Criar/abrir relatório express finalizado
2. Gerar PDF
3. Verificar:
   - ✅ Imagens aparecem corretamente
   - ✅ Logo aparece maior
   - ✅ Horário está em Brasília
   - ✅ Campo Empresa mostra empresa_nome
   - ✅ Legendas compostas aparecem

### Teste 3: Logs de Debug
1. Gerar PDF (normal ou express)
2. Verificar logs do servidor:
   - ✅ Logs de processamento de fotos aparecem
   - ✅ Mensagens indicam se carregou do PostgreSQL ou filesystem
   - ✅ Erros específicos se imagem não encontrada

---

## Logs de Debug Implementados

### Processamento de Fotos:
```
🔍 Processando foto 1: filename=foto123.jpg
✅ Foto 1 carregada do PostgreSQL (memoryview): 245678 bytes
📝 Foto 1 - Legenda: Emboco bem-acabado
```

### Quando Imagem Não Encontrada:
```
⚠️ Foto 2: campo imagem não existe ou está vazio
🔍 Tentando carregar do filesystem: uploads/foto456.jpg
❌ Arquivo não encontrado: uploads/foto456.jpg
❌ ERRO: Foto 2 NÃO CARREGADA - não encontrada no PostgreSQL nem no filesystem
```

---

## Compatibilidade

### ✅ Relatórios Normais
- Mantém compatibilidade total
- Melhorias aplicadas sem quebrar funcionalidades existentes

### ✅ Relatórios Express
- Herda melhorias do WeasyPrintReportGenerator
- Campo `imagem` agora copiado corretamente
- Legendas compostas automaticamente

### ✅ Fallback ReportLab
- Mantido intacto para ambos os geradores
- Não afetado pelas mudanças (WeasyPrint only)

---

## Notas Técnicas

### Timezone do Brasil
- Timezone: `America/Sao_Paulo` (UTC-3)
- Usa biblioteca `pytz` para garantir compatibilidade
- Conversão automática via `datetime.now(brazil_tz)` e `.astimezone(brazil_tz)`

### Carregamento de Imagens
- **Prioridade 1**: PostgreSQL campo `imagem` (BYTEA)
  - Tipos suportados: `memoryview` e `bytes`
- **Fallback**: Filesystem em `uploads/{filename}`
- Todas as imagens convertidas para base64 para embedding no HTML

### Processamento Express
- Usa herança de `WeasyPrintReportGenerator`
- Cria objetos mock (MockReport, MockProject, MockFoto)
- Campo `imagem` CRÍTICO - deve ser copiado do original

---

## Checklist de Implementação

- [x] Instalar pytz
- [x] Implementar timezone do Brasil
- [x] Corrigir campo empresa (relatório normal)
- [x] Aumentar logo (CSS)
- [x] Melhorar logs de processamento de imagens
- [x] Corrigir prioridade de legendas
- [x] Adicionar campo imagem ao MockFoto (express)
- [x] Testar servidor (sem erros ao iniciar)
- [ ] Testar geração de PDF normal
- [ ] Testar geração de PDF express
- [ ] Validar com usuário

---

## Próximos Passos

1. **Testar geração de PDF** com relatórios que tenham fotos
2. **Verificar logs** para confirmar que imagens estão carregando
3. **Validar com usuário** se todos os problemas foram resolvidos
4. **Documentar** quaisquer issues adicionais que aparecerem nos testes
