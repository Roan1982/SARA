#!/usr/bin/env python
"""
Script para ejecutar el servidor ASGI con Django Channels
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sara.settings')
django.setup()

# Ahora importar y ejecutar uvicorn
import uvicorn

if __name__ == '__main__':
    uvicorn.run(
        'sara.asgi:application',
        host='0.0.0.0',
        port=8000,
        reload=False,  # Desactivar reload para evitar problemas
        log_level='info'
    )
