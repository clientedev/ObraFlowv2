# Sistema de Salvamento Automático de Relatórios

## Visão Geral

O sistema de autosave permite a criação e edição de relatórios de visita com salvamento automático a cada 3 segundos, gestão completa de imagens (upload, edição, reordenação, exclusão) e sincronização em tempo real entre frontend e backend.

## Funcionalidades Principais

### 1. Salvamento Automático
- **Debounce de 3 segundos**: Alterações são salvas automaticamente após 3 segundos de inatividade
- **Indicador visual**: Mostra status "Salvando..." e "Salvo"
- **Sincronização completa**: Todos os campos e imagens são sincronizados automaticamente

### 2. Gestão de Imagens
- **Upload**: Até 50 imagens por relatório
- **Limite de tamanho**: 50MB por arquivo
- **Formatos suportados**: jpg, jpeg, png, gif, bmp, webp
- **Drag and Drop**: Reordenação visual das imagens arrastando e soltando
- **Edição**: Legenda, categoria e local para cada imagem
- **Exclusão**: Remoção individual com confirmação

### 3. Campos do Relatório
- **Campos básicos**: Título, descrição, categoria, local
- **Observações finais**: Campo de texto livre
- **Lembrete próxima visita**: Data/hora para próxima visita
- **Status**: em_andamento, enviado, aprovado, rejeitado, concluido

## API Endpoints

### POST /api/relatorios
Cria um novo relatório com imagens.

**Headers**:
```
Content-Type: multipart/form-data
```

**Body** (form-data):
```
projeto_id: 123
titulo: "Relatório de Visita"
descricao: "Descrição detalhada"
categoria: "Estrutura"
local: "Bloco A"
observacoes_finais: "Observações gerais"
lembrete_proxima_visita: "2025-11-15T10:00:00"
status: "em_andamento"
imagens[]: [arquivo1.jpg, arquivo2.png, ...]
legenda_0: "Legenda da primeira imagem"
legenda_1: "Legenda da segunda imagem"
```

**Response** (201):
```json
{
  "success": true,
  "id": 456,
  "numero": "PROJ-001-R002",
  "imagens": [
    {
      "id": 789,
      "url": "/uploads/relatorio_456_20251102_120000_foto1.jpg",
      "legenda": "Legenda da primeira imagem",
      "ordem": 0
    }
  ],
  "message": "Relatório criado com sucesso"
}
```

**Erro 413** (arquivo muito grande):
```json
{
  "success": false,
  "error": "Erro de validação de arquivo",
  "details": "Arquivo muito grande: 55.23MB. Máximo permitido: 50MB"
}
```

### GET /api/relatorios/:id
Busca um relatório existente com todas as imagens.

**Response** (200):
```json
{
  "success": true,
  "relatorio": {
    "id": 456,
    "numero": "PROJ-001-R002",
    "titulo": "Relatório de Visita",
    "descricao": "Descrição detalhada",
    "categoria": "Estrutura",
    "local": "Bloco A",
    "observacoes_finais": "Observações gerais",
    "lembrete_proxima_visita": "2025-11-15T10:00:00",
    "status": "em_andamento",
    "imagens": [
      {
        "id": 789,
        "url": "/uploads/relatorio_456_20251102_120000_foto1.jpg",
        "legenda": "Legenda da primeira imagem",
        "ordem": 0
      }
    ]
  }
}
```

### PUT /api/relatorios/:id
Atualiza relatório existente e sincroniza imagens.

**Headers**:
```
Content-Type: multipart/form-data
```

**Body** (form-data):
```
titulo: "Título atualizado"
descricao: "Nova descrição"
categoria: "Acabamento"
imagens_existentes: '[{"id": 789, "legenda": "Nova legenda", "ordem": 0}]'
imagens_excluir: '[790, 791]'
imagens[]: [novo_arquivo.jpg]
legenda_0: "Legenda da nova imagem"
```

**Sincronização de imagens**:
1. **Atualização**: Imagens em `imagens_existentes` têm legenda e ordem atualizadas
2. **Exclusão**: IDs em `imagens_excluir` são removidos do banco e sistema de arquivos
3. **Adição**: Novos arquivos em `imagens[]` são adicionados com ordem sequencial

**Response** (200):
```json
{
  "success": true,
  "message": "Relatório atualizado com sucesso",
  "imagens": [...]
}
```

### DELETE /api/relatorios/:id/imagens/:imagem_id
Remove uma imagem específica.

**Response** (200):
```json
{
  "success": true,
  "message": "Imagem removida com sucesso"
}
```

## Frontend - Uso do ReportAutoSave

### Inclusão do Script

```html
<script src="/static/js/relatorios-autosave.js"></script>
```

### HTML Requerido

```html
<!-- Status do autosave -->
<div id="autosave-status" class="autosave-status"></div>

<!-- Formulário do relatório -->
<form id="relatorio-form">
    <input type="text" id="titulo" name="titulo" placeholder="Título" />
    <textarea id="descricao" name="descricao" placeholder="Descrição"></textarea>
    <input type="text" id="categoria" name="categoria" placeholder="Categoria" />
    <input type="text" id="local" name="local" placeholder="Local" />
    <textarea id="observacoes_finais" name="observacoes_finais" placeholder="Observações Finais"></textarea>
    <input type="datetime-local" id="lembrete_proxima_visita" name="lembrete_proxima_visita" />
    <select id="status" name="status">
        <option value="em_andamento">Em Andamento</option>
        <option value="enviado">Enviado</option>
        <option value="aprovado">Aprovado</option>
        <option value="rejeitado">Rejeitado</option>
        <option value="concluido">Concluído</option>
    </select>
</form>

<!-- Upload de imagens -->
<input type="file" id="imagem-upload" accept="image/*" multiple />

<!-- Container de imagens (drag and drop habilitado) -->
<div id="imagens-container"></div>
```

### Inicialização

```javascript
document.addEventListener('DOMContentLoaded', () => {
    // Obter ID do relatório da URL ou contexto
    const urlParams = new URLSearchParams(window.location.search);
    const relatorioId = urlParams.get('id') || null;
    const projetoId = urlParams.get('projeto_id');
    
    // Inicializar sistema de autosave
    const autosave = new ReportAutoSave(relatorioId, projetoId);
});
```

### Estrutura de Card de Imagem

O sistema espera cards de imagem com a seguinte estrutura:

```html
<div class="image-card" draggable="true" data-image-id="789">
    <img src="/uploads/relatorio_456_20251102_120000_foto1.jpg" />
    <input type="text" class="image-legenda" value="Legenda da imagem" />
    <button class="btn-excluir-imagem">Excluir</button>
</div>
```

### Eventos e Callbacks

```javascript
// O sistema dispara eventos personalizados
document.addEventListener('autosave:success', (e) => {
    console.log('Relatório salvo:', e.detail);
});

document.addEventListener('autosave:error', (e) => {
    console.error('Erro ao salvar:', e.detail);
});

document.addEventListener('image:uploaded', (e) => {
    console.log('Imagem adicionada:', e.detail);
});

document.addEventListener('image:deleted', (e) => {
    console.log('Imagem removida:', e.detail);
});
```

## Fluxo de Trabalho

### Criação de Novo Relatório

1. Usuário acessa página de criação (`/relatorios/novo?projeto_id=123`)
2. ReportAutoSave inicializado com `relatorioId = null`
3. Usuário preenche campos do formulário
4. Após 3 segundos de inatividade, POST /api/relatorios é chamado
5. Backend cria relatório e retorna ID
6. Frontend armazena ID e passa a usar PUT para atualizações

### Edição de Relatório Existente

1. Usuário acessa página de edição (`/relatorios/editar?id=456`)
2. ReportAutoSave inicializado com `relatorioId = 456`
3. GET /api/relatorios/456 carrega dados existentes
4. Formulário preenchido automaticamente
5. Alterações salvas automaticamente via PUT /api/relatorios/456

### Upload de Imagens

1. Usuário seleciona arquivos via input file ou drag and drop
2. Sistema valida tamanho (máx 50MB) e tipo
3. Imagens adicionadas ao próximo autosave (PUT)
4. Backend processa e retorna URLs das imagens salvas
5. Frontend exibe imagens carregadas

### Reordenação de Imagens

1. Usuário arrasta card de imagem
2. Durante drag, `dragover` reordena visualmente
3. Em `drop`, autosave agendado
4. PUT /api/relatorios/:id enviado com nova ordem
5. Backend atualiza campo `ordem` de cada imagem

### Exclusão de Imagens

1. Usuário clica botão "Excluir" em card de imagem
2. Card removido visualmente
3. ID adicionado à lista `imagens_excluir`
4. Próximo autosave (PUT) inclui lista de exclusão
5. Backend remove do banco e sistema de arquivos

## Validações e Tratamento de Erros

### Backend
- ✅ Tamanho máximo: 50MB por arquivo
- ✅ Tipos permitidos: jpg, jpeg, png, gif, bmp, webp
- ✅ Transações atômicas com rollback automático
- ✅ Erro 413 para arquivos muito grandes
- ✅ Erro 400 para tipos inválidos
- ✅ Erro 404 para relatório não encontrado

### Frontend
- ✅ Validação de campos obrigatórios
- ✅ Feedback visual durante salvamento
- ✅ Mensagens de erro claras
- ✅ Retry automático em caso de falha de rede (implementar se necessário)

## Considerações de Performance

- **Debounce**: Evita salvamentos excessivos durante digitação rápida
- **Batch de imagens**: Múltiplas imagens enviadas em única requisição
- **Ordem otimizada**: Reordenação persiste apenas campo `ordem`, sem reenvio de arquivos

## Segurança

- ✅ CSRF protection em todos os endpoints
- ✅ Login required em todas as rotas
- ✅ Validação de permissões (usuário só acessa seus relatórios)
- ✅ Sanitização de nomes de arquivo (secure_filename)
- ✅ Validação de tipos de arquivo
- ✅ Proteção contra path traversal

## Próximos Passos (Opcionais)

1. **Testes automatizados**: Upload oversized, drag and drop, sincronização
2. **Cleanup de arquivos órfãos**: Remover arquivos não associados a relatórios
3. **Compressão de imagens**: Reduzir tamanho automaticamente
4. **Preview antes do upload**: Mostrar imagens antes de enviar
5. **Progress bar**: Indicador de progresso durante upload de múltiplas imagens
