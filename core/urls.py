from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    login_view, logout_view, dashboard_view, registro_form,
    panel_usuario_view, panel_equipo_view, recomendacion_ia_view,
    registro_usuario, mis_insignias,
    hello_world, crear_registro, recomendacion_ia,
    UsuarioViewSet, RegistroViewSet, ErrorViewSet, InsigniaViewSet, MetricaViewSet,
    SesionTrabajoViewSet, ReportePersonalizadoViewSet, TareaAutomaticaViewSet,
    ComentarioRegistroViewSet, PlantillaRegistroViewSet, IntegracionExternaViewSet,
    panel_usuario, panel_equipo, validar_registro,
    notificaciones_view, insignias_view, perfil_usuario_view,
    sesiones_trabajo_view, reportes_personalizados_view, tareas_automaticas_view, plantillas_registro_view,
    comentarios_registro_view, integraciones_externas_view,
    user_level_api, notifications_count_api, mark_notification_read_api,
    notificacion_prueba,
    chat_users_api, chat_messages_api
)

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'registros', RegistroViewSet)
router.register(r'errores', ErrorViewSet)
router.register(r'insignias', InsigniaViewSet)
router.register(r'metricas', MetricaViewSet)
router.register(r'sesiones-trabajo', SesionTrabajoViewSet)
router.register(r'reportes-personalizados', ReportePersonalizadoViewSet)
router.register(r'tareas-automaticas', TareaAutomaticaViewSet)
router.register(r'comentarios-registro', ComentarioRegistroViewSet)
router.register(r'plantillas-registro', PlantillaRegistroViewSet)
router.register(r'integraciones-externas', IntegracionExternaViewSet)

urlpatterns = [
    path('notificacion_prueba/', notificacion_prueba, name='notificacion_prueba'),
    path('mis_insignias/', mis_insignias, name='mis_insignias'),
    path('registro_usuario/', registro_usuario, name='registro_usuario'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('', dashboard_view, name='dashboard'),
    path('registro_form/', registro_form, name='registro_form'),
    path('panel_usuario/', panel_usuario_view, name='panel_usuario_view'),
    path('panel_equipo/', panel_equipo_view, name='panel_equipo_view'),
    path('recomendacion_ia/', recomendacion_ia_view, name='recomendacion_ia_view'),
    path('notificaciones/', notificaciones_view, name='notificaciones'),
    path('insignias/', insignias_view, name='insignias'),
    path('perfil/', perfil_usuario_view, name='perfil'),
    path('sesiones-trabajo/', sesiones_trabajo_view, name='sesiones_trabajo'),
    path('reportes-personalizados/', reportes_personalizados_view, name='reportes_personalizados'),
    path('tareas-automaticas/', tareas_automaticas_view, name='tareas_automaticas'),
    path('plantillas-registro/', plantillas_registro_view, name='plantillas_registro'),
    path('comentarios-registro/', comentarios_registro_view, name='comentarios_registro'),
    path('integraciones-externas/', integraciones_externas_view, name='integraciones_externas'),
    path('hello/', hello_world, name='hello_world'),
    path('registro/', crear_registro, name='crear_registro'),
    path('recomendacion/<int:usuario_id>/', recomendacion_ia, name='recomendacion_ia'),
    path('panel_usuario/<int:usuario_id>/', panel_usuario, name='panel_usuario'),
    path('panel_equipo/', panel_equipo, name='panel_equipo'),
    path('validar_registro/', validar_registro, name='validar_registro'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/level/', user_level_api, name='user_level_api'),
    path('notifications/count/', notifications_count_api, name='notifications_count_api'),
    path('notifications/<int:notification_id>/read/', mark_notification_read_api, name='mark_notification_read_api'),
    path('chat/users/', chat_users_api, name='chat_users_api'),
    path('chat/messages/', chat_messages_api, name='chat_messages_api'),
    path('', include(router.urls)),
]
