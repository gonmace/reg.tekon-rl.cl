from django import forms
from .models import PasoDefinicion


def _validate_decimal_coord(value):
    if not value:
        return
    try:
        float(value)
    except (TypeError, ValueError):
        raise forms.ValidationError(
            'Ingresa la coordenada en grados decimales (ej: -33.456789), no en formato DMS.'
        )


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
            fields['lat'] = forms.CharField(required=False, label='Latitud', validators=[_validate_decimal_coord])
            fields['lon'] = forms.CharField(required=False, label='Longitud', validators=[_validate_decimal_coord])
        elif slug == 'comentario_widget':
            fields['comentario'] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={'rows': 4}),
                label='Comentario',
            )
        elif slug == 'poste_form_widget':
            cfg = pw.config
            poste_defaults = {
                k: v for k, v in {
                    'tipo_estructura': cfg.get('default_tipo_estructura', ''),
                    'altura': cfg.get('default_altura', ''),
                    'tension': cfg.get('default_tension', ''),
                    'acceso_camion_grua': bool(cfg.get('default_acceso_camion_grua')),
                }.items() if v != '' and v is not False
            }
            merged_initial.update(poste_defaults)
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
            fields['empresa_energia'] = forms.CharField(required=False, label='Empresa de Energía')
            fields['comentario'] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={'rows': 3}),
                label='Comentario',
            )
        elif slug == 'form_dinamico_widget':
            from widgets.widget_types.form_dinamico import parse_campos, django_field
            for campo in parse_campos(pw.config.get('campos', '')):
                fields[campo['nombre']] = django_field(campo)
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
