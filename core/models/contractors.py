"""
Modelos para contratistas.
"""

from django.db import models
from django.core.validators import RegexValidator
from simple_history.models import HistoricalRecords


class Contractor(models.Model):
    """
    Modelo para contratistas.
    """
    name = models.CharField(
        max_length=200, 
        verbose_name='Nombre',
        help_text='Nombre del contratista'
    )
    code = models.CharField(
        max_length=50, 
        verbose_name='Código',
        unique=True,
        help_text='Código único del contratista'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el contratista está activo'
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='Eliminado',
        help_text='Soft delete: el contratista no aparece en la lista'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualización'
    )
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Contratista'
        verbose_name_plural = 'Contratistas'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

    def clean(self):
        """Validación personalizada"""
        from django.core.exceptions import ValidationError
        
        # Validar que el código sea único (excluyendo el registro actual)
        if Contractor.objects.filter(code=self.code).exclude(pk=self.pk).exists():
            raise ValidationError({'code': 'Ya existe un contratista con este código.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
