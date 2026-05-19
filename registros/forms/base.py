"""
Formularios base genéricos para registros.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div
from registros.forms.utils import get_form_field_css_class
from django.utils.html import format_html as HTML


class BasePasoForm(forms.ModelForm):
    """
    Formulario base para pasos de registros.
    Proporciona funcionalidad común para todos los formularios de pasos.
    """
    
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        self.registro_model = kwargs.pop('registro_model', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'pb-4'
        self.helper.label_class = 'text-sm text-base-content'
        self.helper.field_class = 'mb-2'
        
        # Configurar el campo registro automáticamente
        self._configure_registro_field()
        
        # Configurar el layout
        self._configure_layout()
    
    def _configure_registro_field(self):
        """Configura el campo registro automáticamente."""
        if 'registro' in self.fields:
            try:
                if self.registro_id and self.registro_model:
                    # Para formularios nuevos, establecer el registro según el ID
                    registro_obj = self.registro_model.objects.get(id=self.registro_id)
                    self.initial['registro'] = registro_obj.id
                    self.fields['registro'].initial = registro_obj.id
                    self.fields['registro'].widget = forms.HiddenInput()
                elif self.instance.pk:
                    # Para formularios existentes, ocultar el campo
                    self.fields['registro'].widget = forms.HiddenInput()
                else:
                    # Si no hay registro_id, ocultar el campo
                    self.fields['registro'].widget = forms.HiddenInput()
            except self.registro_model.DoesNotExist:
                # Si el registro no existe, ocultar el campo
                self.fields['registro'].widget = forms.HiddenInput()
    
    def _configure_layout(self):
        """Configura el layout del formulario. Debe ser sobrescrito por subclases."""
        # Layout básico que puede ser extendido
        self.helper.layout = Layout(
            Field('registro'),
            Submit('submit', 'Guardar', css_class='btn btn-save'),
        )
    
    def get_field_css_class(self, field_name):
        """Obtiene la clase CSS para un campo específico."""
        return get_form_field_css_class(self, field_name)


class BasePasoFormWithMap(BasePasoForm):
    """
    Formulario base para pasos que incluyen un mapa.
    """
    
    def _configure_layout(self):
        """Configura el layout con mapa."""
        # HTML para botón de ubicar en mapa
        btn_ubicar_mapa_html = '''
        <button type="button"
            id="btn-ubicar-mapa"
            class="btn btn-ghost p-0 h-10 m-0 sm:h-12 w-10 sm:w-12 my-auto">
                <svg width="64px" height="64px" viewBox="0 0 1024 1024" class="icon sombra" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M640 213.333333L384 128 128 213.333333v682.666667l256-85.333333 256 85.333333 256-85.333333V128z" fill="#FFECB3"></path><path d="M384 128v682.666667l256 85.333333V213.333333z" fill="#FFE082"></path><path d="M640 320c-82.496 0-149.333333 70.250667-149.333333 156.821333S640 768 640 768s149.333333-204.629333 149.333333-291.178667S722.496 320 640 320z" fill="#F44336"></path><path d="M640 469.333333m-64 0a64 64 0 1 0 128 0 64 64 0 1 0-128 0Z" fill="#FFEBEE"></path></g></svg>
        </button>
        '''
        
        # Configurar campos de latitud y longitud si existen
        lat_lon_fields = []
        if 'lat' in self.fields and 'lon' in self.fields:
            lat_lon_fields = [
                Div(
                    HTML(btn_ubicar_mapa_html),
                    Div(
                        HTML('{% include "registros/forms/lat_lon_input.html" with field=form.lat %}'),
                        HTML('{% include "registros/forms/lat_lon_input.html" with field=form.lon %}'),
                        css_class='flex flex-row justify-between gap-3 mb-3'
                    ),
                    css_class='flex flex-row justify-between gap-3 mb-3'
                )
            ]
        
        # Obtener todos los campos excepto registro, lat, lon
        other_fields = []
        for field_name in self.fields:
            if field_name not in ['registro', 'lat', 'lon']:
                css_class = self.get_field_css_class(field_name)
                if field_name == 'comentarios':
                    other_fields.append(Field(field_name, css_class=f"{css_class} w-full"))
                else:
                    other_fields.append(Field(field_name, css_class=f"{css_class} w-full"))
        
        # Organizar campos en grupos
        field_groups = []
        current_group = []
        
        for field in other_fields:
            current_group.append(field)
            # Crear un nuevo grupo cada 2 campos (excepto comentarios)
            if len(current_group) == 2 and 'comentarios' not in str(field):
                field_groups.append(Div(*current_group, css_class='flex sm:flex-row flex-col justify-between gap-3'))
                current_group = []
        
        # Agregar campos restantes
        if current_group:
            if len(current_group) == 1 and 'comentarios' in str(current_group[0]):
                field_groups.append(Div(current_group[0], css_class='mb-3'))
            else:
                field_groups.append(Div(*current_group, css_class='flex flex-row justify-between gap-3'))
        
        self.helper.layout = Layout(
            Field('registro'),
            *lat_lon_fields,
            *field_groups,
            Div(
                Submit('submit', 'Guardar Registro', css_class='btn btn-save w-full mt-4'),
                css_class='text-center'
            ),
        ) 