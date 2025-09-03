// SARA - Sistema Administrativo de Registros - JavaScript Principal

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-cerrar alertas después de 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Funcionalidad de notificaciones
    initializeNotifications();

    // Funcionalidad de insignias
    initializeInsignias();

    // Funcionalidad de formularios
    initializeForms();

    // Funcionalidad de dashboard
    initializeDashboard();
});

// Funciones de notificaciones
function initializeNotifications() {
    // Marcar notificación como leída
    document.querySelectorAll('.mark-as-read').forEach(function(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            var notificationId = this.dataset.notificationId;

            fetch('/notificaciones/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCSRFToken()
                },
                body: 'notificacion_id=' + notificationId + '&accion=marcar_leida'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.closest('.notification-item').classList.remove('unread');
                    this.remove();
                    updateNotificationCount();
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
}

// Funciones de insignias
function initializeInsignias() {
    // Animación de progreso de insignias
    document.querySelectorAll('.progress-bar').forEach(function(progressBar) {
        var width = progressBar.style.width;
        progressBar.style.width = '0%';
        setTimeout(function() {
            progressBar.style.width = width;
        }, 500);
    });
}

// Funciones de formularios
function initializeForms() {
    // Validación en tiempo real para formularios de registro
    document.querySelectorAll('input[data-validate]').forEach(function(input) {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });

    // Máscara para campos específicos
    document.querySelectorAll('input[data-mask]').forEach(function(input) {
        input.addEventListener('input', function() {
            applyMask(this);
        });
    });
}

// Funciones del dashboard
function initializeDashboard() {
    // Actualizar estadísticas en tiempo real cada 30 segundos
    if (document.querySelector('.dashboard-stats')) {
        setInterval(updateDashboardStats, 30000);
    }

    // Inicializar gráficos si existen
    initializeCharts();
}

// Actualizar estadísticas del dashboard
function updateDashboardStats() {
    fetch(window.location.href, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Actualizar contadores
        if (data.estadisticas_rapidas) {
            updateStatsCards(data.estadisticas_rapidas);
        }
    })
    .catch(error => console.error('Error updating stats:', error));
}

// Actualizar tarjetas de estadísticas
function updateStatsCards(stats) {
    document.querySelectorAll('.stats-card').forEach(function(card) {
        var statType = card.dataset.statType;
        var valueElement = card.querySelector('.stat-number');

        if (stats[statType] !== undefined && valueElement) {
            var currentValue = parseInt(valueElement.textContent);
            var newValue = stats[statType];

            if (currentValue !== newValue) {
                animateNumber(valueElement, currentValue, newValue);
            }
        }
    });
}

// Animar cambio de números
function animateNumber(element, from, to) {
    var duration = 1000;
    var start = Date.now();
    var step = function() {
        var progress = (Date.now() - start) / duration;
        if (progress < 1) {
            element.textContent = Math.floor(from + (to - from) * progress);
            requestAnimationFrame(step);
        } else {
            element.textContent = to;
        }
    };
    requestAnimationFrame(step);
}

// Inicializar gráficos con Chart.js
function initializeCharts() {
    // Gráfico de registros por día
    var registrosChart = document.getElementById('registrosChart');
    if (registrosChart) {
        new Chart(registrosChart, {
            type: 'line',
            data: {
                labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                datasets: [{
                    label: 'Registros',
                    data: [12, 19, 3, 5, 2, 3, 9],
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Registros de la Semana'
                    }
                }
            }
        });
    }

    // Gráfico de precisión
    var precisionChart = document.getElementById('precisionChart');
    if (precisionChart) {
        new Chart(precisionChart, {
            type: 'doughnut',
            data: {
                labels: ['Preciso', 'Errores'],
                datasets: [{
                    data: [85, 15],
                    backgroundColor: ['#198754', '#dc3545'],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
}

// Validación de campos
function validateField(field) {
    var validationType = field.dataset.validate;
    var value = field.value;
    var isValid = true;
    var message = '';

    switch (validationType) {
        case 'email':
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            isValid = emailRegex.test(value);
            message = isValid ? '' : 'Formato de email inválido';
            break;
        case 'dni':
            var dniRegex = /^\d{7,8}$/;
            isValid = dniRegex.test(value);
            message = isValid ? '' : 'DNI debe tener 7 u 8 dígitos';
            break;
        case 'telefono':
            var telRegex = /^[\d\s\-\+\(\)]{8,}$/;
            isValid = telRegex.test(value);
            message = isValid ? '' : 'Formato de teléfono inválido';
            break;
    }

    // Mostrar/ocultar mensaje de error
    var feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback) {
        if (!isValid && message) {
            feedback.textContent = message;
            feedback.style.display = 'block';
            field.classList.add('is-invalid');
        } else {
            feedback.style.display = 'none';
            field.classList.remove('is-invalid');
        }
    }
}

// Aplicar máscaras a campos
function applyMask(field) {
    var maskType = field.dataset.mask;
    var value = field.value;

    switch (maskType) {
        case 'dni':
            // Remover caracteres no numéricos
            value = value.replace(/\D/g, '');
            // Limitar a 8 dígitos
            value = value.substring(0, 8);
            break;
        case 'telefono':
            // Mantener solo números, espacios, guiones, paréntesis y +
            value = value.replace(/[^\d\s\-\+\(\)]/g, '');
            break;
    }

    field.value = value;
}

// Obtener token CSRF
function getCSRFToken() {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Actualizar contador de notificaciones
function updateNotificationCount() {
    var countElement = document.querySelector('.notification-count');
    if (countElement) {
        var currentCount = parseInt(countElement.textContent) || 0;
        if (currentCount > 0) {
            countElement.textContent = currentCount - 1;
            if (currentCount - 1 === 0) {
                countElement.style.display = 'none';
            }
        }
    }
}

// Funciones de utilidad
function showToast(message, type = 'info') {
    var toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    var toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    var bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Remover toast después de que se oculte
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Función de prueba para el dropdown (se puede llamar desde la consola)
window.testUserDropdown = function() {
    const userMenuToggle = document.querySelector('.user-menu');
    const userMenuDropdownMenu = document.querySelector('.navbar .dropdown-menu');

    if (userMenuToggle && userMenuDropdownMenu) {
        console.log('=== PRUEBA DEL DROPDOWN ===');
        console.log('Botón del menú:', userMenuToggle);
        console.log('Menú desplegable:', userMenuDropdownMenu);
        console.log('Estado actual:', userMenuDropdownMenu.classList.contains('show') ? 'ABIERTO' : 'CERRADO');

        // Simular click
        userMenuToggle.click();

        setTimeout(() => {
            console.log('Estado después del click:', userMenuDropdownMenu.classList.contains('show') ? 'ABIERTO' : 'CERRADO');
        }, 100);

        return 'Prueba completada. Revisa la consola para ver los detalles.';
    } else {
        return 'Error: No se encontraron los elementos del dropdown';
    }
};

// Exportar funciones para uso global
window.SARA = window.SARA || {};
window.SARA.testUserDropdown = window.testUserDropdown;

// Funcionalidad del Navbar Mejorado
document.addEventListener('DOMContentLoaded', function() {
    initializeNavbar();
});

function initializeNavbar() {
    // Toggle del tema oscuro/claro
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // Funcionalidad de búsqueda
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSearch(this.value);
            }
        });
    }

    // Animaciones de entrada para elementos del navbar
    animateNavbarElements();

    // Actualizar indicadores en tiempo real
    setInterval(updateNavbarIndicators, 30000); // Cada 30 segundos
}

// Toggle del tema
function toggleTheme() {
    const body = document.body;
    const themeText = document.getElementById('theme-text');
    const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';

    if (currentTheme === 'light') {
        body.classList.add('dark-theme');
        localStorage.setItem('theme', 'dark');
        if (themeText) themeText.textContent = 'Tema Claro';
        showToast('Tema oscuro activado', 'info');
    } else {
        body.classList.remove('dark-theme');
        localStorage.setItem('theme', 'light');
        if (themeText) themeText.textContent = 'Tema Oscuro';
        showToast('Tema claro activado', 'info');
    }

    // Actualizar icono del tema
    updateThemeIcon();
}

// Cargar tema guardado
function loadSavedTheme() {
    const savedTheme = localStorage.getItem('theme');
    const themeText = document.getElementById('theme-text');

    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
        if (themeText) themeText.textContent = 'Tema Claro';
    } else {
        if (themeText) themeText.textContent = 'Tema Oscuro';
    }

    updateThemeIcon();
}

// Actualizar icono del tema
function updateThemeIcon() {
    const themeIcon = document.querySelector('.theme-icon');
    if (themeIcon) {
        const isDark = document.body.classList.contains('dark-theme');
        themeIcon.className = `fas ${isDark ? 'fa-sun' : 'fa-moon'} me-3 text-info`;
    }
}

// Manejar búsqueda
function handleSearch(e) {
    const query = e.target.value.trim();
    if (query.length > 2) {
        showSearchSuggestions(query);
    } else {
        hideSearchSuggestions();
    }
}

// Mostrar sugerencias de búsqueda
function showSearchSuggestions(query) {
    // Crear contenedor de sugerencias si no existe
    let suggestionsContainer = document.querySelector('.search-suggestions');
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'search-suggestions position-absolute bg-white border rounded shadow-lg mt-1';
        suggestionsContainer.style.cssText = 'z-index: 1000; width: 300px; max-height: 300px; overflow-y: auto;';

        const searchGroup = document.querySelector('.search-group');
        searchGroup.style.position = 'relative';
        searchGroup.appendChild(suggestionsContainer);
    }

    // Simular sugerencias (en un caso real, esto vendría de una API)
    const suggestions = [
        { text: `Buscar "${query}" en registros`, icon: 'fas fa-search', action: () => performSearch(query) },
        { text: `Buscar "${query}" en usuarios`, icon: 'fas fa-users', action: () => performSearch(query, 'users') },
        { text: `Buscar "${query}" en documentos`, icon: 'fas fa-file-alt', action: () => performSearch(query, 'docs') }
    ];

    suggestionsContainer.innerHTML = suggestions.map(suggestion => `
        <div class="suggestion-item p-2 border-bottom cursor-pointer" onclick="this.suggestionAction()">
            <i class="${suggestion.icon} me-2 text-muted"></i>
            <span>${suggestion.text}</span>
        </div>
    `).join('');

    // Agregar acciones a las sugerencias
    suggestions.forEach((suggestion, index) => {
        const item = suggestionsContainer.children[index];
        item.suggestionAction = suggestion.action;
    });

    suggestionsContainer.style.display = 'block';
}

// Ocultar sugerencias de búsqueda
function hideSearchSuggestions() {
    const suggestionsContainer = document.querySelector('.search-suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

// Realizar búsqueda
function performSearch(query, type = 'all') {
    if (!query.trim()) return;

    hideSearchSuggestions();

    // Mostrar indicador de carga
    showToast(`Buscando "${query}"...`, 'info');

    // Simular búsqueda (en un caso real, esto haría una petición AJAX)
    setTimeout(() => {
        showToast(`Búsqueda completada para "${query}"`, 'success');
    }, 1000);
}

// Animaciones del navbar
function animateNavbarElements() {
    const navItems = document.querySelectorAll('.navbar-nav .nav-item');
    navItems.forEach((item, index) => {
        item.style.animationDelay = `${(index + 1) * 0.1}s`;
        item.classList.add('animate-slide-in');
    });
}

// Actualizar indicadores del navbar
function updateNavbarIndicators() {
    // Actualizar contador de notificaciones
    fetch('/api/notifications/count/')
        .then(response => response.json())
        .then(data => {
            updateNotificationBadge(data.count);
        })
        .catch(error => console.log('Error updating notifications:', error));

    // Actualizar nivel del usuario
    fetch('/api/user/level/')
        .then(response => response.json())
        .then(data => {
            updateLevelBadge(data.level);
        })
        .catch(error => console.log('Error updating level:', error));
}

// Actualizar badge de notificaciones
function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Actualizar badge de nivel
function updateLevelBadge(level) {
    const badge = document.querySelector('.level-badge');
    if (badge && level) {
        badge.textContent = `Lv.${level}`;
    }
}

// Efectos hover mejorados
document.addEventListener('mouseover', function(e) {
    if (e.target.classList.contains('nav-link')) {
        e.target.style.transform = 'translateY(-2px)';
    }
});

document.addEventListener('mouseout', function(e) {
    if (e.target.classList.contains('nav-link')) {
        e.target.style.transform = 'translateY(0)';
    }
});

// Click outside para cerrar dropdowns y sugerencias
document.addEventListener('click', function(e) {
    // Cerrar sugerencias de búsqueda
    if (!e.target.closest('.search-group')) {
        hideSearchSuggestions();
    }

    // NO interferir con el comportamiento natural de Bootstrap para dropdowns
    // Bootstrap ya maneja automáticamente el cierre de dropdowns al hacer click fuera
    // El código comentado abajo estaba causando conflictos:

    /*
    // Cerrar dropdowns cuando se hace click fuera
    if (!e.target.closest('.dropdown')) {
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
    */
});

// Inicializar tema al cargar la página
loadSavedTheme();

// Funcionalidad específica del dropdown del menú de usuario
document.addEventListener('DOMContentLoaded', function() {
    // Pequeño retraso para asegurar que Bootstrap esté completamente cargado
    setTimeout(() => {
        initializeUserMenuDropdown();
        initializeBootstrapDropdowns();
    }, 100);
});

function initializeBootstrapDropdowns() {
    // Inicializar todos los dropdowns de Bootstrap
    const dropdownElements = document.querySelectorAll('.dropdown-toggle');
    dropdownElements.forEach(element => {
        new bootstrap.Dropdown(element);
    });
}

function initializeUserMenuDropdown() {
    try {
        const userMenuDropdown = document.querySelector('.navbar .dropdown');
        const userMenuToggle = document.querySelector('.user-menu');
        const userMenuDropdownMenu = document.querySelector('.navbar .dropdown-menu');

        if (!userMenuToggle || !userMenuDropdownMenu) {
            console.warn('No se encontraron elementos del menú de usuario');
            return;
        }

        console.log('Inicializando dropdown del menú de usuario...');

        // Event listener para asegurar z-index cuando se abre
        userMenuDropdown.addEventListener('shown.bs.dropdown', function() {
            userMenuDropdownMenu.style.setProperty('z-index', '9999', 'important');
            userMenuDropdownMenu.style.setProperty('position', 'absolute', 'important');
            console.log('Dropdown abierto - z-index aplicado');
        });

        // Limpiar estilos cuando se cierra
        userMenuDropdown.addEventListener('hidden.bs.dropdown', function() {
            userMenuDropdownMenu.style.zIndex = '';
            userMenuDropdownMenu.style.position = '';
            console.log('Dropdown cerrado - estilos limpiados');
        });

        // Asegurar que el click en el botón funcione correctamente
        userMenuToggle.addEventListener('click', function(e) {
            console.log('Click en botón del menú de usuario');
            // No prevenir el comportamiento por defecto, dejar que Bootstrap lo maneje
            // Solo asegurar que el dropdown tenga la prioridad correcta
            setTimeout(() => {
                if (userMenuDropdownMenu.classList.contains('show')) {
                    userMenuDropdownMenu.style.setProperty('z-index', '9999', 'important');
                    console.log('Dropdown visible - aplicando z-index máximo');
                }
            }, 1);
        });

        console.log('Dropdown del menú de usuario inicializado correctamente');

    } catch (error) {
        console.error('Error al inicializar dropdown del menú de usuario:', error);
    }

    // Asegurar que el dropdown tenga máxima prioridad en todo momento
    ensureDropdownPriority();
}

function ensureDropdownPriority() {
    const dropdownMenus = document.querySelectorAll('.navbar .dropdown-menu');

    dropdownMenus.forEach((menu, index) => {
        // Monitorear cambios en el DOM para asegurar prioridad
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    if (menu.classList.contains('show')) {
                        // Forzar máxima prioridad cuando está abierto
                        menu.style.setProperty('z-index', '9999', 'important');
                        menu.style.setProperty('position', 'absolute', 'important');
                        menu.style.setProperty('display', 'block', 'important');

                        // Debug: mostrar en consola que el dropdown se abrió
                        console.log('Dropdown del menú de usuario abierto con z-index 9999');
                    } else {
                        // Limpiar estilos cuando se cierra
                        menu.style.zIndex = '';
                        menu.style.position = '';
                        menu.style.display = '';

                        // Debug: mostrar en consola que el dropdown se cerró
                        console.log('Dropdown del menú de usuario cerrado');
                    }
                }
            });
        });

        observer.observe(menu, {
            attributes: true,
            attributeFilter: ['class']
        });

        // Debug: mostrar que el observer se configuró
        console.log(`Observer configurado para dropdown ${index + 1}`);
    });
}
