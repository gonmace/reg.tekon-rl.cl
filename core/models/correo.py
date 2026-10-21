from django.conf import settings
from django.db import models


class ConfiguracionCorreo(models.Model):
    """Configuración SMTP alternativa a la del `.env` (una sola fila, pk=1).

    Si `activa` y tiene `host`, el envío de correos la usa en lugar de `.env`; si no, rige `.env`.
    OJO: la contraseña se guarda en texto plano (decisión del proyecto): nunca se muestra en pantalla,
    pero quien tenga acceso a la base o a un respaldo puede leerla.
    """
    SEGURIDAD_CHOICES = [('ssl', 'SSL/TLS'), ('tls', 'STARTTLS'), ('none', 'Sin cifrado')]

    activa = models.BooleanField('Usar esta configuración en vez de .env', default=False)
    host = models.CharField('Servidor SMTP', max_length=255, blank=True)
    port = models.PositiveIntegerField('Puerto', default=465)
    seguridad = models.CharField('Seguridad', max_length=4, choices=SEGURIDAD_CHOICES, default='ssl')
    usuario = models.CharField('Usuario', max_length=255, blank=True)
    password = models.CharField('Contraseña', max_length=255, blank=True)
    remitente = models.CharField('Remitente', max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='+')

    class Meta:
        verbose_name = 'Configuración de correo'
        verbose_name_plural = 'Configuración de correo'

    def __str__(self):
        return f'Correo personalizado ({"activa" if self.activa else "inactiva"})'

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def como_config(self):
        return {
            'origen': 'personalizada', 'host': self.host.strip(), 'port': self.port,
            'use_ssl': self.seguridad == 'ssl', 'use_tls': self.seguridad == 'tls',
            'usuario': self.usuario.strip(), 'password': self.password,
            'remitente': self.remitente.strip() or self.usuario.strip() or settings.DEFAULT_FROM_EMAIL,
            'timeout': getattr(settings, 'EMAIL_TIMEOUT', None) or 20,
        }
