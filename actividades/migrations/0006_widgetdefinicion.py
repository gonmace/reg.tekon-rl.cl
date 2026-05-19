import django.db.models.deletion
from django.db import migrations, models


def _migrate_forward(apps, schema_editor):
    ConfigWidget = apps.get_model('actividades', 'ConfigWidget')
    WidgetDefinicion = apps.get_model('actividades', 'WidgetDefinicion')

    TIPO_NOMBRES = {
        'FORM':   'Formulario',
        'CAMERA': 'Cámara / fotos',
        'MAP_1':  'Mapa 1 punto',
        'MAP_2':  'Mapa 2 puntos',
        'MAP_3':  'Mapa 3 puntos',
    }

    for cw in ConfigWidget.objects.order_by('id'):
        nombre = TIPO_NOMBRES.get(cw.tipo, cw.tipo)
        wd = WidgetDefinicion.objects.create(
            nombre=nombre,
            tipo=cw.tipo,
            params=cw.params or {},
        )
        cw.widgetdef = wd
        cw.save()


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0005_remove_filawidgets'),
    ]

    operations = [
        # 1. Crear WidgetDefinicion
        migrations.CreateModel(
            name='WidgetDefinicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre')),
                ('tipo', models.CharField(
                    choices=[('FORM', 'Formulario'), ('MAP_1', 'Mapa 1 punto'),
                             ('MAP_2', 'Mapa 2 puntos'), ('MAP_3', 'Mapa 3 puntos'),
                             ('CAMERA', 'Cámara / fotos')],
                    max_length=20, verbose_name='Tipo')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('params', models.JSONField(blank=True, default=dict, verbose_name='Parámetros')),
            ],
            options={
                'verbose_name': 'Widget',
                'verbose_name_plural': 'Widgets',
                'ordering': ['tipo', 'nombre'],
            },
        ),
        # 2. Agregar widgetdef FK (nullable temporalmente)
        migrations.AddField(
            model_name='configwidget',
            name='widgetdef',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='asignaciones',
                to='actividades.widgetdefinicion',
                verbose_name='Widget',
            ),
        ),
        # 3. Migrar datos existentes
        migrations.RunPython(
            code=_migrate_forward,
            reverse_code=migrations.RunPython.noop,
        ),
        # 4. Hacer widgetdef no-nullable
        migrations.AlterField(
            model_name='configwidget',
            name='widgetdef',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='asignaciones',
                to='actividades.widgetdefinicion',
                verbose_name='Widget',
            ),
        ),
        # 5. Eliminar tipo y params de ConfigWidget
        migrations.RemoveField(model_name='configwidget', name='tipo'),
        migrations.RemoveField(model_name='configwidget', name='params'),
        # 6. Actualizar meta
        migrations.AlterModelOptions(
            name='configwidget',
            options={
                'verbose_name': 'Widget asignado',
                'verbose_name_plural': 'Widgets asignados',
                'ordering': ['orden'],
            },
        ),
    ]
