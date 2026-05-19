"""
Configuración declarativa para registros.
Permite definir registros de forma simple sin duplicar código.
"""

from typing import Dict, Any, Type, Optional, List
from django import forms
from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from registros.components.base import ElementoRegistro


class SubElementoConfig:
    """
    Configuración de un sub-elemento (mapa, fotos, tabla editable, etc.).
    """
    def __init__(
        self,
        tipo: str,
        config: Dict[str, Any] = None,
        template_name: str = None,
        css_classes: str = "",
        template_datos_clave: str = None,
        title: str = "",
        description: str = "",
        success_message: str = None,
        error_message: str = None
    ):
        self.tipo = tipo  # 'mapa', 'fotos', 'editable_table', etc.
        self.config = config or {}
        self.template_name = template_name
        self.css_classes = css_classes
        self.template_datos_clave = template_datos_clave
        self.title = title
        self.description = description
        self.success_message = success_message
        self.error_message = error_message


class ElementoConfig:
    """
    Configuración de un elemento dentro de un paso.
    """
    def __init__(
        self,
        nombre: str,
        model: Type[models.Model],
        form_class: Type[forms.Form] = None,
        fields: list = None,
        title: str = "",
        description: str = "",
        template_name: str = "components/elemento_form.html",
        success_message: str = "Datos guardados exitosamente.",
        error_message: str = "Error al guardar los datos.",
        widgets: Optional[Dict[str, Any]] = None,
        css_classes: Optional[Dict[str, str]] = None,
        sub_elementos: List[SubElementoConfig] = None
    ):
        self.nombre = nombre
        self.model = model
        self.form_class = form_class
        self.fields = fields or []
        self.title = title
        self.description = description
        self.template_name = template_name
        self.success_message = success_message
        self.error_message = error_message
        self.widgets = widgets or {}
        self.css_classes = css_classes or {}
        self.sub_elementos = sub_elementos or []
        
        # Validar que se proporcione al menos fields, form_class, o sub_elementos
        if not self.fields and not self.form_class and not self.sub_elementos:
            raise ValueError("Debe proporcionar 'fields', 'form_class', o 'sub_elementos'")


class PasoConfig:
    """
    Configuración de un paso de registro.
    """
    def __init__(
        self,
        elemento: ElementoConfig,
        title: str = "",
        description: str = "",
        template_name: str = "components/paso_form.html",
        success_message: str = "Paso completado exitosamente.",
        error_message: str = "Error al completar el paso."
    ):
        self.elemento = elemento
        self.title = title
        self.description = description
        self.template_name = template_name
        self.success_message = success_message
        self.error_message = error_message


class RegistroConfig:
    """
    Configuración completa de un tipo de registro.
    """
    def __init__(
        self,
        registro_model: Type[models.Model],
        pasos: Dict[str, PasoConfig],
        list_template: str = "registros/list.html",
        steps_template: str = "registros/steps.html",
        title: str = "Registros",
        app_namespace: str = None,
        breadcrumbs: list = None,
        header_title: str = None,
        allow_multiple_per_site: bool = False,
        project: bool = False
    ):
        self.registro_model = registro_model
        self.pasos = pasos
        self.list_template = list_template
        self.steps_template = steps_template
        self.title = title
        self.app_namespace = app_namespace
        self.breadcrumbs = breadcrumbs or []
        self.header_title = header_title
        self.allow_multiple_per_site = allow_multiple_per_site
        self.project = project


class ElementoGenerico(ElementoRegistro):
    """
    Elemento genérico que se configura dinámicamente.
    """
    def __init__(self, registro, elemento_config: ElementoConfig, instance=None):
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