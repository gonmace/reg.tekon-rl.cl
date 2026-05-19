from django.db import migrations


def rename_user_types(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(user_type='MANAGER').update(user_type='GERENCIA')
    User.objects.filter(user_type='CLIENT').update(user_type='VISITA')


def reverse_rename_user_types(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(user_type='GERENCIA').update(user_type='MANAGER')
    User.objects.filter(user_type='VISITA').update(user_type='CLIENT')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_update_user_types'),
    ]

    operations = [
        migrations.RunPython(rename_user_types, reverse_rename_user_types),
    ]
