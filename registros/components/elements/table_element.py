"""
Elemento de tabla para el sistema flexible.
"""

from typing import Dict, Any, Optional
from .base_element import BaseElement


class TableElement(BaseElement):
    """
    Elemento para manejar tablas editables.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        super().__init__(registro, config)
        self.model_class = config.get('model_class')
        self.columns = config.get('columns', [])
        self.page_length = config.get('page_length', 10)
        self.allow_create = config.get('allow_create', True)
        self.allow_edit = config.get('allow_edit', True)
        self.allow_delete = config.get('allow_delete', True)
        self.min_rows = config.get('min_rows', 0)
        self.max_rows = config.get('max_rows')
        self.api_url = config.get('api_url')
    
    def get_element_type(self) -> str:
        return 'table'
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto de la tabla."""
        return {
            'model_class': self.model_class,
            'title': self.title,
            'description': self.description,
            'columns': self.columns,
            'page_length': self.page_length,
            'allow_create': self.allow_create,
            'allow_edit': self.allow_edit,
            'allow_delete': self.allow_delete,
            'is_required': self.is_required,
            'min_rows': self.min_rows,
            'max_rows': self.max_rows,
            'api_url': self.api_url,
            'css_classes': self.css_classes
        }
    
    def is_complete(self) -> bool:
        """Verifica si la tabla está completa."""
        if not self.is_required:
            return True
        
        if not self.model_class:
            return False
        
        count = self.model_class.objects.filter(registro=self.registro).count()
        
        if self.min_rows and count < self.min_rows:
            return False
        
        if self.max_rows and count > self.max_rows:
            return False
        
        return True
    
    def get_validation_errors(self) -> list:
        """Obtiene errores de validación de la tabla."""
        errors = []
        
        if self.is_required and self.model_class:
            count = self.model_class.objects.filter(registro=self.registro).count()
            
            if self.min_rows and count < self.min_rows:
                errors.append(f"La tabla '{self.title}' debe tener al menos {self.min_rows} filas")
            
            if self.max_rows and count > self.max_rows:
                errors.append(f"La tabla '{self.title}' no puede tener más de {self.max_rows} filas")
        
        return errors
    
    def get_row_count(self) -> int:
        """Obtiene el número de filas en la tabla."""
        if not self.model_class:
            return 0
        
        return self.model_class.objects.filter(registro=self.registro).count() 