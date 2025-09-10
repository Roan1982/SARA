import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notificacion, Usuario


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer para manejar notificaciones en tiempo real vía WebSocket"""

    async def connect(self):
        """Se ejecuta cuando un cliente se conecta al WebSocket"""
        import logging
        logger = logging.getLogger("channels.auth")
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notifications_{self.user_id}'

        user = self.scope.get('user')
        logger.info(f"[WS] Intento de conexión: user en scope={user}, user.id={getattr(user, 'id', None)}, user_id en URL={self.user_id}")

        if isinstance(user, AnonymousUser):
            logger.warning(f"[WS] Usuario anónimo. Cerrando conexión WebSocket para user_id={self.user_id}")
            await self.close()
            return
        if str(user.id) != self.user_id:
            logger.warning(f"[WS] user.id ({user.id}) != user_id en URL ({self.user_id}). Cerrando conexión.")
            await self.close()
            return

        logger.info(f"[WS] Usuario autenticado y autorizado. user_id={self.user_id}. Uniendo al grupo {self.room_group_name}")
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"[WS] Conexión WebSocket aceptada para user_id={self.user_id}")

        # Enviar notificaciones no leídas al conectar
        await self.send_unread_notifications_to_client()

    async def disconnect(self, close_code):
        """Se ejecuta cuando un cliente se desconecta"""
        # Salir del grupo
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Manejar mensajes del cliente"""
        try:
            data = json.loads(text_data)
            action = data.get('action')

            if action == 'mark_read':
                notification_id = data.get('notification_id')
                await self.mark_notification_read(notification_id)
            elif action == 'get_unread_count':
                await self.send_unread_count_to_client()

        except json.JSONDecodeError:
            pass

    async def notification_message(self, event):
        """Enviar notificación al cliente"""
        notification = event['notification']

        # Enviar la notificación al WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))

    async def stats_update(self, event):
        """Enviar actualización de estadísticas"""
        stats = event['stats']

        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': stats
        }))

    async def send_unread_notifications_to_client(self):
        """Obtener y enviar notificaciones no leídas al cliente conectado"""
        try:
            user = await database_sync_to_async(Usuario.objects.get)(id=self.user_id)
            notifications = await database_sync_to_async(
                lambda: list(Notificacion.objects.filter(
                    usuario=user,
                    leida=False
                ).order_by('-fecha')[:10])
            )()

            for notification in notifications:
                # Enviar cada notificación directamente al cliente
                notification_data = {
                    'id': notification.id,
                    'titulo': notification.titulo,
                    'mensaje': notification.mensaje,
                    'tipo': notification.tipo,
                    'fecha': notification.fecha.isoformat(),
                    'leida': notification.leida,
                    'url_accion': notification.url_accion,
                    'texto_accion': notification.texto_accion,
                }

                await self.send(text_data=json.dumps({
                    'type': 'notification',
                    'notification': notification_data
                }))

        except Usuario.DoesNotExist:
            pass

    async def mark_notification_read(self, notification_id):
        """Marcar notificación como leída"""
        try:
            user = await database_sync_to_async(Usuario.objects.get)(id=self.user_id)
            notification = await database_sync_to_async(
                Notificacion.objects.get
            )(id=notification_id, usuario=user)
            
            await database_sync_to_async(notification.marcar_leida)()

            # Notificar a otros consumidores del mismo usuario
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'notification_message',
                    'notification': {
                        'id': notification.id,
                        'leida': True
                    }
                }
            )

        except (Usuario.DoesNotExist, Notificacion.DoesNotExist):
            pass

    async def send_unread_count_to_client(self):
        """Enviar conteo de notificaciones no leídas al cliente"""
        try:
            user = await database_sync_to_async(Usuario.objects.get)(id=self.user_id)
            count = await database_sync_to_async(
                lambda: Notificacion.objects.filter(
                    usuario=user,
                    leida=False
                ).count()
            )()

            await self.send(text_data=json.dumps({
                'type': 'stats_update',
                'stats': {
                    'unread_notifications': count
                }
            }))

        except Usuario.DoesNotExist:
            pass


# Función utilitaria para enviar notificaciones desde cualquier parte del código
async def send_notification_to_user(user_id, notification_data):
    """Enviar notificación a un usuario específico"""
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{user_id}'

    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'notification_message',
            'notification': notification_data
        }
    )


async def send_stats_update_to_user(user_id, stats_data):
    """Enviar actualización de estadísticas a un usuario"""
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    room_group_name = f'notifications_{user_id}'

    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'stats_update',
            'stats': stats_data
        }
    )
