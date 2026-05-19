"""
Modelo base para registros que será heredado por cada aplicación específica.
"""

from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from core.models.core_models import BaseModel
from core.models.sites import Site
from users.models import User
from datetime import date


class RegistroBase(BaseModel):
    """
    Modelo base para todos los registros.
    Cada aplicación específica debe heredar de esta clase.
    """
    sitio = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Sitio")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    fecha = models.DateField(verbose_name="Fecha de registro", default=date.today)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    # GenericRelation para las fotos
    photos = GenericRelation('photos.Photos', related_query_name='registro')
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['sitio', 'user', 'fecha'],
                name='unique_sitio_user_fecha_%(class)s_combination'
            )
        ]

    def __str__(self):
        return f"{self.sitio} - {self.fecha.strftime('%d/%m/%Y')}"
    
    def activar_registro(self):
        """Activa el registro."""
        self.is_active = True
        self.save()
    
    @property
    def sitio_codigo(self):
        """Obtiene el código del sitio para breadcrumbs."""
        try:
            return self.sitio.pti_cell_id
        except AttributeError:
            try:
                return self.sitio.operator_id
            except AttributeError:
                return 'Sitio'
    
    @property
    def is_complete(self):
        """Verifica si el registro está completo."""
        # Implementar lógica de completitud específica
        return True 