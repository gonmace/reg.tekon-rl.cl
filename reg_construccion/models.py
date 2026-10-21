"""
Registro "Construcción Sitios": un registro por visita del ITO a un sitio en obra.
Un sitio activado acumula varias visitas, una por fecha.
"""
from decimal import Decimal

from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from core.models.contractors import Contractor
from core.models.sites import Site
from registros.models.base import RegistroBase
from users.models import User

# Paso (PasoDefinicion.nombre) que contiene la tabla de partidas y avance.
PASO_AVANCE = 'obra_avance'

# Pasos/etapas opcionales (Eléctrico y Libro de obras): sus datos y fotos no cuentan para el
# color de la visita (verde/amarillo/rojo). Deben coincidir con los widgets `opcional`/foto_min 0.
ETAPAS_OPCIONALES = ('obra_electrico', 'obra_libro')

ESTADO_OBRA_CHOICES = [
    ('construccion', 'Construcción'),
    ('paralizado', 'Paralizado'),
    ('cancelado', 'Cancelado'),
    ('concluido', 'Concluido'),
]
DESCRIPCION_DEFAULT = 'Construcción de nuevo sitio de telecomunicación'


class RegConstruccionQuerySet(models.QuerySet):
    def with_estado(self):
        """Anota `has_widgets` (datos/fotos de pasos NO opcionales) y `orden_estado` (1 en proceso, 2 concluido, 3 vacío)."""
        from django.db import connection
        from django.db.models import Case, Exists, IntegerField, OuterRef, Value, When
        from django.contrib.contenttypes.models import ContentType
        from actividades.models import DatoPaso
        from core.models.google_maps import GoogleMapsImage
        from photos.models import Photos

        ct = ContentType.objects.get_for_model(self.model)
        datopaso = (DatoPaso.objects.filter(content_type=ct, object_id=OuterRef('pk'))
                    .exclude(paso_nombre__in=ETAPAS_OPCIONALES))
        if connection.vendor == 'postgresql':
            datopaso = datopaso.extra(
                where=["EXISTS(SELECT 1 FROM jsonb_each_text(datos) j WHERE j.value NOT IN ('', '[]'))"]
            )
        else:
            datopaso = datopaso.exclude(datos={})
        has_widgets = (
            Exists(datopaso)
            | Exists(Photos.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False)
                           .exclude(etapa__in=ETAPAS_OPCIONALES))
            | Exists(GoogleMapsImage.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
        )
        return self.annotate(
            has_widgets=has_widgets,
            orden_estado=Case(
                When(concluido=False, has_widgets=True, then=Value(1)),
                When(concluido=True, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            ),
        )


class RegConstruccion(RegistroBase):
    # SET_NULL: borrar un sitio/usuario/contratista no debe arrastrar las visitas.
    sitio = models.ForeignKey(Site, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name='Sitio', related_name='reg_construccion')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name='ITO', related_name='reg_construccion')
    contratista = models.ForeignKey(Contractor, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Contratista', related_name='reg_construccion')
    proyecto = models.CharField('Proyecto', max_length=120, blank=True)
    descripcion = models.CharField('Descripción del proyecto', max_length=255, blank=True,
                                   default=DESCRIPCION_DEFAULT)
    revision = models.PositiveSmallIntegerField('Revisión', default=0)
    estado_obra = models.CharField('Estado de la obra', max_length=20,
                                   choices=ESTADO_OBRA_CHOICES, default='construccion')
    concluido = models.BooleanField('Concluido', default=False, db_index=True)
    # Denormalizado: % de avance total acumulado hasta esta visita (ver signals.py).
    avance_pct = models.DecimalField('Avance total %', max_digits=5, decimal_places=2, default=Decimal('0'))
    # Denormalizado: todos los pasos NO opcionales están completos (ver signals.py). Pinta la fila de verde.
    completo = models.BooleanField('Pasos obligatorios completos', default=False)
    history = HistoricalRecords()

    objects = RegConstruccionQuerySet.as_manager()

    class Meta:
        verbose_name = 'Registro de construcción'
        verbose_name_plural = 'Registros de construcción'
        ordering = ['-fecha', '-id']
        constraints = [
            models.UniqueConstraint(
                fields=['sitio', 'fecha'],
                condition=Q(is_deleted=False),
                name='unique_visita_sitio_fecha_regconstruccion',
                violation_error_message='Ya existe un reporte de este sitio en esa fecha.',
            ),
        ]
        indexes = [models.Index(fields=['sitio', 'fecha'], name='regconstr_sitio_fecha_idx')]

    def __str__(self):
        return f'Construcción {self.sitio_id}/{self.fecha}'

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.sitio_id and self.sitio.tipo_sitio != Site.TORRE:
            raise ValidationError({'sitio': 'Construcción Sitios solo aplica a sitios de tipo Torre.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_reg_app_name(self):
        return 'reg_construccion'

    @property
    def numero_visita(self):
        """Posición de esta visita entre las de su sitio (por fecha)."""
        return (
            type(self).objects.filter(sitio_id=self.sitio_id, is_deleted=False)
            .filter(Q(fecha__lt=self.fecha) | Q(fecha=self.fecha, id__lte=self.id))
            .count()
        )

    @property
    def ito_nombre(self):
        if not self.user:
            return '—'
        return self.user.get_full_name.strip() or self.user.username

    @property
    def coordenadas(self):
        """(lat, lon) del sitio para la obra: construcción, si no ingeniería, si no mandato."""
        sitio = self.sitio
        if not sitio:
            return None, None
        for lat, lon in ((sitio.lat_con, sitio.lon_con), (sitio.lat_ing, sitio.lon_ing),
                         (sitio.lat_man, sitio.lon_man)):
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        return None, None
