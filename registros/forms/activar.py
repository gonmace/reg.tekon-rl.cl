from django import forms
from users.models import User
from crispy_forms.layout import Layout, Submit, Button, Div, Field
from crispy_forms.helper import FormHelper
from core.models.sites import Site
from registros.models.base import RegistroBase


def create_activar_registro_form(registro_model, title_default='Registro', description_default='Registro activado desde el formulario', allow_multiple_per_site=False, project=False, sitio_queryset=None):
    """
    Factory function para crear un formulario de activación específico para un modelo.
    
    Args:
        registro_model: Clase del modelo que hereda de RegistroBase
        title_default: Título por defecto
        description_default: Descripción por defecto
        allow_multiple_per_site: Si permite múltiples registros por sitio (muestra solo campo fecha)
        project: Si debe mostrar campo de estructura/grupo de proyectos
    
    Returns:
        Clase de formulario configurada
    """
    _model_field_names = {f.name for f in registro_model._meta.get_fields()}
    _optional_fields = [f for f in ['title', 'description'] if f in _model_field_names]

    class ActivarRegistroForm(forms.ModelForm):
        """
        Formulario para activar registros.
        """
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            self.helper = FormHelper()
            self.helper.form_tag = True
            self.helper.form_method = 'post'
            self.helper.form_action = ''
            self.helper.label_class = 'text-sm'
            self.helper.field_class = 'mb-2'
            
            # Construir layout dinámicamente según allow_multiple_per_site
            layout_fields = []
            
            # Si no es múltiple por sitio, mostrar sitio e ITO
            if not allow_multiple_per_site:
                layout_fields.append(
                    Div(
                        Div(Field('sitio', css_class='w-full'), css_class='w-full'),
                        Div(Field('user', css_class='w-full'), css_class='w-full'),
                        css_class='flex flex-wrap -mx-2 mb-4',
                    )
                )

            # Si es múltiple por sitio, solo mostrar fecha
            if allow_multiple_per_site:
                layout_fields.append(
                    Div(
                        Div(Field('fecha', css_class='w-full'), css_class='w-full'),
                        css_class='mb-4',
                    )
                )

            layout_fields.append(
                Div(
                    Button('cancel', 'Cancelar', css_class='btn btn-cancel mt-6', type='button', onclick='closeModal()'),
                    Submit('submit', 'Activar Registro', css_class='btn btn-save flex-grow mt-6', css_id='activar-registro-btn'),
                    css_class='flex gap-2 justify-center',
                )
            )
            
            self.helper.layout = Layout(*layout_fields)
            
            # Configurar campos ocultos
            if 'title' in self.fields:
                self.fields['title'].widget = forms.HiddenInput()
            if 'description' in self.fields:
                self.fields['description'].widget = forms.HiddenInput()
            
            # Si es múltiple por sitio, ocultar sitio e ITO
            if allow_multiple_per_site:
                if 'sitio' in self.fields:
                    self.fields['sitio'].widget = forms.HiddenInput()
                if 'user' in self.fields:
                    self.fields['user'].widget = forms.HiddenInput()
            else:
                # Configurar campos visibles solo si no es múltiple por sitio
                self.fields['sitio'].queryset = sitio_queryset if sitio_queryset is not None else Site.get_actives()
                self.fields['user'].queryset = User.objects.filter(
                    user_type__in=User.ITO_LIKE_ROLES,
                    is_active=True,
                    is_deleted=False,
                ).order_by('first_name', 'last_name', 'username')
            
            # Configurar el campo de fecha
            if 'fecha' in self.fields:
                self.fields['fecha'].widget = forms.DateInput(attrs={'type': 'date'})
                from datetime import date
                self.fields['fecha'].initial = date.today()
                # Cuando no se permite múltiple por sitio, fecha no se muestra;
                # el servidor la asigna en form_valid (date.today()).
                if not allow_multiple_per_site:
                    self.fields['fecha'].required = False
            
            # Establecer valores por defecto
            if not self.instance.pk:
                if 'title' in self.fields:
                    self.fields['title'].initial = title_default
                if 'description' in self.fields:
                    self.fields['description'].initial = description_default
        
        class Meta:
            model = registro_model
            fields = ['sitio', 'user'] + _optional_fields + ['fecha'] + (['estructura'] if project else [])
    
    return ActivarRegistroForm