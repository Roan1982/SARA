#!/usr/bin/env python
"""
Script para probar las conexiones WebSocket
"""
import asyncio
import websockets
import json
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sara.settings')
django.setup()

async def test_websocket():
    """Probar conexión WebSocket"""
    uri = "ws://localhost:8000/ws/notifications/1/"  # Usuario ID 1

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conexión WebSocket establecida")

            # Enviar un mensaje de prueba
            test_message = {
                "action": "get_unread_count"
            }

            await websocket.send(json.dumps(test_message))
            print("📤 Mensaje enviado:", test_message)

            # Recibir respuesta
            response = await websocket.recv()
            print("📥 Respuesta recibida:", response)

            # Esperar un poco más para ver si llegan más mensajes
            try:
                response2 = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print("📥 Segundo mensaje:", response2)
            except asyncio.TimeoutError:
                print("⏰ No se recibió más mensajes (timeout)")

    except Exception as e:
        print(f"❌ Error en WebSocket: {e}")

if __name__ == "__main__":
    print("🔌 Probando conexión WebSocket...")
    asyncio.run(test_websocket())
