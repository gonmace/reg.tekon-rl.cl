"""
Formularios para registros Reporte de construcción.
"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, Row, Column, HTML
from .models import RegConstruccion, AvanceComponente, AvanceComponenteComentarios, Objetivo
from proyectos.models import Componente
from registros.forms.utils import get_form_field_css_class


class ObjetivoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'card bg-base-100 shadow-xl'
        self.helper.label_class = 'label-text font-medium text-base-content'
        self.helper.field_class = 'form-control w-full'
        
        # Configurar el campo registro automáticamente
        self.fields['registro'].queryset = RegConstruccion.objects.all()
        
        try:
            if self.registro_id:
                registro_obj = RegConstruccion.objects.get(id=self.registro_id)
                self.fields['registro'].widget = forms.HiddenInput()
                self.initial['registro'] = registro_obj.id
                self.fields['registro'].initial = registro_obj.id
            elif self.instance.pk:
                self.fields['registro'].widget = forms.HiddenInput()
            else:
                self.fields['registro'].widget = forms.HiddenInput()
        except RegConstruccion.DoesNotExist:
            self.fields['registro'].widget = forms.HiddenInput()

        # Mejorar el campo objetivo
        self.fields['objetivo'].widget.attrs.update({
            'placeholder': 'Describe el objetivo principal del reporte de construcción...',
            'rows': 4,
        })

        self.helper.layout = Layout(
            HTML('<div class="card-body">'),
            HTML('<h2 class="card-title text-primary mb-4">'),
            HTML('<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'),
            HTML('<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>'),
            HTML('</svg>'),
            HTML('Objetivo del Reporte'),
            HTML('</h2>'),
            Field('registro'),
            Field('objetivo', css_class='form-control w-full'),
            HTML('<div class="card-actions justify-end mt-6">'),
            Submit('submit', 'Guardar Objetivo', css_class='btn btn-save btn-wide'),
            HTML('</div>'),
            HTML('</div>'),
        )
    
    class Meta:
        model = Objetivo
        fields = ['registro', 'objetivo']


class AvanceComponenteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'card bg-base-100 shadow-xl'
        self.helper.label_class = 'label-text font-medium text-base-content'
        self.helper.field_class = 'form-control w-full'
        
        # Configurar el campo registro automáticamente
        self.fields['registro'].queryset = RegConstruccion.objects.all()
        
        try:
            if self.registro_id:
                registro_obj = RegConstruccion.objects.get(id=self.registro_id)
                self.fields['registro'].widget = forms.HiddenInput()
                self.initial['registro'] = registro_obj.id
                self.fields['registro'].initial = registro_obj.id
            elif self.instance.pk:
                self.fields['registro'].widget = forms.HiddenInput()
            else:
                self.fields['registro'].widget = forms.HiddenInput()
        except RegConstruccion.DoesNotExist:
            self.fields['registro'].widget = forms.HiddenInput()

        # Atributos no-visuales (placeholder, type, min/max). Las clases las
        # aplica crispy-daisyui automáticamente desde styles.css.
        self.fields['fecha'].widget.attrs.update({'type': 'date'})
        self.fields['porcentaje_actual'].widget.attrs.update({'min': '0', 'max': '100', 'placeholder': '0-100'})
        self.fields['porcentaje_acumulado'].widget.attrs.update({'min': '0', 'max': '100', 'placeholder': '0-100'})
        self.fields['comentarios'].widget.attrs.update({
            'placeholder': 'Comentarios adicionales sobre el avance...',
            'rows': 3,
        })

        self.helper.layout = Layout(
            HTML('<div class="card-body">'),
            HTML('<h2 class="card-title text-primary mb-4">'),
            HTML('<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'),
            HTML('<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>'),
            HTML('</svg>'),
            HTML('Avance por Componente'),
            HTML('</h2>'),
            Field('registro'),
            Row(
                Column('componente', css_class='form-control w-full'),
                Column('fecha', css_class='form-control w-full'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
            ),
            Row(
                Column('porcentaje_actual', css_class='form-control w-full'),
                Column('porcentaje_acumulado', css_class='form-control w-full'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
            ),
            Field('comentarios', css_class='form-control w-full'),
            HTML('<div class="card-actions justify-end mt-6">'),
            Submit('submit', 'Guardar Avance', css_class='btn btn-save btn-wide'),
            HTML('</div>'),
            HTML('</div>'),
        )
    
    class Meta:
        model = AvanceComponente
        fields = ['registro', 'componente', 'fecha', 'porcentaje_actual', 'porcentaje_acumulado', 'comentarios']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'porcentaje_actual': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'porcentaje_acumulado': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def clean(self):
        cleaned_data = super().clean()
        porcentaje_actual = cleaned_data.get('porcentaje_actual')
        porcentaje_acumulado = cleaned_data.get('porcentaje_acumulado')
        
        if porcentaje_actual is not None and porcentaje_acumulado is not None:
            if porcentaje_acumulado < porcentaje_actual:
                raise forms.ValidationError(
                    'El porcentaje acumulado no puede ser menor al porcentaje actual.'
                )
        
        return cleaned_data


class AvanceComponenteComentariosForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'card bg-base-100 shadow-xl'
        self.helper.label_class = 'label-text font-medium text-base-content'
        self.helper.field_class = 'form-control w-full'
        
        # Configurar el campo registro automáticamente
        self.fields['registro'].queryset = RegConstruccion.objects.all()
        
        try:
            if self.registro_id:
                registro_obj = RegConstruccion.objects.get(id=self.registro_id)
                self.fields['registro'].widget = forms.HiddenInput()
                self.initial['registro'] = registro_obj.id
                self.fields['registro'].initial = registro_obj.id
            elif self.instance.pk:
                self.fields['registro'].widget = forms.HiddenInput()
            else:
                self.fields['registro'].widget = forms.HiddenInput()
        except RegConstruccion.DoesNotExist:
            self.fields['registro'].widget = forms.HiddenInput()

        # Mejorar el campo comentarios
        self.fields['comentarios'].widget.attrs.update({
            'placeholder': 'Comentarios generales sobre el avance de construcción...',
            'rows': 4,
        })

        self.helper.layout = Layout(
            HTML('<div class="card-body">'),
            HTML('<h2 class="card-title text-primary mb-4">'),
            HTML('<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'),
            HTML('<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>'),
            HTML('</svg>'),
            HTML('Comentarios Generales'),
            HTML('</h2>'),
            Field('registro'),
            Field('comentarios', css_class='form-control w-full'),
            HTML('<div class="card-actions justify-end mt-6">'),
            Submit('submit', 'Guardar Comentarios', css_class='btn btn-save btn-wide'),
            HTML('</div>'),
            HTML('</div>'),
        )
    
    class Meta:
        model = AvanceComponenteComentarios
        fields = ['registro', 'comentarios']


class RegConstruccionForm(forms.ModelForm):
    """Formulario principal para crear/editar registros de construcción."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.form_class = 'card bg-base-100 shadow-xl max-w-2xl mx-auto'
        self.helper.label_class = 'label-text font-medium text-base-content'
        self.helper.field_class = 'form-control w-full'
        
        # Solo placeholders/atributos no-visuales. Las clases las aplica crispy-daisyui.
        self.fields['title'].widget.attrs.update({'placeholder': 'Título del reporte de construcción'})
        self.fields['description'].widget.attrs.update({
            'placeholder': 'Descripción general del reporte...',
            'rows': 3,
        })

        self.helper.layout = Layout(
            HTML('<div class="card-body">'),
            HTML('<h2 class="card-title text-primary mb-6">'),
            HTML('<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">'),
            HTML('<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>'),
            HTML('</svg>'),
            HTML('Nuevo Reporte de Construcción'),
            HTML('</h2>'),
            Row(
                Column('sitio', css_class='form-control w-full'),
                Column('estructura', css_class='form-control w-full'),
                css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
            ),
            Field('title', css_class='form-control w-full'),
            Field('description', css_class='form-control w-full'),
            HTML('<div class="card-actions justify-end mt-6">'),
            HTML('<a href="{% url "reg_construccion:list" %}" class="btn btn-cancel">Cancelar</a>'),
            Submit('submit', 'Crear Reporte', css_class='btn btn-save'),
            HTML('</div>'),
            HTML('</div>'),
        )
    
    class Meta:
        model = RegConstruccion
        fields = ['sitio', 'estructura', 'title', 'description']

