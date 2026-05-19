import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0004_regactividad_tipo_sitio'),
    ]

    operations = [
        # 1. Agregar paso FK a ConfigWidget (nullable temporalmente)
        migrations.AddField(
            model_name='configwidget',
            name='paso',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='widgets',
                to='actividades.pasoactividad',
                verbose_name='Paso',
            ),
        ),
        # 2. Renombrar orden_en_fila → orden
        migrations.RenameField(
            model_name='configwidget',
            old_name='orden_en_fila',
            new_name='orden',
        ),
        # 3. Actualizar verbose_name del campo orden
        migrations.AlterField(
            model_name='configwidget',
            name='orden',
            field=models.PositiveIntegerField(default=0, verbose_name='Orden (izq → der)'),
        ),
        # 4. Actualizar help_text de params
        migrations.AlterField(
            model_name='configwidget',
            name='params',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='CAMERA: {"label": "Fotos", "foto_min": 2} | MAP_1: {"lat_field": "lat", "lon_field": "lon", "label": "Ubicación"}',
                verbose_name='Parámetros',
            ),
        ),
        # 5. Eliminar FK a FilaWidgets
        migrations.RemoveField(
            model_name='configwidget',
            name='fila',
        ),
        # 6. Hacer paso FK no-nullable
        migrations.AlterField(
            model_name='configwidget',
            name='paso',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='widgets',
                to='actividades.pasoactividad',
                verbose_name='Paso',
            ),
        ),
        # 7. Eliminar FilaWidgets
        migrations.DeleteModel(
            name='FilaWidgets',
        ),
    ]
