"""
Elemento de fotos para el sistema flexible.
"""

from typing import Dict, Any, Optional
from .base_element import BaseElement


class PhotosElement(BaseElement):
    """
    Elemento para manejar fotografías.
    """
    
    def __init__(self, registro, config: Dict[str, Any]):
        super().__init__(registro, config)
        self.min_count = config.get('min_count', 4)
        self.max_count = config.get('max_count')
        self.allowed_types = config.get('allowed_types', ['image/jpeg', 'image/png'])
    
    def get_element_type(self) -> str:
        return 'photos'
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto de las fotos."""
        return {
            'title': self.title,
            'description': self.description,
            'min_count': self.min_count,
            'max_count': self.max_count,
            'allowed_types': self.allowed_types,
            'is_required': self.is_required,
            'css_classes': self.css_classes,
            'template_name': self.config.get('template_name', 'widgets/camera_widget_page.html')
        }
    
    def is_complete(self) -> bool:
        """Verifica si las fotos están completas."""
        if not self.is_required:
            return True
        
        # Contar fotos del registro
        photo_count = self.get_photo_count()
        
        if self.min_count and photo_count < self.min_count:
            return False
        
        if self.max_count and photo_count > self.max_count:
            return False
        
        return True
    
    def get_validation_errors(self) -> list:
        """Obtiene errores de validación de las fotos."""
        errors = []
        
        if self.is_required:
            photo_count = self.get_photo_count()
            
            if self.min_count and photo_count < self.min_count:
                errors.append(f"Se requieren al menos {self.min_count} fotos para '{self.title}'")
            
            if self.max_count and photo_count > self.max_count:
                errors.append(f"No se pueden subir más de {self.max_count} fotos para '{self.title}'")
        
        return errors
    
    def get_photo_count(self) -> int:
        """Obtiene el número de fotos del registro."""
        try:
            from photos.models import Photos
            from django.contrib.contenttypes.models import ContentType
            
            content_type = ContentType.objects.get_for_model(type(self.registro))
            return Photos.objects.filter(
                content_type=content_type,
                object_id=self.registro.id
            ).count()
        except ImportError:
            # Si el módulo de fotos no está disponible
            return 0
        except Exception:
            return 0
    
    def get_photos(self) -> list:
        """Obtiene las fotos del registro."""
        try:
            from photos.models import Photos
            from django.contrib.contenttypes.models import ContentType
            
            content_type = ContentType.objects.get_for_model(type(self.registro))
            return list(Photos.objects.filter(
                content_type=content_type,
                object_id=self.registro.id
            ).order_by('created_at'))
        except ImportError:
            return []
        except Exception:
            return [] 