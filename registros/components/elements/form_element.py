"""
Elemento de formulario para el sistema flexible.
"""

from typing import Dict, Any, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from .base_element import BaseElement


class FormElement(BaseElement):
    """
    Elemento para manejar formularios Django.
    """
    
    def __init__(self, registro, config: Dict[str, Any], instance=None):
        super().__init__(registro, config)
        self.instance = instance
        self.model_class = config.get('model_class')
        self.form_class = config.get('form_class')
        self.fields = config.get('fields', [])
        self.success_message = config.get('success_message')
        self.error_message = config.get('error_message')
    
    def get_element_type(self) -> str:
        return 'form'
    
    def get_form(self, data=None, files=None):
        """Obtiene una instancia del formulario."""
        if not self.form_class:
            return None
            
        if self.instance:
            return self.form_class(data=data, files=files, instance=self.instance)
        else:
            return self.form_class(data=data, files=files, registro_id=self.registro.id)
    
    def save(self, form):
        """Guarda el formulario."""
        try:
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.registro = self.registro
                obj.save()
                return obj
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Error al guardar: {str(e)}")
    
    def get_or_create(self):
        """Obtiene la instancia existente o crea una nueva."""
        if not self.model_class:
            return None
            
        try:
            return self.model_class.objects.filter(registro=self.registro).first()
        except Exception:
            return None
    
    def get_context_data(self) -> Dict[str, Any]:
        """Obtiene los datos de contexto del formulario."""
        instance = self.get_or_create()
        form = self.get_form()
        
        return {
            'form': form,
            'instance': instance,
            'title': self.title,
            'description': self.description,
            'is_required': self.is_required,
            'css_classes': self.css_classes
        }
    
    def is_complete(self) -> bool:
        """Verifica si el formulario está completo."""
        if not self.is_required:
            return True
            
        instance = self.get_or_create()
        if not instance:
            return False
        
        # Verificar campos requeridos
        for field_name in self.fields:
            if hasattr(instance, field_name):
                value = getattr(instance, field_name)
                if value is None or value == '':
                    return False
        
        return True
    
    def get_validation_errors(self) -> list:
        """Obtiene errores de validación del formulario."""
        errors = []
        
        if self.is_required:
            instance = self.get_or_create()
            if not instance:
                errors.append(f"El formulario '{self.title}' es requerido")
            else:
                for field_name in self.fields:
                    if hasattr(instance, field_name):
                        value = getattr(instance, field_name)
                        if value is None or value == '':
                            errors.append(f"El campo '{field_name}' es requerido")
        
        return errors 