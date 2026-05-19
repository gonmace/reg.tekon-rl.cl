"""
Modelos para registros TX/TSS.
"""

from registros.models.base import RegistroBase
from registros.models.paso import PasoBase
from django.db import models
from registros.models.validators import validar_latitud, validar_longitud
from registros.models.completeness_checker import check_model_completeness
from core.models.sites import Site
from users.models import User
from simple_history.models import HistoricalRecords

ALTERNATIVA_CHOICES = [
    ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'),
]


class RegTxtss(RegistroBase):
    """
    Modelo para registros TX/TSS.
    """
    sitio = models.ForeignKey(Site, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Sitio', related_name='reg_txtss')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='Usuario', related_name='reg_txtss')
    alternativa = models.CharField(
        max_length=1, choices=ALTERNATIVA_CHOICES, default='A', blank=True, verbose_name='Alternativa'
    )
    history = HistoricalRecords()
    
    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['sitio', 'user', 'fecha', 'alternativa'],
                name='unique_sitio_user_fecha_alternativa_regtxtss',
            )
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

# Pasos específicos
class RSitio(PasoBase):
    """Paso Sitio para registros TX/TSS."""
    registro = models.ForeignKey(RegTxtss, on_delete=models.CASCADE, verbose_name='Registro')
    lat = models.FloatField(validators=[validar_latitud], verbose_name='Latitud Inspeccion')
    lon = models.FloatField(validators=[validar_longitud], verbose_name='Longitud Inspeccion')
    altura = models.CharField(max_length=100, verbose_name='Altura Torre')
    dimensiones = models.CharField(max_length=100, verbose_name='Dimensiones del Sitio')
    deslindes = models.CharField(max_length=100, verbose_name='Deslindes')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Registro Sitio'
        verbose_name_plural = 'Registros Sitio'
    
    @staticmethod
    def get_etapa():
        return 'sitio'
    
    @staticmethod
    def get_actives():
        return RSitio.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness(rsitio_id):
        return check_model_completeness(RSitio, rsitio_id)


class RAcceso(PasoBase):
    """Paso Acceso para registros TX/TSS."""
    registro = models.ForeignKey(RegTxtss, on_delete=models.CASCADE, verbose_name='Registro')
    tipo_suelo = models.CharField(max_length=100, verbose_name='Tipo de Suelo')
    distancia = models.CharField(max_length=100, verbose_name='Distancia')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Registro Acceso'
        verbose_name_plural = 'Registros Acceso'
    
    @staticmethod
    def get_etapa():
        return 'acceso'
    
    @staticmethod
    def get_actives():
        return RAcceso.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness(racceso_id):
        return check_model_completeness(RAcceso, racceso_id)


class REmpalme(PasoBase):
    """Paso Empalme para registros TX/TSS."""
    registro = models.ForeignKey(RegTxtss, on_delete=models.CASCADE, verbose_name='Registro')
    lat = models.FloatField(validators=[validar_latitud], verbose_name='Latitud Empalme', null=True, blank=True)
    lon = models.FloatField(validators=[validar_longitud], verbose_name='Longitud Empalme', null=True, blank=True)
    proveedor = models.CharField(max_length=100, verbose_name='Proveedor')
    capacidad = models.CharField(max_length=100, verbose_name='Capacidad')
    comentarios = models.TextField(blank=True, null=True, verbose_name='Comentarios')
    
    class Meta:
        verbose_name = 'Registro Empalme'
        verbose_name_plural = 'Registros Empalme'
    
    @staticmethod
    def get_etapa():
        return 'empalme'
    
    @staticmethod
    def get_actives():
        return REmpalme.objects.filter(is_deleted=False)

    @staticmethod
    def check_completeness(rempalme_id):
        return check_model_completeness(REmpalme, rempalme_id) 