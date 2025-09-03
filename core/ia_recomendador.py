import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from collections import Counter
from .models import Error, Usuario, Registro, Metrica
import re
from datetime import datetime, timedelta

# Base de conocimientos de microlecciones
MICROLECCIONES = {
    'email': {
        'titulo': 'Validación de Correos Electrónicos',
        'contenido': 'Los correos deben tener formato usuario@dominio.com. Evite espacios y caracteres especiales.',
        'ejemplos': ['usuario@empresa.com', 'nombre.apellido@gmail.com'],
        'errores_comunes': ['usuario@empresa', 'usuario empresa.com', 'usuario@empresa.']
    },
    'dni': {
        'titulo': 'Formato de Documento Nacional de Identidad',
        'contenido': 'El DNI debe contener solo números, con 7 u 8 dígitos.',
        'ejemplos': ['12345678', '87654321'],
        'errores_comunes': ['12.345.678', '1234567A', '123456789']
    },
    'telefono': {
        'titulo': 'Formato de Números Telefónicos',
        'contenido': 'Use formato internacional o local. Ej: +54 11 1234-5678 o 11 12345678',
        'ejemplos': ['+54 11 1234-5678', '011 15 1234 5678'],
        'errores_comunes': ['12345678', '11-1234-5678', '01112345678']
    },
    'apellido': {
        'titulo': 'Validación de Apellidos',
        'contenido': 'Los apellidos deben contener solo letras, espacios y apóstrofes.',
        'ejemplos': ['García', 'Fernández López', "O'Connor"],
        'errores_comunes': ['García123', 'Fernández-López', 'GARCÍA']
    },
    'fecha_nacimiento': {
        'titulo': 'Formato de Fechas',
        'contenido': 'Use formato DD/MM/YYYY o YYYY-MM-DD.',
        'ejemplos': ['15/08/1990', '1990-08-15'],
        'errores_comunes': ['15-08-90', '1990/08/15', '15/08/1990 12:00']
    }
}

class RecomendadorIA:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
        self.modelo_entrenado = False

    def analizar_patron_errores(self, usuario_id):
        """Analiza patrones de error del usuario usando machine learning"""
        errores = Error.objects.filter(registro__usuario_id=usuario_id)

        if not errores.exists():
            return None

        # Crear dataset de errores
        datos_errores = []
        for error in errores:
            datos_errores.append({
                'campo': error.campo,
                'tipo': error.tipo,
                'mensaje': error.mensaje.lower(),
                'gravedad': error.gravedad
            })

        df = pd.DataFrame(datos_errores)

        # Análisis de frecuencia por campo
        campo_mas_frecuente = df['campo'].value_counts().idxmax()
        frecuencia_campo = df['campo'].value_counts().max()

        # Análisis de tipos de error
        tipo_mas_frecuente = df['tipo'].value_counts().idxmax()

        # Clustering de mensajes de error similares
        if len(df) > 3:
            try:
                # Vectorizar mensajes de error
                mensajes = df['mensaje'].fillna('')
                tfidf_matrix = self.vectorizer.fit_transform(mensajes)

                # Clustering
                n_clusters = min(3, len(df))
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(tfidf_matrix)

                # Encontrar el cluster más grande
                cluster_mas_grande = Counter(clusters).most_common(1)[0][0]
                mensajes_cluster = df.iloc[np.where(clusters == cluster_mas_grande)[0]]['mensaje']

                patron_principal = mensajes_cluster.mode().iloc[0] if not mensajes_cluster.empty else ""
            except:
                patron_principal = ""
        else:
            patron_principal = ""

        return {
            'campo_principal': campo_mas_frecuente,
            'frecuencia_campo': frecuencia_campo,
            'tipo_principal': tipo_mas_frecuente,
            'patron_principal': patron_principal,
            'total_errores': len(df)
        }

    def recomendar_microleccion(self, usuario_id):
        """Recomienda la microlección más apropiada para el usuario"""
        analisis = self.analizar_patron_errores(usuario_id)

        if not analisis:
            return {
                'titulo': '¡Excelente trabajo!',
                'contenido': 'No hemos detectado errores recurrentes en tus registros.',
                'tipo': 'success'
            }

        campo = analisis['campo_principal']

        if campo in MICROLECCIONES:
            microleccion = MICROLECCIONES[campo].copy()
            microleccion['tipo'] = 'warning'
            microleccion['estadisticas'] = {
                'errores_en_campo': analisis['frecuencia_campo'],
                'total_errores': analisis['total_errores']
            }
            return microleccion

        # Recomendación genérica si no hay microlección específica
        return {
            'titulo': 'Mejora General de Calidad',
            'contenido': f'Hemos detectado {analisis["total_errores"]} errores, principalmente en el campo "{campo}". Revisa la documentación para mejores prácticas.',
            'tipo': 'info',
            'estadisticas': {
                'errores_en_campo': analisis['frecuencia_campo'],
                'total_errores': analisis['total_errores']
            }
        }

    def predecir_errores_posibles(self, datos_registro):
        """Predice posibles errores en un registro basado en patrones históricos"""
        errores_predichos = []

        # Análisis de email
        if 'email' in datos_registro:
            email = datos_registro['email']
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                errores_predichos.append({
                    'campo': 'email',
                    'tipo': 'formato',
                    'probabilidad': 0.9,
                    'mensaje': 'El formato del email parece incorrecto'
                })

        # Análisis de DNI
        if 'dni' in datos_registro:
            dni = str(datos_registro['dni'])
            if not re.match(r'^\d{7,8}$', dni):
                errores_predichos.append({
                    'campo': 'dni',
                    'tipo': 'formato',
                    'probabilidad': 0.8,
                    'mensaje': 'El DNI debe tener 7 u 8 dígitos numéricos'
                })

        # Análisis de teléfono
        if 'telefono' in datos_registro:
            telefono = str(datos_registro['telefono'])
            if not re.match(r'^\+?[\d\s\-\(\)]+$', telefono) or len(re.sub(r'\D', '', telefono)) < 8:
                errores_predichos.append({
                    'campo': 'telefono',
                    'tipo': 'formato',
                    'probabilidad': 0.7,
                    'mensaje': 'El formato del teléfono parece incorrecto'
                })

        return errores_predichos

    def calcular_precision_usuario(self, usuario_id):
        """Calcula la precisión del usuario basada en su historial"""
        registros = Registro.objects.filter(usuario_id=usuario_id)

        if not registros.exists():
            return 0.0

        total_registros = registros.count()
        registros_con_errores = registros.filter(errores__isnull=False).distinct().count()

        if total_registros == 0:
            return 0.0

        precision = ((total_registros - registros_con_errores) / total_registros) * 100
        return round(precision, 2)

    def sugerir_mejoras(self, usuario_id):
        """Sugiere mejoras específicas para el usuario"""
        usuario = Usuario.objects.get(id=usuario_id)
        precision = self.calcular_precision_usuario(usuario_id)

        sugerencias = []

        if precision < 70:
            sugerencias.append({
                'tipo': 'capacitacion',
                'titulo': 'Capacitación Recomendada',
                'descripcion': 'Tu precisión actual es baja. Te recomendamos completar el módulo de validación de datos.'
            })

        # Análisis de patrones de error
        analisis = self.analizar_patron_errores(usuario_id)
        if analisis and analisis['total_errores'] > 10:
            sugerencias.append({
                'tipo': 'practica',
                'titulo': 'Práctica Específica',
                'descripcion': f'Enfócate en mejorar la validación del campo "{analisis["campo_principal"]}".'
            })

        # Verificar racha actual
        if usuario.racha_actual < 5:
            sugerencias.append({
                'tipo': 'motivacion',
                'titulo': 'Mantén la Racha',
                'descripcion': '¡Estás cerca de conseguir una insignia! Sigue registrando datos sin errores.'
            })

        return sugerencias

# Instancia global del recomendador
recomendador = RecomendadorIA()

def recomendar_microleccion(usuario_id):
    """Función de compatibilidad con el código existente"""
    return recomendador.recomendar_microleccion(usuario_id)

def analizar_usuario(usuario_id):
    """Análisis completo del usuario"""
    return {
        'precision': recomendador.calcular_precision_usuario(usuario_id),
        'recomendacion': recomendador.recomendar_microleccion(usuario_id),
        'sugerencias': recomendador.sugerir_mejoras(usuario_id),
        'analisis_errores': recomendador.analizar_patron_errores(usuario_id)
    }