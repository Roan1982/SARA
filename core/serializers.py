from rest_framework import serializers
from .models import Usuario, Registro, Error, Insignia, Metrica, SesionTrabajo, ReportePersonalizado, TareaAutomatica, ComentarioRegistro, PlantillaRegistro, IntegracionExterna

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'rol',
            'perfil_publico', 'mostrar_estadisticas', 'notificaciones_push',
            'idioma_preferido', 'zona_horaria', 'formato_fecha',
            'fecha_creacion', 'ultimo_login'
        ]

class RegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registro
        fields = ['id', 'usuario', 'fecha', 'datos']

class ErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Error
        fields = ['id', 'registro', 'campo', 'mensaje', 'timestamp']

class InsigniaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insignia
        fields = ['id', 'nombre', 'descripcion']

class MetricaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Metrica
        fields = ['id', 'usuario', 'tipo', 'valor', 'fecha']

class SesionTrabajoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionTrabajo
        fields = ['id', 'usuario', 'fecha_inicio', 'fecha_fin', 'duracion', 'registros_creados', 'errores_detectados', 'tiempo_promedio_registro', 'ip_address', 'user_agent', 'dispositivo']

class ReportePersonalizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportePersonalizado
        fields = ['id', 'nombre', 'descripcion', 'tipo', 'campos_seleccionados', 'filtros', 'agrupamiento', 'creado_por', 'fecha_creacion', 'publico', 'veces_ejecutado']

class TareaAutomaticaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TareaAutomatica
        fields = ['id', 'nombre', 'descripcion', 'tipo', 'frecuencia', 'hora_ejecucion', 'dias_ejecucion', 'activa', 'ultima_ejecucion', 'proxima_ejecucion', 'parametros', 'creada_por', 'fecha_creacion']

class ComentarioRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComentarioRegistro
        fields = ['id', 'registro', 'autor', 'contenido', 'fecha', 'likes', 'comentario_padre']

class PlantillaRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantillaRegistro
        fields = ['id', 'nombre', 'descripcion', 'tipo', 'campos_requeridos', 'campos_opcionales', 'validaciones', 'creada_por', 'fecha_creacion', 'activa', 'veces_usada']

class IntegracionExternaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegracionExterna
        fields = ['id', 'nombre', 'descripcion', 'tipo', 'url_endpoint', 'api_key', 'headers', 'autenticacion', 'activa', 'ultima_sincronizacion', 'estado_sincronizacion', 'creada_por', 'fecha_creacion']
