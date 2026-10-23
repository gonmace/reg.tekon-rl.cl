from django import forms
from django.db.models import Q
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button, Div, Field
from .models.sites import Site


TIPO_COORDENADA_CHOICES = [
    ('MAN', 'Mandato'),
    ('ING', 'Ingeniería'),
    ('CON', 'Construcción'),
]
TIPO_TO_FIELDS = {
    'MAN': ('lat_man', 'lon_man'),
    'ING': ('lat_ing', 'lon_ing'),
    'CON': ('lat_con', 'lon_con'),
}


class SiteForm(forms.ModelForm):
    """
    Form de Site con un solo par de inputs lat/lon + un selector que decide
    a cuál par de campos del modelo (mandato/ingeniería/construcción) escribir.
    """

    tipo_coordenada = forms.ChoiceField(
        choices=TIPO_COORDENADA_CHOICES,
        initial='MAN',
        label='Tipo de coordenada',
    )
    lat = forms.FloatField(
        required=False,
        label='Latitud',
        widget=forms.NumberInput(attrs={'step': 'any'}),
    )
    lon = forms.FloatField(
        required=False,
        label='Longitud',
        widget=forms.NumberInput(attrs={'step': 'any'}),
    )

    class Meta:
        model = Site
        fields = ['pti_cell_id', 'operator_id', 'name', 'tipo_sitio', 'tipo_estructura', 'alt', 'region', 'comuna']
        labels = {
            'alt': 'Altura (m)',
            'tipo_estructura': 'Tipo de estructura',
            'region': 'Región',
            'comuna': 'Comuna',
            'pti_cell_id': 'PTI ID',
            'operator_id': 'Operador ID',
            'name': 'Nombre Sitio',
            'tipo_sitio': 'Tipo de sitio',
        }
        widgets = {
            # Sin clases custom — crispy-daisyui aplica el estilo estándar.
            # Duplicar 'class' rompe el render (HTML inválido).
        }

    def __init__(self, *args, visita=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.visita = visita

        # En edición, precargar lat/lon del Mandato (default del selector)
        if self.instance and self.instance.pk:
            self.fields['lat'].initial = self.instance.lat_man
            self.fields['lon'].initial = self.instance.lon_man

        self.helper = FormHelper()
        self.helper.form_tag = False  # el <form> lo provee el template wrapper
        self.helper.label_class = 'text-sm text-base-content'
        self.helper.field_class = 'mb-2'
        self.helper.layout = Layout(
            Div(
                Div(Field('pti_cell_id'), css_class='w-1/2 md:w-1/3 px-2'),
                Div(Field('operator_id'), css_class='w-1/2 md:w-1/3 px-2'),
                Div(Field('alt'), css_class='w-1/2 md:w-1/3 px-2'),
                css_class='flex flex-wrap -mx-2 mb-4',
            ),
            Div(
                Div(Field('tipo_estructura'), css_class='w-full px-2'),
                css_class='flex flex-wrap -mx-2 mb-4',
            ),
            Div(
                Div(Field('name'), css_class='w-full md:w-2/3 px-2'),
                Div(Field('tipo_sitio'), css_class='w-full md:w-1/3 px-2'),
                css_class='flex flex-wrap items-end -mx-2 mb-4',
            ),
            Div(
                Div(Field('region'), css_class='w-full md:w-1/2 px-2'),
                Div(Field('comuna'), css_class='w-full md:w-1/2 px-2'),
                css_class='flex flex-wrap -mx-2 mb-4',
            ),
            # Coordenadas: un solo par lat/lon + selector de tipo
            Div(
                Div(Field('tipo_coordenada'), css_class='w-full md:w-1/3 px-2'),
                Div(Field('lat'), css_class='w-1/2 md:w-1/3 px-2'),
                Div(Field('lon'), css_class='w-1/2 md:w-1/3 px-2'),
                css_class='flex flex-wrap -mx-2 mb-4',
            ),
            Div(
                Button('cancel', 'Cancelar', css_class='btn btn-cancel mt-6', type='button', onclick='closeModal()'),
                Submit('submit', 'Guardar', css_class='btn btn-save flex-grow mt-6'),
                css_class='flex gap-2 justify-center',
            ),
        )

        # Contratista: vive en la visita (no en el sitio); se edita sobre la última visita.
        if visita is not None:
            from .models.contractors import Contractor
            self.fields['contratista'] = forms.ModelChoiceField(
                queryset=Contractor.objects.filter(
                    Q(is_active=True, is_deleted=False) | Q(pk=visita.contratista_id)).order_by('name'),
                required=False,
                initial=visita.contratista_id, label='Contratista (último reporte)',
                empty_label='— Sin contratista —',
            )
            self.helper.layout.insert(-1, Div(
                Div(Field('contratista'), css_class='w-full px-2'),
                css_class='flex flex-wrap -mx-2 mb-4',
            ))

    # ModelForm omite las restricciones únicas condicionales cuando el campo de la
    # condición (is_deleted) no está en el formulario; se valida explícitamente aquí.
    def _unico_entre_activos(self, campo, mensaje):
        valor = self.cleaned_data.get(campo)
        if valor in (None, ''):
            return valor
        qs = Site.objects.filter(is_deleted=False, **{campo: valor})
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(mensaje)
        return valor

    def clean_pti_cell_id(self):
        return self._unico_entre_activos('pti_cell_id', 'Ya existe un sitio activo con este PTI ID.')

    def clean_name(self):
        return self._unico_entre_activos('name', 'Ya existe un sitio activo con este nombre.')

    def save(self, commit=True):
        site = super().save(commit=False)
        tipo = self.cleaned_data.get('tipo_coordenada') or 'MAN'
        lat = self.cleaned_data.get('lat')
        lon = self.cleaned_data.get('lon')
        lat_field, lon_field = TIPO_TO_FIELDS.get(tipo, ('lat_man', 'lon_man'))
        setattr(site, lat_field, lat)
        setattr(site, lon_field, lon)
        if commit:
            site.save()
            if self.visita is not None and 'contratista' in self.cleaned_data:
                nuevo = self.cleaned_data['contratista']
                if (nuevo.pk if nuevo else None) != self.visita.contratista_id:
                    self.visita.contratista = nuevo
                    self.visita.save(update_fields=['contratista'])
        return site
