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

