"""«Actividades» exige un mínimo de 4 fotos (antes 1): el botón de cámara queda verde desde 4."""
from django.db import migrations

PASO = 'obra_objetivos'


def _foto_min(apps, valor):
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    for pw in PasoWidget.objects.filter(pasodef__nombre=PASO, widget_slug='camera_widget'):
        pw.config = {**(pw.config or {}), 'foto_min': valor}
        pw.save(update_fields=['config'])


def adelante(apps, schema_editor):
    _foto_min(apps, 4)


def atras(apps, schema_editor):
    _foto_min(apps, 1)


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0008_pasos_electrico_fotos')]
    operations = [migrations.RunPython(adelante, atras)]
