// Main JavaScript file for Construction Site Visit Tracking System

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeComponents();
    setupFormValidation();
    setupDateTimeInputs();
    setupPhotoPreview();
    setupLocationServices();
    setupNotifications();
});

// Initialize all components
function initializeComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
}

// Setup form validation
function setupFormValidation() {
    // Custom validation for forms
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            validateEmail(this);
        });
    });

    // Phone validation (Brazilian format)
    const phoneInputs = document.querySelectorAll('input[name="telefone"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            formatPhoneNumber(this);
        });
    });
}

// Setup date and time inputs
function setupDateTimeInputs() {
    // Set minimum date to today for future dates
    const futureDateInputs = document.querySelectorAll('input[type="date"]:not(.allow-past)');
    const today = new Date().toISOString().split('T')[0];
    
    futureDateInputs.forEach(function(input) {
        if (!input.value) {
            input.min = today;
        }
    });

    // Set default datetime for visit scheduling
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    datetimeInputs.forEach(function(input) {
        if (!input.value) {
            const now = new Date();
            now.setMinutes(0); // Round to the hour
            now.setSeconds(0);
            now.setMilliseconds(0);
            input.value = now.toISOString().slice(0, 16);
            input.min = now.toISOString().slice(0, 16);
        }
    });
}

// Setup photo preview functionality
function setupPhotoPreview() {
    const photoInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    
    photoInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            previewImage(this);
        });
    });
}

// Setup location services
function setupLocationServices() {
    const getLocationBtns = document.querySelectorAll('#getLocationBtn');
    
    getLocationBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            getCurrentLocation(this);
        });
    });
}

// Setup notification system
function setupNotifications() {
    // Check for notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
}

// Utility functions

// Email validation
function validateEmail(input) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(input.value);
    
    if (input.value && !isValid) {
        input.classList.add('is-invalid');
        showFieldError(input, 'Por favor, insira um email válido.');
    } else {
        input.classList.remove('is-invalid');
        hideFieldError(input);
    }
}

// Format phone number (Brazilian format)
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length >= 11) {
        value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 10) {
        value = value.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 6) {
        value = value.replace(/(\d{2})(\d{4})(\d*)/, '($1) $2-$3');
    } else if (value.length >= 2) {
        value = value.replace(/(\d{2})(\d*)/, '($1) $2');
    }
    
    input.value = value;
}

// Preview uploaded image
function previewImage(input) {
    const file = input.files[0];
    if (!file) return;

    // Sem limite individual de arquivo - apenas limite total do relatório (3GB)

    // Validate file type
    if (!file.type.startsWith('image/')) {
        showAlert('Erro: Por favor, selecione apenas arquivos de imagem.', 'danger');
        input.value = '';
        return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        let preview = document.getElementById('imagePreview');
        
        if (!preview) {
            preview = document.createElement('div');
            preview.id = 'imagePreview';
            preview.className = 'mt-3';
            input.parentNode.appendChild(preview);
        }
        
        preview.innerHTML = `
            <div class="card" style="max-width: 300px;">
                <img src="${e.target.result}" class="card-img-top" alt="Preview">
                <div class="card-body p-2">
                    <small class="text-muted">
                        <i class="fas fa-file-image me-1"></i>
                        ${file.name} (${formatFileSize(file.size)})
                    </small>
                </div>
            </div>
        `;
    };
    
    reader.readAsDataURL(file);
}

// Get current location using GPS
function getCurrentLocation(button) {
    if (!navigator.geolocation) {
        showAlert('Geolocalização não é suportada neste navegador.', 'warning');
        return;
    }

    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Obtendo...';
    button.disabled = true;

    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
    };

    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            const accuracy = position.coords.accuracy;

            // Fill form fields
            const latInput = document.querySelector('input[name="latitude"]');
            const lngInput = document.querySelector('input[name="longitude"]');
            const addressInput = document.querySelector('input[name="endereco_gps"]');

            if (latInput) latInput.value = lat;
            if (lngInput) lngInput.value = lng;
            if (addressInput) {
                addressInput.value = `Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)} (±${Math.round(accuracy)}m)`;
            }

            // Show success
            button.innerHTML = '<i class="fas fa-check me-1"></i>Localização Obtida';
            button.classList.remove('btn-outline-primary');
            button.classList.add('btn-success');

            showAlert('Localização obtida com sucesso!', 'success');

            // Try to get address from coordinates (optional)
            reverseGeocode(lat, lng, addressInput);
        },
        function(error) {
            let errorMessage;
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = 'Acesso à localização foi negado pelo usuário.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = 'Informação de localização não disponível.';
                    break;
                case error.TIMEOUT:
                    errorMessage = 'Tempo esgotado ao obter localização.';
                    break;
                default:
                    errorMessage = 'Erro desconhecido ao obter localização.';
                    break;
            }

            showAlert(errorMessage, 'danger');
            button.innerHTML = originalText;
            button.disabled = false;
        },
        options
    );
}

// Reverse geocoding using backend proxy
// Função para mostrar instruções sobre como habilitar localização
function showLocationInstructions() {
    const isAndroid = /Android/i.test(navigator.userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    
    let instructions = '';
    
    if (isAndroid) {
        instructions = `
            <strong>📱 Para habilitar localização no Android:</strong><br>
            1. Toque no ícone de cadeado/informações na barra de endereço<br>
            2. Selecione "Localização" → "Permitir"<br>
            3. Ou vá em Configurações → Apps → Navegador → Permissões → Localização
        `;
    } else if (isIOS) {
        instructions = `
            <strong>📱 Para habilitar localização no iOS:</strong><br>
            1. Vá em Configurações → Privacidade → Serviços de Localização<br>
            2. Ative "Serviços de Localização"<br>
            3. Role para baixo até seu navegador (Safari/Chrome) e ative
        `;
    } else {
        instructions = `
            <strong>💻 Para habilitar localização:</strong><br>
            1. Clique no ícone de localização na barra de endereço<br>
            2. Selecione "Sempre permitir"<br>
            3. Recarregue a página
        `;
    }
    
    return instructions;
}

// Função melhorada para tratar erros de geolocalização
function handleGeolocationError(error, buttonElement) {
    let errorMessage = '';
    let instructions = '';
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '🚫 Permissão de localização negada';
            instructions = showLocationInstructions();
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '📍 Localização indisponível';
            instructions = 'Verifique se o GPS está ativado e tente novamente.';
            break;
        case error.TIMEOUT:
            errorMessage = '⏰ Tempo limite para obter localização';
            instructions = 'Tente novamente em alguns segundos.';
            break;
        default:
            errorMessage = '❌ Erro desconhecido de localização';
            instructions = 'Verifique as configurações do seu dispositivo.';
            break;
    }
    
    // Mostrar modal com instruções
    const modal = document.createElement('div');
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${errorMessage}</h5>
                    <button type="button" class="btn-close" onclick="this.closest('.modal').remove()"></button>
                </div>
                <div class="modal-body">
                    <p>${instructions}</p>
                    <div class="alert alert-info">
                        <strong>💡 Dica:</strong> Após alterar as configurações, recarregue a página e tente novamente.
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">Entendi</button>
                    <button type="button" class="btn btn-primary" onclick="window.location.reload()">Recarregar Página</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Restaurar botão se fornecido
    if (buttonElement) {
        buttonElement.innerHTML = '<i class="fas fa-map-marker-alt"></i> Tentar Novamente';
        buttonElement.disabled = false;
        buttonElement.className = 'btn btn-outline-warning';
    }
}

function reverseGeocode(lat, lng, addressInput) {
    if (!addressInput) return;

    fetch('/api/reverse-geocoding', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({
            latitude: lat,
            longitude: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.endereco) {
            addressInput.value = data.endereco;
            console.log('Endereço obtido:', data.endereco);
        } else {
            console.log('Não foi possível obter endereço, mantendo coordenadas');
        }
    })
    .catch(error => {
        console.log('Erro no reverse geocoding:', error);
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type} alert-dismissible fade show`;
    alertContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert at the top of the main container
    const mainContainer = document.querySelector('main.container');
    if (mainContainer) {
        mainContainer.insertBefore(alertContainer, mainContainer.firstChild);
    }

    // Auto-remove after 5 seconds
    setTimeout(function() {
        if (alertContainer.parentNode) {
            alertContainer.remove();
        }
    }, 5000);
}

// Show field error
function showFieldError(input, message) {
    let errorDiv = input.parentNode.querySelector('.invalid-feedback');
    
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        input.parentNode.appendChild(errorDiv);
    }
    
    errorDiv.textContent = message;
}

// Hide field error
function hideFieldError(input) {
    const errorDiv = input.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Currency formatting
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

// Date formatting
function formatDate(date) {
    return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
}

// DateTime formatting
function formatDateTime(date) {
    return new Intl.DateTimeFormat('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Confirm deletion
function confirmDelete(message = 'Tem certeza que deseja excluir este item?') {
    return confirm(message);
}

// Show loading state
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Carregando...';
    element.disabled = true;
    return originalContent;
}

// Hide loading state
function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('Copiado para a área de transferência!', 'success');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showAlert('Copiado para a área de transferência!', 'success');
    }
}

// Check network status
function checkNetworkStatus() {
    if (!navigator.onLine) {
        showAlert('Você está offline. Algumas funcionalidades podem não estar disponíveis.', 'warning');
    }
}

// Initialize network status check
window.addEventListener('online', function() {
    showAlert('Conexão restabelecida!', 'success');
});

window.addEventListener('offline', function() {
    showAlert('Você está offline!', 'warning');
});

// Export functions for global use
window.ConstructionApp = {
    showAlert,
    formatCurrency,
    formatDate,
    formatDateTime,
    confirmDelete,
    showLoading,
    hideLoading,
    copyToClipboard,
    getCurrentLocation
};
