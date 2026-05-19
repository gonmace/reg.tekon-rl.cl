from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='actividades.DatoPaso')
def dato_paso_post_save(sender, instance, **kwargs):
    """Reconstruye el contexto cuando se guardan datos de un widget (incluyendo cambios desde admin)."""
    try:
        registro = instance.content_type.get_object_for_this_type(pk=instance.object_id)
        from actividades.context_builder import rebuild_contexto
        rebuild_contexto(registro)
    except Exception:
        pass
