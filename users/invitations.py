"""Invitación por correo: el usuario recibe un enlace para crear su contraseña e iniciar sesión.

Reutiliza el flujo de «restablecer contraseña» (token firmado con la contraseña actual, caduca según
`PASSWORD_RESET_TIMEOUT`): el enlace apunta a `users:password_reset_confirm`.
"""
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def enlace_de_invitacion(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    ruta = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    return f"{settings.SITE_URL.rstrip('/')}{ruta}"


def enviar_invitacion(user, invitador=None):
    """Envía el correo de invitación. Lanza la excepción del backend si el envío falla."""
    contexto = {
        'user': user,
        'invitador': invitador,
        'enlace': enlace_de_invitacion(user),
        'dias_validez': max(1, settings.PASSWORD_RESET_TIMEOUT // 86400),
    }
    asunto = ''.join(render_to_string('users/invitation_subject.txt', contexto).splitlines())
    cuerpo = render_to_string('users/invitation_email.txt', contexto)
    send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [user.email or user.username], fail_silently=False)
