from django.db import migrations, models


def copy_lat_lon_to_per_type(apps, schema_editor):
    """Copia el lat/lon viejo al campo correspondiente según tipo_coordenada."""
    Site = apps.get_model('core', 'Site')
    for site in Site.objects.all():
        lat = site.lat
        lon = site.lon
        tipo = site.tipo_coordenada or 'MANDATO'
        if tipo == 'MANDATO':
            site.lat_man, site.lon_man = lat, lon
        elif tipo == 'INGENIERIA':
            site.lat_ing, site.lon_ing = lat, lon
        elif tipo == 'CONSTRUCCION':
            site.lat_con, site.lon_con = lat, lon
        site.save()


def reverse_copy(apps, schema_editor):
    Site = apps.get_model('core', 'Site')
    for site in Site.objects.all():
        # En el rollback, preferir mandato; si no, ing; si no, con.
        if site.lat_man is not None:
            site.lat, site.lon, site.tipo_coordenada = site.lat_man, site.lon_man, 'MANDATO'
        elif site.lat_ing is not None:
            site.lat, site.lon, site.tipo_coordenada = site.lat_ing, site.lon_ing, 'INGENIERIA'
        elif site.lat_con is not None:
            site.lat, site.lon, site.tipo_coordenada = site.lat_con, site.lon_con, 'CONSTRUCCION'
        site.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_rename_lat_lon_add_tipo_coordenada'),
    ]

    operations = [
        # 1) Agregar los nuevos campos (nullable) en Site e HistoricalSite
        migrations.AddField(
            model_name='site',
            name='lat_man',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Mandato'),
        ),
        migrations.AddField(
            model_name='site',
            name='lon_man',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Mandato'),
        ),
        migrations.AddField(
            model_name='site',
            name='lat_ing',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Ingeniería'),
        ),
        migrations.AddField(
            model_name='site',
            name='lon_ing',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Ingeniería'),
        ),
        migrations.AddField(
            model_name='site',
            name='lat_con',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Construcción'),
        ),
        migrations.AddField(
            model_name='site',
            name='lon_con',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Construcción'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lat_man',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Mandato'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lon_man',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Mandato'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lat_ing',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Ingeniería'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lon_ing',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Ingeniería'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lat_con',
            field=models.FloatField(blank=True, null=True, verbose_name='Latitud Construcción'),
        ),
        migrations.AddField(
            model_name='historicalsite',
            name='lon_con',
            field=models.FloatField(blank=True, null=True, verbose_name='Longitud Construcción'),
        ),

        # 2) Copiar los datos viejos al campo según tipo_coordenada
        migrations.RunPython(copy_lat_lon_to_per_type, reverse_code=reverse_copy),

        # 3) Borrar los campos viejos
        migrations.RemoveField(model_name='site', name='lat'),
        migrations.RemoveField(model_name='site', name='lon'),
        migrations.RemoveField(model_name='site', name='tipo_coordenada'),
        migrations.RemoveField(model_name='historicalsite', name='lat'),
        migrations.RemoveField(model_name='historicalsite', name='lon'),
        migrations.RemoveField(model_name='historicalsite', name='tipo_coordenada'),
    ]
