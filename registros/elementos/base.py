"""
Clase base para elementos de registro.
"""

from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from typing import Dict, Any, Optional


class ElementoBase:
    """
    Clase base para elementos de registro.
    Cada elemento representa un paso con su formulario y sub-elementos.
    """
    model = None              # Modelo asociado al elemento
    form_class = None         # Formulario asociado al elemento
    template_name = None      # Template a renderizar
    tipo = 'form'            # Tipo de elemento
    success_message = "Elemento guardado exitosamente."
    error_message = "Error al guardar el elemento."
    sub_elementos = {}        # Diccionario de sub-elementos

    def __init__(self, registro, instance=None):
        self.registro = registro
        self.instance = instance
        self.sub_elementos_instancias = {}

    def get_queryset(self):
        """Obtiene el queryset filtrado por registro."""
        if self.model:
            return self.model.objects.filter(registro=self.registro)
        return None

    def get_form(self, data=None, files=None):
        """Obtiene una instancia del formulario."""
        if not self.form_class:
            return None
            
        if self.instance:
            return self.form_class(data=data, files=files, instance=self.instance)
        else:
            return self.form_class(data=data, files=files, registro_id=self.registro.id)

    def save(self, form):
        """Guarda el formulario y asocia el registro."""
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
        try:
            queryset = self.get_queryset()
            if queryset:
                return queryset.first()
        except Exception:
            pass
        return None

    def get_sub_elemento(self, tipo_sub_elemento):
        """Obtiene un sub-elemento específico."""
        if tipo_sub_elemento not in self.sub_elementos:
            return None
            
        if tipo_sub_elemento not in self.sub_elementos_instancias:
            sub_elemento_class = self.sub_elementos[tipo_sub_elemento]
            self.sub_elementos_instancias[tipo_sub_elemento] = sub_elemento_class(self)
            
        return self.sub_elementos_instancias[tipo_sub_elemento]

    def get_all_sub_elementos(self):
        """Obtiene todos los sub-elementos."""
        sub_elementos = {}
        for tipo in self.sub_elementos.keys():
            sub_elementos[tipo] = self.get_sub_elemento(tipo)
        return sub_elementos

    def get_completeness_info(self, instance_id=None):
        """Obtiene información de completitud."""
        if not self.instance:
            return None
        
        return self.model.check_completeness(self.instance.id)

    def get_tipo(self):
        """Obtiene el tipo del elemento."""
        return self.tipo

    def to_dict(self):
        """Convierte el elemento a diccionario."""
        return {
            'tipo': self.tipo,
            'model': self.model.__name__ if self.model else None,
            'has_instance': self.instance is not None,
        } 