from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, EmailValidator
from django.utils import timezone
from django.conf import settings
import uuid

class Usuario(AbstractUser):
    ROLES = (
        ('operador', 'Operador'),
        ('lider', 'Líder'),
        ('rrhh', 'RRHH'),
        ('admin', 'Administrador'),
    )

    rol = models.CharField(max_length=20, choices=ROLES, default='operador')
    insignias = models.ManyToManyField('Insignia', blank=True, related_name='usuarios')

    # Campos adicionales para mejor perfil
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True, max_length=500)

    # Sistema de gamificación
    nivel = models.PositiveIntegerField(default=1)
    puntos_experiencia = models.PositiveIntegerField(default=0)
    puntos_totales = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)
    mejor_racha = models.PositiveIntegerField(default=0)

    # Estadísticas
    ultimo_login = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    registros_totales = models.PositiveIntegerField(default=0)
    precision_promedio = models.FloatField(default=0.0)

    # Configuración de privacidad y preferencias
    perfil_publico = models.BooleanField(default=False, help_text='Si el perfil es visible para otros usuarios')
    mostrar_estadisticas = models.BooleanField(default=True, help_text='Mostrar estadísticas en el perfil público')
    notificaciones_push = models.BooleanField(default=True, help_text='Recibir notificaciones push')
    idioma_preferido = models.CharField(max_length=10, default='es', choices=[
        ('es', 'Español'), ('en', 'English'), ('pt', 'Português')
    ], help_text='Idioma preferido de la interfaz')

    # Configuración adicional
    zona_horaria = models.CharField(max_length=50, default='America/Argentina/Buenos_Aires',
                                   help_text='Zona horaria del usuario')
    formato_fecha = models.CharField(max_length=20, default='DD/MM/YYYY',
                                    help_text='Formato de fecha preferido')

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_usuario_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_usuario_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"

    def calcular_nivel(self):
        """Calcula el nivel basado en puntos de experiencia"""
        # Cada nivel requiere 100 puntos más que el anterior
        puntos_necesarios = 0
        nivel = 1
        while puntos_necesarios <= self.puntos_experiencia:
            puntos_necesarios += nivel * 100
            if puntos_necesarios <= self.puntos_experiencia:
                nivel += 1
        return nivel

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas del usuario"""
        registros = Registro.objects.filter(usuario=self)
        self.registros_totales = registros.count()

        if self.registros_totales > 0:
            errores_totales = Error.objects.filter(registro__usuario=self).count()
            self.precision_promedio = ((self.registros_totales - errores_totales) / self.registros_totales) * 100

        self.save()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

class Insignia(models.Model):
    TIPOS_INSIGNIA = (
        ('logro', 'Logro'),
        ('habilidad', 'Habilidad'),
        ('dedicacion', 'Dedicación'),
        ('calidad', 'Calidad'),
        ('liderazgo', 'Liderazgo'),
    )

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_INSIGNIA, default='logro')
    icono = models.CharField(max_length=50, default='fas fa-star', help_text='Clase CSS del icono (FontAwesome)')
    color = models.CharField(max_length=20, default='#FFD700', help_text='Color hexadecimal')

    # Sistema de puntos y niveles
    puntos_otorgados = models.PositiveIntegerField(default=10)
    nivel_requerido = models.PositiveIntegerField(default=1)
    experiencia_otorgada = models.PositiveIntegerField(default=50)

    # Condiciones para obtener la insignia
    registros_minimos = models.PositiveIntegerField(default=0)
    precision_minima = models.FloatField(default=0.0, help_text='Precisión mínima requerida (0-100)')
    errores_maximos = models.PositiveIntegerField(default=999)
    dias_consecutivos = models.PositiveIntegerField(default=0)

    # Metadatos
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    creada_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def verificar_condicion(self, usuario):
        """Verifica si un usuario cumple las condiciones para obtener esta insignia"""
        if not self.activa:
            return False

        # Verificar nivel mínimo
        if usuario.nivel < self.nivel_requerido:
            return False

        # Verificar registros mínimos
        if usuario.registros_totales < self.registros_minimos:
            return False

        # Verificar precisión mínima
        if usuario.precision_promedio < self.precision_minima:
            return False

        # Verificar errores máximos
        errores_usuario = Error.objects.filter(registro__usuario=usuario).count()
        if errores_usuario > self.errores_maximos:
            return False

        # Verificar días consecutivos (esto requeriría más lógica compleja)
        # Por ahora, solo verificamos que tenga registros recientes
        if self.dias_consecutivos > 0:
            dias_ultimo_registro = (timezone.now().date() - Registro.objects.filter(
                usuario=usuario
            ).order_by('-fecha').first().fecha.date()).days
            if dias_ultimo_registro > self.dias_consecutivos:
                return False

        return True

    class Meta:
        verbose_name = 'Insignia'
        verbose_name_plural = 'Insignias'
        ordering = ['tipo', 'nivel_requerido', 'nombre']

class Registro(models.Model):
    ESTADOS = (
        ('pendiente', 'Pendiente'),
        ('validado', 'Validado'),
        ('rechazado', 'Rechazado'),
        ('corregido', 'Corregido'),
    )

    # Información básica
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='registros')
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')

    # Datos del registro (estructurados)
    dni = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\d{7,8}$', 'DNI debe tener 7 u 8 dígitos')],
        help_text='Documento Nacional de Identidad',
        default=''
    )
    apellido = models.CharField(max_length=100, default='')
    nombres = models.CharField(max_length=100, blank=True, default='')
    email = models.EmailField(validators=[EmailValidator()], default='')
    telefono = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?[\d\s\-\(\)]+$', 'Formato de teléfono inválido')],
        default=''
    )
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(blank=True, max_length=200, default='')

    # Metadatos
    tiempo_procesamiento = models.DurationField(null=True, blank=True)
    fuente = models.CharField(max_length=50, default='web', choices=[
        ('web', 'Interfaz Web'),
        ('api', 'API REST'),
        ('bulk', 'Carga Masiva'),
        ('mobile', 'Aplicación Móvil')
    ])
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Sistema de calidad
    puntuacion_calidad = models.FloatField(default=0.0, help_text='Puntuación de calidad (0-100)')
    revisiones = models.PositiveIntegerField(default=0)
    ultima_revision = models.DateTimeField(null=True, blank=True)

    # Campos legacy para compatibilidad
    datos = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Registro {self.id} - {self.apellido}, {self.nombres or 'N/A'} ({self.usuario.username})"

    def save(self, *args, **kwargs):
        # Actualizar datos JSON para compatibilidad
        self.datos = {
            'dni': self.dni,
            'apellido': self.apellido,
            'nombres': self.nombres,
            'email': self.email,
            'telefono': self.telefono,
            'fecha_nacimiento': str(self.fecha_nacimiento) if self.fecha_nacimiento else None,
            'direccion': self.direccion,
        }
        super().save(*args, **kwargs)

    def calcular_puntuacion_calidad(self):
        """Calcula la puntuación de calidad del registro"""
        puntuacion = 100.0

        # Penalizaciones por campos vacíos
        campos_obligatorios = [self.dni, self.apellido, self.email]
        for campo in campos_obligatorios:
            if not campo:
                puntuacion -= 20

        # Penalización por errores asociados
        errores = self.errores.count()
        puntuacion -= errores * 5

        # Bonificación por revisiones positivas
        if self.estado == 'validado':
            puntuacion += 10

        self.puntuacion_calidad = max(0, min(100, puntuacion))
        self.save()

    class Meta:
        verbose_name = 'Registro'
        verbose_name_plural = 'Registros'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', 'fecha']),
            models.Index(fields=['estado']),
            models.Index(fields=['dni']),
        ]

class Error(models.Model):
    TIPOS_ERROR = (
        ('formato', 'Error de Formato'),
        ('validacion', 'Error de Validación'),
        ('duplicado', 'Dato Duplicado'),
        ('requerido', 'Campo Requerido'),
        ('logico', 'Error Lógico'),
        ('sistema', 'Error del Sistema'),
    )

    GRAVEDAD = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    )

    registro = models.ForeignKey('Registro', on_delete=models.CASCADE, related_name='errores')
    campo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS_ERROR, default='validacion')
    gravedad = models.CharField(max_length=20, choices=GRAVEDAD, default='media')

    # Descripción detallada del error
    mensaje = models.TextField()
    mensaje_usuario = models.CharField(max_length=200, blank=True, help_text='Mensaje amigable para el usuario')
    sugerencia_correccion = models.TextField(blank=True, help_text='Sugerencia de cómo corregir el error')

    # Metadatos
    timestamp = models.DateTimeField(default=timezone.now)
    corregido = models.BooleanField(default=False)
    fecha_correccion = models.DateTimeField(null=True, blank=True)
    corregido_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='errores_corregidos')

    # Sistema de aprendizaje
    patron_detectado = models.CharField(max_length=100, blank=True, help_text='Patrón de error identificado')
    frecuencia_patron = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Error en {self.campo}: {self.mensaje[:50]}..."

    def marcar_corregido(self, usuario):
        """Marca el error como corregido"""
        self.corregido = True
        self.fecha_correccion = timezone.now()
        self.corregido_por = usuario
        self.save()

    class Meta:
        verbose_name = 'Error'
        verbose_name_plural = 'Errores'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['registro']),
            models.Index(fields=['tipo']),
            models.Index(fields=['corregido']),
        ]

class Metrica(models.Model):
    TIPOS_METRICA = (
        # Métricas de productividad
        ('registros_por_hora', 'Registros por Hora'),
        ('tiempo_promedio_registro', 'Tiempo Promedio por Registro'),
        ('registros_por_dia', 'Registros por Día'),

        # Métricas de calidad
        ('errores_detectados', 'Errores Detectados'),
        ('tasa_error', 'Tasa de Error (%)'),
        ('precision_promedio', 'Precisión Promedio (%)'),
        ('puntuacion_calidad_promedio', 'Puntuación Calidad Promedio'),

        # Métricas de usuario
        ('sesiones_activas', 'Sesiones Activas'),
        ('tiempo_sesion_promedio', 'Tiempo de Sesión Promedio'),
        ('insignias_obtenidas', 'Insignias Obtenidas'),

        # Métricas del sistema
        ('uptime_sistema', 'Tiempo Activo del Sistema (%)'),
        ('respuesta_api_promedio', 'Tiempo Respuesta API (ms)'),
        ('uso_cpu', 'Uso de CPU (%)'),
        ('uso_memoria', 'Uso de Memoria (%)'),
    )

    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='metricas')
    tipo = models.CharField(max_length=50, choices=TIPOS_METRICA)
    valor = models.FloatField()
    fecha = models.DateTimeField(default=timezone.now)

    # Metadatos adicionales
    periodo = models.CharField(max_length=20, default='hora', choices=[
        ('minuto', 'Por Minuto'),
        ('hora', 'Por Hora'),
        ('dia', 'Por Día'),
        ('semana', 'Por Semana'),
        ('mes', 'Por Mes'),
    ])
    contexto = models.JSONField(default=dict, blank=True, help_text='Información adicional del contexto')

    # Sistema de alertas
    umbral_minimo = models.FloatField(null=True, blank=True)
    umbral_maximo = models.FloatField(null=True, blank=True)
    alerta_generada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()}: {self.valor}"

    def verificar_umbral(self):
        """Verifica si el valor está fuera de los umbrales definidos"""
        if self.umbral_minimo is not None and self.valor < self.umbral_minimo:
            return 'bajo'
        if self.umbral_maximo is not None and self.valor > self.umbral_maximo:
            return 'alto'
        return 'normal'

    class Meta:
        verbose_name = 'Métrica'
        verbose_name_plural = 'Métricas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['usuario', 'tipo', 'fecha']),
            models.Index(fields=['tipo', 'fecha']),
            models.Index(fields=['periodo']),
        ]

class Notificacion(models.Model):
    TIPOS_NOTIFICACION = (
        ('info', 'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('achievement', 'Logro'),
        ('system', 'Sistema'),
    )

    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPOS_NOTIFICACION, default='info')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    # Estado de la notificación
    leida = models.BooleanField(default=False)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    # Acciones relacionadas
    url_accion = models.URLField(blank=True, help_text='URL para redireccionar al hacer clic')
    texto_accion = models.CharField(max_length=50, blank=True, help_text='Texto del botón de acción')

    # Metadatos
    creada_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True, related_name='notificaciones_creadas')
    prioridad = models.PositiveIntegerField(default=1, help_text='1=Baja, 5=Crítica')

    def __str__(self):
        return f"{self.usuario.username}: {self.titulo}"

    def marcar_leida(self):
        """Marca la notificación como leída"""
        self.leida = True
        self.fecha_lectura = timezone.now()
        self.save()

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha']

class LogAuditoria(models.Model):
    ACCIONES = (
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('create', 'Creación'),
        ('update', 'Actualización'),
        ('delete', 'Eliminación'),
        ('view', 'Visualización'),
        ('export', 'Exportación'),
        ('import', 'Importación'),
        ('error', 'Error'),
        ('system', 'Acción del Sistema'),
    )

    usuario = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modelo_afectado = models.CharField(max_length=100, blank=True)
    objeto_id = models.PositiveIntegerField(null=True, blank=True)
    descripcion = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    # Información técnica
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    datos_anteriores = models.JSONField(default=dict, blank=True)
    datos_nuevos = models.JSONField(default=dict, blank=True)

    def __str__(self):
        usuario = self.usuario.username if self.usuario else 'Sistema'
        return f"{usuario} - {self.get_accion_display()} - {self.fecha}"

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha']

class ConfiguracionSistema(models.Model):
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    tipo_dato = models.CharField(max_length=20, default='string', choices=[
        ('string', 'Texto'),
        ('integer', 'Número Entero'),
        ('float', 'Número Decimal'),
        ('boolean', 'Verdadero/Falso'),
        ('json', 'JSON'),
    ])
    descripcion = models.TextField(blank=True)
    categoria = models.CharField(max_length=50, default='general')
    modificable_por_usuario = models.BooleanField(default=False)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.clave}: {self.valor}"

    @classmethod
    def get_valor(cls, clave, default=None):
        """Obtiene el valor de una configuración"""
        try:
            config = cls.objects.get(clave=clave)
            if config.tipo_dato == 'boolean':
                return config.valor.lower() in ('true', '1', 'yes')
            elif config.tipo_dato == 'integer':
                return int(config.valor)
            elif config.tipo_dato == 'float':
                return float(config.valor)
            elif config.tipo_dato == 'json':
                import json
                return json.loads(config.valor)
            return config.valor
        except cls.DoesNotExist:
            return default

    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['categoria', 'clave']


class SesionTrabajo(models.Model):
    """Modelo para rastrear sesiones de trabajo del usuario"""
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='sesiones_trabajo')
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    duracion = models.DurationField(null=True, blank=True)

    # Estadísticas de la sesión
    registros_creados = models.PositiveIntegerField(default=0)
    errores_detectados = models.PositiveIntegerField(default=0)
    tiempo_promedio_registro = models.DurationField(null=True, blank=True)

    # Metadatos
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    dispositivo = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Sesión de {self.usuario.username} - {self.fecha_inicio.date()}"

    def calcular_duracion(self):
        """Calcula la duración de la sesión"""
        if self.fecha_fin and self.fecha_inicio:
            self.duracion = self.fecha_fin - self.fecha_inicio
            self.save()

    class Meta:
        verbose_name = 'Sesión de Trabajo'
        verbose_name_plural = 'Sesiones de Trabajo'
        ordering = ['-fecha_inicio']


class ReportePersonalizado(models.Model):
    """Reportes personalizados que pueden crear los usuarios"""
    TIPOS_REPORTE = (
        ('barras', 'Gráfico de Barras'),
        ('lineas', 'Gráfico de Líneas'),
        ('circular', 'Gráfico Circular'),
        ('tabla', 'Tabla de Datos'),
        ('metricas', 'Métricas Clave'),
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_REPORTE, default='tabla')

    # Configuración del reporte
    campos_seleccionados = models.JSONField(default=list, help_text='Campos a incluir en el reporte')
    filtros = models.JSONField(default=dict, help_text='Filtros aplicados al reporte')
    agrupamiento = models.JSONField(default=dict, help_text='Configuración de agrupamiento')

    # Metadatos
    creado_por = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    publico = models.BooleanField(default=False, help_text='Si otros usuarios pueden ver este reporte')
    veces_ejecutado = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = 'Reporte Personalizado'
        verbose_name_plural = 'Reportes Personalizados'
        ordering = ['-fecha_creacion']


class TareaAutomatica(models.Model):
    """Sistema de tareas automáticas y recordatorios"""
    TIPOS_TAREA = (
        ('revision', 'Revisión Periódica'),
        ('limpieza', 'Limpieza de Datos'),
        ('backup', 'Copia de Seguridad'),
        ('reporte', 'Generación de Reporte'),
        ('notificacion', 'Envío de Notificación'),
    )

    FRECUENCIAS = (
        ('diaria', 'Diaria'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
        ('personalizada', 'Personalizada'),
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_TAREA, default='revision')

    # Configuración de ejecución
    frecuencia = models.CharField(max_length=20, choices=FRECUENCIAS, default='diaria')
    hora_ejecucion = models.TimeField(default='09:00:00')
    dias_ejecucion = models.JSONField(default=list, help_text='Días de la semana para ejecutar')

    # Estado
    activa = models.BooleanField(default=True)
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    proxima_ejecucion = models.DateTimeField(null=True, blank=True)

    # Configuración específica
    parametros = models.JSONField(default=dict, help_text='Parámetros específicos de la tarea')

    # Metadatos
    creada_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nombre} ({self.get_frecuencia_display()})"

    class Meta:
        verbose_name = 'Tarea Automática'
        verbose_name_plural = 'Tareas Automáticas'


class ComentarioRegistro(models.Model):
    """Sistema de comentarios en registros"""
    registro = models.ForeignKey('Registro', on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha = models.DateTimeField(default=timezone.now)

    # Sistema de likes
    likes = models.ManyToManyField('Usuario', related_name='comentarios_liked', blank=True)

    # Respuestas
    comentario_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='respuestas')

    def __str__(self):
        return f"Comentario de {self.autor.username} en registro {self.registro.id}"

    class Meta:
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
        ordering = ['fecha']


class PlantillaRegistro(models.Model):
    """Plantillas reutilizables para diferentes tipos de registros"""
    TIPOS_PLANTILLA = (
        ('cliente', 'Cliente'),
        ('proveedor', 'Proveedor'),
        ('empleado', 'Empleado'),
        ('contacto', 'Contacto'),
        ('personalizado', 'Personalizado'),
    )

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_PLANTILLA, default='personalizado')

    # Campos de la plantilla (JSON schema)
    campos_requeridos = models.JSONField(default=list, help_text='Lista de campos obligatorios')
    campos_opcionales = models.JSONField(default=list, help_text='Lista de campos opcionales')
    validaciones = models.JSONField(default=dict, help_text='Reglas de validación personalizadas')

    # Metadatos
    creada_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    veces_usada = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    class Meta:
        verbose_name = 'Plantilla de Registro'
        verbose_name_plural = 'Plantillas de Registro'


class IntegracionExterna(models.Model):
    """Integraciones con sistemas externos"""
    TIPOS_INTEGRACION = (
        ('api', 'API REST'),
        ('webhook', 'Webhook'),
        ('database', 'Base de Datos'),
        ('email', 'Correo Electrónico'),
        ('sms', 'SMS'),
    )

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_INTEGRACION, default='api')

    # Configuración de conexión
    url_endpoint = models.URLField(blank=True)
    api_key = models.CharField(max_length=255, blank=True)
    headers = models.JSONField(default=dict)
    autenticacion = models.JSONField(default=dict)

    # Estado y monitoreo
    activa = models.BooleanField(default=True)
    ultima_sincronizacion = models.DateTimeField(null=True, blank=True)
    estado_sincronizacion = models.CharField(max_length=50, default='pendiente')

    # Metadatos
    creada_por = models.ForeignKey('Usuario', on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Integración Externa'
        verbose_name_plural = 'Integraciones Externas'


class ChatMessage(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE, null=True, blank=True)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_bot = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.text[:30]}"

