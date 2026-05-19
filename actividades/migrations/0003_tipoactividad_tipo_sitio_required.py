from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0002_tipoactividad_tipo_sitio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoactividad',
            name='tipo_sitio',
            field=models.CharField(
                choices=[('POSTE', 'Poste'), ('TORRE', 'Torre')],
                default='TORRE',
                help_text='Debe coincidir con el tipo_sitio del sitio (POSTE o TORRE).',
                max_length=10,
                verbose_name='Tipo de sitio',
            ),
            preserve_default=False,
        ),
    ]
