"""«Actividades» gana una segunda cámara: imágenes del libro de obras (opcionales, etapa obra_libro)."""
from django.db import migrations

PASO = 'obra_objetivos'
SLUG = 'camera_libro_widget'


def adelante(apps, schema_editor):
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    paso = PasoDefinicion.objects.filter(nombre=PASO).first()
    if paso:
        PasoWidget.objects.get_or_create(
            pasodef=paso, widget_slug=SLUG, defaults={'orden': 3, 'config': {'foto_min': 0, 'etapa': 'obra_libro'}})


def atras(apps, schema_editor):
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    # Las imágenes ya subidas (etapa obra_libro) se conservan en la base.
    PasoWidget.objects.filter(pasodef__nombre=PASO, widget_slug=SLUG).delete()


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0010_electrico_fotos_opcionales')]
    operations = [migrations.RunPython(adelante, atras)]
