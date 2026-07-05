"""
Modelos para registros TX/TSS.
"""

from registros.models.base import RegistroBase
from django.db import models, connection
from core.models.sites import Site
from users.models import User
from simple_history.models import HistoricalRecords

ALTERNATIVA_CHOICES = [
    ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'),
]


class RegTxtssQuerySet(models.QuerySet):
    """QuerySet con la lógica de estado del registro, antes duplicada en las
    vistas de lista, `locate_registro`, `mapa_registros_geojson` y el dashboard."""

    def with_estado(self):
        """Anota `has_widgets` (el registro tiene datos/fotos/mapas) y
        `orden_estado` (1 = en proceso/amarillo, 2 = concluido/verde,
        3 = vacío/rojo). Portable entre PostgreSQL y SQLite."""
        from django.db.models import Exists, OuterRef, Case, When, IntegerField, Value
        from django.contrib.contenttypes.models import ContentType
        from actividades.models import DatoPaso
        from photos.models import Photos
        from core.models.google_maps import GoogleMapsImage

        ct = ContentType.objects.get_for_model(RegTxtss)
        datopaso = DatoPaso.objects.filter(content_type=ct, object_id=OuterRef('pk'))
        if connection.vendor == 'postgresql':
            # Filtra dicts totalmente vacíos como {'lat': '', 'lon': ''}.
            datopaso = datopaso.extra(
                where=["EXISTS(SELECT 1 FROM jsonb_each_text(datos) j WHERE j.value != '')"]
            )
        else:
            # Fallback portable (SQLite/otros motores en dev): considera "con
            # datos" cualquier DatoPaso cuyo JSON no sea el objeto vacío.
            datopaso = datopaso.exclude(datos={})

        has_widgets_qs = (
            Exists(datopaso)
            | Exists(Photos.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
            | Exists(GoogleMapsImage.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
        )
        return self.annotate(
            has_widgets=has_widgets_qs,
            orden_estado=Case(
                When(concluido=False, has_widgets=True, then=Value(1)),  # amarillo
                When(concluido=True,                    then=Value(2)),  # verde
                default=Value(3),                                         # rojo
                output_field=IntegerField(),
            ),
        )


class RegTxtss(RegistroBase):
    """
    Modelo para registros TX/TSS.
    """
    # SET_NULL: borrar un sitio o usuario no debe eliminar en cascada los
    # registros de inspección (dato de campo irrecuperable).
    sitio = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Sitio', related_name='reg_txtss')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Usuario', related_name='reg_txtss')
    alternativa = models.CharField(
        max_length=1, choices=ALTERNATIVA_CHOICES, default='A', blank=True, verbose_name='Alternativa'
    )
    concluido = models.BooleanField(default=False, verbose_name='Concluido', db_index=True)
    history = HistoricalRecords()

    objects = RegTxtssQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['sitio', 'user', 'fecha', 'alternativa'],
                name='unique_sitio_user_fecha_alternativa_regtxtss',
            )
        ]
        indexes = [
            models.Index(fields=['fecha'], name='regtxtss_fecha_idx'),
        ]
    
    def __str__(self):
        return f"RegTxtss {self.id}"
    
    def clean(self):
        """Custom validation method"""
        super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 

    def get_reg_app_name(self):
        return "reg_txtss"
