from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_appsettings_parent_app_url'),
    ]

    operations = [
        # Renombrar lat_base -> lat, lon_base -> lon (preserva datos existentes)
        migrations.RenameField(
            model_name='site',
            old_name='lat_base',
            new_name='lat',
        ),
        migrations.RenameField(
            model_name='site',
            old_name='lon_base',
            new_name='lon',
        ),
        migrations.RenameField(
            model_name='historicalsite',
            old_name='lat_base',
            new_name='lat',
        ),
        migrations.RenameField(
            model_name='historicalsite',
            old_name='lon_base',
            new_name='lon',
        ),
        # Actualizar verbose_name
        migrations.AlterField(
            model_name='site',
            name='lat',
            field=models.FloatField(blank=True, null=True, unique=True, verbose_name='Latitud'),
        ),
        migrations.AlterField(
            model_name='site',
            name='lon',
            field=models.FloatField(blank=True, null=True, unique=True, verbose_name='Longitud'),
        ),
        migrations.AlterField(
            model_name='historicalsite',
            name='lat',
            field=models.FloatField(blank=True, db_index=True, null=True, verbose_name='Latitud'),
        ),
        migrations.AlterField(
            model_name='historicalsite',
            name='lon',
            field=models.FloatField(blank=True, db_index=True, null=True, verbose_name='Longitud'),
        ),
        # Nuevo campo tipo_coordenada (default MANDATO para datos existentes)
        migrations.AddField(
            model_name='site',
            name='tipo_coordenada',
            field=models.CharField(
                choices=[('MANDATO', 'Mandato'), ('INGENIERIA', 'Ingeniería'), ('CONSTRUCCION', 'Construcción')],
                default='MANDATO',
                max_length=20,
                verbose_name='Tipo de coordenada',
            ),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='tipo_coordenada',
            field=models.CharField(
                choices=[('MANDATO', 'Mandato'), ('INGENIERIA', 'Ingeniería'), ('CONSTRUCCION', 'Construcción')],
                default='MANDATO',
                max_length=20,
                verbose_name='Tipo de coordenada',
            ),
        ),
    ]
