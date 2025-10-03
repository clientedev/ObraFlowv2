// reports-upload.js - Sistema unificado de upload de fotos (mobile-first)
// Corrige o problema de imagens não sendo enviadas ao backend
(() => {
  const form = document.getElementById('reportForm');
  const photoInput = document.getElementById('photoInput');
  const mobileInput = document.getElementById('mobileCameraInput');
  const mobileGalleryInput = document.getElementById('mobilePhotoInput');
  const preview = document.getElementById('photosPreview');
  const submitButton = form?.querySelector('button[type="submit"]');
  const photoCountBadge = document.getElementById('photoCount');

  // Fila de arquivos selecionados (File objects or Blob)
  const selectedFiles = [];

  // Helper: render preview
  function renderPreviews() {
    if (!preview) return;
    
    preview.innerHTML = '';
    selectedFiles.forEach((file, i) => {
      const url = URL.createObjectURL(file);
      const el = document.createElement('div');
      el.className = 'col-md-3 col-6 mb-3';
      el.innerHTML = `
        <div class="photo-card border rounded p-2">
          <img src="${url}" alt="foto ${i + 1}" class="img-fluid rounded mb-2" style="max-height:150px; width:100%; object-fit:cover"/>
          <button type="button" data-index="${i}" class="btn btn-sm btn-danger w-100 btn-remove-photo">
            <i class="fas fa-trash"></i> Remover
          </button>
        </div>
      `;
      preview.appendChild(el);
    });

    // Atualizar contador
    if (photoCountBadge) {
      photoCountBadge.textContent = selectedFiles.length;
    }

    console.log(`📸 Preview atualizado: ${selectedFiles.length} fotos`);
  }

  // Add files to fila
  function addFiles(filesList) {
    if (!filesList || filesList.length === 0) return;
    
    for (let i = 0; i < filesList.length; i++) {
      const f = filesList[i];
      
      // Validar tipo
      if (!f.type.startsWith('image/')) {
        console.warn(`⚠️ Arquivo ${f.name} não é uma imagem, ignorado`);
        continue;
      }
      
      // Validar tamanho (máximo 10MB por imagem)
      if (f.size > 10 * 1024 * 1024) {
        alert(`Arquivo ${f.name} é muito grande (máximo 10MB). Por favor, comprima a imagem.`);
        continue;
      }
      
      selectedFiles.push(f);
      console.log(`✅ Imagem adicionada: ${f.name} (${(f.size / 1024 / 1024).toFixed(2)}MB)`);
    }
    
    renderPreviews();
  }

  // Event listeners mobile/desktop
  if (photoInput) {
    photoInput.addEventListener('change', e => {
      console.log('📷 Desktop input changed:', e.target.files.length, 'arquivos');
      addFiles(e.target.files);
    });
  }

  if (mobileInput) {
    mobileInput.addEventListener('change', e => {
      console.log('📸 Mobile camera input changed:', e.target.files.length, 'arquivos');
      addFiles(e.target.files);
    });
  }

  if (mobileGalleryInput) {
    mobileGalleryInput.addEventListener('change', e => {
      console.log('🖼️ Mobile gallery input changed:', e.target.files.length, 'arquivos');
      addFiles(e.target.files);
    });
  }

  // Remove preview
  if (preview) {
    preview.addEventListener('click', (e) => {
      if (e.target.classList.contains('btn-remove-photo') || e.target.closest('.btn-remove-photo')) {
        const btn = e.target.classList.contains('btn-remove-photo') ? e.target : e.target.closest('.btn-remove-photo');
        const idx = Number(btn.dataset.index);
        console.log(`🗑️ Removendo foto índice ${idx}`);
        selectedFiles.splice(idx, 1);
        renderPreviews();
      }
    });
  }

  // Função que cria/atualiza relatório e retorna report_id
  async function ensureReportExists() {
    // Verificar se já existe um report_id (modo de edição)
    const existing = form.querySelector('input[name="edit_report_id"]');
    if (existing && existing.value) {
      console.log(`✅ Relatório já existe (ID: ${existing.value})`);
      return existing.value;
    }

    // Criar relatório via AJAX
    console.log('📝 Criando relatório via AJAX...');
    const fd = new FormData(form);
    
    // NÃO anexar imagens nesta etapa - apenas dados do relatório
    // (o backend não espera imagens no endpoint de criação)
    
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const res = await fetch(form.action, {
      method: 'POST',
      body: fd,
      headers: token ? { 'X-CSRFToken': token } : {}
    });

    if (!res.ok) {
      const text = await res.text().catch(() => null);
      throw new Error(`Erro ao criar relatório: ${res.status} ${text || res.statusText}`);
    }

    // Tentar parsear JSON
    const contentType = res.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const json = await res.json();
      if (json.report_id) {
        console.log(`✅ Relatório criado (ID: ${json.report_id})`);
        return json.report_id;
      }
    }

    // Se não retornou JSON com report_id, tentar extrair do redirect
    const redirectUrl = res.url;
    const match = redirectUrl.match(/\/reports\/(\d+)/);
    if (match) {
      const reportId = match[1];
      console.log(`✅ Relatório criado via redirect (ID: ${reportId})`);
      return reportId;
    }

    throw new Error('Não foi possível obter o ID do relatório criado');
  }

  // Função de upload de uma foto ao servidor
  async function uploadPhotoToServer(reportId, file) {
    console.log(`📤 Uploading ${file.name} para relatório ${reportId}...`);
    
    const fd = new FormData();
    fd.append('photos', file, file.name);
    
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const res = await fetch(`/reports/${reportId}/photos/upload`, {
      method: 'POST',
      body: fd,
      headers: token ? { 'X-CSRFToken': token } : {}
    });

    if (!res.ok) {
      const text = await res.text().catch(() => null);
      throw new Error(`Upload falhou: ${res.status} ${text || res.statusText}`);
    }

    const json = await res.json();
    console.log(`✅ Upload concluído:`, json);
    return json;
  }

  // Upload all selected files
  async function uploadAllFiles(reportId) {
    console.log(`📤 Iniciando upload de ${selectedFiles.length} fotos...`);
    const results = [];
    
    for (let i = 0; i < selectedFiles.length; i++) {
      const f = selectedFiles[i];
      try {
        const result = await uploadPhotoToServer(reportId, f);
        results.push(result);
        console.log(`✅ Foto ${i + 1}/${selectedFiles.length} enviada`);
      } catch (err) {
        console.error(`❌ Erro ao enviar foto ${i + 1}:`, err);
        throw err; // Propagar erro
      }
    }
    
    return results;
  }

  // Handler do submit: cria relatório → upload fotos → redireciona
  if (form && submitButton) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      try {
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        
        console.log('💾 Iniciando processo de salvamento...');
        
        // 1) Criar/garantir que relatório existe
        const reportId = await ensureReportExists();

        // 2) Se existirem fotos selecionadas, fazer upload
        if (selectedFiles.length > 0) {
          console.log(`📸 ${selectedFiles.length} fotos para enviar`);
          await uploadAllFiles(reportId);
          console.log('✅ Todas as fotos enviadas com sucesso!');
        } else {
          console.log('ℹ️ Nenhuma foto para enviar');
        }

        // 3) Redirecionar para página do relatório
        console.log(`✅ Redirecionando para /reports/${reportId}`);
        window.location.href = `/reports/${reportId}`;
        
      } catch (err) {
        console.error('❌ Erro:', err);
        
        // Mostrar erro ao usuário
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
        errorDiv.innerHTML = `
          <strong>Erro ao salvar relatório:</strong> ${err.message}
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        form.insertBefore(errorDiv, form.firstChild);
        
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fas fa-save"></i> Concluir relatório';
      }
    });
  }

  // Expor funções globais para botões que abrem o picker
  window.openPhotoPicker = (from) => {
    if (from === 'mobile-camera' && mobileInput) {
      console.log('📸 Abrindo câmera mobile...');
      mobileInput.click();
    } else if (from === 'mobile-gallery' && mobileGalleryInput) {
      console.log('🖼️ Abrindo galeria mobile...');
      mobileGalleryInput.click();
    } else if (photoInput) {
      console.log('📷 Abrindo seletor de fotos desktop...');
      photoInput.click();
    }
  };

  console.log('✅ Sistema de upload de fotos inicializado');
})();
