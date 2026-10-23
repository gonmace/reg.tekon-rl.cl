def can_hijack(*, hijacker, hijacked):
    """Solo is_superuser de Django puede impersonar, y nunca a otro superuser."""
    return bool(
        hijacker.is_superuser
        and not hijacked.is_superuser
        and hijacked.is_active
        and not hijacked.is_deleted
    )


def roles_asignables(actor):
    """Tipos de usuario que `actor` puede crear o asignar desde Usuarios."""
    from .models import User
    if actor.is_supermanager or actor.is_admin_global:
        return [User.ADMINISTRADOR, User.ITO, User.SEARCHER, User.VISITA]
    return [User.ITO, User.SEARCHER, User.VISITA]


def validar_rol_empresa(actor, user_type, contractor):
    """Mensaje de error si `actor` no puede dejar a un usuario con ese tipo y empresa; None si sí."""
    from .models import User
    if user_type not in roles_asignables(actor):
        return 'No puedes asignar ese tipo de usuario'
    if not (actor.is_supermanager or actor.is_admin_global) and contractor != actor.contractor:
        return 'Solo puedes asignar usuarios a tu empresa'
    if user_type != User.ADMINISTRADOR and contractor is None:
        return 'Este tipo de usuario debe pertenecer a una empresa'
    if actor.is_admin_global and user_type == User.ADMINISTRADOR and contractor is None:
        return 'Solo el superusuario puede crear administradores globales (sin empresa)'
    return None


def matriz_permisos():
    """Filas de la matriz de permisos por rol, agrupadas, con el valor vigente y el de por defecto."""
    from core.permisos_catalogo import ACCIONES, ROLES_CONFIGURABLES, por_defecto
    from core.permissions import permiso_de_rol
    grupos = {}
    for key, accion in ACCIONES.items():
        celdas = [
            {'rol': rol, 'permitido': permiso_de_rol(rol, key), 'defecto': por_defecto(rol, key)}
            for rol in ROLES_CONFIGURABLES
        ]
        grupos.setdefault(accion.grupo, []).append({'key': key, 'label': accion.label, 'celdas': celdas})
    return [{'nombre': nombre, 'filas': filas} for nombre, filas in grupos.items()]


def excepciones_de_usuario(user):
    """Acciones con el estado de la excepción de `user` ('inherit', 'allow' o 'deny') y lo que hereda del rol."""
    from core.permisos_catalogo import ACCIONES
    from core.permissions import permiso_de_rol
    guardadas = {p.accion: p.permitido for p in user.permisos_extra.all()}
    return [
        {
            'key': key, 'label': accion.label, 'grupo': accion.grupo,
            'estado': 'inherit' if key not in guardadas else ('allow' if guardadas[key] else 'deny'),
            'hereda': permiso_de_rol(user.user_type, key),
        }
        for key, accion in ACCIONES.items()
    ]
