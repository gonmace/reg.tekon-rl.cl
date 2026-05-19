from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def dict_get(d, key):
    """{{ my_dict|dict_get:variable_key }}"""
    if isinstance(d, dict):
        return d.get(key, '')
    return ''


@register.simple_tag(takes_context=True)
def render_widget(context, widget):
    """Renders a widget template with its config merged into context."""
    from django.template.loader import get_template
    tpl = get_template(widget.template_path)
    ctx = dict(context.flatten())
    ctx.update(widget.config)
    ctx['widget'] = widget

    # BoundFields para ubicacion_widget
    form = ctx.get('form')
    if form and hasattr(form, 'fields'):
        for fname in ('lat', 'lon'):
            if fname in form.fields:
                ctx[f'{fname}_field'] = form[fname]

    # Pre-población de value para comentario_widget
    datos = ctx.get('datos', {})
    field_name = widget.config.get('name', widget.widget_slug.replace('_widget', ''))
    if field_name in datos:
        ctx.setdefault('value', datos[field_name])

    # Normalizar descripciones de string CSV a lista
    if 'descripciones' in ctx and isinstance(ctx['descripciones'], str):
        ctx['descripciones'] = [d.strip() for d in ctx['descripciones'].split(',') if d.strip()]

    return mark_safe(tpl.render(ctx))
