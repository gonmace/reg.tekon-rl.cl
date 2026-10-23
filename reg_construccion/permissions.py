from functools import wraps

from django.core.exceptions import PermissionDenied

from core.permissions import can_access_registro, puede_escribir_registro, tiene_permiso


def puede_ver(user, registro):
    """Alcance sobre la visita (ver `core.permissions.can_access_registro`)."""
    return can_access_registro(user, registro)


def puede_gestionar(user, registro):
    """Editar cabecera / crear nueva visita: permiso `cargar_datos` dentro del alcance."""
    return puede_escribir_registro(user, registro)


def puede_cambiar_ito(user, registro=None):
    """Reasignar la visita a otro ITO/Buscador: permiso `cambiar_responsable` (y alcance, si se indica la visita)."""
    return tiene_permiso(user, 'cambiar_responsable') and (registro is None or can_access_registro(user, registro))



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
