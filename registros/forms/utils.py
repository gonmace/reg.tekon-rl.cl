"""
Helper para generar clases CSS de validación visual en campos de formulario.

Convención: solo devuelve clases SEMÁNTICAS de validación (input-success/error/warning,
textarea-success/error/warning). El estilo base (.input, .textarea, etc.) y el ancho
(w-full) los aplica el template/Crispy/CSS central.
"""


def _validation_state(field, field_name=None, form_instance=None):
    """Devuelve 'success' / 'error' / 'warning' según si el campo es requerido y tiene datos."""
    is_required = field.required

    has_data = False
    if form_instance and field_name:
        if hasattr(form_instance, 'instance') and form_instance.instance.pk:
            field_value = getattr(form_instance.instance, field_name, None)
            has_data = field_value not in (None, '')
        elif hasattr(form_instance, 'initial') and field_name in form_instance.initial:
            initial = form_instance.initial[field_name]
            has_data = initial not in (None, '')

    if not is_required:
        return 'warning'
    return 'success' if has_data else 'error'


def get_field_css_class(field, field_name=None, base_class=None, form_instance=None):
    """
    Devuelve la clase de validación adecuada para un campo (sin estilo base).

    Returns:
        str: 'input-success' | 'input-error' | 'input-warning'
             o 'textarea-success' | 'textarea-error' | 'textarea-warning'
    """
    widget_type = type(field.widget).__name__.lower()
    prefix = 'textarea' if 'textarea' in widget_type else 'input'
    state = _validation_state(field, field_name, form_instance)
    return f'{prefix}-{state}'


def get_form_field_css_class(form, field_name, base_class=None):
    """Versión que toma el formulario y el nombre del campo."""
    field = form.fields[field_name]
    return get_field_css_class(field, field_name, base_class, form)


def get_field_css_class_simple(field, base_class=None):
    """Alias compatible con la API previa — sin clases específicas por nombre de campo."""
    return get_field_css_class(field, field_name=None, base_class=base_class)


def get_form_field_css_class_simple(form, field_name, base_class=None):
    """Alias compatible con la API previa."""
    field = form.fields[field_name]
    return get_field_css_class_simple(field, base_class)
