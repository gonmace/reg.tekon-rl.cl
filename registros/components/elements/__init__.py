"""
Módulo de elementos para el sistema flexible de pasos.
Cada elemento representa un tipo específico de funcionalidad (formulario, tabla, mapa, etc.).
"""

from .base_element import BaseElement
from .form_element import FormElement
from .table_element import TableElement
from .map_element import MapElement
from .photos_element import PhotosElement
from .info_element import InfoElement
from .custom_element import CustomElement

__all__ = [
    'BaseElement',
    'FormElement',
    'TableElement', 
    'MapElement',
    'PhotosElement',
    'InfoElement',
    'CustomElement'
] 