import os
from django.db import migrations


def backfill_file_size(apps, schema_editor):
    Photos = apps.get_model('photos', 'Photos')
    for photo in Photos.objects.filter(file_size__isnull=True):
        try:
            path = photo.imagen.path
            if os.path.exists(path):
                Photos.objects.filter(pk=photo.pk).update(
                    file_size=os.path.getsize(path)
                )
        except Exception:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('photos', '0003_photos_file_size'),
    ]

    operations = [
        migrations.RunPython(backfill_file_size, migrations.RunPython.noop),
    ]
