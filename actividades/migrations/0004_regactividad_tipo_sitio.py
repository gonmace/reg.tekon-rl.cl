from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0003_tipoactividad_tipo_sitio_required'),
    ]

    operations = [
        migrations.AddField(
            model_name='regactividad',
            name='tipo_sitio',
            field=models.CharField(
                choices=[('POSTE', 'Poste'), ('TORRE', 'Torre')],
                default='TORRE',
                editable=False,
                max_length=10,
                verbose_name='Tipo de sitio',
            ),
            preserve_default=False,
        ),
    ]
