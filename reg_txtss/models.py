"""
Modelos para registros TX/TSS.
"""

from registros.models.base import RegistroBase
from django.db import models
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
    concluido = models.BooleanField(default=False, verbose_name='Concluido')
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
