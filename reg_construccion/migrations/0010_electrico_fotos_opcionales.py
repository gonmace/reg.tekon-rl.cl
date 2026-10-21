"""Las fotos del paso «Eléctrico» son opcionales (foto_min 0: el botón queda verde aun sin fotos)."""
from django.db import migrations

PASO = 'obra_electrico'


def _foto_min(apps, valor):
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    for pw in PasoWidget.objects.filter(pasodef__nombre=PASO, widget_slug='camera_widget'):
        pw.config = {**(pw.config or {}), 'foto_min': valor}
        pw.save(update_fields=['config'])


def adelante(apps, schema_editor):
    _foto_min(apps, 0)


def atras(apps, schema_editor):
    _foto_min(apps, 1)


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0009_actividades_minimo_4_fotos')]
    operations = [migrations.RunPython(adelante, atras)]
