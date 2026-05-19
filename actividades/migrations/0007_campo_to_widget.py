import django.db.models.deletion
from django.db import migrations, models


def _migrate_forward(apps, schema_editor):
    PasoActividad = apps.get_model('actividades', 'PasoActividad')
    WidgetDefinicion = apps.get_model('actividades', 'WidgetDefinicion')
    ConfigWidget = apps.get_model('actividades', 'ConfigWidget')
    CampoFormulario = apps.get_model('actividades', 'CampoFormulario')

    for paso in PasoActividad.objects.order_by('id'):
        campos = list(CampoFormulario.objects.filter(paso=paso).order_by('orden'))
        if not campos:
            continue
        wd = WidgetDefinicion.objects.create(
            nombre=paso.titulo or paso.nombre,
            tipo='FORM',
            descripcion='',
            params={},
        )
        for campo in campos:
            campo.widgetdef = wd
            campo.save()
        # Shift existing widgets to make room at orden=0
        for cw in ConfigWidget.objects.filter(paso=paso).order_by('-orden'):
            cw.orden = cw.orden + 1
            cw.save()
        ConfigWidget.objects.create(paso=paso, widgetdef=wd, orden=0)


def _migrate_backward(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0006_widgetdefinicion'),
    ]

    operations = [
        # 1. Add nullable widgetdef FK
        migrations.AddField(
            model_name='campoformulario',
            name='widgetdef',
            field=models.ForeignKey(
                'actividades.WidgetDefinicion',
                null=True, blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='campos',
                verbose_name='Widget',
            ),
        ),
        # 2. Data migration
        migrations.RunPython(_migrate_forward, _migrate_backward),
        # 3. Make non-nullable
        migrations.AlterField(
            model_name='campoformulario',
            name='widgetdef',
            field=models.ForeignKey(
                'actividades.WidgetDefinicion',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='campos',
                verbose_name='Widget',
            ),
        ),
        # 4. Drop old unique_together (references paso)
        migrations.AlterUniqueTogether(
            name='campoformulario',
            unique_together=set(),
        ),
        # 5. Remove paso FK
        migrations.RemoveField(
            model_name='campoformulario',
            name='paso',
        ),
        # 6. Add new unique_together
        migrations.AlterUniqueTogether(
            name='campoformulario',
            unique_together={('widgetdef', 'nombre')},
        ),
    ]
