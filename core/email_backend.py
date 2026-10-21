"""Backend de correo de Django que resuelve la configuración al enviar (`.env` o personalizada)."""
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

from core.email_config import crear_backend, get_email_config


class ConfigurableEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.config = get_email_config()
        timeout = kwargs.pop('timeout', None)
        if timeout:
            self.config = {**self.config, 'timeout': timeout}
        self.delegate = crear_backend(self.config, fail_silently=fail_silently)

    def open(self):
        return self.delegate.open()

    def close(self):
        return self.delegate.close()

    def send_messages(self, email_messages):
        # Los correos que usan el remitente por defecto salen con el de la configuración activa
        for mensaje in email_messages:
            if mensaje.from_email == settings.DEFAULT_FROM_EMAIL:
                mensaje.from_email = self.config['remitente']
        return self.delegate.send_messages(email_messages)
