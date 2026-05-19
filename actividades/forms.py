from django import forms
from .models import PasoDefinicion

_POSTE_DEFAULTS = {
    'tipo_estructura': 'Poste de Hormigón Armado',
    'altura': '13 m',
    'tension': 'Baja Tension',
    'acceso_camion_grua': True,
}


def build_dynamic_form(paso, data=None, initial=None, widget_slug=None):
    """Builds a form for a paso's widgets. If widget_slug is given, only that widget's fields."""
    fields = {}
    merged_initial = {}
    pws = paso.paso_widgets.order_by('orden')
    if widget_slug:
        pws = pws.filter(widget_slug=widget_slug)
    for pw in pws:
        slug = pw.widget_slug
        if slug == 'ubicacion_widget':
            fields['lat'] = forms.CharField(required=False, label='Latitud')
            fields['lon'] = forms.CharField(required=False, label='Longitud')
        elif slug == 'comentario_widget':
            fields['comentario'] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={'rows': 4}),
                label='Comentario',
            )
        elif slug == 'poste_form_widget':
            merged_initial.update(_POSTE_DEFAULTS)
            fields['tipo_estructura'] = forms.CharField(required=True, label='Tipo de Estructura')
            fields['altura'] = forms.CharField(required=True, label='Altura')
            fields['placa_poste'] = forms.CharField(required=False, label='Placa Poste')
            fields['obstaculos'] = forms.CharField(required=False, label='Obstáculos')
            fields['luminaria'] = forms.BooleanField(required=False, label='Luminaria')
            fields['red_protegida'] = forms.BooleanField(required=False, label='Red Protegida')
            fields['acceso_camion_grua'] = forms.BooleanField(required=False, label='Acceso Camión Grúa')
            fields['vegetacion'] = forms.BooleanField(required=False, label='Vegetación')
            fields['antena_microondas'] = forms.BooleanField(required=False, label='Antena Microondas')
            fields['tension'] = forms.CharField(required=True, label='Tensión')
            fields['comentario'] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={'rows': 3}),
                label='Comentario',
            )
    merged_initial.update(initial or {})
    DynamicForm = type('DynamicForm', (forms.BaseForm,), {'base_fields': fields})
    return DynamicForm(data=data, initial=merged_initial)


class PasoDefinicionForm(forms.ModelForm):
    class Meta:
        model = PasoDefinicion
        fields = ('nombre', 'titulo', 'descripcion')
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 2}),
        }
