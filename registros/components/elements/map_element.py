"""
Elemento de mapa para el sistema flexible.
"""

from typing import Dict, Any, Optional
from .base_element import BaseElement


class MapElement(BaseElement):
    """
    Elemento para manejar mapas y ubicaciones geográficas.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        super().__init__(registro, config)
        self.map_type = config.get('type', 'single_point')
        self.zoom = config.get('zoom', 15)
        self.lat_field = config.get('lat_field', 'lat')
        self.lon_field = config.get('lon_field', 'lon')
        self.name_field = config.get('name_field', 'name')
        self.icon_config = config.get('icon_config', {})
        self.points = config.get('points', [])
    
    def get_element_type(self) -> str:
        return 'map'
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto del mapa."""
        return {
            'map_config': {
                'type': self.map_type,
                'zoom': self.zoom,
                'lat_field': self.lat_field,
                'lon_field': self.lon_field,
                'name_field': self.name_field,
                'icon_config': self.icon_config,
                'points': self.points,
                'template_name': self.config.get('template_name', 'components/mapa.html')
            },
            'title': self.title,
            'description': self.description,
            'is_required': self.is_required,
            'css_classes': self.css_classes
        }
    
    def is_complete(self) -> bool:
        """Verifica si el mapa está completo."""
        if not self.is_required:
            return True
        
        # Verificar si hay coordenadas válidas
        if self.map_type == 'single_point':
            # Verificar si el registro tiene coordenadas
            if hasattr(self.registro, self.lat_field) and hasattr(self.registro, self.lon_field):
                lat = getattr(self.registro, self.lat_field)
                lon = getattr(self.registro, self.lon_field)
                return lat is not None and lon is not None
        
        elif self.map_type == 'multi_point':
            # Verificar si hay puntos definidos
            return len(self.points) > 0
        
        return True
    
    def get_validation_errors(self) -> list:
        """Obtiene errores de validación del mapa."""
        errors = []
        
        if self.is_required:
            if self.map_type == 'single_point':
                if hasattr(self.registro, self.lat_field) and hasattr(self.registro, self.lon_field):
                    lat = getattr(self.registro, self.lat_field)
                    lon = getattr(self.registro, self.lon_field)
                    if lat is None or lon is None:
                        errors.append(f"El mapa '{self.title}' requiere coordenadas válidas")
                else:
                    errors.append(f"El registro no tiene los campos de coordenadas requeridos")
            
            elif self.map_type == 'multi_point':
                if len(self.points) == 0:
                    errors.append(f"El mapa '{self.title}' requiere al menos un punto")
        
        return errors
    
    def get_coordinates(self) -> Dict[str, Any]:
        """Obtiene las coordenadas del mapa."""
        if self.map_type == 'single_point':
            if hasattr(self.registro, self.lat_field) and hasattr(self.registro, self.lon_field):
                return {
                    'lat': getattr(self.registro, self.lat_field),
                    'lon': getattr(self.registro, self.lon_field),
                    'name': getattr(self.registro, self.name_field, 'Ubicación')
                }
        
        return None 