"""
Crea el superusuario inicial si no existe ninguno.

Lee las credenciales desde variables de entorno:
  DJANGO_SUPERUSER_USERNAME  (default: admin)
  DJANGO_SUPERUSER_EMAIL     (default: admin@example.com)
  DJANGO_SUPERUSER_PASSWORD  (obligatorio)

Uso: python manage.py create_default_superuser
"""

import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea el superusuario inicial leyendo credenciales desde variables de entorno'

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.WARNING('Ya existe un superusuario — omitiendo creación.'))
            return

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')

        if not password:
            raise CommandError(
                'DJANGO_SUPERUSER_PASSWORD no está definido. '
                'Define la variable de entorno antes de ejecutar este comando.'
            )

        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado correctamente.'))
        except Exception as e:
            raise CommandError(f'Error al crear superusuario: {e}')
