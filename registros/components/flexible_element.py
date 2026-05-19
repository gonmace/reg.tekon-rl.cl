"""
Componente flexible para manejar múltiples elementos en un solo paso.
"""

from typing import Dict, Any, Optional, List
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from registros.components.base import ElementoRegistro
from registros.components.registro_config import ElementoConfig, SubElementoConfig
from registros.components.elements import (
    FormElement,
    TableElement,
    MapElement,
    PhotosElement,
    InfoElement,
    CustomElement
)


class FlexibleElement(ElementoRegistro):
    """
    Elemento flexible que puede contener múltiples tipos de elementos:
    - Formularios
    - Tablas editables
    - Mapas
    - Fotos
    - Elementos informativos
    - Elementos personalizados
    """
    
    def __init__(self, registro, elemento_config: ElementoConfig, instance=None):
        self.elemento_config = elemento_config
        self.registro = registro
        self.instance = instance
        self.elements = {}
        
        # Inicializar cada elemento según su tipo
        for sub_elemento in elemento_config.sub_elementos:
            element_type = sub_elemento.tipo
            if element_type == 'form':
                self.elements['form'] = FormElement(registro, sub_elemento.config, instance)
            elif element_type == 'table':
                self.elements['table'] = TableElement(registro, sub_elemento.config)
            elif element_type == 'map':
                self.elements['map'] = MapElement(registro, sub_elemento.config)
            elif element_type == 'photos':
                self.elements['photos'] = PhotosElement(registro, sub_elemento.config)
            elif element_type == 'info':
                self.elements['info'] = InfoElement(registro, sub_elemento.config)
            elif element_type == 'custom':
                self.elements['custom'] = CustomElement(registro, sub_elemento.config)
    
    def get_form(self, data=None, files=None):
        """Obtiene el formulario si existe un elemento de tipo form."""
        if 'form' in self.elements:
            return self.elements['form'].get_form(data, files)
        return None
    
    def save(self, form):
        """Guarda el formulario si existe un elemento de tipo form."""
        if 'form' in self.elements:
            return self.elements['form'].save(form)
        return None
    
    def get_context_data(self):
        """Obtiene los datos de contexto para todos los elementos."""
        context = {}
        
        for element_type, handler in self.elements.items():
            element_context = handler.get_context_data()
            if element_context:
                context[element_type] = element_context
        
        return context
    
    def validate_completeness(self):
        """Valida la completitud de todos los elementos requeridos."""
        completeness = {
            'is_complete': True,
            'missing_elements': [],
            'total_elements': len(self.elements),
            'completed_elements': 0,
            'validation_errors': []
        }
        
        for element_type, handler in self.elements.items():
            if handler.is_required:
                if not handler.is_complete():
                    completeness['is_complete'] = False
                    completeness['missing_elements'].append(element_type)
                else:
                    completeness['completed_elements'] += 1
            
            # Recolectar errores de validación
            errors = handler.get_validation_errors()
            if errors:
                completeness['validation_errors'].extend(errors)
        
        return completeness
    
    def get_element_by_type(self, element_type: str):
        """Obtiene un elemento específico por tipo."""
        return self.elements.get(element_type)
    
    def has_element_type(self, element_type: str) -> bool:
        """Verifica si existe un elemento de un tipo específico."""
        return element_type in self.elements
    
    def get_required_elements(self) -> List[str]:
        """Obtiene la lista de elementos requeridos."""
        return [element_type for element_type, handler in self.elements.items() 
                if handler.is_required]
    
    def get_optional_elements(self) -> List[str]:
        """Obtiene la lista de elementos opcionales."""
        return [element_type for element_type, handler in self.elements.items() 
                if not handler.is_required] 