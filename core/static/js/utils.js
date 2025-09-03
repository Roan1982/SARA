// SARA - Sistema Administrativo de Registros - Utilidades JavaScript

// Función para mostrar notificaciones toast
function showToast(message, type = 'info', duration = 3000) {
    // Crear contenedor si no existe
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Crear toast
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white border-0 show ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Auto-remover después de la duración
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, duration);

    // Agregar funcionalidad de cerrar
    const closeBtn = toast.querySelector('.btn-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            toast.remove();
        });
    }
}

// Obtener icono según el tipo de toast
function getToastIcon(type) {
    const icons = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

// Función para mostrar loading overlay
function showLoading(message = 'Cargando...') {
    // Remover loading existente
    hideLoading();

    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.id = 'loading-overlay';

    loadingOverlay.innerHTML = `
        <div class="text-center">
            <div class="loading-spinner mx-auto"></div>
            <div class="mt-3 text-white">${message}</div>
        </div>
    `;

    document.body.appendChild(loadingOverlay);
}

// Función para ocultar loading overlay
function hideLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// Función para confirmar acciones
function confirmAction(message, callback) {
    if (window.confirm(message)) {
        callback();
    }
}

// Función para copiar al portapapeles
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copiado al portapapeles', 'success');
    } catch (err) {
        // Fallback para navegadores antiguos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Copiado al portapapeles', 'success');
    }
}

// Función para formatear fechas
function formatDate(date, format = 'DD/MM/YYYY') {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    switch (format) {
        case 'DD/MM/YYYY':
            return `${day}/${month}/${year}`;
        case 'MM/DD/YYYY':
            return `${month}/${day}/${year}`;
        case 'YYYY-MM-DD':
            return `${year}-${month}-${day}`;
        default:
            return `${day}/${month}/${year}`;
    }
}

// Función para validar email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Función para validar contraseña
function isValidPassword(password) {
    // Al menos 8 caracteres, una mayúscula, una minúscula y un número
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$/;
    return passwordRegex.test(password);
}

// Función para debounce (prevenir llamadas excesivas)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Función para throttle (limitar frecuencia de llamadas)
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Función para animar elementos al hacer scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
            }
        });
    });

    elements.forEach(element => {
        observer.observe(element);
    });
}

// Función para manejar errores AJAX
function handleAjaxError(xhr, status, error) {
    console.error('Error AJAX:', error);

    let message = 'Ha ocurrido un error inesperado.';

    if (xhr.status === 400) {
        message = 'Datos inválidos. Por favor, verifica la información.';
    } else if (xhr.status === 401) {
        message = 'No autorizado. Por favor, inicia sesión nuevamente.';
    } else if (xhr.status === 403) {
        message = 'No tienes permisos para realizar esta acción.';
    } else if (xhr.status === 404) {
        message = 'Recurso no encontrado.';
    } else if (xhr.status === 500) {
        message = 'Error interno del servidor. Inténtalo más tarde.';
    }

    showToast(message, 'error');
}

// Función para actualizar CSRF token
function updateCsrfToken(newToken) {
    const csrfInputs = document.querySelectorAll('input[name="csrfmiddlewaretoken"]');
    csrfInputs.forEach(input => {
        input.value = newToken;
    });
}

// Función para obtener parámetros de URL
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// Función para validar formularios
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });

    // Validar emails
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });

    // Validar contraseñas
    const passwordFields = form.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        if (field.value && !isValidPassword(field.value)) {
            field.classList.add('is-invalid');
            isValid = false;
        }
    });

    return isValid;
}

// Función para limpiar validaciones de formulario
function clearFormValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const invalidFields = form.querySelectorAll('.is-invalid');
    invalidFields.forEach(field => {
        field.classList.remove('is-invalid');
    });
}

// Función para mostrar/ocultar contraseña
function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);

    if (input && button) {
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';

        const icon = button.querySelector('i');
        if (icon) {
            icon.className = isPassword ? 'fas fa-eye-slash' : 'fas fa-eye';
        }
    }
}

// Función para inicializar tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Función para inicializar popovers
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    animateOnScroll();
    initializeTooltips();
    initializePopovers();
});

// Exportar funciones globales
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.confirmAction = confirmAction;
window.copyToClipboard = copyToClipboard;
window.formatDate = formatDate;
window.isValidEmail = isValidEmail;
window.isValidPassword = isValidPassword;
window.debounce = debounce;
window.throttle = throttle;
window.handleAjaxError = handleAjaxError;
window.updateCsrfToken = updateCsrfToken;
window.getUrlParameter = getUrlParameter;
window.validateForm = validateForm;
window.clearFormValidation = clearFormValidation;
window.togglePasswordVisibility = togglePasswordVisibility;
