from django.db import migrations, models
import django.db.models.deletion


def migrate_pasos_forward(apps, schema_editor):
    PasoActividad = apps.get_model('actividades', 'PasoActividad')
    PasoDefinicion = apps.get_model('actividades', 'PasoDefinicion')
    ConfigPaso = apps.get_model('actividades', 'ConfigPaso')
    ConfigWidget = apps.get_model('actividades', 'ConfigWidget')

    paso_map = {}  # PasoActividad.id → PasoDefinicion.id

    for paso in PasoActividad.objects.order_by('tipo_id', 'orden'):
        nombre = paso.nombre
        suffix = 1
        orig = nombre
        while PasoDefinicion.objects.filter(nombre=nombre).exists():
            nombre = f"{orig}-{suffix}"
            suffix += 1
        pasodef = PasoDefinicion.objects.create(
            nombre=nombre,
            titulo=paso.titulo,
            descripcion=paso.descripcion or '',
        )
        ConfigPaso.objects.create(
            tipo_id=paso.tipo_id,
            pasodef=pasodef,
            orden=paso.orden,
        )
        paso_map[paso.id] = pasodef.id

    for cw in ConfigWidget.objects.all():
        if cw.paso_id in paso_map:
            cw.paso_new_id = paso_map[cw.paso_id]
            cw.save(update_fields=['paso_new_id'])


def migrate_pasos_reverse(apps, schema_editor):
    pass  # irreversible


class Migration(migrations.Migration):

    dependencies = [
        ('actividades', '0011_campo_text_btn'),
    ]

    operations = [
        # 1. Create PasoDefinicion table
        migrations.CreateModel(
            name='PasoDefinicion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.SlugField(unique=True, verbose_name='Nombre (slug)')),
                ('titulo', models.CharField(max_length=100, verbose_name='Título')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
            ],
            options={
                'verbose_name': 'Paso',
                'verbose_name_plural': 'Pasos',
                'ordering': ['titulo'],
            },
        ),
        # 2. Create ConfigPaso table
        migrations.CreateModel(
            name='ConfigPaso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveIntegerField(default=0, verbose_name='Orden')),
                ('tipo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='config_pasos',
                    to='actividades.tipoactividad',
                )),
                ('pasodef', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='asignaciones',
                    to='actividades.pasodefinicion',
                )),
            ],
            options={
                'verbose_name': 'Paso asignado',
                'verbose_name_plural': 'Pasos asignados',
                'ordering': ['orden'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='configpaso',
            unique_together={('tipo', 'pasodef')},
        ),
        # 3. Add temporary nullable FK on ConfigWidget pointing to PasoDefinicion
        migrations.AddField(
            model_name='configwidget',
            name='paso_new',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='widgets_new',
                to='actividades.pasodefinicion',
            ),
        ),
        # 4. Data migration
        migrations.RunPython(migrate_pasos_forward, migrate_pasos_reverse),
        # 5. Make paso_new non-null
        migrations.AlterField(
            model_name='configwidget',
            name='paso_new',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='widgets_new',
                to='actividades.pasodefinicion',
            ),
        ),
        # 6. Remove old ConfigWidget.paso FK (to PasoActividad)
        migrations.RemoveField(
            model_name='configwidget',
            name='paso',
        ),
        # 7. Rename paso_new → paso
        migrations.RenameField(
            model_name='configwidget',
            old_name='paso_new',
            new_name='paso',
        ),
        # 8. Delete PasoActividad model
        migrations.DeleteModel(
            name='PasoActividad',
        ),
    ]
