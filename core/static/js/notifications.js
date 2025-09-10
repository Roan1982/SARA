/**
 * Sistema de Notificaciones Push en Tiempo Real para SARA
 * Maneja conexiones WebSocket y notificaciones del navegador
 */

class NotificationManager {
    constructor(userId = null) {
        this.ws = null;
        this.reconnectAttempts = 0;
    this.maxReconnectAttempts = Infinity; // Reconexión indefinida
    this.baseReconnectInterval = 3000; // 3 segundos base
    this.reconnectInterval = this.baseReconnectInterval;
        this.userId = userId || this.getCurrentUserId();
        this.isConnected = false;

        // Elementos del DOM
        this.notificationContainer = null;
        this.notificationBadge = null;

        this.init();
    }

    init() {
        if (!this.userId) {
            console.warn('No se pudo obtener el ID del usuario. Las notificaciones en tiempo real no estarán disponibles.');
            return;
        }

        this.createNotificationContainer();
        this.requestNotificationPermission();
        this.connectWebSocket();
        this.setupEventListeners();
        this.updateNavbarStats();
    }

    getCurrentUserId() {
        // Si ya tenemos el userId del constructor, usarlo
        if (this.userId) {
            return this.userId;
        }

        // Intentar obtener el user ID de diferentes formas
        const userIdElement = document.getElementById('current-user-id');
        if (userIdElement && userIdElement.value) {
            return userIdElement.value;
        }

        // Intentar obtenerlo del contexto de Django
        if (window.djangoUserId) {
            return window.djangoUserId;
        }

        // Intentar obtenerlo de la URL o localStorage
        const storedUserId = localStorage.getItem('sara_user_id');
        if (storedUserId) {
            return storedUserId;
        }

        return null;
    }

    createNotificationContainer() {
        // Crear contenedor para notificaciones toast
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'notification-container';
        this.notificationContainer.className = 'notification-container';
        this.notificationContainer.innerHTML = `
            <style>
                .notification-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 9999;
                    max-width: 400px;
                }
                .notification-toast {
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    margin-bottom: 10px;
                    padding: 16px;
                    border-left: 4px solid #007bff;
                    animation: slideIn 0.3s ease-out;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                .notification-toast:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.2);
                }
                .notification-toast.success { border-left-color: #28a745; }
                .notification-toast.warning { border-left-color: #ffc107; }
                .notification-toast.error { border-left-color: #dc3545; }
                .notification-toast.info { border-left-color: #17a2b8; }
                .notification-toast.achievement { border-left-color: #fd7e14; }
                .notification-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                .notification-title {
                    font-weight: 600;
                    font-size: 14px;
                    color: #333;
                    margin: 0;
                }
                .notification-close {
                    background: none;
                    border: none;
                    font-size: 18px;
                    cursor: pointer;
                    color: #999;
                    padding: 0;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .notification-message {
                    font-size: 13px;
                    color: #666;
                    line-height: 1.4;
                    margin: 0;
                }
                .notification-time {
                    font-size: 11px;
                    color: #999;
                    margin-top: 8px;
                }
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                .notification-fade-out {
                    animation: fadeOut 0.3s ease-out forwards;
                }
            </style>
        `;
        document.body.appendChild(this.notificationContainer);
    }

    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    console.log('Permiso de notificaciones concedido');
                }
            });
        }
    }

    connectWebSocket() {
        if (!this.userId) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/${this.userId}/`;

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = (event) => {
                console.log('WebSocket conectado para notificaciones');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectInterval = this.baseReconnectInterval;
                this.showConnectionStatus('Conectado', 'success');
                this.hideConnectionStatusAfterDelay();
            };

            this.ws.onmessage = (event) => {
                this.handleWebSocketMessage(event);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket desconectado:', event.code, event.reason);
                this.isConnected = false;
                this.handleReconnection();
            };

            this.ws.onerror = (error) => {
                console.error('Error en WebSocket:', error);
                this.isConnected = false;
            };

        } catch (error) {
            console.error('Error al crear WebSocket:', error);
            this.handleReconnection();
        }
    }

    handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'notification') {
                this.handleNewNotification(data.notification);
            } else if (data.type === 'stats_update') {
                this.handleStatsUpdate(data.stats);
            }
        } catch (error) {
            console.error('Error al procesar mensaje WebSocket:', error);
        }
    }

    handleNewNotification(notification) {
        // Mostrar notificación toast
        this.showNotificationToast(notification);

        // Mostrar notificación del navegador si está permitido
        this.showBrowserNotification(notification);

        // Actualizar badge del navbar
        this.updateNotificationBadge();

        // Reproducir sonido si está habilitado
        this.playNotificationSound();
    }

    handleStatsUpdate(stats) {
        // Actualizar elementos del navbar con las nuevas estadísticas
        this.updateNavbarWithStats(stats);
    }

    showNotificationToast(notification) {
        const toast = document.createElement('div');
        toast.className = `notification-toast ${notification.tipo || 'info'}`;

        const fecha = new Date(notification.fecha);
        const tiempoRelativo = this.getRelativeTime(fecha);

        toast.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">${notification.titulo}</h4>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            <p class="notification-message">${notification.mensaje}</p>
            <div class="notification-time">${tiempoRelativo}</div>
        `;

        // Agregar evento de click para marcar como leída y redireccionar
        toast.addEventListener('click', (e) => {
            if (!e.target.classList.contains('notification-close')) {
                this.markNotificationAsRead(notification.id);
                if (notification.url_accion) {
                    window.location.href = notification.url_accion;
                }
            }
        });

        this.notificationContainer.appendChild(toast);

        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (toast.parentElement) {
                toast.classList.add('notification-fade-out');
                setTimeout(() => toast.remove(), 300);
            }
        }, 5000);
    }

    showBrowserNotification(notification) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const browserNotification = new Notification(notification.titulo, {
                body: notification.mensaje,
                icon: '/static/img/notification-icon.png', // Puedes cambiar esto
                badge: '/static/img/badge.png',
                tag: `notification-${notification.id}`,
                requireInteraction: false,
                silent: false
            });

            browserNotification.onclick = () => {
                window.focus();
                if (notification.url_accion) {
                    window.location.href = notification.url_accion;
                }
                browserNotification.close();
            };

            // Auto-cerrar después de 4 segundos
            setTimeout(() => browserNotification.close(), 4000);
        }
    }

    updateNotificationBadge() {
        // Actualizar el badge de notificaciones en el navbar
        const badge = document.querySelector('.notification-badge');
        if (badge) {
            // Aquí puedes hacer una llamada AJAX para obtener el conteo actual
            this.fetchNotificationCount();
        }
    }

    updateNavbarWithStats(stats) {
        // Actualizar elementos del navbar con estadísticas en tiempo real
        if (stats.nivel !== undefined) {
            const levelElement = document.querySelector('.user-level');
            if (levelElement) {
                levelElement.textContent = stats.nivel;
            }
        }

        if (stats.puntos_experiencia !== undefined) {
            const pointsElement = document.querySelector('.user-points');
            if (pointsElement) {
                pointsElement.textContent = stats.puntos_experiencia;
            }
        }

        if (stats.insignias_total !== undefined) {
            const badgesElement = document.querySelector('.user-badges-count');
            if (badgesElement) {
                badgesElement.textContent = stats.insignias_total;
            }
        }

        if (stats.unread_notifications !== undefined) {
            const notificationBadge = document.querySelector('.notification-badge');
            if (notificationBadge) {
                notificationBadge.textContent = stats.unread_notifications;
                notificationBadge.style.display = stats.unread_notifications > 0 ? 'inline' : 'none';
            }
        }
    }

    markNotificationAsRead(notificationId) {
        if (!notificationId) return;

        fetch(`/api/notifications/${notificationId}/read/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        }).then(response => {
            if (response.ok) {
                console.log('Notificación marcada como leída');
            }
        }).catch(error => {
            console.error('Error al marcar notificación como leída:', error);
        });
    }

    fetchNotificationCount() {
        fetch('/api/notifications/count/')
            .then(response => response.json())
            .then(data => {
                const badge = document.querySelector('.notification-badge');
                if (badge && data.unread_count !== undefined) {
                    badge.textContent = data.unread_count;
                    badge.style.display = data.unread_count > 0 ? 'inline' : 'none';
                }
            })
            .catch(error => {
                console.error('Error al obtener conteo de notificaciones:', error);
            });
    }

    updateNavbarStats() {
        // Actualizar estadísticas del navbar periódicamente
        this.fetchNotificationCount();

        // Actualizar cada 30 segundos
        setInterval(() => {
            this.fetchNotificationCount();
        }, 30000);
    }

    handleReconnection() {
        this.reconnectAttempts++;
        // Backoff exponencial hasta 1 minuto
        this.reconnectInterval = Math.min(this.baseReconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 60000);
        console.log(`Intentando reconectar WebSocket... (intento ${this.reconnectAttempts}, en ${this.reconnectInterval / 1000}s)`);
        this.showConnectionStatus(`Desconectado - Reintentando conexión (${this.reconnectAttempts})...`, 'error');
        setTimeout(() => {
            this.connectWebSocket();
        }, this.reconnectInterval);
    }

    showConnectionStatus(message, type) {
        // Mostrar estado de conexión en el indicador visual o crear uno si no existe
        let statusElement = document.getElementById('ws-status-indicator');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'ws-status-indicator';
            statusElement.style.position = 'fixed';
            statusElement.style.bottom = '20px';
            statusElement.style.right = '20px';
            statusElement.style.zIndex = 10000;
            document.body.appendChild(statusElement);
        }
        statusElement.innerHTML = `
            <i class="fas fa-circle ${type === 'success' ? 'text-success' : type === 'error' ? 'text-danger' : 'text-muted'} me-1"></i>
            ${message}
        `;
        statusElement.className = `badge ${type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-secondary'}`;
        statusElement.style.padding = '10px 18px';
        statusElement.style.fontSize = '15px';
        statusElement.style.borderRadius = '8px';
        statusElement.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
        statusElement.style.display = 'block';
        console.log(`Estado de conexión: ${message}`);
    }

    hideConnectionStatusAfterDelay() {
        // Ocultar el mensaje de estado de conexión tras 2 segundos si está conectado
        setTimeout(() => {
            const statusElement = document.getElementById('ws-status-indicator');
            if (statusElement && this.isConnected) {
                statusElement.style.display = 'none';
            }
        }, 2000);
    }

    getRelativeTime(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Ahora mismo';
        if (diffInSeconds < 3600) return `Hace ${Math.floor(diffInSeconds / 60)} minutos`;
        if (diffInSeconds < 86400) return `Hace ${Math.floor(diffInSeconds / 3600)} horas`;
        return `Hace ${Math.floor(diffInSeconds / 86400)} días`;
    }

    getCSRFToken() {
        // Obtener token CSRF para requests POST
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    playNotificationSound() {
        // Reproducir sonido de notificación (opcional)
        try {
            const audio = new Audio('/static/audio/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(() => {
                // Silenciar error si el navegador bloquea autoplay
            });
        } catch (error) {
            // Silenciar error si no hay archivo de audio
        }
    }

    setupEventListeners() {
        // Escuchar eventos de visibilidad de página
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && (!this.ws || this.ws.readyState === WebSocket.CLOSED)) {
                console.log('Página visible nuevamente, reconectando WebSocket...');
                this.reconnectAttempts = 0;
                this.reconnectInterval = this.baseReconnectInterval;
                this.connectWebSocket();
            }
        });

        // Escuchar eventos de foco de ventana
        window.addEventListener('focus', () => {
            if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
                console.log('Ventana enfocada, reconectando WebSocket...');
                this.reconnectAttempts = 0;
                this.reconnectInterval = this.baseReconnectInterval;
                this.connectWebSocket();
            }
        });
    }

    // Método público para enviar mensajes al WebSocket
    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('WebSocket no está conectado');
        }
    }

    // Método público para desconectar
    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Inicializar el sistema de notificaciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Crear instancia global del NotificationManager
    window.notificationManager = new NotificationManager();

    // Agregar el user ID al contexto de Django si está disponible
    const userIdElement = document.querySelector('[name="user_id"]');
    if (userIdElement && userIdElement.value) {
        window.djangoUserId = userIdElement.value;
        localStorage.setItem('sara_user_id', userIdElement.value);
    }
});

// Exportar para uso en otros módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}
