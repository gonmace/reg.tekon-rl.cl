from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0007_campo_to_widget'),
    ]

    operations = [
        migrations.AddField(
            model_name='campoformulario',
            name='ancho',
            field=models.CharField(
                choices=[
                    ('full', 'Ancho completo'),
                    ('half', 'Mitad (½)'),
                    ('third', 'Un tercio (⅓)'),
                    ('two_thirds', 'Dos tercios (⅔)'),
                ],
                default='full',
                max_length=10,
                verbose_name='Ancho',
            ),
        ),
    ]
