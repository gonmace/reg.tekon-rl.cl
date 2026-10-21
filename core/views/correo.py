"""Configuración de correo (solo superusuario).

Por defecto se usa lo que Django lee del `.env` (EMAIL_*). Opcionalmente se guarda una configuración
personalizada en base (`ConfiguracionCorreo`) para cambiar de cuenta sin editar el `.env`; mientras
esté activa tiene prioridad (ver `core.email_config.get_email_config`). Las pruebas usan lo que haya
en el formulario, aunque no se haya guardado.
"""
import json
import logging
import re
from email.utils import parseaddr

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from core.email_config import (
    config_env, config_personalizada, crear_backend, get_email_config, seguridad_de,
)
from core.models.correo import ConfiguracionCorreo
from core.permissions import SuperuserRequiredMixin

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
HOST_RE = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$')


def resumen(cfg):
    """Datos de `cfg` para mostrar en pantalla (sin la contraseña)."""
    return {
        'origen': cfg['origen'],
        'modo': 'smtp' if cfg['host'] else 'consola',
        'host': cfg['host'], 'port': cfg['port'], 'seguridad': seguridad_de(cfg),
        'usuario': cfg['usuario'], 'password_definida': bool(cfg['password']),
        'remitente': cfg['remitente'], 'timeout': cfg['timeout'],
    }


def _payload(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except ValueError:
        return {}


def cfg_desde_payload(data, guardada):
    """Config a probar/guardar según el formulario. Lanza ValueError con el mensaje si es inválida.

    `guardada` es la fila de base (o None): si la contraseña viene vacía se usa la guardada (solo con el mismo servidor y usuario).
    """
    if data.get('origen') != 'personalizada':
        return config_env()
    host = str(data.get('host', '')).strip()
    if not host or not HOST_RE.match(host):
        raise ValueError('Ingresa un servidor SMTP válido (ej: mail.tu-dominio.cl)')
    try:
        port = int(data.get('port'))
        if not 1 <= port <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError('El puerto debe ser un número entre 1 y 65535')
    seguridad = data.get('seguridad', 'ssl')
    if seguridad not in ('ssl', 'tls', 'none'):
        raise ValueError('Seguridad inválida')
    usuario = str(data.get('usuario', '')).strip()
    password = data.get('password') or ''
    if not password and guardada and guardada.host.lower() == host.lower() and guardada.usuario == usuario:
        password = guardada.password  # misma cuenta: nunca se reenvía la guardada a otro servidor o usuario
    if usuario and not password:
        raise ValueError('Falta la contraseña del usuario SMTP (al cambiar de servidor o usuario hay que ingresarla de nuevo)')
    remitente = str(data.get('remitente', '')).strip() or usuario
    if not EMAIL_RE.match(parseaddr(remitente)[1] or ''):
        raise ValueError('Ingresa un remitente válido (ej: Reportes Tekon <reportes@tu-dominio.cl>)')
    return {
        'origen': 'personalizada', 'host': host, 'port': port,
        'use_ssl': seguridad == 'ssl', 'use_tls': seguridad == 'tls',
        'usuario': usuario, 'password': password, 'remitente': remitente,
        'timeout': getattr(settings, 'EMAIL_TIMEOUT', None) or 20,
    }


def _error(e, cfg):
    """Texto del error sin filtrar la contraseña."""
    detalle = str(e)
    if cfg.get('password'):
        detalle = detalle.replace(cfg['password'], '***')
    return f'{type(e).__name__}: {detalle[:200]}'


def conectar(cfg):
    """Abre conexión y autentica (sin enviar nada). Lanza la excepción del servidor si falla."""
    backend = crear_backend(cfg)
    backend.open()
    backend.close()


class SoloSuperusuarioPagina(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_supermanager:
            messages.error(request, 'Sin permisos suficientes.')
            return redirect('dashboard:dashboard')
        return super().dispatch(request, *args, **kwargs)


class CorreoConfigView(SoloSuperusuarioPagina, TemplateView):
    template_name = 'pages/correo_config.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activa = resumen(get_email_config())
        guardada = config_personalizada() or ConfiguracionCorreo()
        site_url = settings.SITE_URL
        context.update({
            'header_title': 'Configuración de correo',
            'activa': activa,
            'env': resumen(config_env()),
            'pers': guardada,
            'pers_password_guardada': bool(guardada.password),
            'usa_personalizada': activa['origen'] == 'personalizada',
            'site_url': site_url,
            'site_url_local': any(h in site_url for h in ('localhost', '127.0.0.1')),
            'correo_prueba': self.request.user.email or '',
        })
        return context


class _ApiCorreo(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Base de los endpoints JSON: solo superusuario."""

    def cfg(self, request):
        data = _payload(request)
        return data, cfg_desde_payload(data, config_personalizada())


class CorreoGuardarView(_ApiCorreo):
    """Elige el origen (.env o personalizada) y guarda la personalizada. No activa una config que no conecta."""

    def post(self, request):
        data = _payload(request)
        fila = ConfiguracionCorreo.get_solo()
        fila.updated_by = request.user
        if data.get('origen') != 'personalizada':
            fila.activa = False
            fila.save()
            return JsonResponse({'success': True, 'message': 'Ahora se usa la configuración del .env'})
        try:
            cfg = cfg_desde_payload(data, fila)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        fila.host, fila.port = cfg['host'], cfg['port']
        fila.seguridad = 'ssl' if cfg['use_ssl'] else ('tls' if cfg['use_tls'] else 'none')
        fila.usuario, fila.password, fila.remitente = cfg['usuario'], cfg['password'], cfg['remitente']
        try:
            conectar(cfg)
        except Exception as e:
            logger.warning('Configuración de correo no activada: %s', _error(e, cfg))
            fila.activa = False
            fila.save()
            return JsonResponse({
                'success': False,
                'message': f'Se guardó, pero NO se activó porque no se pudo conectar: {_error(e, cfg)}',
            }, status=400)
        fila.activa = True
        fila.save()
        return JsonResponse({'success': True, 'message': 'Configuración guardada y activa'})


class CorreoConexionView(_ApiCorreo):
    """Prueba de conexión y autenticación SMTP, sin enviar ningún correo."""

    def post(self, request):
        try:
            data, cfg = self.cfg(request)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        if not cfg['host']:
            return JsonResponse({'success': True, 'message': 'Modo consola: no hay servidor SMTP que probar. Define EMAIL_HOST en .env o usa una configuración personalizada.'})
        try:
            conectar(cfg)
        except Exception as e:
            logger.warning('Falló la prueba de conexión SMTP: %s', _error(e, cfg))
            return JsonResponse({'success': False, 'message': f'No se pudo conectar: {_error(e, cfg)}'}, status=502)
        return JsonResponse({'success': True, 'message': f'Conexión y autenticación correctas con {cfg["host"]}:{cfg["port"]}'})


class CorreoProbarView(_ApiCorreo):
    """POST {to, ...config}: envía un correo de prueba con la configuración del formulario."""

    def post(self, request):
        try:
            data, cfg = self.cfg(request)
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        destino = str(data.get('to', '')).strip()
        if not EMAIL_RE.match(destino):
            return JsonResponse({'success': False, 'message': 'Ingresa un correo de destino válido'}, status=400)
        cuerpo = (
            'Este es un correo de prueba de Reportes Tekon.\n\n'
            f'Enviado por: {request.user.display_name}\n'
            f'Fecha: {timezone.localtime():%d/%m/%Y %H:%M:%S}\n'
            f'Configuración: {"personalizada" if cfg["origen"] == "personalizada" else ".env"} · '
            f'{cfg["host"] or "(consola)"}:{cfg["port"]} · {seguridad_de(cfg)}\n\n'
            'Si lo recibiste, la configuración de correo funciona. Puedes ignorar este mensaje.'
        )
        try:
            enviados = EmailMessage('Prueba de correo — Reportes Tekon', cuerpo, cfg['remitente'], [destino],
                                    connection=crear_backend(cfg)).send()
        except Exception as e:
            logger.exception('Falló el correo de prueba a %s', destino)
            return JsonResponse({'success': False, 'message': f'No se pudo enviar: {_error(e, cfg)}'}, status=502)
        if not enviados:
            return JsonResponse({'success': False, 'message': 'El servidor no aceptó el correo'}, status=502)
        if not cfg['host']:
            return JsonResponse({'success': True, 'message': 'Modo consola: el correo se imprimió en la terminal del servidor, no se envió de verdad.'})
        return JsonResponse({'success': True, 'message': f'Correo de prueba enviado a {destino}'})
