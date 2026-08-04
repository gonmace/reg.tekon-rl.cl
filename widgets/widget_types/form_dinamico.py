import re

from django import forms

from widgets.base import WidgetBase
from widgets.registry import register_widget

TIPOS_VALIDOS = {'text', 'textarea', 'toggle', 'number', 'date', 'select'}

# Nombres ya usados por otros widgets de tipo form que comparten DatoPaso.datos
# de forma plana (ver actividades/forms.py::build_dynamic_form).
RESERVED_NAMES = {
    'lat', 'lon',
    'comentario',
    'tipo_estructura', 'altura', 'tension', 'placa_poste', 'obstaculos',
    'empresa_energia', 'luminaria', 'red_protegida', 'acceso_camion_grua',
    'vegetacion', 'antena_microondas',
}

_NOMBRE_RE = re.compile(r'^[a-z0-9_]+$')


def _split_lines(raw):
    """Divide el DSL en líneas de campo, aceptando ';' y '\n' como separador de campos."""
    if not raw:
        return []
    normalized = str(raw).replace(';', '\n')
    lines = [l.strip() for l in normalized.splitlines()]
    return [l for l in lines if l and not l.startswith('#')]


def _split_columns(line):
    return [p.strip() for p in line.split('|')]


def parse_campos(raw: str) -> list:
    """
    Parsea el DSL 'campos' en una lista de dicts:
    {nombre, tipo, label, placeholder, opciones, required, imagen, ayuda}

    'imagen' es el slug de una ImagenEjemplo (6ª columna, opcional) que se
    muestra como ejemplo visual justo debajo de ese campo, no de todo el widget.
    'ayuda' es un texto de instrucciones libre (7ª columna, opcional) que se
    muestra debajo del campo independientemente de si tiene imagen o no.

    Líneas mal formadas (nombre inválido o tipo desconocido) se descartan en
    silencio — para reportar errores usar validate_campos_config().
    """
    campos = []
    for line in _split_lines(raw):
        parts = _split_columns(line)
        nombre = parts[0] if parts else ''
        if not _NOMBRE_RE.match(nombre):
            continue
        tipo = parts[1].strip().lower() if len(parts) > 1 and parts[1].strip() else 'text'
        if tipo not in TIPOS_VALIDOS:
            continue
        label = parts[2].strip() if len(parts) > 2 and parts[2].strip() else nombre.replace('_', ' ').capitalize()
        extra = parts[3].strip() if len(parts) > 3 else ''
        required = len(parts) > 4 and parts[4].strip() == '*'
        imagen = parts[5].strip() if len(parts) > 5 else ''
        ayuda = parts[6].strip() if len(parts) > 6 else ''
        campo = {
            'nombre': nombre, 'tipo': tipo, 'label': label, 'required': required,
            'imagen': imagen, 'ayuda': ayuda,
        }
        if tipo == 'select':
            campo['opciones'] = [o.strip() for o in extra.split(',') if o.strip()]
            campo['placeholder'] = ''
        else:
            campo['opciones'] = []
            campo['placeholder'] = extra
        campos.append(campo)
    return campos


def validate_campos_config(raw: str) -> list:
    """Valida el DSL completo y devuelve una lista de mensajes de error (vacía si es válido)."""
    from widgets.models import ImagenEjemplo

    errors = []
    seen = set()
    for i, line in enumerate(_split_lines(raw), start=1):
        parts = _split_columns(line)
        nombre = parts[0] if parts else ''
        if not _NOMBRE_RE.match(nombre):
            errors.append(f"Línea {i}: nombre de campo inválido ('{nombre}'). Usa minúsculas, números y guion bajo.")
            continue
        if nombre in RESERVED_NAMES:
            errors.append(f"Línea {i}: '{nombre}' es un nombre reservado, usa otro.")
        if nombre in seen:
            errors.append(f"Línea {i}: el campo '{nombre}' está duplicado.")
        seen.add(nombre)

        tipo = parts[1].strip().lower() if len(parts) > 1 and parts[1].strip() else 'text'
        if tipo not in TIPOS_VALIDOS:
            errors.append(f"Línea {i}: tipo '{tipo}' inválido. Usa: {', '.join(sorted(TIPOS_VALIDOS))}.")
            continue
        if tipo == 'select':
            extra = parts[3].strip() if len(parts) > 3 else ''
            opciones = [o.strip() for o in extra.split(',') if o.strip()]
            if not opciones:
                errors.append(f"Línea {i}: el campo select '{nombre}' necesita opciones separadas por coma.")

        imagen = parts[5].strip() if len(parts) > 5 else ''
        if imagen and not ImagenEjemplo.objects.filter(slug=imagen).exists():
            errors.append(f"Línea {i}: no existe una Imagen de ejemplo con slug '{imagen}'.")
    return errors


def django_field(campo: dict) -> forms.Field:
    """Traduce un campo del DSL a un forms.Field. Nunca usa DateField/DecimalField
    (no son serializables en el JSONField de DatoPaso.datos)."""
    tipo = campo['tipo']
    required = campo.get('required', False)
    label = campo.get('label', campo['nombre'])
    placeholder = campo.get('placeholder', '')

    if tipo == 'textarea':
        attrs = {'rows': 3}
        if placeholder:
            attrs['placeholder'] = placeholder
        return forms.CharField(required=required, label=label, widget=forms.Textarea(attrs=attrs))
    if tipo == 'toggle':
        return forms.BooleanField(required=False, label=label)
    if tipo == 'number':
        return forms.FloatField(required=required, label=label)
    if tipo == 'select':
        choices = [(o, o) for o in campo.get('opciones', [])]
        return forms.ChoiceField(required=required, label=label, choices=choices)
    # 'text' y 'date' (date se guarda como texto libre, no forms.DateField)
    attrs = {'placeholder': placeholder} if placeholder else {}
    return forms.CharField(required=required, label=label, widget=forms.TextInput(attrs=attrs))


@register_widget
class FormDinamicoWidget(WidgetBase):
    slug = "form_dinamico_widget"
    nombre = "Formulario Dinámico"
    icon = "fa-solid fa-list-check"

    def validate_config(self, config):
        return validate_campos_config(config.get('campos', ''))

    def validate_data(self, data):
        return []

    def completeness(self, data):
        # Fallback sin config disponible (ver completeness_with_config).
        return 0 if not data else 3

    def completeness_with_config(self, data, config):
        campos = parse_campos(config.get('campos', ''))
        if not campos:
            return 0
        total = len(campos)
        filled = 0
        for c in campos:
            if c['tipo'] == 'toggle':
                # Un toggle nunca tocado no aparece como clave en data. False sí es
                # una respuesta válida, pero solo cuenta una vez que se guardó.
                is_filled = c['nombre'] in data
            else:
                val = data.get(c['nombre'])
                is_filled = val not in (None, '')
            if is_filled:
                filled += 1
        if filled == 0:
            return 1
        return 3 if filled == total else 2

    def to_display(self, data, config):
        campos = parse_campos(config.get('campos', ''))
        items = []
        for c in campos:
            val = data.get(c['nombre'])
            if c['tipo'] == 'toggle':
                valor = ('Sí' if val else 'No') if c['nombre'] in data else 'Sin responder'
            else:
                valor = val if val not in (None, '') else ''
            items.append({'label': c['label'], 'valor': valor, 'tipo': c['tipo']})
        return {
            'label': config.get('label', self.nombre),
            'campos': items,
            'is_empty': not any(data.get(c['nombre']) for c in campos),
        }
