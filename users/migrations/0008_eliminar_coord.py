from django.db import migrations, models


def coord_a_administrador(apps, schema_editor):
    """Los ADMINISTRADOR actuales pasan a globales (sin empresa); los COORD pasan a
    ADMINISTRADOR de su empresa; el superusuario (sin rol) no tiene empresa."""
    User = apps.get_model('users', 'User')
    User.objects.filter(user_type='ADMINISTRADOR').update(contractor=None)
    User.objects.filter(user_type='COORD').update(user_type='ADMINISTRADOR')
    User.objects.filter(user_type='').update(contractor=None)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_rename_gerencia_administrador'),
    ]

    operations = [
        migrations.RunPython(coord_a_administrador, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(blank=True, choices=[('ADMINISTRADOR', 'Administrador'), ('ITO', 'ITO'), ('SEARCHER', 'Buscador'), ('VISITA', 'Visita')], default='ITO', max_length=50, verbose_name='Tipo de Usuario'),
        ),
    ]
