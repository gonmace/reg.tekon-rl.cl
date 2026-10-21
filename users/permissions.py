def can_hijack(*, hijacker, hijacked):
    """Solo is_superuser de Django puede impersonar, y nunca a otro superuser."""
    return bool(
        hijacker.is_superuser
        and not hijacked.is_superuser
        and hijacked.is_active
        and not hijacked.is_deleted
    )


def puede_editar_usuario(actor, target):
    """Quién puede modificar/eliminar a `target` desde Usuarios.

    Superusuario/supermanager: a cualquiera, salvo superusers (solo otro superuser).
    COORD: solo ITO/Buscador de su propia empresa, nunca superusers.
    """
    if not actor or not actor.is_authenticated or target.is_superuser and not actor.is_superuser:
        return False
    if actor.is_supermanager:
        return True
    if actor.is_coord:
        return (
            target.user_type in type(target).ITO_LIKE_ROLES
            and actor.contractor_id is not None
            and target.contractor_id == actor.contractor_id
        )
    return False
