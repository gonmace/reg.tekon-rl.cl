"""Siembra el TipoActividad 'reg_construccion_torres' con sus 4 pasos y la plantilla de ítems."""
from django.db import migrations

NAMESPACE = 'reg_construccion_torres'

PLANTILLA_TORRE = {
    'nombre': 'Torre estándar',
    'partidas': [
        {'nombre': 'Instalación de faenas', 'incidencia': 5},
        {'nombre': 'Replanteo y Trazado', 'incidencia': 5},
        {'nombre': 'Excavación para la fundación', 'incidencia': 5},
        {'nombre': 'Enfierradura de la fundación', 'incidencia': 15},
        {'nombre': 'Hormigonado de la fundación', 'incidencia': 15},
        {'nombre': 'Relleno y compactado', 'incidencia': 5},
        {'nombre': 'Montaje de la Torre', 'incidencia': 15},
        {'nombre': 'Losa Radier de Equipos', 'incidencia': 5},
        {'nombre': 'Cierre perimetral', 'incidencia': 5},
        {'nombre': 'Sistema puesta a tierra', 'incidencia': 5},
        {'nombre': 'Sistema Eléctrico', 'incidencia': 5},
        {'nombre': 'Línea Eléctrica Provisoria', 'incidencia': 5},
        {'nombre': 'Línea Eléctrica definitiva', 'incidencia': 5},
        {'nombre': 'Trabajos Finales / Adicionales', 'incidencia': 5},
    ],
}

PASOS = [
    ('obra_objetivos', 'Actividades inspeccionadas', 'lista_widget',
     {'label': 'Actividades inspeccionadas', 'placeholder': 'Ej: Revisión de izaje y montaje de torre', 'max_items': 30}),
    ('obra_avance', 'Ítems y avance', 'tabla_avance_widget', {'plantillas': [PLANTILLA_TORRE]}),
    ('obra_comentarios', 'Comentarios generales', 'lista_widget',
     {'label': 'Comentarios generales', 'placeholder': 'Observación de la visita', 'max_items': 50}),
    ('obra_fotos', 'Registro fotográfico', 'camera_widget', {'foto_min': 1}),
]


def seed(apps, schema_editor):
    TipoActividad = apps.get_model('actividades', 'TipoActividad')
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    ConfigPaso = apps.get_model('actividades', 'ConfigPaso')

    tipo, _ = TipoActividad.objects.get_or_create(
        app_namespace=NAMESPACE,
        defaults={'nombre': 'Construcción Torres', 'tipo_sitio': 'TORRE', 'activo': True,
                  'descripcion': 'Informe de visita del ITO a obras de torres'},
    )
    for orden, (nombre, titulo, widget_slug, config) in enumerate(PASOS, start=1):
        paso, _ = PasoDefinicion.objects.get_or_create(nombre=nombre, defaults={'titulo': titulo})
        PasoWidget.objects.get_or_create(
            pasodef=paso, widget_slug=widget_slug, defaults={'orden': 1, 'config': config})
        ConfigPaso.objects.get_or_create(tipo=tipo, pasodef=paso, defaults={'orden': orden})


def unseed(apps, schema_editor):
    TipoActividad = apps.get_model('actividades', 'TipoActividad')
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    TipoActividad.objects.filter(app_namespace=NAMESPACE).delete()
    PasoDefinicion.objects.filter(nombre__in=[p[0] for p in PASOS], asignaciones__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('reg_construccion', '0001_initial'),
        ('actividades', '0022_contexto_registro'),
    ]
    operations = [migrations.RunPython(seed, unseed)]
