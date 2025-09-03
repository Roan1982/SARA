from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import Usuario, Insignia, Registro, Error, Metrica, Notificacion, LogAuditoria, ConfiguracionSistema, ConfiguracionSistema
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de ejemplo'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de ejemplo...')

        # Crear insignias mejoradas
        insignias_data = [
            {
                'nombre': 'Primer Registro',
                'descripcion': 'Por crear tu primer registro',
                'tipo': 'logro',
                'icono': 'fas fa-plus-circle',
                'color': '#28a745',
                'puntos_otorgados': 10,
                'nivel_requerido': 1,
                'experiencia_otorgada': 50,
                'registros_minimos': 1,
                'precision_minima': 0,
                'errores_maximos': 999,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Operador Estrella',
                'descripcion': 'Por completar 10 registros sin errores',
                'tipo': 'habilidad',
                'icono': 'fas fa-star',
                'color': '#ffc107',
                'puntos_otorgados': 25,
                'nivel_requerido': 1,
                'experiencia_otorgada': 100,
                'registros_minimos': 10,
                'precision_minima': 90,
                'errores_maximos': 1,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Líder del Equipo',
                'descripcion': 'Por ser líder de equipo',
                'tipo': 'liderazgo',
                'icono': 'fas fa-users',
                'color': '#007bff',
                'puntos_otorgados': 50,
                'nivel_requerido': 2,
                'experiencia_otorgada': 200,
                'registros_minimos': 0,
                'precision_minima': 0,
                'errores_maximos': 999,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Administrador',
                'descripcion': 'Por ser administrador del sistema',
                'tipo': 'liderazgo',
                'icono': 'fas fa-crown',
                'color': '#6f42c1',
                'puntos_otorgados': 100,
                'nivel_requerido': 3,
                'experiencia_otorgada': 500,
                'registros_minimos': 0,
                'precision_minima': 0,
                'errores_maximos': 999,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Experto en Datos',
                'descripcion': 'Por procesar más de 50 registros',
                'tipo': 'dedicacion',
                'icono': 'fas fa-brain',
                'color': '#e83e8c',
                'puntos_otorgados': 75,
                'nivel_requerido': 2,
                'experiencia_otorgada': 300,
                'registros_minimos': 50,
                'precision_minima': 85,
                'errores_maximos': 5,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Perfeccionista',
                'descripcion': 'Por mantener una precisión del 95% o superior',
                'tipo': 'calidad',
                'icono': 'fas fa-bullseye',
                'color': '#fd7e14',
                'puntos_otorgados': 40,
                'nivel_requerido': 2,
                'experiencia_otorgada': 150,
                'registros_minimos': 20,
                'precision_minima': 95,
                'errores_maximos': 1,
                'dias_consecutivos': 0,
            },
            {
                'nombre': 'Racha Dorada',
                'descripcion': 'Por mantener 7 días consecutivos sin errores',
                'tipo': 'dedicacion',
                'icono': 'fas fa-fire',
                'color': '#dc3545',
                'puntos_otorgados': 60,
                'nivel_requerido': 1,
                'experiencia_otorgada': 250,
                'registros_minimos': 7,
                'precision_minima': 100,
                'errores_maximos': 0,
                'dias_consecutivos': 7,
            },
        ]

        insignias = []
        for data in insignias_data:
            insignia, created = Insignia.objects.get_or_create(
                nombre=data['nombre'],
                defaults={
                    'descripcion': data['descripcion'],
                    'tipo': data['tipo'],
                    'icono': data['icono'],
                    'color': data['color'],
                    'puntos_otorgados': data['puntos_otorgados'],
                    'nivel_requerido': data['nivel_requerido'],
                    'experiencia_otorgada': data['experiencia_otorgada'],
                    'registros_minimos': data['registros_minimos'],
                    'precision_minima': data['precision_minima'],
                    'errores_maximos': data['errores_maximos'],
                    'dias_consecutivos': data['dias_consecutivos'],
                }
            )
            insignias.append(insignia)
            if created:
                self.stdout.write(f'  ✓ Creada insignia: {insignia.nombre} ({insignia.get_tipo_display()})')

        # Crear usuarios
        usuarios_data = [
            {'username': 'admin', 'email': 'admin@sara.com', 'rol': 'admin', 'password': 'admin123'},
            {'username': 'lider1', 'email': 'lider1@sara.com', 'rol': 'lider', 'password': 'lider123'},
            {'username': 'operador1', 'email': 'operador1@sara.com', 'rol': 'operador', 'password': 'operador123'},
            {'username': 'operador2', 'email': 'operador2@sara.com', 'rol': 'operador', 'password': 'operador123'},
            {'username': 'rrhh1', 'email': 'rrhh1@sara.com', 'rol': 'rrhh', 'password': 'rrhh123'},
        ]

        usuarios = []
        for data in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'rol': data['rol'],
                    'password': make_password(data['password'])
                }
            )
            usuarios.append(usuario)
            if created:
                self.stdout.write(f'  ✓ Creado usuario: {usuario.username} ({usuario.rol})')

        # Asignar insignias a usuarios
        admin_user = Usuario.objects.get(username='admin')
        admin_user.insignias.add(insignias[3])  # Administrador

        lider_user = Usuario.objects.get(username='lider1')
        lider_user.insignias.add(insignias[2])  # Líder del Equipo

        for operador in Usuario.objects.filter(rol='operador'):
            operador.insignias.add(insignias[0])  # Primer Registro
            if random.choice([True, False]):
                operador.insignias.add(insignias[1])  # Operador Estrella

        # Crear registros de ejemplo
        nombres_apellidos = [
            ('Juan', 'Pérez'), ('María', 'González'), ('Carlos', 'Rodríguez'),
            ('Ana', 'Fernández'), ('Luis', 'López'), ('Carmen', 'Martínez'),
            ('José', 'Sánchez'), ('Isabel', 'Ramírez'), ('Francisco', 'Torres'),
            ('Pilar', 'Flores'), ('Antonio', 'Rivera'), ('Rosa', 'Gómez')
        ]

        registros_creados = 0
        for i in range(50):  # Crear 50 registros
            usuario = random.choice([u for u in usuarios if u.rol == 'operador'])
            nombre, apellido = random.choice(nombres_apellidos)

            registro = Registro.objects.create(
                usuario=usuario,
                datos={
                    'dni': f'{random.randint(10000000, 99999999)}',
                    'apellido': apellido,
                    'email': f'{nombre.lower()}.{apellido.lower()}@ejemplo.com',
                    'telefono': f'11{random.randint(10000000, 99999999)}',
                    'direccion': f'Calle {random.randint(1, 1000)} {random.randint(1000, 9999)}'
                }
            )
            registros_creados += 1

            # Crear algunos errores aleatorios
            if random.random() < 0.3:  # 30% de probabilidad de error
                campos_con_error = ['dni', 'email', 'telefono']
                campo = random.choice(campos_con_error)
                Error.objects.create(
                    registro=registro,
                    campo=campo,
                    mensaje=f'Error en el campo {campo}: formato inválido'
                )

        self.stdout.write(f'  ✓ Creados {registros_creados} registros')

        # Crear métricas de ejemplo
        metricas_creadas = 0
        tipos_metrica = ['registros_por_hora', 'errores_detectados', 'tiempo_promedio', 'precision']

        for usuario in usuarios:
            for tipo in tipos_metrica:
                for i in range(5):  # 5 métricas por tipo por usuario
                    fecha = datetime.now() - timedelta(days=random.randint(0, 30))
                    valor = random.uniform(1, 100)

                    Metrica.objects.create(
                        usuario=usuario,
                        tipo=tipo,
                        valor=round(valor, 2),
                        fecha=fecha
                    )
                    metricas_creadas += 1

        self.stdout.write(f'  ✓ Creadas {metricas_creadas} métricas')

        # Crear configuraciones del sistema
        configuraciones_data = [
            {
                'clave': 'puntos_por_registro',
                'valor': '10',
                'tipo_dato': 'integer',
                'descripcion': 'Puntos de experiencia otorgados por cada registro válido',
                'categoria': 'gamificacion',
                'modificable_por_usuario': False,
            },
            {
                'clave': 'puntos_por_error',
                'valor': '-2',
                'tipo_dato': 'integer',
                'descripcion': 'Puntos restados por cada error cometido',
                'categoria': 'gamificacion',
                'modificable_por_usuario': False,
            },
            {
                'clave': 'dias_racha_maxima',
                'valor': '30',
                'tipo_dato': 'integer',
                'descripcion': 'Días máximos para mantener una racha activa',
                'categoria': 'gamificacion',
                'modificable_por_usuario': False,
            },
            {
                'clave': 'notificaciones_email_habilitadas',
                'valor': 'true',
                'tipo_dato': 'boolean',
                'descripcion': 'Habilitar envío de notificaciones por email',
                'categoria': 'notificaciones',
                'modificable_por_usuario': True,
            },
            {
                'clave': 'umbral_alerta_precision',
                'valor': '80',
                'tipo_dato': 'integer',
                'descripcion': 'Umbral mínimo de precisión para generar alertas (%)',
                'categoria': 'alertas',
                'modificable_por_usuario': False,
            },
            {
                'clave': 'max_registros_por_hora',
                'valor': '60',
                'tipo_dato': 'integer',
                'descripcion': 'Límite máximo de registros por hora por usuario',
                'categoria': 'limites',
                'modificable_por_usuario': False,
            },
        ]

        for config_data in configuraciones_data:
            ConfiguracionSistema.objects.get_or_create(
                clave=config_data['clave'],
                defaults=config_data
            )

        self.stdout.write('  ✓ Configuraciones del sistema creadas')

        self.stdout.write(self.style.SUCCESS('¡Datos de ejemplo creados exitosamente!'))
        self.stdout.write('')
        self.stdout.write('Usuarios de prueba:')
        for data in usuarios_data:
            self.stdout.write(f'  - {data["username"]}: {data["rol"]} (password: {data["password"]})')
        self.stdout.write('')
        self.stdout.write('Ahora puedes iniciar el servidor y probar el sistema.')
