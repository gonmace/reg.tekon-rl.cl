"""
Modelo base para pasos de registros.
"""

from django.db import models
from core.models.core_models import BaseModel


class PasoBase(BaseModel):
    """
    Modelo base para todos los pasos de registros.
    Cada paso específico debe heredar de esta clase.
    """
    # Usar una referencia genérica que puede ser sobrescrita por subclases
    registro = None  # Debe ser definido por las subclases
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.registro} - {self.get_etapa()}"
    
    @staticmethod
    def get_etapa():
        """Retorna el nombre de la etapa. Debe ser sobrescrito por subclases."""
        return 'paso'
    
    @staticmethod
    def get_actives():
        """Retorna los registros activos. Debe ser sobrescrito por subclases."""
        return []
    
    @staticmethod
    def check_completeness(paso_id):
        """Verifica la completitud del paso. Debe ser sobrescrito por subclases."""
        return {
            'color': 'gray',
            'is_complete': False,
            'missing_fields': [],
            'total_fields': 0,
            'filled_fields': 0
        } 