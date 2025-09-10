from django.conf import settings
from django.db.utils import OperationalError
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Crear el usuario bot automáticamente si no existe
        try:
            from .models import Usuario
            Usuario.objects.get_or_create(
                username='sara_bot',
                defaults={
                    'first_name': 'SARA',
                    'last_name': 'Bot',
                    'email': 'sara-bot@localhost',
                    'is_active': True,
                    'rol': 'operador',
                }
            )
        except OperationalError:
            # La base de datos puede no estar lista en migraciones
            pass
        except Exception:
            pass
