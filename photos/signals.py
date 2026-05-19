from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Photos


def _get_registro(instance):
    """Navega del objeto genérico del GenericFK hasta el registro principal."""
    try:
        obj = instance.content_type.get_object_for_this_type(pk=instance.object_id)
        # Registro principal (RegTxtss u otro con TipoActividad)
        if hasattr(obj, 'sitio') or hasattr(obj, 'get_reg_app_name'):
            return obj
        # Modelo legacy de paso (RSitio, REmpalme, etc.) → subir al registro padre
        if hasattr(obj, 'registro'):
            return obj.registro
    except Exception:
        pass
    return None


def _rebuild(instance):
    registro = _get_registro(instance)
    if registro:
        try:
            from actividades.context_builder import rebuild_contexto
            rebuild_contexto(registro)
        except Exception:
            pass


@receiver(post_save, sender=Photos)
def photos_post_save(sender, instance, **kwargs):
    _rebuild(instance)


@receiver(post_delete, sender=Photos)
def photos_post_delete(sender, instance, **kwargs):
    _rebuild(instance)
