from functools import wraps

from django.core.exceptions import PermissionDenied

from core.permissions import can_access_registro


def mismo_contratista(user, registro):
    return bool(registro.user and user.contractor_id and registro.user.contractor_id == user.contractor_id)


def puede_ver(user, registro):
    """Dueño, supermanager, visita, administrador y coordinación del contratista de la visita."""
    if can_access_registro(user, registro) or user.is_administrador:
        return True
    return bool(user.is_coord and mismo_contratista(user, registro))


def puede_gestionar(user, registro):
    """Editar cabecera / crear nueva visita: superusuario, coordinación del contratista o el ITO dueño."""
    if user.is_visita or user.is_administrador:
        return False
    if user.is_supermanager:
        return True
    if user.is_coord:
        return mismo_contratista(user, registro)
    return registro.user_id == user.id


def puede_cambiar_ito(user):
    """Reasignar la visita a otro ITO/Buscador: superusuario y ADMINISTRADOR."""
    return user.is_supermanager or user.is_administrador



MENSAJE_POSTERIOR_CONCLUIDA = (
    'Hay una visita posterior de este sitio ya concluida: reábrela para modificar el avance, '
    'la fecha o eliminar esta visita (el avance acumulado de la posterior cambiaría).'
)


def hay_posterior_concluida(registro, fecha=None):
    """¿El sitio tiene una visita concluida con fecha posterior a `fecha` (por defecto, la del registro)?

    El % anterior/acumulado de una visita depende de las anteriores, así que tocar una visita
    antigua alteraría los datos de una posterior ya cerrada.
    """
    from .models import RegConstruccion
    return RegConstruccion.objects.filter(
        sitio_id=registro.sitio_id, is_deleted=False, concluido=True,
        fecha__gt=fecha or registro.fecha,
    ).exists()


def requiere_acceso_reporte(view):
    """Envuelve una vista: los usuarios con `report_access` sin «construccion» reciben 403 (no solo se oculta el menú)."""
    @wraps(view)
    def envuelta(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not user.has_report_access('construccion'):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return envuelta
