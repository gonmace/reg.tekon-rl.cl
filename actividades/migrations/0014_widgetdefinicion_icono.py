from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0013_alter_configwidget_paso'),
    ]

    operations = [
        migrations.AddField(
            model_name='widgetdefinicion',
            name='icono',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Clase FontAwesome (ej. fas fa-wifi) o SVG inline',
                max_length=500,
                verbose_name='Icono',
            ),
        ),
    ]
