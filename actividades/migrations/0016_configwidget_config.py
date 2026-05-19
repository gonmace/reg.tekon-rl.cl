from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0015_configwidget_min_fotos'),
    ]

    operations = [
        migrations.AddField(
            model_name='configwidget',
            name='config',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Parámetros específicos de esta asignación (sobreescriben los del catálogo).',
                verbose_name='Configuración',
            ),
        ),
    ]
