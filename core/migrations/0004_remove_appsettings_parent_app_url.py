from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_appsettings_parent_app_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='appsettings',
            name='parent_app_url',
        ),
    ]
