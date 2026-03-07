
let map;
let marker;
let selectedLat = null;
let selectedLng = null;

// GPS Location capture with automatic address filling
function getGPSLocationAndAddress() {
    const statusElement = document.getElementById('locationStatus');
    
    if (!navigator.geolocation) {
        statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> GPS não suportado neste navegador';
        return;
    }
    
    statusElement.innerHTML = '<i class="fas fa-spinner fa-spin text-primary"></i> Capturando localização e endereço...';
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            // Set coordinates in hidden fields
            const latField = document.querySelector('input[name="latitude"]');
            const lngField = document.querySelector('input[name="longitude"]');
            if (latField) latField.value = lat;
            if (lngField) lngField.value = lng;
            
            // Get address from coordinates and fill address field
            reverseGeocodeAndFillAddress(lat, lng);
            
            statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Localização capturada! Obtendo endereço...';
        },
        function(error) {
            let errorMsg = 'Erro ao capturar localização';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMsg = 'Permissão negada para acessar localização';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMsg = 'Localização não disponível';
                    break;
                case error.TIMEOUT:
                    errorMsg = 'Tempo limite excedido';
                    break;
            }
            statusElement.innerHTML = '<i class="fas fa-exclamation-circle text-danger"></i> ' + errorMsg;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 600000
        }
    );
}

// Legacy function for compatibility
function getGPSLocation() {
    getGPSLocationAndAddress();
}

// Reverse geocoding to get address from coordinates and fill address field
function reverseGeocodeAndFillAddress(lat, lng) {
    // Use backend endpoint for consistent geocoding
    fetch('/get_location', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify({
            latitude: lat,
            longitude: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const endereco = document.querySelector('textarea[name="endereco"]') || document.getElementById('endereco');
            if (endereco) {
                endereco.value = data.endereco;
                
                // Show address preview
                const addressPreview = document.getElementById('addressPreview');
                const capturedAddress = document.getElementById('capturedAddress');
                if (addressPreview && capturedAddress) {
                    addressPreview.style.display = 'block';
                    capturedAddress.textContent = data.endereco;
                }
                
                // Update status to show completion
                const statusElement = document.getElementById('locationStatus');
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Localização e endereço capturados com sucesso!';
                }
            }
        } else {
            console.log('Erro ao obter endereço do servidor');
            
            // Fallback to coordinates
            const endereco = document.querySelector('textarea[name="endereco"]') || document.getElementById('endereco');
            if (endereco) {
                endereco.value = `Lat: ${lat}, Lng: ${lng}`;
            }
        }
    })
    .catch(error => {
        console.log('Erro ao obter endereço:', error);
        
        // Fallback to coordinates
        const endereco = document.querySelector('textarea[name="endereco"]') || document.getElementById('endereco');
        if (endereco) {
            endereco.value = `Lat: ${lat}, Lng: ${lng}`;
        }
    });
}

// Legacy function for compatibility
function reverseGeocode(lat, lng) {
    reverseGeocodeAndFillAddress(lat, lng);
}

// Initialize map
function initMap() {
    // Default center (São Paulo)
    const defaultLat = -23.5505;
    const defaultLng = -46.6333;
    
    map = L.map('map').setView([defaultLat, defaultLng], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Click handler
    map.on('click', function(e) {
        const lat = e.latlng.lat;
        const lng = e.latlng.lng;
        
        // Remove existing marker
        if (marker) {
            map.removeLayer(marker);
        }
        
        // Add new marker
        marker = L.marker([lat, lng]).addTo(map);
        
        selectedLat = lat;
        selectedLng = lng;
        
        // Get address for this location and fill the address field
        reverseGeocodeAndFillAddress(lat, lng);
    });
}

// Open map modal
function openMapModal() {
    const mapModal = new bootstrap.Modal(document.getElementById('mapModal'));
    mapModal.show();
    
    // Initialize map when modal is shown
    document.getElementById('mapModal').addEventListener('shown.bs.modal', function () {
        if (!map) {
            initMap();
        } else {
            map.invalidateSize();
        }
        
        // If we have existing coordinates, show them on map
        const latField = document.querySelector('input[name="latitude"]');
        const lngField = document.querySelector('input[name="longitude"]');
        const lat = latField ? latField.value : '';
        const lng = lngField ? lngField.value : '';
        
        if (lat && lng) {
            const latFloat = parseFloat(lat);
            const lngFloat = parseFloat(lng);
            
            map.setView([latFloat, lngFloat], 15);
            
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker([latFloat, lngFloat]).addTo(map);
            selectedLat = latFloat;
            selectedLng = lngFloat;
        }
    });
}

// Confirm map location
function confirmMapLocation() {
    if (selectedLat && selectedLng) {
        const latField = document.querySelector('input[name="latitude"]');
        const lngField = document.querySelector('input[name="longitude"]');
        if (latField) latField.value = selectedLat;
        if (lngField) lngField.value = selectedLng;
        
        // Get address for this location and fill address field
        reverseGeocodeAndFillAddress(selectedLat, selectedLng);
        
        const statusElement = document.getElementById('locationStatus');
        statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Localização selecionada no mapa';
        
        // Close modal
        const mapModal = bootstrap.Modal.getInstance(document.getElementById('mapModal'));
        if (mapModal) {
            mapModal.hide();
        }
    }
}

// Funções para gerenciar campo de cargo com opções pré-definidas
function handleProjectCargoChange(select, index) {
    const customContainer = document.getElementById(`cargo_custom_container_${index}`);
    const cargoHidden = document.getElementById(`cargo_hidden_${index}`);
    
    if (select.value === 'outro') {
        customContainer.style.display = 'block';
        const customInput = customContainer.querySelector('.cargo-custom-input');
        cargoHidden.value = customInput ? customInput.value : '';
    } else {
        customContainer.style.display = 'none';
        cargoHidden.value = select.value;
    }
}

function updateProjectCargoHidden(input, index) {
    const cargoHidden = document.getElementById(`cargo_hidden_${index}`);
    cargoHidden.value = input.value;
}

// Gestão de Contatos da Obra
let categoriaCounter = 0;
let contatosExcluidos = [];
let contatoCounter = "jinja_var";

document.getElementById('addContatoBtn').addEventListener('click', function() {
    const lista = document.getElementById('lista-contatos');
    const novo = document.createElement('div');
    novo.classList.add('card-contato');
    novo.setAttribute('data-index', contatoCounter);
    novo.innerHTML = `
        <div class="form-group">
            <label>Nome</label>
            <input type="text" name="contatos[${contatoCounter}][nome]" class="form-control" required>
        </div>
        <div class="form-group">
            <label>Cargo</label>
            <select name="contatos[${contatoCounter}][cargo_select]" class="form-select cargo-select" onchange="handleProjectCargoChange(this, ${contatoCounter})">
                <option value="">Selecione um cargo...</option>
                <option value="Engenheiro/a">Engenheiro/a</option>
                <option value="Arquiteto/a">Arquiteto/a</option>
                <option value="Analista">Analista</option>
                <option value="Assistente">Assistente</option>
                <option value="Encarregado">Encarregado</option>
                <option value="Mestre">Mestre</option>
                <option value="Estagiário/a">Estagiário/a</option>
                <option value="outro">Outro (adicionar novo)</option>
            </select>
            <div class="cargo-custom-container mt-2" id="cargo_custom_container_${contatoCounter}" style="display: none;">
                <input type="text" class="form-control cargo-custom-input" placeholder="Digite o cargo personalizado" onchange="updateProjectCargoHidden(this, ${contatoCounter})">
            </div>
            <input type="hidden" name="contatos[${contatoCounter}][cargo]" class="cargo-hidden" id="cargo_hidden_${contatoCounter}" value="">
        </div>
        <div class="form-group">
            <label>Empresa</label>
            <input type="text" name="contatos[${contatoCounter}][empresa]" class="form-control">
        </div>
        <div class="form-group">
            <label>E-mail (opcional)</label>
            <input type="email" name="contatos[${contatoCounter}][email]" class="form-control" placeholder="email@exemplo.com">
        </div>
        <div class="form-group">
            <label>Telefone (opcional)</label>
            <input type="text" name="contatos[${contatoCounter}][telefone]" class="form-control">
        </div>
        <button type="button" class="btn btn-danger btn-sm btn-excluir" onclick="removerContato(this)">
            <i class="bi bi-trash"></i> Excluir
        </button>`;
    lista.appendChild(novo);
    contatoCounter++;
});

function removerContato(btn, contatoId) {
    const card = btn.closest('.card-contato');
    
    // Se o contato tem ID (já existe no banco), marcar para exclusão
    if (contatoId) {
        contatosExcluidos.push(contatoId);
        
        // Adicionar campo hidden para enviar IDs dos contatos a serem excluídos
        const form = document.getElementById('projectForm');
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'contatos_excluidos[]';
        input.value = contatoId;
        form.appendChild(input);
    }
    
    // Remover o card da interface
    card.remove();
}

// Função para remover e-mail
function removerEmail(id) {
    const emailDiv = document.getElementById(`email-${id}`);
    if (emailDiv) {
        emailDiv.remove();
    }
}

// Função para adicionar categoria - Item 16
function adicionarCategoria() {
    categoriaCounter++;
    const categoriasList = document.getElementById('categorias-list');
    
    const categoriaDiv = document.createElement('div');
    categoriaDiv.className = 'border rounded p-3 mb-3';
    categoriaDiv.id = `categoria-${categoriaCounter}`;
    
    categoriaDiv.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <label class="form-label">Nome da Categoria</label>
                <input type="text" class="form-control" name="categorias[${categoriaCounter}][nome]" placeholder="Ex: Torre 1, Área Comum, etc." required>
            </div>
            <div class="col-md-4">
                <label class="form-label">Ordem de Exibição</label>
                <input type="number" class="form-control" name="categorias[${categoriaCounter}][ordem]" value="${categoriaCounter}" min="0">
            </div>
            <div class="col-md-2 d-flex align-items-end">
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removerCategoria(${categoriaCounter})">
                    <i class="fas fa-trash"></i> Remover
                </button>
            </div>
        </div>
    `;
    
    categoriasList.appendChild(categoriaDiv);
}

// Função para remover categoria
function removerCategoria(id) {
    const categoriaDiv = document.getElementById(`categoria-${id}`);
    if (categoriaDiv) {
        categoriaDiv.remove();
    }
}


// Script de edição de categorias - conforme orientações do prompt
const categoriasExistentes = "jinja_var";
console.log("Categorias carregadas:", categoriasExistentes);

const container = document.getElementById("categorias-container");

// Função para renderizar as categorias
function renderCategorias() {
  container.innerHTML = "";
  categoriasExistentes.forEach(cat => {
    const card = document.createElement("div");
    card.className = "card mb-3";
    card.innerHTML = `
      <div class="card-body">
        <label>Nome da Categoria</label>
        <input type="text" class="form-control nome-categoria" data-id="${cat.id}" value="${cat.nome || ''}">
        <small class="text-muted d-block mt-1">Categoria vinculada ao projeto #${cat.project_id}</small>

        <label class="mt-2">Ordem de Exibição</label>
        <input type="number" class="form-control ordem-categoria" data-id="${cat.id}" value="${cat.ordem || 0}">

        <div class="mt-3 d-flex gap-2">
          <button type="button" class="btn btn-danger btn-delete" data-id="${cat.id}">🗑️ Excluir</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}
renderCategorias();

// Remover botão salvar e lidar com atualização via formulário principal
container.addEventListener("input", (e) => {
  if (e.target.classList.contains("nome-categoria") || e.target.classList.contains("ordem-categoria")) {
    const id = e.target.dataset.id;
    const cat = categoriasExistentes.find(c => c.id == id);
    if (cat) {
      if (e.target.classList.contains("nome-categoria")) cat.nome = e.target.value;
      if (e.target.classList.contains("ordem-categoria")) cat.ordem = e.target.value;
      updateCategoriasHiddenField();
    }
  }
});

// Garantir que os dados sejam atualizados antes da submissão
document.getElementById('projectForm').addEventListener('submit', function(e) {
  updateCategoriasHiddenField();
});

function updateCategoriasHiddenField() {
  let hiddenField = document.getElementById('categoriasHidden');
  if (!hiddenField) {
    hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.id = 'categoriasHidden';
    hiddenField.name = 'categorias_json';
    document.getElementById('projectForm').appendChild(hiddenField);
  }
  
  // Sincronizar dados atuais dos inputs antes de salvar no JSON
  categoriasExistentes.forEach(cat => {
    const nomeInput = document.querySelector(`.nome-categoria[data-id='${cat.id}']`);
    const ordemInput = document.querySelector(`.ordem-categoria[data-id='${cat.id}']`);
    if (nomeInput) cat.nome = nomeInput.value;
    if (ordemInput) cat.ordem = ordemInput.value;
  });
  
  hiddenField.value = JSON.stringify(categoriasExistentes);
}

container.addEventListener("click", async (e) => {
  if (e.target.classList.contains("btn-delete")) {
    const id = e.target.dataset.id;
    if (!confirm("Deseja realmente excluir esta categoria?")) return;

    const res = await fetch(`/api/categorias/${id}/delete`, { method: "DELETE" });
    const data = await res.json();
    alert(data.message || "Categoria excluída!");
    categoriasExistentes.splice(categoriasExistentes.findIndex(c => c.id == id), 1);
    renderCategorias();
  }
});

// Adicionar nova categoria (visualmente)
document.getElementById("btnAddCategoria").addEventListener("click", () => {
  const nova = {
    id: Date.now(), // temporário até salvar
    nome: "",
    ordem: categoriasExistentes.length + 1,
    project_id: "jinja_var"
  };
  categoriasExistentes.push(nova);
  renderCategorias();
  updateCategoriasHiddenField();
});


// Aplicar normalização de endereços quando carregar a página
document.addEventListener('DOMContentLoaded', function() {
    
    const enderecoField = document.querySelector('textarea[name="endereco"]') || document.getElementById('endereco');
    
    if (enderecoField && window.normalizeAddress) {
        // Normalizar quando o usuário sair do campo
        enderecoField.addEventListener('blur', function() {
            const originalValue = this.value;
            const normalizedValue = window.normalizeAddress(originalValue);
            
            if (originalValue !== normalizedValue) {
                this.value = normalizedValue;
                
                // Mostrar feedback visual
                const statusElement = document.getElementById('locationStatus');
                if (statusElement) {
                    statusElement.innerHTML = '<i class="fas fa-check text-success"></i> Endereço normalizado automaticamente';
                    setTimeout(() => {
                        statusElement.innerHTML = '';
                    }, 3000);
                }
            }
        });
        
    }
});

// Função para geocodificar endereço digitado para coordenadas
function geocodeAddressToCoordinates() {
    const enderecoField = document.querySelector('textarea[name="endereco"]') || document.getElementById('endereco');
    const statusElement = document.getElementById('locationStatus');
    
    if (!enderecoField || !enderecoField.value.trim()) {
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-warning"></i> Por favor, digite um endereço primeiro';
        }
        return;
    }
    
    const originalAddress = enderecoField.value.trim();
    const normalizedAddress = window.normalizeAddress ? window.normalizeAddress(originalAddress) : originalAddress;
    
    // Update field with normalized address if different
    if (originalAddress !== normalizedAddress) {
        enderecoField.value = normalizedAddress;
    }
    
    if (statusElement) {
        statusElement.innerHTML = '<i class="fas fa-spinner fa-spin text-primary"></i> Buscando coordenadas...';
    }
    
    // Create a simple geocoding API call to backend
    fetch('/api/geocode-address', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
        },
        body: JSON.stringify({
            address: normalizedAddress
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.latitude && data.longitude) {
            // Fill coordinate fields
            const latField = document.querySelector('input[name="latitude"]');
            const lngField = document.querySelector('input[name="longitude"]');
            if (latField) latField.value = data.latitude;
            if (lngField) lngField.value = data.longitude;
            
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Coordenadas encontradas!';
            }
            
            // Show address preview
            const addressPreview = document.getElementById('addressPreview');
            const capturedAddress = document.getElementById('capturedAddress');
            if (addressPreview && capturedAddress) {
                addressPreview.style.display = 'block';
                capturedAddress.textContent = `Coords: ${data.latitude}, ${data.longitude}`;
            }
        } else {
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-exclamation-circle text-danger"></i> Não foi possível encontrar as coordenadas';
            }
        }
    })
    .catch(error => {
        console.error('Erro no geocoding:', error);
        if (statusElement) {
            statusElement.innerHTML = '<i class="fas fa-exclamation-circle text-danger"></i> Erro de conexão';
        }
    });
}

// Checklist Configuration System
let currentChecklistType = '"jinja_var"''padrao';
let customChecklistItems = [];
const isNewProject = falsetrue;

// Standard checklist items for pre-loading when switching to personalized
const standardChecklistItems = [
    
    { id: "jinja_var", texto: ""jinja_var"", ordem: "jinja_var" },
    
];

// Initialize checklist on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize hidden fields ONLY for new projects (form submission)
    // Existing projects use API-only updates (no form submission for checklists)
    if (isNewProject) {
        updateChecklistTypeHiddenField(currentChecklistType);
        updateChecklistItemsHiddenField();
    }
    
    if (!isNewProject) {
        // Set initial button state for existing projects
        updateChecklistTypeButtons(currentChecklistType);
        selectChecklistType(currentChecklistType, true);
        
        // Load custom checklist items for existing projects with custom checklist
        
        loadCustomChecklistItems();
        
    } else {
        // For new projects, allow both options
        updateChecklistTypeButtons('padrao');
        selectChecklistType('padrao');
    }
});

function selectChecklistType(tipo, skipSave = false) {
    currentChecklistType = tipo;
    
    // Update button states
    updateChecklistTypeButtons(tipo);
    
    // Show/hide appropriate sections
    const padraoPreview = document.getElementById('checklistPadraoPreview');
    const personalizadoEditor = document.getElementById('checklistPersonalizadoEditor');
    const currentDisplay = document.getElementById('currentChecklistDisplay');
    
    if (tipo === 'padrao') {
        padraoPreview.style.display = 'block';
        personalizadoEditor.style.display = 'none';
        if (currentDisplay) currentDisplay.style.display = 'none';
        
        // Clear custom items for new projects when switching to padrao
        if (isNewProject) {
            customChecklistItems = [];
            updateChecklistItemsHiddenField();
        }
        
        // Save configuration for existing projects
        if (!isNewProject && !skipSave) {
            saveChecklistConfig('padrao');
        }
    } else {
        padraoPreview.style.display = 'none';
        personalizadoEditor.style.display = 'block';
        if (currentDisplay) currentDisplay.style.display = 'none';
        
        // For new projects, pre-load standard checklist items if empty
        if (isNewProject) {
            if (customChecklistItems.length === 0 && standardChecklistItems.length > 0) {
                customChecklistItems = JSON.parse(JSON.stringify(standardChecklistItems));
                updateChecklistItemsHiddenField();
            }
            renderCustomChecklistItems();
        }
        
        // Save configuration for existing projects and load items
        if (!isNewProject) {
            if (!skipSave) saveChecklistConfig('personalizado');
            loadCustomChecklistItems();
        }
    }
    
    // Update hidden field for form submission
    updateChecklistTypeHiddenField(tipo);
}

function updateChecklistTypeButtons(tipo) {
    const btnPadrao = document.getElementById('btnChecklistPadrao');
    const btnPersonalizado = document.getElementById('btnChecklistPersonalizado');
    
    if (tipo === 'padrao') {
        btnPadrao.classList.remove('btn-outline-primary');
        btnPadrao.classList.add('btn-primary');
        btnPersonalizado.classList.remove('btn-success');
        btnPersonalizado.classList.add('btn-outline-success');
    } else {
        btnPadrao.classList.remove('btn-primary');
        btnPadrao.classList.add('btn-outline-primary');
        btnPersonalizado.classList.remove('btn-outline-success');
        btnPersonalizado.classList.add('btn-success');
    }
}

function saveChecklistConfig(tipo) {
    if (isNewProject) {
        console.log('Skipping config save for new project');
        return;
    }
    
    
    const projectId = "jinja_var";
    
    fetch(`/projects/${projectId}/checklist/config`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tipo_checklist: tipo
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Checklist config saved:', data.message);
        } else {
            console.error('Error saving config:', data.error);
            alert('Erro ao salvar configuração: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Erro ao salvar configuração do checklist');
    });
    
}

function loadCustomChecklistItems() {
    if (isNewProject) {
        console.log('Skipping load for new project');
        return;
    }
    
    
    const projectId = "jinja_var";
    
    fetch(`/projects/${projectId}/checklist/items/list`, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            customChecklistItems = data.items;
            renderCustomChecklistItems();
        }
    })
    .catch(error => {
        console.error('Error loading items:', error);
    });
    
}

function addChecklistItem(event) {
    if (event) event.preventDefault();
    
    const texto = document.getElementById('newChecklistItemText').value.trim();
    
    if (!texto) {
        alert('Por favor, digite o texto do item');
        return;
    }
    
    if (isNewProject) {
        // For new projects, store temporarily in memory
        const newItem = {
            id: Date.now(), // Temporary ID
            texto: texto,
            ordem: customChecklistItems.length + 1
        };
        customChecklistItems.push(newItem);
        renderCustomChecklistItems();
        updateChecklistItemsHiddenField();
        document.getElementById('newChecklistItemText').value = '';
    } else {
        
        // For existing projects, use API-only approach (immediate save to database)
        const projectId = "jinja_var";
        
        fetch(`/projects/${projectId}/checklist/items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                texto: texto
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                customChecklistItems.push(data.item);
                renderCustomChecklistItems();
                document.getElementById('newChecklistItemText').value = '';
            } else {
                alert('Erro: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erro ao adicionar item');
        });
        
    }
}

function editChecklistItem(itemId) {
    const card = document.querySelector(`[data-checklist-item-id="${itemId}"]`);
    const textSpan = card.querySelector('.item-text');
    const editInput = card.querySelector('.item-edit-input');
    const editBtn = card.querySelector('.btn-edit-item');
    const saveBtn = card.querySelector('.btn-save-item');
    const cancelBtn = card.querySelector('.btn-cancel-item');
    const deleteBtn = card.querySelector('.btn-delete-item');
    
    textSpan.classList.add('d-none');
    editInput.classList.remove('d-none');
    editBtn.classList.add('d-none');
    saveBtn.classList.remove('d-none');
    cancelBtn.classList.remove('d-none');
    deleteBtn.classList.add('d-none');
    
    editInput.focus();
}

function saveChecklistItem(itemId) {
    const card = document.querySelector(`[data-checklist-item-id="${itemId}"]`);
    const editInput = card.querySelector('.item-edit-input');
    const texto = editInput.value.trim();
    
    if (!texto) {
        alert('Digite o texto do item');
        return;
    }
    
    if (isNewProject) {
        // For new projects, update in memory
        const item = customChecklistItems.find(i => i.id === itemId);
        if (item) {
            item.texto = texto;
            renderCustomChecklistItems();
            updateChecklistItemsHiddenField();
        }
    } else {
        
        const projectId = "jinja_var";
        
        fetch(`/projects/${projectId}/checklist/items/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                texto: texto
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const item = customChecklistItems.find(i => i.id === itemId);
                if (item) item.texto = texto;
                renderCustomChecklistItems();
            } else {
                alert('Erro: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erro ao salvar item');
        });
        
    }
}

function cancelEditChecklistItem(itemId) {
    renderCustomChecklistItems();
}

function deleteChecklistItem(itemId) {
    if (!confirm('Tem certeza que deseja remover este item do checklist?')) {
        return;
    }
    
    if (isNewProject) {
        // For new projects, remove from memory
        customChecklistItems = customChecklistItems.filter(i => i.id !== itemId);
        renderCustomChecklistItems();
        updateChecklistItemsHiddenField();
    } else {
        
        const projectId = "jinja_var";
        
        fetch(`/projects/${projectId}/checklist/items/${itemId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                customChecklistItems = customChecklistItems.filter(i => i.id !== itemId);
                renderCustomChecklistItems();
            } else {
                alert('Erro: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erro ao remover item');
        });
        
    }
}

function moveChecklistItemUp(itemId) {
    const index = customChecklistItems.findIndex(i => i.id === itemId);
    if (index > 0) {
        // Swap with previous
        const temp = customChecklistItems[index];
        customChecklistItems[index] = customChecklistItems[index - 1];
        customChecklistItems[index - 1] = temp;
        
        // Update order numbers
        customChecklistItems.forEach((item, i) => item.ordem = i + 1);
        
        renderCustomChecklistItems();
        if (isNewProject) {
            updateChecklistItemsHiddenField();
        } else {
            saveReorderedItems();
        }
    }
}

function moveChecklistItemDown(itemId) {
    const index = customChecklistItems.findIndex(i => i.id === itemId);
    if (index >= 0 && index < customChecklistItems.length - 1) {
        // Swap with next
        const temp = customChecklistItems[index];
        customChecklistItems[index] = customChecklistItems[index + 1];
        customChecklistItems[index + 1] = temp;
        
        // Update order numbers
        customChecklistItems.forEach((item, i) => item.ordem = i + 1);
        
        renderCustomChecklistItems();
        if (isNewProject) {
            updateChecklistItemsHiddenField();
        } else {
            saveReorderedItems();
        }
    }
}

function saveReorderedItems() {
    
    const projectId = "jinja_var";
    const orderData = customChecklistItems.map(item => ({ id: item.id, ordem: item.ordem }));
    
    fetch(`/projects/${projectId}/checklist/items/reorder`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ items: orderData })
    })
    .catch(error => {
        console.error('Error reordering items:', error);
    });
    
}


function renderCustomChecklistItems() {
    const container = document.getElementById('customChecklistItems');
    const emptyMessage = document.getElementById('emptyChecklistMessage');
    
    if (!container) return;
    
    if (customChecklistItems.length === 0) {
        if (emptyMessage) emptyMessage.style.display = 'block';
        container.innerHTML = '';
        return;
    }
    
    if (emptyMessage) emptyMessage.style.display = 'none';
    
    let html = '';
    customChecklistItems.forEach((item, index) => {
        const isFirst = index === 0;
        const isLast = index === customChecklistItems.length - 1;
        
        html += `
            <div class="card mb-2" data-checklist-item-id="${item.id}">
                <div class="card-body py-2">
                    <div class="row align-items-center g-2">
                        <div class="col-auto d-flex flex-column" style="gap:4px;">
                            <button type="button" onclick="moveChecklistItemUp(${item.id})" title="Subir item" ${isFirst ? 'disabled' : ''}
                                style="display:flex;align-items:center;justify-content:center;width:44px;height:38px;border:1px solid #ced4da;border-radius:6px;background:#f8f9fa;color:#495057;cursor:pointer;font-size:0.85rem;${isFirst ? 'opacity:0.35;pointer-events:none;' : ''}">
                                <i class="fas fa-chevron-up"></i>
                            </button>
                            <button type="button" onclick="moveChecklistItemDown(${item.id})" title="Descer item" ${isLast ? 'disabled' : ''}
                                style="display:flex;align-items:center;justify-content:center;width:44px;height:38px;border:1px solid #ced4da;border-radius:6px;background:#f8f9fa;color:#495057;cursor:pointer;font-size:0.85rem;${isLast ? 'opacity:0.35;pointer-events:none;' : ''}">
                                <i class="fas fa-chevron-down"></i>
                            </button>
                        </div>
                        <div class="col">
                            <span class="item-text">${item.texto}</span>
                            <input type="text" class="form-control d-none item-edit-input" value="${item.texto}">
                        </div>
                        <div class="col-auto text-end">
                            <button type="button" class="btn btn-sm btn-outline-primary me-1 btn-edit-item" onclick="editChecklistItem(${item.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-success d-none btn-save-item" onclick="saveChecklistItem(${item.id})">
                                <i class="fas fa-check"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-secondary d-none btn-cancel-item" onclick="cancelEditChecklistItem(${item.id})">
                                <i class="fas fa-times"></i>
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger btn-delete-item" onclick="deleteChecklistItem(${item.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Helper function to update hidden field with checklist type
function updateChecklistTypeHiddenField(tipo) {
    let hiddenField = document.getElementById('checklistTypeHidden');
    if (!hiddenField) {
        hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.id = 'checklistTypeHidden';
        hiddenField.name = 'checklist_tipo';
        document.getElementById('projectForm').appendChild(hiddenField);
    }
    hiddenField.value = tipo;
}

// Chevron animation for Informações Técnicas
document.addEventListener('DOMContentLoaded', function() {
    const collapseEl = document.getElementById('collapseTechInfo');
    const chevron = document.getElementById('techInfoChevron');
    if (collapseEl && chevron) {
        collapseEl.addEventListener('show.bs.collapse', function() {
            chevron.style.transform = 'rotate(180deg)';
        });
        collapseEl.addEventListener('hide.bs.collapse', function() {
            chevron.style.transform = 'rotate(0deg)';
        });
    }
});

// Helper function to update hidden field with custom checklist items
function updateChecklistItemsHiddenField() {
    let hiddenField = document.getElementById('checklistItemsHidden');
    if (!hiddenField) {
        hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.id = 'checklistItemsHidden';
        hiddenField.name = 'checklist_items';
        document.getElementById('projectForm').appendChild(hiddenField);
    }
    hiddenField.value = JSON.stringify(customChecklistItems);
}
