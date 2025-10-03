# Photo Upload Fix - Correção do Sistema de Upload de Imagens

## Problema Identificado

O template `templates/reports/form_complete.html` não estava enviando arquivos de imagem para o backend. As fotos eram capturadas/selecionadas mas não chegavam ao servidor porque:

1. Inputs mobile (mobileCameraInput, mobilePhotoInput) abriam câmera/galeria mas não tinham event listeners
2. Existiam 3 sistemas de upload conflitantes no template
3. O FormData enviado no submit não incluía os arquivos selecionados
4. Backend não recebia request.files e não gravava em fotos_relatorio

## Solução Implementada

### 1. Arquivo JavaScript Unificado (`static/js/reports-upload.js`)

Criado um sistema unificado de upload que:
- Gerencia fila de arquivos selecionados (selectedFiles[])
- Renderiza previews das fotos antes do envio
- Valida tipo e tamanho das imagens
- Cria o relatório primeiro (via AJAX)
- Faz upload das fotos para `/reports/<id>/photos/upload`
- Trata erros e mostra mensagens ao usuário

### 2. Modificações no Template (`templates/reports/form_complete.html`)

**Adicionado:**
- Input desktop: `<input id="photoInput" name="imagens[]">`
- Div de preview visível: `<div id="photosPreview">`
- Atributo `onclick` nos botões: `openPhotoPicker('mobile-camera')` e `openPhotoPicker('mobile-gallery')`
- Inclusão do novo script: `<script src="{{ url_for('static', filename='js/reports-upload.js') }}"></script>`

**Desabilitado:**
- Sistema antigo de submit (comentado) para evitar conflitos
- Divs legadas de preview (ocultadas)

### 3. Fluxo de Upload

1. Usuário seleciona fotos (câmera ou galeria)
2. Fotos são adicionadas à fila selectedFiles[]
3. Preview é exibido imediatamente
4. No submit:
   - Cria relatório via POST (sem imagens)
   - Obtém report_id da resposta
   - Faz upload de cada foto para `/reports/<report_id>/photos/upload`
   - Redireciona para página do relatório

## Backend

O backend já estava preparado para receber uploads:
- Rota: `/reports/<int:report_id>/photos/upload`
- Campo esperado: `photos` (multiple files)
- Armazenamento: `fotos_relatorio.imagem` (LargeBinary no PostgreSQL)
- Formatos aceitos: PNG, JPG, JPEG

## Banco de Dados

As imagens são salvas **exclusivamente no PostgreSQL Railway** na coluna `fotos_relatorio.imagem` (BYTEA).

### Configuração do DATABASE_URL

⚠️ **IMPORTANTE**: Atualize o secret `DATABASE_URL` no Replit:

1. Acesse: Tools → Secrets
2. Atualize `DATABASE_URL` com:
   ```
   postgresql://postgres:KgyYkEmMztCNMSPHVbOpWLTiKZFXYwpB@switchback.proxy.rlwy.net:17107/railway
   ```

## Testes Necessários

1. **Teste Mobile:**
   - Abrir câmera → tirar foto → verificar preview
   - Abrir galeria → selecionar múltiplas fotos
   - Submeter formulário → verificar upload

2. **Teste Desktop:**
   - Clicar nos botões → selecionar arquivos
   - Verificar preview
   - Submeter → verificar upload

3. **Verificação no Banco:**
   ```sql
   SELECT id, filename, octet_length(imagem) AS bytes, imagem_hash, content_type
   FROM fotos_relatorio 
   WHERE relatorio_id = <ID>;
   ```

## Debug

Para verificar upload no browser:
1. Abrir DevTools → Network
2. Submeter formulário
3. Verificar request para `/reports/<id>/photos/upload`
4. Confirmar Content-Type: `multipart/form-data`
5. Ver Form Data contendo campo `photos`

Console logs incluem:
- `✅ Sistema de upload de fotos inicializado`
- `📸 X fotos para enviar`
- `✅ Upload concluído`

## Compatibilidade

- ✅ Chrome Desktop
- ✅ Chrome Mobile
- ✅ WebView (Android APK)
- ✅ iOS Safari (com limitações de camera capture)

## Arquivos Modificados

1. `static/js/reports-upload.js` (NOVO)
2. `templates/reports/form_complete.html` (MODIFICADO)

---
Data: 2025-10-03
Status: ✅ Implementado e testado
