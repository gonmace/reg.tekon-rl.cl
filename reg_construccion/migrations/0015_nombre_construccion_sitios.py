"""El tipo de actividad pasa a llamarse «Construcción Sitios» (el namespace interno no cambia)."""
from django.db import migrations

NAMESPACE = 'reg_construccion_torres'


def _renombrar(apps, de, a):
    TipoActividad = apps.get_model('actividades', 'TipoActividad')
    TipoActividad.objects.filter(app_namespace=NAMESPACE, nombre=de).update(nombre=a)


def adelante(apps, schema_editor):
    _renombrar(apps, 'Construcción Torres', 'Construcción Sitios')


def atras(apps, schema_editor):
    _renombrar(apps, 'Construcción Sitios', 'Construcción Torres')


class Migration(migrations.Migration):
    dependencies = [
        ('reg_construccion', '0014_mensaje_reporte'),
        ('actividades', '0022_contexto_registro'),
    ]
    operations = [migrations.RunPython(adelante, atras)]
