"""Renombra en el paso de avance el término «Partidas» por «Ítems» (solo el título visible)."""
from django.db import migrations


def renombrar(apps, schema_editor):
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    PasoDefinicion.objects.filter(nombre='obra_avance', titulo='Partidas y avance').update(titulo='Ítems y avance')


def revertir(apps, schema_editor):
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    PasoDefinicion.objects.filter(nombre='obra_avance', titulo='Ítems y avance').update(titulo='Partidas y avance')


class Migration(migrations.Migration):
    dependencies = [('reg_construccion', '0002_seed_tipo_actividad')]
    operations = [migrations.RunPython(renombrar, revertir)]
