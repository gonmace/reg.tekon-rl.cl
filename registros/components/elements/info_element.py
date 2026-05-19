"""
Elemento informativo para el sistema flexible.
"""

from typing import Dict, Any, Optional
from .base_element import BaseElement


class InfoElement(BaseElement):
    """
    Elemento para mostrar información estática.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        super().__init__(registro, config)
        self.content = config.get('content', '')
        self.icon = config.get('icon', 'info')
        self.color = config.get('color', 'info')
    
    def get_element_type(self) -> str:
        return 'info'
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto de la información."""
        return {
            'title': self.title,
            'content': self.content,
            'icon': self.icon,
            'color': self.color,
            'css_classes': self.css_classes
        }
    
    def is_complete(self) -> bool:
        """Los elementos informativos siempre están completos."""
        return True
    
    def get_validation_errors(self) -> list:
        """Los elementos informativos no tienen errores de validación."""
        return []
    
    def get_icon_svg(self) -> str:
        """Obtiene el SVG del icono según el tipo."""
        icons = {
            'info': '''
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current flex-shrink-0 w-6 h-6">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            ''',
            'warning': '''
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
            ''',
            'success': '''
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            ''',
            'error': '''
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            '''
        }
        
        return icons.get(self.icon, icons['info']) 