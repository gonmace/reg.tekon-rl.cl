from django.core.management.base import BaseCommand
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from users.models import User


class Command(BaseCommand):
    help = 'Envía a cada usuario activo un email con enlace de reset de contraseña'

    def handle(self, *args, **opts):
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        sent = 0
        skipped = 0

        usuarios = User.objects.filter(is_active=True).exclude(email='')
        self.stdout.write(f'Procesando {usuarios.count()} usuarios con email...')

        for user in usuarios:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = site_url + reverse(
                'users:password_reset_confirm',
                kwargs={'uidb64': uid, 'token': token}
            )
            subject = 'Establece tu contraseña — Reportes Tekon'
            body = (
                f'Hola {user.get_full_name() or user.username},\n\n'
                f'El sistema Reportes Tekon ha migrado su autenticación. '
                f'Para poder iniciar sesión necesitas establecer una contraseña local.\n\n'
                f'Usa este enlace (válido por 24 horas):\n{link}\n\n'
                f'Si tienes dudas, contacta al administrador.\n\n'
                f'— Reportes Tekon'
            )
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email])
                self.stdout.write(f'  ✓ {user.username} <{user.email}>')
                sent += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ✗ {user.username}: {e}'))
                skipped += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nEnviados: {sent}  |  Con error: {skipped}'
        ))
        if skipped:
            self.stdout.write(
                'Para usuarios sin email usa: python manage.py changepassword <username>'
            )
