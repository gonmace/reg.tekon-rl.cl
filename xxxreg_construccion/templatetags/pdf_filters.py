from django import template

register = template.Library()

@register.filter
def get_item(list_obj, index):
    """Filtro para obtener un elemento de una lista por índice"""
    try:
        return list_obj[index]
    except (IndexError, TypeError):
        return 0

@register.filter
def get_progress_class(percentage):
    """Filtro para obtener la clase CSS basada en el porcentaje de progreso"""
    try:
        value = float(percentage)
        if value >= 90:
            return 'alto'
        elif value >= 50:
            return 'medio'
        else:
            return 'bajo'
    except (ValueError, TypeError):
        return 'bajo'
