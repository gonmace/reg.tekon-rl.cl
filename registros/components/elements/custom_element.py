"""
Elemento personalizado para el sistema flexible.
"""

from typing import Dict, Any, Optional
from .base_element import BaseElement


class CustomElement(BaseElement):
    """
    Elemento para funcionalidades personalizadas.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        super().__init__(registro, config)
        self.custom_config = config.get('config', {})
        self.template_name = config.get('template_name', 'components/elements/custom_element.html')
    
    def get_element_type(self) -> str:
        return 'custom'
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto del elemento personalizado."""
        return {
            'config': self.custom_config,
            'registro': self.registro,
            'title': self.title,
            'description': self.description,
            'css_classes': self.css_classes,
            'template_name': self.template_name
        }
    
    def is_complete(self) -> bool:
        """Verifica si el elemento personalizado está completo."""
        # Por defecto, los elementos personalizados están completos
        # Se puede sobrescribir en configuraciones específicas
        return self.custom_config.get('is_complete', True)
    
    def get_validation_errors(self) -> list:
        """Obtiene errores de validación del elemento personalizado."""
        # Los elementos personalizados pueden definir sus propios errores
        return self.custom_config.get('validation_errors', [])
    
    def get_custom_data(self) -> Dict[str, Any]:
        """Obtiene datos personalizados del elemento."""
        return self.custom_config.get('data', {})
    
    def execute_custom_logic(self, *args, **kwargs) -> Any:
        """Ejecuta lógica personalizada del elemento."""
        # Los elementos personalizados pueden definir funciones específicas
        custom_function = self.custom_config.get('function')
        if custom_function and callable(custom_function):
            return custom_function(self.registro, *args, **kwargs)
        return None 