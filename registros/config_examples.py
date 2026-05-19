"""
Ejemplos de uso de la configuración genérica de registros.
Este archivo muestra cómo usar las diferentes funciones de configuración.
"""

from registros.config import (
    create_simple_config,
    create_map_only_config,
    create_photo_config,
    create_photo_map_config,
    create_custom_config,
    create_registro_config,
    create_single_point_map_config,
    create_1_point_map_config,
    create_2_point_map_config,
    create_3_point_map_config,
    create_photos_config,
    create_sub_element_only_config
)
from django.db import models


# ============================================================================
# EJEMPLO 1: Configuración simple solo con formulario
# ============================================================================

def ejemplo_simple_config():
    """
    Ejemplo de configuración simple solo con formulario.
    """
    from .models import MiModelo
    from .forms import MiFormulario
    
    paso_config = create_simple_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Información Básica",
        description="Ingrese la información básica del registro"
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 2: Configuración con mapa (usando función de ayuda)
# ============================================================================

def ejemplo_config_with_map():
    """
    Ejemplo de configuración con formulario y mapa usando función de ayuda.
    """
    from .models import Sitio
    from .forms import SitioForm
    
    paso_config = create_map_only_config(
        model_class=Sitio,
        form_class=SitioForm,
        title="Ubicación del Sitio",
        description="Seleccione la ubicación del sitio en el mapa",
        lat_field='latitud',  # Campo personalizado de latitud
        lon_field='longitud',  # Campo personalizado de longitud
        name_field='nombre',   # Campo personalizado de nombre
        zoom=12
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 3: Configuración con fotos (usando función de ayuda)
# ============================================================================

def ejemplo_config_with_photos():
    """
    Ejemplo de configuración con formulario y fotos usando función de ayuda.
    """
    from .models import Documentacion
    from .forms import DocumentacionForm
    
    paso_config = create_photo_config(
        model_class=Documentacion,
        form_class=DocumentacionForm,
        title="Documentación Fotográfica",
        description="Suba las fotos de la documentación",
        photo_min=6,
        photos_template='photos/photos_custom.html'
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 4: Configuración con mapa y fotos (usando función de ayuda)
# ============================================================================

def ejemplo_config_with_map_and_photos():
    """
    Ejemplo de configuración con formulario, mapa y fotos usando función de ayuda.
    """
    from .models import Sitio
    from .forms import SitioForm
    
    paso_config = create_photo_map_config(
        model_class=Sitio,
        form_class=SitioForm,
        title="Sitio con Fotos",
        description="Configure el sitio y suba las fotos",
        photo_min=4,
        lat_field='latitud',
        lon_field='longitud',
        name_field='nombre',
        zoom=15
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 5: Configuración con mapa de múltiples puntos
# ============================================================================

def ejemplo_config_with_multi_point_map():
    """
    Ejemplo de configuración con formulario y mapa de múltiples puntos.
    """
    from .models import Sitio, PuntoReferencia
    from .forms import SitioForm
    
    # Crear componente de mapa de dos puntos
    mapa_component = create_2_point_map_config(
        model_class1='current',
        lat1='latitud',
        lon1='longitud',
        name1='nombre',
        model_class2=PuntoReferencia,
        lat2='lat',
        lon2='lon',
        name2='descripcion',
        second_model_relation_field='sitio',
        descripcion_distancia='Distancia desde el sitio principal',
        zoom=15
    )
    
    # Crear configuración usando create_custom_config
    paso_config = create_custom_config(
        model_class=Sitio,
        form_class=SitioForm,
        title="Sitio con Puntos de Referencia",
        description="Configure el sitio y puntos de referencia",
        sub_elementos=[mapa_component]
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 6: Configuración personalizada usando create_simple_config directamente
# ============================================================================

def ejemplo_configuracion_personalizada():
    """
    Ejemplo de configuración personalizada usando create_simple_config directamente.
    """
    from .models import MiModelo
    from .forms import MiFormulario
    
    # Crear componentes personalizados
    mapa_component = create_single_point_map_config(
        lat_field='coordenada_lat',
        lon_field='coordenada_lon',
        name_field='titulo',
        zoom=18,
        template_name='components/mapa_personalizado.html',
        css_classes='mi-mapa-container'
    )
    
    fotos_component = create_photos_config(
        photo_min=8,
        allowed_types=['image/jpeg', 'image/png', 'image/webp'],
        photos_template='photos/photos_avanzado.html',
        css_classes='mis-fotos-container'
    )
    
    # Crear configuración usando create_simple_config
    paso_config = create_simple_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Configuración Personalizada",
        description="Ejemplo de configuración usando componentes personalizados",
        template_form='components/formulario_personalizado.html',
        success_message="¡Configuración personalizada guardada con éxito!",
        error_message="Hubo un error en la configuración personalizada.",
        sub_elementos=[mapa_component, fotos_component]
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 7: Configuración flexible usando create_flexible_config
# ============================================================================

def ejemplo_flexible_config():
    """
    Ejemplo de configuración flexible especificando componentes.
    """
    from .models import MiModelo, PuntoReferencia
    from .forms import MiFormulario
    
    # Solo formulario
    config1 = create_custom_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Paso 1",
        description="Solo formulario"
    )
    
    # Formulario con mapa
    mapa_component = create_single_point_map_config(
        lat_field='latitud',
        lon_field='longitud',
        name_field='nombre'
    )
    config2 = create_custom_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Paso 2",
        description="Formulario con mapa",
        sub_elementos=[mapa_component]
    )
    
    # Formulario con fotos
    fotos_component = create_photos_config(photo_min=6)
    config3 = create_custom_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Paso 3",
        description="Formulario con fotos",
        sub_elementos=[fotos_component]
    )
    
    # Formulario con mapa y fotos
    mapa_fotos_component = create_single_point_map_config(
        lat_field='latitud',
        lon_field='longitud'
    )
    fotos_mapa_component = create_photos_config(photo_min=4)
    config4 = create_custom_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Paso 4",
        description="Formulario con mapa y fotos",
        sub_elementos=[mapa_fotos_component, fotos_mapa_component]
    )
    
    # Formulario con mapa de dos puntos
    multi_mapa_component = create_2_point_map_config(
        model_class1='current',
        lat1='latitud',
        lon1='longitud',
        name1='nombre',
        model_class2=PuntoReferencia,
        lat2='lat',
        lon2='lon',
        name2='descripcion',
        second_model_relation_field='registro'
    )
    config5 = create_custom_config(
        model_class=MiModelo,
        form_class=MiFormulario,
        title="Paso 5",
        description="Formulario con mapa de múltiples puntos",
        sub_elementos=[multi_mapa_component]
    )
    
    return [config1, config2, config3, config4, config5]


# ============================================================================
# EJEMPLO 8: Configuración completa de registro
# ============================================================================

def ejemplo_registro_completo():
    """
    Ejemplo de configuración completa de un registro con múltiples pasos.
    """
    from .models import RegistroPrincipal, Sitio, Documentacion, Evaluacion
    from .forms import RegistroForm, SitioForm, DocumentacionForm, EvaluacionForm
    
    # Paso 1: Información básica
    paso1 = create_simple_config(
        model_class=RegistroPrincipal,
        form_class=RegistroForm,
        title="Información General",
        description="Datos básicos del registro"
    )
    
    # Paso 2: Ubicación con mapa
    paso2 = create_map_only_config(
        model_class=Sitio,
        form_class=SitioForm,
        title="Ubicación",
        description="Seleccione la ubicación en el mapa",
        lat_field='latitud',
        lon_field='longitud',
        name_field='nombre'
    )
    
    # Paso 3: Documentación fotográfica
    paso3 = create_photo_config(
        model_class=Documentacion,
        form_class=DocumentacionForm,
        title="Documentación",
        description="Suba las fotos de documentación",
        photo_min=6
    )
    
    # Paso 4: Evaluación con mapa y fotos
    paso4 = create_photo_map_config(
        model_class=Evaluacion,
        form_class=EvaluacionForm,
        title="Evaluación Final",
        description="Complete la evaluación y suba fotos",
        photo_min=4,
        lat_field='lat',
        lon_field='lon',
        name_field='titulo'
    )
    
    # Configuración completa del registro
    pasos_config = {
        'informacion': paso1,
        'ubicacion': paso2,
        'documentacion': paso3,
        'evaluacion': paso4
    }
    
    registro_config = create_registro_config(
        registro_model=RegistroPrincipal,
        pasos_config=pasos_config,
        title="Registro Completo",
        app_namespace="mi_app",
        list_template="pages/lista_personalizada.html",
        steps_template="pages/pasos_personalizados.html",
        header_title="Sistema de Registros"
    )
    
    return registro_config


# ============================================================================
# FUNCIÓN DE AYUDA PARA CREAR CONFIGURACIONES RÁPIDAS
# ============================================================================

def crear_configuracion_rapida(
    model_class,
    form_class,
    title,
    description,
    incluir_mapa=False,
    incluir_fotos=False,
    incluir_multi_mapa=False,
    photo_min=4,
    lat_field='lat',
    lon_field='lon',
    name_field='name',
    zoom=15,
    second_model_class=None,
    **kwargs
):
    """
    Función de ayuda para crear configuraciones rápidas según las necesidades.
    
    Args:
        model_class: Clase del modelo
        form_class: Clase del formulario
        title: Título del paso
        description: Descripción del paso
        incluir_mapa: Si incluir mapa de un punto
        incluir_fotos: Si incluir fotos
        incluir_multi_mapa: Si incluir mapa de múltiples puntos
        photo_min: Número mínimo de fotos
        lat_field: Campo de latitud
        lon_field: Campo de longitud
        name_field: Campo de nombre
        zoom: Nivel de zoom del mapa
        second_model_class: Modelo para mapa múltiple
        **kwargs: Argumentos adicionales
    
    Returns:
        PasoConfig configurado
    """
    if incluir_multi_mapa:
        # Crear componente de mapa de dos puntos
        mapa_component = create_2_point_map_config(
            model_class1='current',
            lat1=lat_field,
            lon1=lon_field,
            name1=name_field,
            model_class2=second_model_class,
            lat2=kwargs.get('lat2', 'lat'),
            lon2=kwargs.get('lon2', 'lon'),
            name2=kwargs.get('name2', 'name'),
            second_model_relation_field=kwargs.get('second_model_relation_field', 'registro'),
            descripcion_distancia=kwargs.get('descripcion_distancia', 'Distancia entre puntos'),
            zoom=zoom
        )
        return create_custom_config(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            sub_elementos=[mapa_component]
        )
    elif incluir_mapa and incluir_fotos:
        # Crear componentes de mapa y fotos
        mapa_component = create_single_point_map_config(
            lat_field=lat_field,
            lon_field=lon_field,
            name_field=name_field,
            zoom=zoom
        )
        fotos_component = create_photos_config(
            photo_min=photo_min,
            photos_template=kwargs.get('photos_template', 'widgets/camera_widget_page.html')
        )
        return create_custom_config(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            sub_elementos=[mapa_component, fotos_component]
        )
    elif incluir_mapa:
        # Crear componente de mapa
        mapa_component = create_single_point_map_config(
            lat_field=lat_field,
            lon_field=lon_field,
            name_field=name_field,
            zoom=zoom
        )
        return create_custom_config(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            sub_elementos=[mapa_component]
        )
    elif incluir_fotos:
        # Crear componente de fotos
        fotos_component = create_photos_config(
            photo_min=photo_min,
            photos_template=kwargs.get('photos_template', 'widgets/camera_widget_page.html')
        )
        return create_custom_config(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            sub_elementos=[fotos_component]
        )
    else:
        return create_simple_config(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            **kwargs
        )


# Ejemplo de uso de la función rápida:
def ejemplo_configuracion_rapida():
    """
    Ejemplo de uso de la función de configuración rápida.
    """
    from .models import MiModelo, PuntoReferencia
    from .forms import MiFormulario
    
    # Solo formulario
    config1 = crear_configuracion_rapida(
        MiModelo, MiFormulario, "Paso 1", "Descripción 1"
    )
    
    # Formulario con mapa
    config2 = crear_configuracion_rapida(
        MiModelo, MiFormulario, "Paso 2", "Descripción 2",
        incluir_mapa=True, lat_field='latitud', lon_field='longitud'
    )
    
    # Formulario con fotos
    config3 = crear_configuracion_rapida(
        MiModelo, MiFormulario, "Paso 3", "Descripción 3",
        incluir_fotos=True, photo_min=6
    )
    
    # Formulario con mapa y fotos
    config4 = crear_configuracion_rapida(
        MiModelo, MiFormulario, "Paso 4", "Descripción 4",
        incluir_mapa=True, incluir_fotos=True, photo_min=4
    )
    
    # Formulario con mapa múltiple
    config5 = crear_configuracion_rapida(
        MiModelo, MiFormulario, "Paso 5", "Descripción 5",
        incluir_multi_mapa=True, second_model_class=PuntoReferencia
    )
    
    return [config1, config2, config3, config4, config5] 


# ============================================================================
# EJEMPLO 9: Configuración solo con componentes (sin formulario)
# ============================================================================

def ejemplo_component_only_config():
    """
    Ejemplo de configuración que solo muestra componentes sin formulario.
    Útil para pasos informativos o de visualización.
    """
    from .models import Site
    from .forms import SiteForm
    
    # Crear componente de mapa para mostrar información del mandato
    mandato_mapa_component = create_1_point_map_config(
        model_class1=Site,  # Modelo del sitio/mandato
        lat1='lat_base',
        lon1='lon_base',
        name1='Mandato',
        icon1_color='blue',
        icon1_size='large',
        zoom=15
    )
    
    # Configuración que solo muestra el mapa del mandato
    paso_config = create_sub_element_only_config(
        title='Información del Mandato',
        description='Visualice la ubicación del mandato en el mapa.',
        sub_elementos=[mandato_mapa_component]  # Solo un componente
    )
    
    return paso_config


def ejemplo_component_only_with_photos():
    """
    Ejemplo de configuración que solo muestra fotos sin formulario.
    Útil para galerías o visualizaciones.
    """
    from .models import Documentacion
    from .forms import DocumentacionForm
    
    # Crear componente de fotos para mostrar galería
    galeria_fotos_component = create_photos_config(
        photo_min=0,  # Sin mínimo para solo visualización
        photos_template='photos/photos_gallery.html'
    )
    
    # Configuración que solo muestra la galería de fotos
    paso_config = create_sub_element_only_config(
        title='Galería de Fotos',
        description='Visualice las fotos del registro.',
        sub_elementos=[galeria_fotos_component]  # Solo un componente
    )
    
    return paso_config


# ============================================================================
# EJEMPLO 10: Configuración completa con componente only
# ============================================================================

def ejemplo_registro_con_component_only():
    """
    Ejemplo de registro completo que incluye un paso solo con componentes.
    """
    from registros.config import (
        create_simple_config,
        create_sub_element_only_config,
        create_1_point_map_config,
        create_registro_config
    )
    from .models import RegistroPrincipal, Sitio, Documentacion
    from .forms import RegistroForm, SitioForm, DocumentacionForm
    
    # Paso 1: Información básica
    paso1 = create_simple_config(
        model_class=RegistroPrincipal,
        form_class=RegistroForm,
        title="Información General",
        description="Datos básicos del registro"
    )
    
    # Paso 2: Visualización del mandato (solo componente)
    mandato_mapa = create_1_point_map_config(
        model_class1=Sitio,
        lat1='lat_base',
        lon1='lon_base',
        name1='Mandato',
        icon1_color='blue'
    )
    
    paso2 = create_sub_element_only_config(
        title="Ubicación del Mandato",
        description="Visualice la ubicación del mandato en el mapa",
        sub_elementos=[mandato_mapa]
    )
    
    # Paso 3: Documentación
    paso3 = create_simple_config(
        model_class=Documentacion,
        form_class=DocumentacionForm,
        title="Documentación",
        description="Suba la documentación requerida"
    )
    
    # Configuración completa del registro
    pasos_config = {
        'informacion': paso1,
        'mandato': paso2,  # Paso solo con componente
        'documentacion': paso3
    }
    
    registro_config = create_registro_config(
        registro_model=RegistroPrincipal,
        pasos_config=pasos_config,
        title="Registro con Componente Only",
        app_namespace="mi_app"
    )
    
    return registro_config


# ============================================================================
# FUNCIÓN DE AYUDA ACTUALIZADA PARA INCLUIR COMPONENT ONLY
# ============================================================================

def crear_configuracion_rapida_actualizada(
    model_class=None,
    form_class=None,
    title="",
    description="",
    tipo_config="simple",
    incluir_mapa=False,
    incluir_fotos=False,
    incluir_multi_mapa=False,
    photo_min=4,
    lat_field='lat',
    lon_field='lon',
    name_field='name',
    zoom=15,
    second_model_class=None,
    **kwargs
):
    """
    Función de ayuda actualizada para crear configuraciones rápidas incluyendo component_only.
    
    Args:
        model_class: Clase del modelo (None para component_only)
        form_class: Clase del formulario (None para component_only)
        title: Título del paso
        description: Descripción del paso
        tipo_config: Tipo de configuración ('simple', 'component_only', 'custom')
        incluir_mapa: Si incluir mapa de un punto
        incluir_fotos: Si incluir fotos
        incluir_multi_mapa: Si incluir mapa de múltiples puntos
        photo_min: Número mínimo de fotos
        lat_field: Campo de latitud
        lon_field: Campo de longitud
        name_field: Campo de nombre
        zoom: Nivel de zoom del mapa
        second_model_class: Modelo para mapa múltiple
        **kwargs: Argumentos adicionales
    
    Returns:
        PasoConfig configurado
    """
    if tipo_config == "component_only":
        # Crear configuración solo con componentes
        sub_elementos = []
        
        if incluir_multi_mapa:
            mapa_component = create_2_point_map_config(
                model_class1='current',
                lat1=lat_field,
                lon1=lon_field,
                name1=name_field,
                model_class2=second_model_class,
                lat2=kwargs.get('lat2', 'lat'),
                lon2=kwargs.get('lon2', 'lon'),
                name2=kwargs.get('name2', 'name'),
                second_model_relation_field=kwargs.get('second_model_relation_field', 'registro'),
                descripcion_distancia=kwargs.get('descripcion_distancia', 'Distancia entre puntos'),
                zoom=zoom
            )
            sub_elementos.append(mapa_component)
        elif incluir_mapa:
            mapa_component = create_single_point_map_config(
                lat_field=lat_field,
                lon_field=lon_field,
                name_field=name_field,
                zoom=zoom
            )
            sub_elementos.append(mapa_component)
        elif incluir_fotos:
            fotos_component = create_photos_config(
                photo_min=photo_min,
                photos_template=kwargs.get('photos_template', 'widgets/camera_widget_page.html')
            )
            sub_elementos.append(fotos_component)
        
        return create_sub_element_only_config(
            title=title,
            description=description,
            sub_elementos=sub_elementos
        )
    else:
        # Usar la función original para otros tipos
        return crear_configuracion_rapida(
            model_class=model_class,
            form_class=form_class,
            title=title,
            description=description,
            incluir_mapa=incluir_mapa,
            incluir_fotos=incluir_fotos,
            incluir_multi_mapa=incluir_multi_mapa,
            photo_min=photo_min,
            lat_field=lat_field,
            lon_field=lon_field,
            name_field=name_field,
            zoom=zoom,
            second_model_class=second_model_class,
            **kwargs
        )


# Ejemplo de uso de la función actualizada:
def ejemplo_configuracion_rapida_actualizada():
    """
    Ejemplo de uso de la función de configuración rápida actualizada.
    """
    from .models import MiModelo, PuntoReferencia
    from .forms import MiFormulario
    
    # Solo formulario
    config1 = crear_configuracion_rapida_actualizada(
        MiModelo, MiFormulario, "Paso 1", "Descripción 1"
    )
    
    # Solo componente de mapa (sin formulario)
    config2 = crear_configuracion_rapida_actualizada(
        title="Visualización de Mapa",
        description="Descripción del mapa",
        tipo_config="component_only",
        incluir_mapa=True,
        lat_field='latitud',
        lon_field='longitud'
    )
    
    # Solo componente de fotos (sin formulario)
    config3 = crear_configuracion_rapida_actualizada(
        title="Galería de Fotos",
        description="Descripción de la galería",
        tipo_config="component_only",
        incluir_fotos=True,
        photo_min=0
    )
    
    # Solo componente de mapa múltiple (sin formulario)
    config4 = crear_configuracion_rapida_actualizada(
        title="Mapa de Referencia",
        description="Descripción del mapa múltiple",
        tipo_config="component_only",
        incluir_multi_mapa=True,
        second_model_class=PuntoReferencia
    )
    
    return [config1, config2, config3, config4] 