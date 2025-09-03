from .models import Notificacion

def user_navbar_context(request):
    """Context processor para agregar información del usuario al navbar"""
    if request.user.is_authenticated:
        # Contador de notificaciones no leídas
        notificaciones_no_leidas = Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).count()

        # Agregar propiedad al usuario
        request.user.notificaciones_no_leidas = notificaciones_no_leidas

        return {
            'user_navbar': {
                'notificaciones_no_leidas': notificaciones_no_leidas,
                'total_insignias': request.user.insignias.count(),
                'nivel_actual': request.user.nivel,
                'puntos_experiencia': request.user.puntos_experiencia,
            }
        }

    return {}
