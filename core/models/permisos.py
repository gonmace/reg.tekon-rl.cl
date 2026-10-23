from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from simple_history.models import HistoricalRecords

CACHE_KEY_ROLES = 'permisos:roles:v1'


class PermisoRol(models.Model):
    """Diferencia con el valor por defecto de `core.permisos_catalogo` para un rol."""
    rol = models.CharField(max_length=50)
    accion = models.CharField(max_length=50)
    permitido = models.BooleanField()
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Permiso por rol'
        verbose_name_plural = 'Permisos por rol'
        constraints = [models.UniqueConstraint(fields=['rol', 'accion'], name='permiso_rol_unico')]

    def __str__(self):
        return f'{self.rol}: {self.accion} = {self.permitido}'


class PermisoUsuario(models.Model):
    """Excepción por usuario: concede o niega una acción por encima de su rol."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permisos_extra')
    accion = models.CharField(max_length=50)
    permitido = models.BooleanField()
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Permiso por usuario'
        verbose_name_plural = 'Permisos por usuario'
        constraints = [models.UniqueConstraint(fields=['user', 'accion'], name='permiso_usuario_unico')]

    def __str__(self):
        return f'{self.user_id}: {self.accion} = {self.permitido}'


def invalidar_cache_permisos():
    cache.delete(CACHE_KEY_ROLES)


@receiver([post_save, post_delete], sender=PermisoRol)
def _invalidar_al_cambiar(sender, **kwargs):
    invalidar_cache_permisos()
