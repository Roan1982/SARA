import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import ChatMessage, Usuario
from .ia_recomendador import ollama_generate

logger = logging.getLogger("chat_ollama")

def get_bot_user():
    from .models import Usuario
    bot_user, _ = Usuario.objects.get_or_create(username='sara_bot', defaults={
        'first_name': 'SARA',
        'last_name': 'Bot',
        'email': 'sara-bot@localhost',
        'is_active': True,
        'rol': 'operador',
    })
    return bot_user

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if isinstance(user, AnonymousUser):
            await self.close()
            return
        self.user_id = str(user.id)
        self.room_group_name = f'chat_{self.user_id}'
        # Obtener el usuario bot y su ID real de forma asíncrona
        bot_user = await database_sync_to_async(get_bot_user)()
        self.bot_user_id = str(bot_user.id)
        self.bot_user = bot_user
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        sender_id = self.user_id
        recipient_id = data.get('recipient_id')
        text = data.get('text')
        is_bot = str(recipient_id) == str(self.bot_user_id)
        logger.info(f"Mensaje recibido: de {sender_id} para {recipient_id} (is_bot={is_bot}): {text}")
        await self.save_message(sender_id, recipient_id, text, is_bot)
        await self.send_message_to_user(sender_id, recipient_id, text, is_bot)
        if is_bot:
            logger.info(f"Enviando prompt a Ollama: {text}")
            response = await database_sync_to_async(ollama_generate)(text)
            logger.info(f"Respuesta de Ollama: {response}")
            await self.save_message(self.bot_user_id, sender_id, response, True)
            await self.send_message_to_user(self.bot_user_id, sender_id, response, True)

    async def send_message_to_user(self, sender_id, recipient_id, text, is_bot):
        group = f'chat_{recipient_id}'
        await self.channel_layer.group_send(
            group,
            {
                'type': 'chat_message',
                'sender_id': sender_id,
                'recipient_id': recipient_id,
                'text': text,
                'is_bot': is_bot
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'sender_id': event['sender_id'],
            'recipient_id': event['recipient_id'],
            'text': event['text'],
            'is_bot': event['is_bot']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, text, is_bot):
        # Obtener o crear el usuario bot
        bot_user = get_bot_user()
        sender = Usuario.objects.filter(id=sender_id).first() if str(sender_id) != str(bot_user.id) else bot_user
        recipient = Usuario.objects.filter(id=recipient_id).first() if str(recipient_id) != str(bot_user.id) else bot_user
        ChatMessage.objects.create(
            sender=sender,
            recipient=recipient,
            text=text,
            is_bot=is_bot
        )
