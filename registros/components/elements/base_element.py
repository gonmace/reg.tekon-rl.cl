"""
Clase base para todos los elementos del sistema flexible.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.db import models


class BaseElement(ABC):
    """
    Clase base abstracta para todos los elementos.
    Define la interfaz común que todos los elementos deben implementar.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        self.registro = registro
        self.config = config
        self.is_required = config.get('required', False)
        self.title = config.get('title', 'Elemento')
        self.description = config.get('description', '')
        self.css_classes = config.get('css_classes', '')
    
    @abstractmethod
    def get_context_data(self) -> Dict[str, Any]:
        """
        Obtiene los datos de contexto para renderizar el elemento.
        Debe ser implementado por cada subclase.
        """
        pass
    
    @abstractmethod
    def is_complete(self) -> bool:
        """
        Verifica si el elemento está completo.
        Debe ser implementado por cada subclase.
        """
        pass
    
    def get_template_name(self) -> str:
        """
        Obtiene el nombre del template para renderizar el elemento.
        """
        return self.config.get('template_name', f'components/elements/{self.get_element_type()}.html')
    
    @abstractmethod
    def get_element_type(self) -> str:
        """
        Obtiene el tipo del elemento.
        Debe ser implementado por cada subclase.
        """
        pass
    
    def get_validation_errors(self) -> list:
        """
        Obtiene errores de validación del elemento.
        Por defecto retorna lista vacía.
        """
        return []
    
    def get_completeness_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada sobre la completitud del elemento.
        """
        return {
            'is_complete': self.is_complete(),
            'is_required': self.is_required,
            'title': self.title,
            'type': self.get_element_type(),
            'errors': self.get_validation_errors()
        } 