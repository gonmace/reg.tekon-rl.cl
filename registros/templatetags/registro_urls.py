from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag
def get_registro_url(etapa, registro_id, tipo='form', app_namespace='reg_txtss'):
    """
    Genera la URL para cualquier tipo de vista relacionada con registros.
    
    Args:
        etapa: Nombre de la etapa (sitio, acceso, etc.)
        registro_id: ID del registro
        tipo: Tipo de URL ('form', 'photos', 'edit', etc.)
        
    Returns:
        URL generada o URL por defecto si no existe
    """
    # Mapeo de tipos de URL a patrones de nombres
    url_patterns = {
        'form': f'{app_namespace}:r_{etapa}',
        'photos': f'{app_namespace}:fotos',
        'edit': f'{app_namespace}:edit_{etapa}',
        'delete': f'{app_namespace}:delete_{etapa}',
        'view': f'{app_namespace}:view_{etapa}',
    }
    
    try:
        # Intentar generar la URL usando el patrón específico
        url_name = url_patterns.get(tipo, f'{app_namespace}:{tipo}_{etapa}')
        if tipo == 'photos':
            return reverse(url_name, kwargs={'registro_id': registro_id, 'paso_nombre': etapa})
        else:
            return reverse(url_name, kwargs={'registro_id': registro_id})
    except NoReverseMatch:
        # Si no existe la URL específica, usar el patrón genérico
        if tipo == 'photos':
            return f'/{app_namespace}/{registro_id}/{etapa}/photos/'
        else:
            return f'/{app_namespace}/{registro_id}/{etapa}/'

@register.simple_tag
def get_registro_photos_url(etapa, registro_id, app_namespace='reg_txtss'):
    """
    Genera la URL para las fotos de una etapa específica de registro.
    
    Args:
        etapa: Nombre de la etapa (sitio, acceso, etc.)
        registro_id: ID del registro
        
    Returns:
        URL generada para las fotos
    """
    return get_registro_url(etapa, registro_id, 'photos', app_namespace)

@register.simple_tag
def get_registro_table_url(etapa, registro_id, app_namespace='reg_txtss'):
    """
    Genera la URL para las tablas de una etapa específica de registro.
    
    Args:
        etapa: Nombre de la etapa (sitio, acceso, etc.)
        registro_id: ID del registro
        
    Returns:
        URL generada para las tablas
    """
    # Para las tablas, usar la URL del elemento (formulario) ya que la tabla se muestra en el mismo paso
    return get_registro_url(etapa, registro_id, 'form', app_namespace)

@register.simple_tag
def get_registro_steps_url(registro_id, app_namespace='reg_txtss'):
    """
    Genera la URL para la vista de pasos de un registro.
    
    Args:
        registro_id: ID del registro
        app_namespace: Namespace de la aplicación
        
    Returns:
        URL generada para los pasos
    """
    try:
        return reverse(f'{app_namespace}:steps', kwargs={'registro_id': registro_id})
    except NoReverseMatch:
        return f'/{app_namespace}/{registro_id}/' 