from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario usando una clave."""
    return dictionary.get(key)

@register.filter
def range_filter(value):
    """Genera una secuencia de números desde 2 hasta el valor especificado."""
    try:
        return range(2, int(value) + 1)
    except (ValueError, TypeError):
        return range(2, 10)  # Default: 2-9 