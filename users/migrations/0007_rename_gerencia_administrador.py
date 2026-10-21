from django.db import migrations, models


def gerencia_a_administrador(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(user_type='GERENCIA').update(user_type='ADMINISTRADOR')


def administrador_a_gerencia(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(user_type='ADMINISTRADOR').update(user_type='GERENCIA')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_add_report_access'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(blank=True, choices=[('ADMINISTRADOR', 'Administrador'), ('COORD', 'Coordinador'), ('ITO', 'ITO'), ('SEARCHER', 'Buscador'), ('VISITA', 'Visita')], default='ITO', max_length=50, verbose_name='Tipo de Usuario'),
        ),
        migrations.RunPython(gerencia_a_administrador, administrador_a_gerencia),
    ]
