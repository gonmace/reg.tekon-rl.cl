"""El paso «Eléctrico» es opcional también en su comentario: vacío se ve gris, con texto verde."""
from django.db import migrations

PASO = 'obra_electrico'


def _opcional(apps, valor):
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    for pw in PasoWidget.objects.filter(pasodef__nombre=PASO, widget_slug='comentario_widget'):
        config = {k: v for k, v in (pw.config or {}).items() if k != 'opcional'}
        if valor:
            config['opcional'] = True
        pw.config = config
        pw.save(update_fields=['config'])


def adelante(apps, schema_editor):
    _opcional(apps, True)


def atras(apps, schema_editor):
    _opcional(apps, False)


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0011_actividades_libro_de_obras')]
    operations = [migrations.RunPython(adelante, atras)]
