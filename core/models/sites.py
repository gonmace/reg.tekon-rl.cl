from django.db import models
from simple_history.models import HistoricalRecords

class Site(models.Model):
    POSTE = "POSTE"
    TORRE = "TORRE"
    TIPO_SITIO_CHOICES = [
        (POSTE, "Poste"),
        (TORRE, "Torre"),
    ]

    pti_cell_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="PTI ID", unique=True)
    operator_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Operador ID")
    name = models.CharField(max_length=100, verbose_name="Nombre del sitio", unique=True)
    tipo_sitio = models.CharField(
        max_length=10,
        choices=TIPO_SITIO_CHOICES,
        default=TORRE,
        verbose_name="Tipo de sitio",
    )
    lat_man = models.FloatField(null=True, blank=True, verbose_name="Latitud Mandato")
    lon_man = models.FloatField(null=True, blank=True, verbose_name="Longitud Mandato")
    lat_ing = models.FloatField(null=True, blank=True, verbose_name="Latitud Ingeniería")
    lon_ing = models.FloatField(null=True, blank=True, verbose_name="Longitud Ingeniería")
    lat_con = models.FloatField(null=True, blank=True, verbose_name="Latitud Construcción")
    lon_con = models.FloatField(null=True, blank=True, verbose_name="Longitud Construcción")
    alt = models.IntegerField(null=True, blank=True, verbose_name="Altura (m)")
    region = models.CharField(max_length=100, blank=True, null=True, verbose_name="Región")
    comuna = models.CharField(max_length=100, blank=True, null=True, verbose_name="Comuna")
    empresa_energia = models.CharField(max_length=200, blank=True, null=True, verbose_name="Empresa de Energía")
    is_deleted = models.BooleanField(default=False)
    history = HistoricalRecords()

    def clean(self):
        """Validación adicional para asegurar que el usuario sea ITO"""
        super().clean()
        

    def save(self, *args, **kwargs):
        """Valida antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.pti_cell_id if self.pti_cell_id else '__________'} - {self.operator_id if self.operator_id else '__________'} - {self.name}"


    class Meta:
        verbose_name = 'Sitio'
        verbose_name_plural = 'Sitios'
        ordering = ['pti_cell_id']

    @staticmethod
    def get_table():
        return 'site'

    @staticmethod
    def get_actives():
        return Site.objects.filter(is_deleted=False)
