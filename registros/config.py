"""
Configuración genérica para aplicaciones de registros.
"""

from registros.components.registro_config import RegistroConfig, PasoConfig, ElementoConfig, SubElementoConfig
from typing import Dict, Any, Type, Optional, List
from django.db import models
from photos.views import set_photos_template_for_step


# ============================================================================
# CONFIGURACIONES DE MAPA
# ============================================================================

def create_single_point_map_config(
    lat_field: str = 'lat',
    lon_field: str = 'lon',
    name_field: str = 'name',
    zoom: int = 20,
    template_name: str = 'components/mapa.html',  # Template extraído de step_generic.html
    css_classes: str = 'mapa-container',
    icon_color: str = 'red',
    icon_size: str = 'normal',
    icon_type: str = 'marker'
) -> SubElementoConfig:
    """
    Crea configuración para un mapa con un solo punto (coordenadas del modelo principal).
    
    Args:
        lat_field: Campo de latitud del modelo
        lon_field: Campo de longitud del modelo
        name_field: Campo de nombre del modelo
        zoom: Nivel de zoom del mapa
        template_name: Template del mapa
        css_classes: Clases CSS para el contenedor
        icon_color: Color del icono (red, blue, green, yellow, etc.)
        icon_size: Tamaño del icono (tiny, small, normal, mid, large)
        icon_type: Tipo de icono (marker, circle, etc.)
    
    Returns:
        SubElementoConfig configurado para mapa de punto único
    """
    map_config = {
        'lat_field': lat_field,
        'lon_field': lon_field,
        'name_field': name_field,
        'zoom': zoom,
        'type': 'single_point',
        'icon_config': {
            'color': icon_color,
            'size': icon_size,
            'type': icon_type
        }
    }
    
    return SubElementoConfig(
        tipo='mapa',
        config=map_config,
        template_name=template_name,
        css_classes=css_classes
    )


def create_1_point_map_config(
    model_class1='current',
    lat1='lat',
    lon1='lon', 
    name1='name',
    zoom=20,
    template_name='components/mapa.html',  # Template extraído de step_generic.html
    css_classes='mapa-container',
    # Configuración de iconos para el primer modelo
    icon1_color='red',
    icon1_size='normal',
    icon1_type='marker'
) -> SubElementoConfig:
    """
    Crea configuración para un mapa con un solo punto.
    
    Args:
        model_class1: Clase del primer modelo o 'current' para el modelo actual
        lat1: Campo de latitud del primer modelo
        lon1: Campo de longitud del primer modelo
        name1: Campo de nombre del primer modelo
        zoom: Nivel de zoom del mapa
        template_name: Template del mapa
        css_classes: Clases CSS para el contenedor
        icon1_color: Color del icono del primer modelo (red, blue, green, yellow, etc.)
        icon1_size: Tamaño del icono del primer modelo (tiny, small, normal, mid, large)
        icon1_type: Tipo de icono del primer modelo (marker, circle, etc.)
    
    Returns:
        SubElementoConfig configurado para mapa de un punto
    """
    map_config = {
        'lat_field': lat1,
        'lon_field': lon1,
        'name_field': name1,
        'zoom': zoom,
        'type': 'single_point',
        'icon_config': {
            'color': icon1_color,
            'size': icon1_size,
            'type': icon1_type
        }
    }
    
    return SubElementoConfig(
        tipo='mapa',
        config=map_config,
        template_name=template_name,
        css_classes=css_classes
    )


def create_2_point_map_config(
    model_class1='current',
    lat1='lat',
    lon1='lon', 
    name1='name',
    model_class2=None,
    lat2='lat',
    lon2='lon', 
    name2='name',
    second_model_relation_field='registro',
    descripcion_distancia='Distancia entre puntos',
    zoom=15,
    template_name='components/mapa.html',  # Template extraído de step_generic.html
    css_classes='mapa-container',
    # Configuración de iconos para el primer modelo
    icon1_color='red',
    icon1_size='normal',
    icon1_type='marker',
    # Configuración de iconos para el segundo modelo
    icon2_color='blue',
    icon2_size='normal',
    icon2_type='marker',
    distancia=False,
    template_datos_clave=None
) -> SubElementoConfig:
    """
    Crea configuración para un mapa con dos puntos (modelo principal + segundo modelo).
    
    Args:
        model_class1: Clase del primer modelo o 'current' para el modelo actual
        lat1: Campo de latitud del primer modelo
        lon1: Campo de longitud del primer modelo
        name1: Campo de nombre del primer modelo
        model_class2: Clase del segundo modelo para el mapa
        lat2: Campo de latitud del segundo modelo
        lon2: Campo de longitud del segundo modelo
        name2: Campo de nombre del segundo modelo
        second_model_relation_field: Campo de relación con el registro (FK)
        descripcion_distancia: Descripción para el cálculo de distancia
        zoom: Nivel de zoom del mapa
        template_name: Template del mapa
        css_classes: Clases CSS para el contenedor
        icon1_color: Color del icono del primer modelo (red, blue, green, yellow, etc.)
        icon1_size: Tamaño del icono del primer modelo (tiny, small, normal, mid, large)
        icon1_type: Tipo de icono del primer modelo (marker, circle, etc.)
        icon2_color: Color del icono del segundo modelo
        icon2_size: Tamaño del icono del segundo modelo
        icon2_type: Tipo de icono del segundo modelo
        distancia: Si True, calcular la distancia entre las dos primeras coordenadas usando geopy
        template_datos_clave: Template para datos clave adicionales (opcional)
    
    Returns:
        SubElementoConfig configurado para mapa de dos puntos
    """
    map_config = {
        'lat_field': lat1,
        'lon_field': lon1,
        'name_field': name1,
        'zoom': zoom,
        'type': 'two_point',
        'icon_config': {
            'color': icon1_color,
            'size': icon1_size,
            'type': icon1_type
        }
    }
    
    # Agregar configuración del segundo modelo si se proporciona
    if model_class2:
        map_config.update({
            'second_model': {
                'model_class': model_class2,
                'lat_field': lat2,
                'lon_field': lon2,
                'name_field': name2,
                'relation_field': second_model_relation_field,
                'icon_config': {
                    'color': icon2_color,
                    'size': icon2_size,
                    'type': icon2_type
                }
            },
            'descripcion_distancia': descripcion_distancia
        })
    if distancia:
        map_config['calcular_distancia'] = True
    
    return SubElementoConfig(
        tipo='mapa',
        config=map_config,
        template_name=template_name,
        css_classes=css_classes,
        template_datos_clave=template_datos_clave
    )


def create_3_point_map_config(
    model_class1='current',
    lat1='lat',
    lon1='lon', 
    name1='name',
    model_class2=None,
    lat2='lat',
    lon2='lon', 
    name2='name',
    model_class3=None,
    lat3='lat',
    lon3='lon', 
    name3='name',
    second_model_relation_field='registro',
    third_model_relation_field='registro',
    descripcion_distancia='Distancia entre puntos',
    zoom=15,
    template_name='components/mapa.html',  # Template extraído de step_generic.html
    css_classes='mapa-container',
    # Configuración de iconos para el primer modelo
    icon1_color='red',
    icon1_size='normal',
    icon1_type='marker',
    # Configuración de iconos para el segundo modelo
    icon2_color='blue',
    icon2_size='normal',
    icon2_type='marker',
    # Configuración de iconos para el tercer modelo
    icon3_color='green',
    icon3_size='normal',
    icon3_type='marker',
    distancia=False,
    template_datos_clave=None
) -> SubElementoConfig:
    """
    Crea configuración para un mapa con tres puntos (modelo principal + segundo modelo + tercer modelo).
    
    Args:
        model_class1: Clase del primer modelo o 'current' para el modelo actual
        lat1: Campo de latitud del primer modelo
        lon1: Campo de longitud del primer modelo
        name1: Campo de nombre del primer modelo
        model_class2: Clase del segundo modelo para el mapa
        lat2: Campo de latitud del segundo modelo
        lon2: Campo de longitud del segundo modelo
        name2: Campo de nombre del segundo modelo
        model_class3: Clase del tercer modelo para el mapa
        lat3: Campo de latitud del tercer modelo
        lon3: Campo de longitud del tercer modelo
        name3: Campo de nombre del tercer modelo
        second_model_relation_field: Campo de relación con el registro (FK) para el segundo modelo
        third_model_relation_field: Campo de relación con el registro (FK) para el tercer modelo
        descripcion_distancia: Descripción para el cálculo de distancia
        zoom: Nivel de zoom del mapa
        template_name: Template del mapa
        css_classes: Clases CSS para el contenedor
        icon1_color: Color del icono del primer modelo (red, blue, green, yellow, etc.)
        icon1_size: Tamaño del icono del primer modelo (tiny, small, normal, mid, large)
        icon1_type: Tipo de icono del primer modelo (marker, circle, etc.)
        icon2_color: Color del icono del segundo modelo
        icon2_size: Tamaño del icono del segundo modelo
        icon2_type: Tipo de icono del segundo modelo
        icon3_color: Color del icono del tercer modelo
        icon3_size: Tamaño del icono del tercer modelo
        icon3_type: Tipo de icono del tercer modelo
        distancia: Si True, calcular la distancia entre las dos primeras coordenadas usando geopy
        template_datos_clave: Template para datos clave adicionales (opcional)
    
    Returns:
        SubElementoConfig configurado para mapa de tres puntos
    """
    map_config = {
        'lat_field': lat1,
        'lon_field': lon1,
        'name_field': name1,
        'zoom': zoom,
        'type': 'three_point',
        'icon_config': {
            'color': icon1_color,
            'size': icon1_size,
            'type': icon1_type
        }
    }
    
    # Agregar configuración del segundo modelo si se proporciona
    if model_class2:
        map_config.update({
            'second_model': {
                'model_class': model_class2,
                'lat_field': lat2,
                'lon_field': lon2,
                'name_field': name2,
                'relation_field': second_model_relation_field,
                'icon_config': {
                    'color': icon2_color,
                    'size': icon2_size,
                    'type': icon2_type
                }
            }
        })
    
    # Agregar configuración del tercer modelo si se proporciona
    if model_class3:
        map_config.update({
            'third_model': {
                'model_class': model_class3,
                'lat_field': lat3,
                'lon_field': lon3,
                'name_field': name3,
                'relation_field': third_model_relation_field,
                'icon_config': {
                    'color': icon3_color,
                    'size': icon3_size,
                    'type': icon3_type
                }
            }
        })
    
    if descripcion_distancia:
        map_config['descripcion_distancia'] = descripcion_distancia
    if distancia:
        map_config['calcular_distancia'] = True
    
    return SubElementoConfig(
        tipo='mapa',
        config=map_config,
        template_name=template_name,
        css_classes=css_classes,
        template_datos_clave=template_datos_clave
    )


# ============================================================================
# CONFIGURACIONES DE FOTOS
# ============================================================================

def create_photos_config(
    photo_min: int = 4,
    allowed_types: List[str] = ['image/jpeg', 'image/png'],
    photos_template: str = 'widgets/camera_widget_page.html',
    css_classes: str = 'fotos-container',
    target_model: str = None
) -> SubElementoConfig:
    """
    Crea configuración para sub-elemento de fotos.
    
    Args:
        photo_min: Número mínimo de fotos requeridas
        allowed_types: Tipos de archivo permitidos
        photos_template: Template para las fotos
        css_classes: Clases CSS para el contenedor
        target_model: Modelo específico al que asociar las fotos (opcional)
    
    Returns:
        SubElementoConfig configurado para fotos
    """
    
    config = {
        'min_files': photo_min,
        'allowed_types': allowed_types
    }
    
    if target_model:
        config['target_model'] = target_model
    
    return SubElementoConfig(
        tipo='fotos',
        config=config,
        template_name=photos_template,
        css_classes=css_classes
    )


def create_table_config(
    table_title: str = "Tabla de Datos",
    table_template: str = 'components/sub_elemento_table.html',
    css_classes: str = 'table-container',
    data_source: str = None,
    fields_to_show: List[str] = None,
    table_model_class: Type[models.Model] = None,
    table_form_class: Type = None
) -> SubElementoConfig:
    """
    Crea configuración para sub-elemento de tabla.
    
    Args:
        table_title: Título de la tabla
        table_template: Template para la tabla (ruta: 'components/sub_elemento_table.html')
        css_classes: Clases CSS para el contenedor
        data_source: Fuente de datos para la tabla (opcional)
        fields_to_show: Lista de campos a mostrar (opcional)
        table_model_class: Modelo específico para la tabla (opcional, para tablas con datos propios)
        table_form_class: Formulario específico para la tabla (opcional, para tablas editables)
    
    Template requerido:
        - Ruta: 'components/sub_elemento_table.html'
        - Debe existir en: registros/templates/components/sub_elemento_table.html
    
    Returns:
        SubElementoConfig configurado para tabla
    """
    
    config = {
        'title': table_title,
        'data_source': data_source,
        'fields_to_show': fields_to_show or []
    }
    
    # Agregar modelo y formulario específicos de la tabla si se proporcionan
    if table_model_class:
        config['table_model_class'] = table_model_class
    if table_form_class:
        config['table_form_class'] = table_form_class
    
    return SubElementoConfig(
        tipo='table',
        config=config,
        template_name=table_template,
        css_classes=css_classes
    )


# ============================================================================
# CONFIGURACIONES DE TABLA EDITABLE
# ============================================================================

def create_editable_table_config(
    model_class: Type[models.Model],
    title: str,
    description: str,
    columns: List[Dict[str, Any]],
    template_name: str = 'components/editable_table.html',
    success_message: str = None,
    error_message: str = None,
    page_length: int = 10,
    allow_create: bool = True,
    allow_delete: bool = True,
    allow_edit: bool = True,
    api_url: str = None
) -> SubElementoConfig:
    """
    Crea configuración para una tabla editable con AJAX.
    
    Args:
        model_class: Clase del modelo para la tabla
        title: Título de la tabla
        description: Descripción de la tabla
        columns: Lista de columnas con configuración
        template_name: Template para la tabla
        success_message: Mensaje de éxito personalizado
        error_message: Mensaje de error personalizado
        page_length: Número de registros por página
        allow_create: Si permite crear nuevos registros
        allow_delete: Si permite eliminar registros
        allow_edit: Si permite editar registros
        api_url: URL de la API para operaciones CRUD
    
    Returns:
        SubElementoConfig configurado para tabla editable
    """
    if success_message is None:
        success_message = f"Datos de {title.lower()} guardados exitosamente."
    if error_message is None:
        error_message = f"Error al guardar los datos de {title.lower()}."
    
    table_config = {
        'model_class': model_class,
        'columns': columns,
        'page_length': page_length,
        'allow_create': allow_create,
        'allow_delete': allow_delete,
        'allow_edit': allow_edit,
        'api_url': api_url
    }
    
    return SubElementoConfig(
        tipo='editable_table',
        config=table_config,
        template_name=template_name,
        css_classes='editable-table-container',
        title=title,
        description=description,
        success_message=success_message,
        error_message=error_message
    )


def create_table_only_config(
    title: str,
    description: str,
    columns: List[Dict[str, Any]],
    model_class: Type[models.Model] = None,
    template_name: str = 'components/editable_table.html',
    sub_elementos: List[SubElementoConfig] = None,
    success_message: str = None,
    error_message: str = None,
    page_length: int = 10,
    allow_create: bool = True,
    allow_delete: bool = True,
    allow_edit: bool = True,
    api_url: str = None
) -> PasoConfig:
    """
    Crea una configuración de paso que solo muestra una tabla editable.
    
    Args:
        title: Título del paso
        description: Descripción del paso
        columns: Lista de columnas con configuración
        model_class: Clase del modelo para la tabla (opcional)
        template_name: Template para la tabla
        sub_elementos: Lista de sub-elementos adicionales
        success_message: Mensaje de éxito personalizado
        error_message: Mensaje de error personalizado
        page_length: Número de registros por página
        allow_create: Si permite crear nuevos registros
        allow_delete: Si permite eliminar registros
        allow_edit: Si permite editar registros
        api_url: URL de la API para operaciones CRUD
    
    Returns:
        PasoConfig configurado para tabla editable
    """
    table_config = create_editable_table_config(
        model_class=model_class,
        title=title,
        description=description,
        columns=columns,
        template_name=template_name,
        success_message=success_message,
        error_message=error_message,
        page_length=page_length,
        allow_create=allow_create,
        allow_delete=allow_delete,
        allow_edit=allow_edit,
        api_url=api_url
    )
    
    # Agregar la tabla a los sub_elementos
    all_sub_elementos = [table_config]
    if sub_elementos:
        all_sub_elementos.extend(sub_elementos)
    
    # Crear un elemento config sin modelo ni formulario
    elemento = ElementoConfig(
        nombre='table_only',
        model=model_class,  # Puede ser None
        form_class=None,  # Sin formulario
        title=title,
        description=description,
        template_name=template_name,
        success_message=success_message or "Tabla actualizada correctamente.",
        error_message=error_message or "Error al actualizar la tabla.",
        sub_elementos=all_sub_elementos
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


# ============================================================================
# CONFIGURACIONES DE ELEMENTOS BASE
# ============================================================================

def create_base_element_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str,
    template_form: str = 'components/elemento_form.html',
    success_message: str = None,
    error_message: str = None,
    sub_elementos: List[SubElementoConfig] = None
) -> ElementoConfig:
    """
    Crea configuración base de un elemento.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        template_form: Template para el formulario
        success_message: Mensaje de éxito personalizado
        error_message: Mensaje de error personalizado
        sub_elementos: Lista de sub-elementos (mapa, fotos, etc.)
    
    Returns:
        ElementoConfig configurado
    """
    if success_message is None:
        success_message = f"Datos de {title.lower()} guardados exitosamente."
    if error_message is None:
        error_message = f"Error al guardar los datos de {title.lower()}."
    
    return ElementoConfig(
        nombre=title.lower(),
        model=model_class,
        form_class=form_class,
        title=title,
        description=description,
        template_name=template_form,
        success_message=success_message,
        error_message=error_message,
        sub_elementos=sub_elementos or []
    )


# ============================================================================
# CONFIGURACIONES DE PASOS ESPECÍFICOS
# ============================================================================

def create_simple_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str
) -> PasoConfig:
    """
    Crea una configuración de paso simple solo con formulario.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
    
    Returns:
        PasoConfig configurado
    """
    elemento = create_base_element_config(
        model_class=model_class,
        form_class=form_class,
        title=title,
        description=description
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


def create_map_only_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str,
    lat_field: str = 'lat',
    lon_field: str = 'lon',
    name_field: str = 'name',
    zoom: int = 20,
    template_form: str = 'components/elemento_form.html',
    map_template: str = 'components/mapa.html'
) -> PasoConfig:
    """
    Crea una configuración de paso con formulario y mapa de un solo punto.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        lat_field: Campo de latitud del modelo
        lon_field: Campo de longitud del modelo
        name_field: Campo de nombre del modelo
        zoom: Nivel de zoom del mapa
        template_form: Template para el formulario
        map_template: Template para el mapa
    
    Returns:
        PasoConfig configurado
    """
    map_config = create_single_point_map_config(
        lat_field=lat_field,
        lon_field=lon_field,
        name_field=name_field,
        zoom=zoom,
        template_name=map_template
    )
    
    elemento = create_base_element_config(
        model_class=model_class,
        form_class=form_class,
        title=title,
        description=description,
        template_form=template_form,
        sub_elementos=[map_config]
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


def create_photo_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str,
    photo_min: int = 4,
    photos_template: str = 'widgets/camera_widget_page.html'
) -> PasoConfig:
    """
    Crea una configuración de paso simple con fotos.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        photo_min: Número mínimo de fotos requeridas
        photos_template: Template para las fotos
    
    Returns:
        PasoConfig configurado
    """
    # Configurar el template de ListPhotosView dinámicamente
    set_photos_template_for_step(title.lower(), photos_template)
    
    photos_config = create_photos_config(
        photo_min=photo_min,
        photos_template=photos_template
    )
    
    elemento = create_base_element_config(
        model_class=model_class,
        form_class=form_class,
        title=title,
        description=description,
        sub_elementos=[photos_config]
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


def create_photo_map_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str,
    photo_min: int = 4,
    template_form: str = 'components/elemento_form.html',
    photos_template: str = 'widgets/camera_widget_page.html',
    # Parámetros para el mapa
    lat_field: str = 'lat',
    lon_field: str = 'lon',
    name_field: str = 'name',
    zoom: int = 20,
    # Parámetros para mapa con dos modelos
    second_model_class: Type[models.Model] = None,
    second_model_lat_field: str = 'lat',
    second_model_lon_field: str = 'lon',
    second_model_name_field: str = 'name',
    second_model_relation_field: str = None,
    descripcion_distancia: str = 'Distancia entre puntos'
) -> PasoConfig:
    """
    Crea una configuración de paso para sitio con mapa y fotos.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        photo_min: Número mínimo de fotos requeridas
        template_form: Template para el formulario
        photos_template: Template para las fotos
        lat_field: Campo de latitud del modelo principal
        lon_field: Campo de longitud del modelo principal
        name_field: Campo de nombre del modelo principal
        zoom: Nivel de zoom del mapa
        second_model_class: Clase del segundo modelo para el mapa
        second_model_lat_field: Campo de latitud del segundo modelo
        second_model_lon_field: Campo de longitud del segundo modelo
        second_model_name_field: Campo de nombre del segundo modelo
        second_model_relation_field: Campo de relación con el registro (FK)
        descripcion_distancia: Descripción para el cálculo de distancia
    
    Returns:
        PasoConfig configurado
    """
    # Configurar el template de ListPhotosView dinámicamente
    set_photos_template_for_step(title.lower(), photos_template)
    
    # Crear configuración de mapa
    if second_model_class:
        map_config = create_2_point_map_config(
            model_class1=model_class,
            lat1=lat_field,
            lon1=lon_field,
            name1=name_field,
            model_class2=second_model_class,
            lat2=second_model_lat_field,
            lon2=second_model_lon_field,
            name2=second_model_name_field,
            second_model_relation_field=second_model_relation_field,
            descripcion_distancia=descripcion_distancia
        )
    else:
        map_config = create_single_point_map_config(
            lat_field=lat_field,
            lon_field=lon_field,
            name_field=name_field,
            zoom=zoom
        )
    
    # Crear configuración de fotos
    photos_config = create_photos_config(
        photo_min=photo_min,
        photos_template=photos_template
    )
    
    elemento = create_base_element_config(
        model_class=model_class,
        form_class=form_class,
        title=title,
        description=description,
        template_form=template_form,
        sub_elementos=[map_config, photos_config]
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


# ============================================================================
# CONFIGURACIÓN PERSONALIZADA
# ============================================================================

def create_custom_config(
    model_class: Type[models.Model],
    form_class: Type,
    title: str,
    description: str,
    template_form: str = 'components/elemento_form.html',
    sub_elementos: List[SubElementoConfig] = None,
    success_message: str = None,
    error_message: str = None
) -> PasoConfig:
    """
    Crea una configuración personalizada usando create_base_element_config.
    
    Args:
        model_class: Clase del modelo del paso
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        template_form: Template para el formulario
        sub_elementos: Lista de sub-elementos (mapa, fotos, etc.)
        success_message: Mensaje de éxito personalizado
        error_message: Mensaje de error personalizado
    
    Returns:
        PasoConfig configurado
    """
    elemento = create_base_element_config(
        model_class=model_class,
        form_class=form_class,
        title=title,
        description=description,
        template_form=template_form,
        success_message=success_message,
        error_message=error_message,
        sub_elementos=sub_elementos or []
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


def create_sub_element_only_config(
    title: str,
    description: str,
    sub_elementos: List[SubElementoConfig] = None,
    template_name: str = 'components/component_only.html',
    success_message: str = None,
    error_message: str = None
) -> PasoConfig:
    """
    Crea una configuración que solo muestra componentes (sin formulario).
    Ideal para pasos que solo necesitan mostrar mapas, fotos u otros componentes.
    
    Args:
        title: Título del paso
        description: Descripción del paso
        sub_elementos: Lista de sub-elementos (mapa, fotos, etc.) - máximo 1 elemento
        template_name: Template para mostrar solo componentes
        success_message: Mensaje de éxito personalizado
        error_message: Mensaje de error personalizado
    
    Returns:
        PasoConfig configurado sin formulario
    
    Raises:
        ValueError: Si se proporcionan más de un sub_elemento
    """
    # Validar que solo se proporcione un subelemento
    if sub_elementos and len(sub_elementos) > 1:
        raise ValueError("create_sub_element_only_config solo acepta un sub_elemento. Se proporcionaron {} elementos.".format(len(sub_elementos)))
    
    # Crear un elemento config sin modelo ni formulario
    elemento = ElementoConfig(
        nombre='component_only',
        model=None,  # Sin modelo
        form_class=None,  # Sin formulario
        title=title,
        description=description,
        template_name=template_name,
        success_message=success_message or "Componente mostrado correctamente.",
        error_message=error_message or "Error al mostrar el componente.",
        sub_elementos=sub_elementos or []
    )
    
    return PasoConfig(
        elemento=elemento,
        title=title,
        description=description
    )


# ============================================================================
# CONFIGURACIÓN DE REGISTRO COMPLETO
# ============================================================================

def create_registro_config(
    registro_model: Type[models.Model],
    pasos_config: Dict[str, PasoConfig],
    title: str,
    app_namespace: str,
    list_template: str = "pages/main_generic.html",
    steps_template: str = "pages/steps_generic.html",
    header_title: str = None,
    allow_multiple_per_site: bool = False,
    project: bool = False
) -> RegistroConfig:
    """
    Crea una configuración completa de registro.
    
    Args:
        registro_model: Modelo principal del registro
        pasos_config: Diccionario con la configuración de pasos
        title: Título de la aplicación
        app_namespace: Namespace de la aplicación
        list_template: Template para listar registros
        steps_template: Template para mostrar pasos
        header_title: Título del header (opcional)
        allow_multiple_per_site: Si permite múltiples registros por sitio (uno por día)
        project: Si debe mostrar campo de estructura/grupo de proyectos
    
    Returns:
        RegistroConfig configurado
    """
    return RegistroConfig(
        registro_model=registro_model,
        pasos=pasos_config,
        list_template=list_template,
        steps_template=steps_template,
        title=title,
        app_namespace=app_namespace,
        breadcrumbs=[
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': title}
        ],
        header_title=header_title,
        allow_multiple_per_site=allow_multiple_per_site,
        project=project
    ) 
