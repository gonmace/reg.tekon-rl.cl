from django.db import migrations, models


def _set_filas(apps, schema_editor):
    CampoFormulario = apps.get_model('actividades', 'CampoFormulario')
    # Each existing field gets its own row (fila = old_orden + 1)
    for campo in CampoFormulario.objects.order_by('orden'):
        campo.fila = campo.orden + 1
        campo.save()


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0008_campo_ancho'),
    ]

    operations = [
        # 1. Add fila field (nullable initially for data migration)
        migrations.AddField(
            model_name='campoformulario',
            name='fila',
            field=models.PositiveIntegerField(default=1, verbose_name='Fila'),
        ),
        # 2. Data migration: fila = orden + 1
        migrations.RunPython(_set_filas, migrations.RunPython.noop),
        # 3. Drop ancho
        migrations.RemoveField(
            model_name='campoformulario',
            name='ancho',
        ),
        # 4. Update ordering (handled by model Meta, no migration needed)
        migrations.AlterModelOptions(
            name='campoformulario',
            options={
                'ordering': ['fila', 'orden'],
                'verbose_name': 'Campo de Formulario',
                'verbose_name_plural': 'Campos de Formulario',
            },
        ),
    ]
