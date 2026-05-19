"""
Validadores comunes para modelos de registros.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validar_latitud(value):
    """Valida que la latitud esté en el rango correcto."""
    if value < -90 or value > 90:
        raise ValidationError(_('La latitud debe estar entre -90 y 90 grados.'))


def validar_longitud(value):
    """Valida que la longitud esté en el rango correcto."""
    if value < -180 or value > 180:
        raise ValidationError(_('La longitud debe estar entre -180 y 180 grados.'))


def validar_porcentaje(value):
    """Valida que el valor esté entre 0 y 100."""
    if value < 0 or value > 100:
        raise ValidationError(_('El porcentaje debe estar entre 0 y 100.'))
