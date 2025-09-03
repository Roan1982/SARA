from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Usuario, Registro, Error, Insignia, Metrica, Notificacion, LogAuditoria, SesionTrabajo, ReportePersonalizado, TareaAutomatica, ComentarioRegistro, PlantillaRegistro, IntegracionExterna
from .serializers import UsuarioSerializer, RegistroSerializer, ErrorSerializer, InsigniaSerializer, MetricaSerializer, SesionTrabajoSerializer, ReportePersonalizadoSerializer, TareaAutomaticaSerializer, ComentarioRegistroSerializer, PlantillaRegistroSerializer, IntegracionExternaSerializer
from .ia_recomendador import recomendador, analizar_usuario
import json

class LoginForm(forms.Form):
	username = forms.CharField()
	password = forms.CharField(widget=forms.PasswordInput)

@login_required
def mis_insignias(request):
	insignias = request.user.insignias.all()
	return render(request, 'core/mis_insignias.html', {'insignias': insignias})

# --- STUBS PARA VISTAS Y VIEWSETS FALTANTES ---

def registro_usuario(request):
    return render(request, 'core/registro_usuario.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard')
        return render(request, 'core/login.html', {'form': form})
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def registro_form(request):
    mensaje = None
    errores_predichos = []
    analisis_usuario = analizar_usuario(request.user.id)

    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        nombres = request.POST.get('nombres', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        fecha_nacimiento = request.POST.get('fecha_nacimiento', '')
        direccion = request.POST.get('direccion', '').strip()

        # Datos para predicción de errores
        datos_registro = {
            'dni': dni,
            'apellido': apellido,
            'email': email,
            'telefono': telefono
        }

        # Predecir posibles errores antes de guardar
        errores_predichos = recomendador.predecir_errores_posibles(datos_registro)

        if not all([dni, apellido, email]):
            mensaje = {'tipo': 'error', 'texto': 'Los campos DNI, Apellido y Email son obligatorios.'}
        elif errores_predichos:
            mensaje = {'tipo': 'warning', 'texto': f'Se detectaron {len(errores_predichos)} posibles errores. Revisa los datos.'}
        else:
            try:
                # Crear el registro con los datos estructurados
                registro = Registro.objects.create(
                    usuario=request.user,
                    dni=dni,
                    apellido=apellido,
                    nombres=nombres,
                    email=email,
                    telefono=telefono,
                    fecha_nacimiento=fecha_nacimiento if fecha_nacimiento else None,
                    direccion=direccion,
                    fuente='web'
                )

                # Calcular puntuación de calidad
                registro.calcular_puntuacion_calidad()
                registro.save()

                # Actualizar estadísticas del usuario
                request.user.registros_totales += 1
                request.user.actualizar_estadisticas()

                # Otorgar puntos de experiencia
                puntos_ganados = 10  # Base
                if registro.puntuacion_calidad > 90:
                    puntos_ganados += 5  # Bonificación por calidad
                if request.user.racha_actual > 0:
                    puntos_ganados += request.user.racha_actual  # Bonificación por racha

                request.user.puntos_experiencia += puntos_ganados
                request.user.puntos_totales += puntos_ganados
                request.user.racha_actual += 1
                request.user.mejor_racha = max(request.user.mejor_racha, request.user.racha_actual)
                request.user.nivel = request.user.calcular_nivel()
                request.user.save()

                # Verificar y otorgar insignias
                insignias_ganadas = []
                for insignia in Insignia.objects.filter(activa=True):
                    if insignia.verificar_condicion(request.user) and not request.user.insignias.filter(id=insignia.id).exists():
                        request.user.insignias.add(insignia)
                        insignias_ganadas.append(insignia)

                        # Crear notificación
                        Notificacion.objects.create(
                            usuario=request.user,
                            tipo='achievement',
                            titulo='¡Nueva Insignia!',
                            mensaje=f'¡Felicitaciones! Has obtenido la insignia "{insignia.nombre}"',
                            url_accion='/mis_insignias/',
                            texto_accion='Ver Insignias'
                        )

                # Registrar en log de auditoría
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion='create',
                    modelo_afectado='Registro',
                    objeto_id=registro.id,
                    descripcion=f'Registro creado: {registro.apellido}, {registro.nombres}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )

                mensaje = {
                    'tipo': 'success',
                    'texto': f'¡Registro guardado exitosamente! +{puntos_ganados} puntos de experiencia.',
                    'insignias_ganadas': [i.nombre for i in insignias_ganadas] if insignias_ganadas else None
                }

            except Exception as e:
                # Registrar error en log
                LogAuditoria.objects.create(
                    usuario=request.user,
                    accion='error',
                    modelo_afectado='Registro',
                    descripcion=f'Error al crear registro: {str(e)}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                mensaje = {'tipo': 'error', 'texto': f'Error al guardar el registro: {str(e)}'}

    return render(request, 'core/registro_form.html', {
        'mensaje': mensaje,
        'errores_predichos': errores_predichos,
        'analisis_usuario': analisis_usuario
    })

@login_required
def panel_usuario_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Calcular métricas avanzadas del usuario actual
    registros = Registro.objects.filter(usuario=request.user)
    total_registros = registros.count()
    total_errores = 0  # Initialize total_errores

    if total_registros > 0:
        # Estadísticas de calidad
        registros_validos = registros.filter(estado='validado').count()
        registros_rechazados = registros.filter(estado='rechazado').count()
        precision_calidad = (registros_validos / total_registros) * 100

        # Estadísticas de tiempo (últimos 30 días)
        fecha_limite = timezone.now() - timedelta(days=30)
        registros_recientes = registros.filter(fecha__gte=fecha_limite)
        registros_por_dia = registros_recientes.count() / 30

        # Análisis de errores
        errores = Error.objects.filter(registro__usuario=request.user)
        total_errores = errores.count()
        tasa_error = (total_errores / total_registros * 100) if total_registros > 0 else 0

        # Errores por campo
        errores_por_campo = errores.values('campo').annotate(
            cantidad=Count('campo')
        ).order_by('-cantidad')[:5]

        # Errores por tipo
        errores_por_tipo = errores.values('tipo').annotate(
            cantidad=Count('tipo')
        ).order_by('-cantidad')

        # Tendencia de errores (últimos 7 días vs semana anterior)
        semana_actual = timezone.now() - timedelta(days=7)
        semana_anterior = timezone.now() - timedelta(days=14)

        errores_semana_actual = errores.filter(timestamp__gte=semana_actual).count()
        errores_semana_anterior = errores.filter(
            timestamp__gte=semana_anterior,
            timestamp__lt=semana_actual
        ).count()

        if errores_semana_anterior > 0:
            tendencia_errores = ((errores_semana_actual - errores_semana_anterior) / errores_semana_anterior) * 100
        else:
            tendencia_errores = 0 if errores_semana_actual == 0 else 100

    else:
        precision_calidad = 0
        registros_por_dia = 0
        tasa_error = 0
        errores_por_campo = []
        errores_por_tipo = []
        tendencia_errores = 0

    # Sistema de gamificación
    progreso_nivel = 0
    if request.user.nivel > 0:
        puntos_base_nivel = (request.user.nivel - 1) * 100
        puntos_para_siguiente = request.user.nivel * 100
        progreso_nivel = ((request.user.puntos_experiencia - puntos_base_nivel) / (puntos_para_siguiente - puntos_base_nivel)) * 100

    # Insignias recientes
    insignias_recientes = request.user.insignias.order_by('-fecha_creacion')[:3]

    # Notificaciones no leídas
    notificaciones_no_leidas = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-fecha')[:5]

    # Análisis de IA
    analisis_ia = analizar_usuario(request.user.id)

    # Obtener métricas recientes para gráficos
    metricas_recientes = Metrica.objects.filter(
        usuario=request.user,
        tipo__in=['registros_por_hora', 'tasa_error', 'precision_promedio']
    ).order_by('-fecha')[:20]

    context = {
        # Estadísticas básicas
        'total_registros': total_registros,
        'total_errores': total_errores,
        'tasa_error': round(tasa_error, 2),
        'precision_calidad': round(precision_calidad, 2),
        'registros_por_dia': round(registros_por_dia, 2),

        # Estadísticas detalladas
        'registros_validos': registros_validos if total_registros > 0 else 0,
        'registros_rechazados': registros_rechazados if total_registros > 0 else 0,
        'errores_por_campo': errores_por_campo,
        'errores_por_tipo': errores_por_tipo,
        'tendencia_errores': round(tendencia_errores, 2),

        # Sistema de gamificación
        'nivel': request.user.nivel,
        'puntos_experiencia': request.user.puntos_experiencia,
        'puntos_totales': request.user.puntos_totales,
        'racha_actual': request.user.racha_actual,
        'mejor_racha': request.user.mejor_racha,
        'progreso_nivel': round(progreso_nivel, 1),
        'insignias_recientes': insignias_recientes,

        # Notificaciones
        'notificaciones_no_leidas': notificaciones_no_leidas,
        'total_notificaciones_no_leidas': notificaciones_no_leidas.count(),

        # IA y recomendaciones
        'analisis_ia': analisis_ia,
        'recomendacion_ia': analisis_ia.get('recomendacion'),
        'sugerencias_mejora': analisis_ia.get('sugerencias', []),

        # Datos para gráficos
        'metricas_recientes': metricas_recientes,
    }

    return render(request, 'core/panel_usuario.html', context)

def panel_equipo_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Verificar permisos (solo líderes y admins pueden ver panel de equipo)
    if request.user.rol not in ['lider', 'admin']:
        return redirect('dashboard')
    
    # Calcular métricas agregadas del equipo
    from django.db.models import Count, Avg
    
    usuarios_metricas = Usuario.objects.annotate(
        total_registros=Count('registros'),
        total_errores=Count('registros__errores')
    ).values('username', 'total_registros', 'total_errores')
    
    # Calcular tasa de error para cada usuario
    for usuario in usuarios_metricas:
        if usuario['total_registros'] > 0:
            usuario['tasa_error'] = round((usuario['total_errores'] / usuario['total_registros']) * 100, 2)
        else:
            usuario['tasa_error'] = 0
    
    # Métricas globales
    total_registros_global = Registro.objects.count()
    total_errores_global = Error.objects.count()
    tasa_error_global = (total_errores_global / total_registros_global * 100) if total_registros_global > 0 else 0
    
    context = {
        'usuarios_metricas': usuarios_metricas,
        'total_registros_global': total_registros_global,
        'total_errores_global': total_errores_global,
        'tasa_error_global': round(tasa_error_global, 2),
    }
    return render(request, 'core/panel_equipo.html', context)

def recomendacion_ia_view(request):
    return render(request, 'core/recomendacion_ia.html')

def hello_world(request):
    return JsonResponse({'hello': 'world'})

@login_required
def crear_registro(request):
    if request.method == 'POST':
        try:
            # Para API REST, esperamos datos JSON
            import json
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                dni = data.get('dni')
                apellido = data.get('apellido')
                email = data.get('email')
            else:
                # Para formularios HTML
                dni = request.POST.get('dni')
                apellido = request.POST.get('apellido')
                email = request.POST.get('email')
            
            if not all([dni, apellido, email]):
                return JsonResponse({'error': 'Todos los campos son obligatorios'}, status=400)
            
            # Crear el registro
            registro = Registro.objects.create(
                usuario=request.user,
                datos={
                    'dni': dni,
                    'apellido': apellido,
                    'email': email
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Registro creado correctamente',
                'registro_id': registro.id
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Error al crear registro: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def recomendacion_ia(request, usuario_id=None):
    return JsonResponse({'recomendacion': 'stub'})

@api_view(['GET'])
def panel_usuario(request, usuario_id):
    try:
        usuario = Usuario.objects.get(id=usuario_id)
        total_registros = Registro.objects.filter(usuario=usuario).count()
        total_errores = Error.objects.filter(registro__usuario=usuario).count()
        tasa_error = (total_errores / total_registros) if total_registros else 0
        
        return Response({
            'usuario': usuario.username,
            'total_registros': total_registros,
            'total_errores': total_errores,
            'tasa_error': tasa_error,
        })
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=404)

@api_view(['GET'])
def panel_equipo(request):
    data = Registro.objects.values('usuario__username').annotate(
        total_registros=Count('id'),
        total_errores=Count('errores'),
    )
    for d in data:
        d['tasa_error'] = (d['total_errores'] / d['total_registros']) if d['total_registros'] else 0
    return Response(list(data))

def validar_registro(request):
    return JsonResponse({'validado': True})

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAdminUser]

class RegistroViewSet(viewsets.ModelViewSet):
    queryset = Registro.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.IsAuthenticated]

class ErrorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Error.objects.all()
    serializer_class = ErrorSerializer
    permission_classes = [permissions.IsAuthenticated]

class InsigniaViewSet(viewsets.ModelViewSet):
    queryset = Insignia.objects.all()
    serializer_class = InsigniaSerializer
    permission_classes = [permissions.IsAdminUser]

class MetricaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Metrica.objects.all()
    serializer_class = MetricaSerializer
    permission_classes = [permissions.IsAuthenticated]

class SesionTrabajoViewSet(viewsets.ModelViewSet):
    queryset = SesionTrabajo.objects.all()
    serializer_class = SesionTrabajoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SesionTrabajo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class ReportePersonalizadoViewSet(viewsets.ModelViewSet):
    queryset = ReportePersonalizado.objects.all()
    serializer_class = ReportePersonalizadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ReportePersonalizado.objects.filter(creado_por=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

class TareaAutomaticaViewSet(viewsets.ModelViewSet):
    queryset = TareaAutomatica.objects.all()
    serializer_class = TareaAutomaticaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TareaAutomatica.objects.filter(creada_por=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creada_por=self.request.user)

class ComentarioRegistroViewSet(viewsets.ModelViewSet):
    queryset = ComentarioRegistro.objects.all()
    serializer_class = ComentarioRegistroSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ComentarioRegistro.objects.filter(registro__usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)

class PlantillaRegistroViewSet(viewsets.ModelViewSet):
    queryset = PlantillaRegistro.objects.all()
    serializer_class = PlantillaRegistroSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PlantillaRegistro.objects.filter(creada_por=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creada_por=self.request.user)

class IntegracionExternaViewSet(viewsets.ModelViewSet):
    queryset = IntegracionExterna.objects.all()
    serializer_class = IntegracionExternaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return IntegracionExterna.objects.filter(creada_por=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creada_por=self.request.user)

@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')

@login_required
def notificaciones_view(request):
    """Vista para gestionar notificaciones del usuario"""
    if request.method == 'POST':
        notificacion_id = request.POST.get('notificacion_id')
        accion = request.POST.get('accion')

        if notificacion_id and accion == 'marcar_leida':
            try:
                notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
                notificacion.marcar_leida()
                return JsonResponse({'success': True})
            except Notificacion.DoesNotExist:
                return JsonResponse({'error': 'Notificación no encontrada'}, status=404)

    # Obtener notificaciones paginadas
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')

    # Estadísticas de notificaciones
    total_notificaciones = notificaciones.count()
    no_leidas = notificaciones.filter(leida=False).count()
    leidas = total_notificaciones - no_leidas

    context = {
        'notificaciones': notificaciones,
        'total_notificaciones': total_notificaciones,
        'no_leidas': no_leidas,
        'leidas': leidas,
    }

    return render(request, 'core/notificaciones.html', context)

@login_required
def insignias_view(request):
    """Vista mejorada para mostrar insignias del usuario"""
    usuario = request.user

    # Insignias obtenidas
    insignias_obtenidas = usuario.insignias.all().order_by('-fecha_creacion')

    # Insignias disponibles (no obtenidas aún)
    insignias_disponibles = Insignia.objects.filter(activa=True).exclude(
        id__in=usuario.insignias.values_list('id', flat=True)
    )

    # Calcular progreso para insignias disponibles
    for insignia in insignias_disponibles:
        progreso = 0

        # Verificar condiciones de progreso
        if insignia.registros_minimos > 0:
            progreso_registros = min(100, (usuario.registros_totales / insignia.registros_minimos) * 100)
            progreso = max(progreso, progreso_registros)

        if insignia.precision_minima > 0:
            progreso_precision = min(100, (usuario.precision_promedio / insignia.precision_minima) * 100)
            progreso = max(progreso, progreso_precision)

        if insignia.nivel_requerido > 0:
            progreso_nivel = min(100, (usuario.nivel / insignia.nivel_requerido) * 100)
            progreso = max(progreso, progreso_nivel)

        insignia.progreso = round(progreso, 1)

    # Estadísticas de gamificación
    estadisticas_gamificacion = {
        'total_insignias': Insignia.objects.filter(activa=True).count(),
        'insignias_obtenidas': insignias_obtenidas.count(),
        'porcentaje_completado': round((insignias_obtenidas.count() / Insignia.objects.filter(activa=True).count()) * 100, 1) if Insignia.objects.filter(activa=True).exists() else 0,
        'puntos_experiencia': usuario.puntos_experiencia,
        'nivel_actual': usuario.nivel,
        'racha_actual': usuario.racha_actual,
    }

    context = {
        'insignias_obtenidas': insignias_obtenidas,
        'insignias_disponibles': insignias_disponibles,
        'estadisticas_gamificacion': estadisticas_gamificacion,
    }

    return render(request, 'core/insignias.html', context)

@login_required
def perfil_usuario_view(request):
    """Vista para el perfil del usuario"""
    if request.method == 'POST':
        # Actualizar perfil
        usuario = request.user
        usuario.first_name = request.POST.get('first_name', usuario.first_name)
        usuario.last_name = request.POST.get('last_name', usuario.last_name)
        usuario.email = request.POST.get('email', usuario.email)
        usuario.telefono = request.POST.get('telefono', usuario.telefono)
        usuario.bio = request.POST.get('bio', usuario.bio)
        usuario.fecha_nacimiento = request.POST.get('fecha_nacimiento') or None

        # Nuevos campos de preferencias
        usuario.perfil_publico = request.POST.get('perfil_publico') == 'on'
        usuario.mostrar_estadisticas = request.POST.get('mostrar_estadisticas') == 'on'
        usuario.notificaciones_push = request.POST.get('notificaciones_push') == 'on'
        usuario.idioma_preferido = request.POST.get('idioma_preferido', usuario.idioma_preferido)
        usuario.zona_horaria = request.POST.get('zona_horaria', usuario.zona_horaria)
        usuario.formato_fecha = request.POST.get('formato_fecha', usuario.formato_fecha)

        try:
            usuario.save()
            mensaje = {'tipo': 'success', 'texto': 'Perfil actualizado correctamente.'}
        except Exception as e:
            mensaje = {'tipo': 'error', 'texto': f'Error al actualizar perfil: {str(e)}'}
    else:
        mensaje = None

    context = {
        'mensaje': mensaje,
        'analisis_usuario': analizar_usuario(request.user.id),
    }

    return render(request, 'core/perfil.html', context)

@login_required
def dashboard_view(request):
    """Dashboard principal mejorado"""
    usuario = request.user

    # Estadísticas rápidas
    estadisticas_rapidas = {
        'total_registros': Registro.objects.filter(usuario=usuario).count(),
        'registros_hoy': Registro.objects.filter(
            usuario=usuario,
            fecha__date=timezone.now().date()
        ).count(),
        'precision_actual': usuario.precision_promedio,
        'nivel_actual': usuario.nivel,
        'insignias_total': usuario.insignias.count(),
        'notificaciones_no_leidas': Notificacion.objects.filter(
            usuario=usuario, leida=False
        ).count(),
    }

    # Agregar propiedades al usuario para el navbar
    usuario.notificaciones_no_leidas = estadisticas_rapidas['notificaciones_no_leidas']

    # Actividad reciente
    actividad_reciente = []

    # Últimos registros
    ultimos_registros = Registro.objects.filter(usuario=usuario).order_by('-fecha')[:3]
    for registro in ultimos_registros:
        actividad_reciente.append({
            'tipo': 'registro',
            'titulo': f'Registro creado: {registro.apellido}, {registro.nombres}',
            'fecha': registro.fecha,
            'icono': 'fas fa-plus-circle',
            'color': 'success'
        })

    # Insignias recientes
    insignias_recientes = usuario.insignias.order_by('-fecha_creacion')[:2]
    for insignia in insignias_recientes:
        actividad_reciente.append({
            'tipo': 'insignia',
            'titulo': f'Insignia obtenida: {insignia.nombre}',
            'fecha': insignia.fecha_creacion,
            'icono': 'fas fa-trophy',
            'color': 'warning'
        })

    # Notificaciones recientes
    notificaciones_recientes = Notificacion.objects.filter(
        usuario=usuario
    ).order_by('-fecha')[:3]
    for notif in notificaciones_recientes:
        actividad_reciente.append({
            'tipo': 'notificacion',
            'titulo': notif.titulo,
            'fecha': notif.fecha,
            'icono': 'fas fa-bell',
            'color': 'info'
        })

    # Ordenar por fecha
    actividad_reciente.sort(key=lambda x: x['fecha'], reverse=True)
    actividad_reciente = actividad_reciente[:6]  # Limitar a 6 elementos

    # Recomendaciones de IA
    analisis_ia = analizar_usuario(usuario.id)
    recomendaciones = analisis_ia.get('sugerencias', [])[:3]

    context = {
        'estadisticas_rapidas': estadisticas_rapidas,
        'actividad_reciente': actividad_reciente,
        'recomendaciones': recomendaciones,
        'analisis_ia': analisis_ia,
    }

    return render(request, 'core/dashboard.html', context)

@login_required
def sesiones_trabajo_view(request):
    """Vista para gestionar sesiones de trabajo"""
    if request.method == 'POST':
        if 'iniciar_sesion' in request.POST:
            # Iniciar nueva sesión de trabajo
            registros_creados = int(request.POST.get('registros_creados', 0))
            errores_detectados = int(request.POST.get('errores_detectados', 0))
            tiempo_promedio = request.POST.get('tiempo_promedio', None)
            dispositivo = request.POST.get('dispositivo', '')

            sesion = SesionTrabajo.objects.create(
                usuario=request.user,
                registros_creados=registros_creados,
                errores_detectados=errores_detectados,
                tiempo_promedio_registro=tiempo_promedio,
                dispositivo=dispositivo,
                fecha_inicio=timezone.now()
            )

            return JsonResponse({
                'success': True,
                'sesion_id': sesion.id,
                'mensaje': 'Sesión de trabajo iniciada'
            })

        elif 'finalizar_sesion' in request.POST:
            # Finalizar sesión activa
            sesion_id = request.POST.get('sesion_id')
            try:
                sesion = SesionTrabajo.objects.get(id=sesion_id, usuario=request.user, fecha_fin__isnull=True)
                sesion.fecha_fin = timezone.now()
                sesion.duracion = (sesion.fecha_fin - sesion.fecha_inicio).total_seconds() / 3600  # en horas
                sesion.save()

                return JsonResponse({
                    'success': True,
                    'duracion': round(sesion.duracion, 2),
                    'mensaje': f'Sesión finalizada. Duración: {round(sesion.duracion, 2)} horas'
                })
            except SesionTrabajo.DoesNotExist:
                return JsonResponse({'error': 'Sesión no encontrada'}, status=404)

    # Obtener sesiones del usuario
    sesiones = SesionTrabajo.objects.filter(usuario=request.user).order_by('-fecha_inicio')[:10]
    sesion_activa = SesionTrabajo.objects.filter(usuario=request.user, fecha_fin__isnull=True).first()

    # Estadísticas de sesiones
    estadisticas = {
        'total_sesiones': SesionTrabajo.objects.filter(usuario=request.user).count(),
        'horas_totales': SesionTrabajo.objects.filter(usuario=request.user).aggregate(
            total=Sum('duracion'))['total'] or 0,
        'sesiones_hoy': SesionTrabajo.objects.filter(
            usuario=request.user,
            fecha_inicio__date=timezone.now().date()
        ).count(),
        'promedio_diario': SesionTrabajo.objects.filter(
            usuario=request.user
        ).aggregate(avg=Avg('duracion'))['avg'] or 0
    }

    context = {
        'sesiones': sesiones,
        'sesion_activa': sesion_activa,
        'estadisticas': estadisticas,
    }

    return render(request, 'core/sesiones_trabajo.html', context)

@login_required
def reportes_personalizados_view(request):
    """Vista para gestionar reportes personalizados"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        tipo = request.POST.get('tipo', 'tabla')
        campos_seleccionados = request.POST.get('campos_seleccionados', '[]')
        filtros = request.POST.get('filtros', '{}')
        agrupamiento = request.POST.get('agrupamiento', '{}')

        try:
            campos_data = json.loads(campos_seleccionados)
            filtros_data = json.loads(filtros)
            agrupamiento_data = json.loads(agrupamiento)

            reporte = ReportePersonalizado.objects.create(
                creado_por=request.user,
                nombre=nombre,
                descripcion=descripcion,
                tipo=tipo,
                campos_seleccionados=campos_data,
                filtros=filtros_data,
                agrupamiento=agrupamiento_data
            )

            return JsonResponse({
                'success': True,
                'reporte_id': reporte.id,
                'mensaje': 'Reporte personalizado creado'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'JSON inválido: {str(e)}'}, status=400)

    # Obtener reportes del usuario
    reportes = ReportePersonalizado.objects.filter(creado_por=request.user).order_by('-fecha_creacion')

    context = {
        'reportes': reportes,
    }

    return render(request, 'core/reportes_personalizados.html', context)

@login_required
def tareas_automaticas_view(request):
    """Vista para gestionar tareas automáticas"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        tipo = request.POST.get('tipo', 'revision')
        frecuencia = request.POST.get('frecuencia', 'diaria')
        hora_ejecucion = request.POST.get('hora_ejecucion', '09:00:00')
        dias_ejecucion = request.POST.get('dias_ejecucion', '[]')
        parametros = request.POST.get('parametros', '{}')
        activa = request.POST.get('activa') == 'on'

        try:
            dias_data = json.loads(dias_ejecucion)
            parametros_data = json.loads(parametros)

            tarea = TareaAutomatica.objects.create(
                creada_por=request.user,
                nombre=nombre,
                descripcion=descripcion,
                tipo=tipo,
                frecuencia=frecuencia,
                hora_ejecucion=hora_ejecucion,
                dias_ejecucion=dias_data,
                parametros=parametros_data,
                activa=activa
            )

            return JsonResponse({
                'success': True,
                'tarea_id': tarea.id,
                'mensaje': 'Tarea automática creada'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'JSON inválido: {str(e)}'}, status=400)

    # Obtener tareas del usuario
    tareas = TareaAutomatica.objects.filter(creada_por=request.user).order_by('-ultima_ejecucion')

    # Estadísticas de tareas
    estadisticas = {
        'total_tareas': tareas.count(),
        'tareas_activas': tareas.filter(activa=True).count(),
        'tareas_ejecutadas_hoy': tareas.filter(
            ultima_ejecucion__date=timezone.now().date()
        ).count(),
    }

    context = {
        'tareas': tareas,
        'estadisticas': estadisticas,
    }

    return render(request, 'core/tareas_automaticas.html', context)

@login_required
def plantillas_registro_view(request):
    """Vista para gestionar plantillas de registro"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        tipo = request.POST.get('tipo', 'personalizado')
        campos_requeridos = request.POST.get('campos_requeridos', '[]')
        campos_opcionales = request.POST.get('campos_opcionales', '[]')
        validaciones = request.POST.get('validaciones', '{}')

        try:
            requeridos_data = json.loads(campos_requeridos)
            opcionales_data = json.loads(campos_opcionales)
            validaciones_data = json.loads(validaciones)

            plantilla = PlantillaRegistro.objects.create(
                creada_por=request.user,
                nombre=nombre,
                descripcion=descripcion,
                tipo=tipo,
                campos_requeridos=requeridos_data,
                campos_opcionales=opcionales_data,
                validaciones=validaciones_data
            )

            return JsonResponse({
                'success': True,
                'plantilla_id': plantilla.id,
                'mensaje': 'Plantilla de registro creada'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'JSON inválido: {str(e)}'}, status=400)

    # Obtener plantillas del usuario
    plantillas = PlantillaRegistro.objects.filter(creada_por=request.user).order_by('-fecha_creacion')

    context = {
        'plantillas': plantillas,
    }

    return render(request, 'core/plantillas_registro.html', context)

@login_required
def comentarios_registro_view(request):
    """Vista para gestionar comentarios en registros"""
    if request.method == 'POST':
        if 'nuevo_comentario' in request.POST:
            registro_id = request.POST.get('registro_id')
            contenido = request.POST.get('contenido')

            try:
                registro = Registro.objects.get(id=registro_id)
                comentario = ComentarioRegistro.objects.create(
                    registro=registro,
                    autor=request.user,
                    contenido=contenido
                )
                return JsonResponse({
                    'success': True,
                    'comentario_id': comentario.id,
                    'mensaje': 'Comentario agregado'
                })
            except Registro.DoesNotExist:
                return JsonResponse({'error': 'Registro no encontrado'}, status=404)

        elif 'respuesta' in request.POST:
            comentario_padre_id = request.POST.get('comentario_padre_id')
            contenido = request.POST.get('contenido')

            try:
                comentario_padre = ComentarioRegistro.objects.get(id=comentario_padre_id)
                respuesta = ComentarioRegistro.objects.create(
                    registro=comentario_padre.registro,
                    autor=request.user,
                    contenido=contenido,
                    comentario_padre=comentario_padre
                )
                return JsonResponse({
                    'success': True,
                    'respuesta_id': respuesta.id,
                    'mensaje': 'Respuesta agregada'
                })
            except ComentarioRegistro.DoesNotExist:
                return JsonResponse({'error': 'Comentario padre no encontrado'}, status=404)

        elif 'like' in request.POST:
            comentario_id = request.POST.get('comentario_id')
            try:
                comentario = ComentarioRegistro.objects.get(id=comentario_id)
                if request.user in comentario.likes.all():
                    comentario.likes.remove(request.user)
                    liked = False
                else:
                    comentario.likes.add(request.user)
                    liked = True

                return JsonResponse({
                    'success': True,
                    'liked': liked,
                    'likes_count': comentario.likes.count()
                })
            except ComentarioRegistro.DoesNotExist:
                return JsonResponse({'error': 'Comentario no encontrado'}, status=404)

    # Obtener comentarios recientes
    comentarios_recientes = ComentarioRegistro.objects.filter(
        registro__usuario=request.user
    ).order_by('-fecha')[:20]

    # Comentarios más valorados
    comentarios_mas_valorados = ComentarioRegistro.objects.filter(
        registro__usuario=request.user
    ).annotate(likes_count=Count('likes')).order_by('-likes_count')[:10]

    # Usuarios más activos en comentarios
    usuarios_mas_activos = Usuario.objects.filter(
        id__in=ComentarioRegistro.objects.filter(
            registro__usuario=request.user
        ).values_list('autor', flat=True)
    ).annotate(
        comentarios_count=Count('comentarioregistro'),
        likes_received=Count('comentarioregistro__likes')
    ).order_by('-comentarios_count')[:10]

    # Estadísticas
    estadisticas = {
        'total_comentarios': ComentarioRegistro.objects.filter(registro__usuario=request.user).count(),
        'comentarios_hoy': ComentarioRegistro.objects.filter(
            registro__usuario=request.user,
            fecha__date=timezone.now().date()
        ).count(),
        'usuarios_activos': len(set(ComentarioRegistro.objects.filter(
            registro__usuario=request.user
        ).values_list('autor', flat=True))),
        'likes_totales': ComentarioRegistro.objects.filter(
            registro__usuario=request.user
        ).aggregate(total=Count('likes'))['total'] or 0
    }

    context = {
        'comentarios_recientes': comentarios_recientes,
        'comentarios_mas_valorados': comentarios_mas_valorados,
        'usuarios_mas_activos': usuarios_mas_activos,
        'total_comentarios': estadisticas['total_comentarios'],
        'comentarios_hoy': estadisticas['comentarios_hoy'],
        'usuarios_activos': estadisticas['usuarios_activos'],
        'likes_totales': estadisticas['likes_totales'],
    }

    return render(request, 'core/comentarios_registro.html', context)

@login_required
def integraciones_externas_view(request):
    """Vista para gestionar integraciones externas"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion', '')
        tipo = request.POST.get('tipo', 'api')
        url_endpoint = request.POST.get('url_endpoint', '')
        api_key = request.POST.get('api_key', '')
        headers = request.POST.get('headers', '{}')
        autenticacion = request.POST.get('autenticacion', '{}')

        try:
            headers_data = json.loads(headers)
            autenticacion_data = json.loads(autenticacion)

            integracion = IntegracionExterna.objects.create(
                creada_por=request.user,
                nombre=nombre,
                descripcion=descripcion,
                tipo=tipo,
                url_endpoint=url_endpoint,
                api_key=api_key,
                headers=headers_data,
                autenticacion=autenticacion_data
            )

            return JsonResponse({
                'success': True,
                'integracion_id': integracion.id,
                'mensaje': 'Integración externa creada'
            })
        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'JSON inválido: {str(e)}'}, status=400)

    # Obtener integraciones del usuario
    integraciones = IntegracionExterna.objects.filter(creada_por=request.user).order_by('-fecha_creacion')

    # Estadísticas
    estadisticas = {
        'total_integraciones': integraciones.count(),
        'integraciones_activas': integraciones.filter(activa=True).count(),
        'sincronizaciones_hoy': integraciones.filter(
            ultima_sincronizacion__date=timezone.now().date()
        ).count(),
    }

    context = {
        'integraciones': integraciones,
        'estadisticas': estadisticas,
    }

    return render(request, 'core/integraciones_externas.html', context)
