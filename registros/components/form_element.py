"""
Componente para manejar formularios de elementos de registro.
"""

from typing import Dict, Any, Optional, Type
from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from registros.components.base import ElementoRegistro


class FormElement(ElementoRegistro):
    """
    Elemento especializado para manejar formularios de registro.
    """
    
    def __init__(self, registro, elemento_config, instance=None):
        self.elemento_config = elemento_config
        self.model = elemento_config.model
        self.template_name = elemento_config.template_name
        self.success_message = elemento_config.success_message
        self.error_message = elemento_config.error_message
        super().__init__(registro, instance)

    def get_queryset(self):
        """Obtiene el queryset filtrado por registro usando el modelo de la configuración."""
        if self.elemento_config and self.elemento_config.model:
            return self.elemento_config.model.objects.filter(registro=self.registro)
        return None

    def get_or_create(self):
        """Obtiene la instancia existente o crea una nueva."""
        try:
            queryset = self.get_queryset()
            if queryset:
                return queryset.first()
            else:
                # Si no existe, crear una nueva instancia
                if self.elemento_config and self.elemento_config.model:
                    instance = self.elemento_config.model.objects.create(registro=self.registro)
                    return instance
        except Exception:
            pass
        return None

    def get_form(self, data=None, files=None):
        """Crea un formulario dinámicamente basado en la configuración."""
        if not self.elemento_config:
            return None
        
        # Si se proporciona un formulario personalizado, usarlo
        if self.elemento_config.form_class:
            # Preparar argumentos para el formulario
            form_kwargs = {'data': data, 'files': files}
            
            # Si el formulario requiere registro_id, pasarlo
            if hasattr(self.elemento_config.form_class, '__init__'):
                import inspect
                sig = inspect.signature(self.elemento_config.form_class.__init__)
                
                # Verificar si el formulario acepta registro_id como parámetro específico
                if 'registro_id' in sig.parameters:
                    form_kwargs['registro_id'] = self.registro.id if self.registro else None
                # Si usa *args/**kwargs, siempre pasar registro_id
                elif 'args' in sig.parameters and 'kwargs' in sig.parameters:
                    form_kwargs['registro_id'] = self.registro.id if self.registro else None
            
            form = self.elemento_config.form_class(**form_kwargs)
            if self.instance:
                form.initial = self._get_initial_data()
            return form
            
        # Crear formulario dinámicamente basado en fields
        if not self.elemento_config.fields:
            return None
            
        # Crear formulario dinámicamente
        form_fields = {}
        for field_name in self.elemento_config.fields:
            model_field = self.elemento_config.model._meta.get_field(field_name)
            
            # Determinar el widget y clases CSS
            widget_class = self.elemento_config.widgets.get(field_name, forms.TextInput)
            css_class = self.elemento_config.css_classes.get(field_name, 'input input-success sombra')
            
            if isinstance(model_field, models.TextField):
                widget_class = forms.Textarea
                css_class = 'textarea textarea-warning sombra rows-2'
            elif isinstance(model_field, models.FloatField):
                widget_class = forms.NumberInput
                css_class = 'input input-success sombra'
            
            form_fields[field_name] = forms.CharField(
                widget=widget_class(attrs={'class': css_class}),
                required=not model_field.blank,
                label=model_field.verbose_name
            )
        
        # Crear clase de formulario dinámicamente
        form_class = type(
            f'{self.elemento_config.model.__name__}Form',
            (forms.Form,),
            form_fields
        )
        
        # Configurar el formulario
        if self.instance:
            return form_class(data=data, files=files, initial=self._get_initial_data())
        else:
            return form_class(data=data, files=files)

    def _get_initial_data(self):
        """Obtiene los datos iniciales del formulario."""
        if not self.instance:
            return {}
        
        initial = {}
        
        # Si hay un formulario personalizado, usar sus campos
        if self.elemento_config.form_class:
            form_fields = self.elemento_config.form_class().fields.keys()
        else:
            # Usar los campos configurados manualmente
            form_fields = self.elemento_config.fields
        
        for field_name in form_fields:
            if hasattr(self.instance, field_name):
                initial[field_name] = getattr(self.instance, field_name)
        return initial

    def save(self, form):
        """Guarda el formulario."""
        try:
            with transaction.atomic():
                # Obtener los campos del formulario
                if self.elemento_config.form_class:
                    form_fields = self.elemento_config.form_class().fields.keys()
                else:
                    form_fields = self.elemento_config.fields
                
                # Crear o actualizar la instancia
                if self.instance:
                    for field_name in form_fields:
                        if field_name in form.cleaned_data:
                            setattr(self.instance, field_name, form.cleaned_data[field_name])
                    self.instance.save()
                    return self.instance
                else:
                    # Crear nueva instancia
                    instance_data = {
                        'registro': self.registro
                    }
                    for field_name in form_fields:
                        if field_name in form.cleaned_data:
                            instance_data[field_name] = form.cleaned_data[field_name]
                    
                    instance = self.elemento_config.model.objects.create(**instance_data)
                    self.instance = instance
                    return instance
        except Exception as e:
            raise ValidationError(f"Error al guardar: {str(e)}")

    def get_completeness_info(self):
        """Obtiene información sobre la completitud del formulario."""
        if not self.instance:
            return {
                'color': 'gray',
                'is_complete': False,
                'missing_fields': [],
                'total_fields': 0,
                'filled_fields': 0
            }
        
        # Si el modelo tiene método de completitud, usarlo
        if hasattr(self.model, 'check_completeness'):
            return self.model.check_completeness(self.instance.id)
        
        # Calcular completitud básica
        if self.elemento_config.form_class:
            form_fields = self.elemento_config.form_class().fields.keys()
        else:
            form_fields = self.elemento_config.fields
        
        total_fields = len(form_fields)
        filled_fields = 0
        missing_fields = []
        
        for field_name in form_fields:
            if hasattr(self.instance, field_name):
                value = getattr(self.instance, field_name)
                if value is not None and value != '':
                    filled_fields += 1
                else:
                    missing_fields.append(field_name)
        
        is_complete = filled_fields == total_fields and total_fields > 0

        if is_complete:
            color = 'paso-verde'
        elif filled_fields > 0:
            color = 'paso-amarillo'
        else:
            color = 'paso-rojo'
        
        return {
            'color': color,
            'is_complete': is_complete,
            'missing_fields': missing_fields,
            'total_fields': total_fields,
            'filled_fields': filled_fields
        }

    def get_context_data(self):
        """Obtiene el contexto para renderizar el formulario."""
        form = self.get_form()
        completeness = self.get_completeness_info()
        
        return {
            'form': form,
            'instance': self.instance,
            'completeness': completeness,
            'title': self.elemento_config.title,
            'description': self.elemento_config.description,
            'success_message': self.success_message,
            'error_message': self.error_message,
        } 