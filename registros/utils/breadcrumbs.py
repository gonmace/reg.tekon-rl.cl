"""
Utilidades para generar breadcrumbs de manera genérica.
"""

from django.shortcuts import get_object_or_404
from django.urls import reverse, NoReverseMatch


def generate_registro_breadcrumbs(registro_id, paso_nombre=None, registro_model=None, registro_config=None):
    """
    Genera breadcrumbs dinámicos para vistas de registro.
    
    Args:
        registro_id: ID del registro
        paso_nombre: Nombre del paso actual (opcional)
        registro_model: Modelo del registro
        registro_config: Configuración del registro
    
    Returns:
        Lista de breadcrumbs resueltos
    """
    breadcrumbs = [
        {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
    ]
    
    # Determinar el tipo de registro y agregar breadcrumb correspondiente
    if registro_config and hasattr(registro_config, 'title'):
        # Obtener el namespace de la aplicación dinámicamente
        app_namespace = get_app_namespace_from_config(registro_config)
        breadcrumbs.append({
            'label': registro_config.title, 
            'url_name': f'{app_namespace}:list'
        })
    else:
        # Fallback genérico
        breadcrumbs.append({'label': 'Registros', 'url_name': 'reg_txtss:list'})
    
    # Obtener el nombre del sitio del registro
    if registro_id and registro_model:
        try:
            registro = get_object_or_404(registro_model, id=registro_id)
            sitio_cod = get_sitio_codigo(registro)
            
            # Obtener el namespace de la aplicación dinámicamente
            app_namespace = get_app_namespace_from_config(registro_config)
            breadcrumbs.append({
                'label': sitio_cod, 
                'url_name': f'{app_namespace}:steps',
                'url_kwargs': {'registro_id': registro_id}
            })
            
            # Agregar el paso actual si se proporciona
            if paso_nombre and registro_config and hasattr(registro_config, 'pasos'):
                if paso_nombre in registro_config.pasos:
                    paso_config = registro_config.pasos[paso_nombre]
                    breadcrumbs.append({'label': paso_config.title})
            
        except Exception:
            breadcrumbs.append({'label': 'Registro'})
    else:
        breadcrumbs.append({'label': 'Registro'})
    
    return resolve_breadcrumbs(breadcrumbs)


def get_app_namespace_from_config(registro_config):
    """
    Determina el namespace de la aplicación basándose en la configuración.
    
    Args:
        registro_config: Configuración del registro
    
    Returns:
        Namespace de la aplicación (ej: 'registros_txtss', 'registros_obra')
    """
    if not registro_config:
        return 'registros_txtss'  # Fallback
    
    # 1. Verificar si el namespace está configurado directamente
    if hasattr(registro_config, 'app_namespace'):
        return registro_config.app_namespace
    
    # 2. Intentar determinar el namespace basándose en el modelo
    if hasattr(registro_config, 'registro_model'):
        app_label = registro_config.registro_model._meta.app_label
        
        # Mapeo de app_label a namespace
        namespace_mapping = {
            'registros_txtss': 'registros_txtss',
            'registros_obra': 'registros_obra',
            'registros_test': 'registros_test',
            # Agregar más mapeos según sea necesario
        }
        
        namespace = namespace_mapping.get(app_label)
        if namespace:
            return namespace
    
    # 3. Fallback basado en el título
    title = getattr(registro_config, 'title', '').lower()
    if 'txtss' in title or 'tx/tss' in title:
        return 'registros_txtss'
    elif 'obra' in title:
        return 'registros_obra'
    elif 'test' in title:
        return 'registros_test'
    
    return 'registros_txtss'  # Fallback por defecto


def resolve_breadcrumbs(breadcrumb_list):
    """
    Resuelve las URLs de los breadcrumbs.
    
    Args:
        breadcrumb_list: Lista de breadcrumbs con url_name y url_kwargs
    
    Returns:
        Lista de breadcrumbs con URLs resueltas
    """
    resolved = []
    for item in breadcrumb_list:
        url = None
        if 'url_name' in item:
            try:
                # Si hay url_kwargs, usarlos para generar la URL
                if 'url_kwargs' in item:
                    url = reverse(item['url_name'], kwargs=item['url_kwargs'])
                else:
                    url = reverse(item['url_name'])
            except NoReverseMatch:
                url = "#"
        resolved.append({"label": item["label"], "url": url})
    return resolved


def get_sitio_codigo(registro):
    """
    Obtiene el código del sitio de un registro.
    
    Args:
        registro: Instancia del modelo de registro
    
    Returns:
        Código del sitio (pti_cell_id o operator_id)
    """
    try:
        return registro.sitio.pti_cell_id
    except AttributeError:
        try:
            return registro.sitio.operator_id
        except AttributeError:
            return "Sitio" 