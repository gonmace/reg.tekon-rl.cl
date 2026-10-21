"""Configuración efectiva de correo: `.env` por defecto, o la personalizada guardada en base.

`get_email_config()` devuelve siempre el mismo formato (dict) para quien envía (backend) y para la
pantalla de configuración. La contraseña viaja en el dict: no lo muestres ni lo loguees.
"""
from django.conf import settings


def config_env():
    """Lo que Django leyó del `.env` (EMAIL_*). Sin EMAIL_HOST el correo va a la consola."""
    return {
        'origen': 'env',
        'host': getattr(settings, 'EMAIL_HOST', '') or '',
        'port': int(getattr(settings, 'EMAIL_PORT', 587) or 587),
        'use_ssl': bool(getattr(settings, 'EMAIL_USE_SSL', False)),
        'use_tls': bool(getattr(settings, 'EMAIL_USE_TLS', False)),
        'usuario': getattr(settings, 'EMAIL_HOST_USER', '') or '',
        'password': getattr(settings, 'EMAIL_HOST_PASSWORD', '') or '',
        'remitente': settings.DEFAULT_FROM_EMAIL,
        'timeout': getattr(settings, 'EMAIL_TIMEOUT', None) or 20,
    }


def config_personalizada():
    """La fila guardada (o None si la tabla aún no existe)."""
    from core.models.correo import ConfiguracionCorreo
    try:
        return ConfiguracionCorreo.objects.filter(pk=1).first()
    except Exception:  # tabla inexistente (migrando) o base caída: se cae a .env
        return None


def get_email_config():
    personalizada = config_personalizada()
    if personalizada and personalizada.activa and personalizada.host.strip():
        return personalizada.como_config()
    return config_env()


def seguridad_de(cfg):
    return 'SSL/TLS' if cfg['use_ssl'] else ('STARTTLS' if cfg['use_tls'] else 'Sin cifrado')


def crear_backend(cfg, fail_silently=False, **kwargs):
    """Backend de Django para `cfg`: SMTP si hay servidor; si no, consola."""
    if cfg['host']:
        from django.core.mail.backends.smtp import EmailBackend
        return EmailBackend(
            host=cfg['host'], port=cfg['port'], username=cfg['usuario'], password=cfg['password'],
            use_tls=cfg['use_tls'], use_ssl=cfg['use_ssl'], timeout=cfg['timeout'],
            fail_silently=fail_silently, **kwargs)
    from django.core.mail.backends.console import EmailBackend
    return EmailBackend(fail_silently=fail_silently, **kwargs)
