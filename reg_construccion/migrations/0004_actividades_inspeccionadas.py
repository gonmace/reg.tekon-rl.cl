"""
Renombra en el paso 'obra_objetivos' el término «Objetivos de la visita» por
«Actividades inspeccionadas» (título del paso y etiqueta del widget).

La clave interna del paso (obra_objetivos) NO cambia: ahí están los datos ya guardados.
"""
from django.db import migrations

PASO = 'obra_objetivos'
ANTIGUO = 'Objetivos de la visita'
NUEVO = 'Actividades inspeccionadas'


def _cambiar(apps, de, a):
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    PasoWidget = apps.get_model('actividades', 'PasoWidget')
    PasoDefinicion.objects.filter(nombre=PASO, titulo=de).update(titulo=a)
    # La etiqueta solo se toca si conserva el valor original (no pisa ediciones manuales).
    for pw in PasoWidget.objects.filter(pasodef__nombre=PASO, widget_slug='lista_widget'):
        if (pw.config or {}).get('label') == de:
            pw.config = {**pw.config, 'label': a}
            pw.save(update_fields=['config'])


def renombrar(apps, schema_editor):
    _cambiar(apps, ANTIGUO, NUEVO)


def revertir(apps, schema_editor):
    _cambiar(apps, NUEVO, ANTIGUO)


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0003_items_en_vez_de_partidas')]
    operations = [migrations.RunPython(renombrar, revertir)]
