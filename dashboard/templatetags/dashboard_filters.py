from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Obtiene un elemento de un diccionario por clave"""
    return dictionary.get(key, 0)
