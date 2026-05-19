"""
Configuración declarativa para registros Reporte de construcción.
"""

from registros.config import (
    create_simple_config, 
    create_registro_config,
    create_1_point_map_config,
    create_2_point_map_config,
    create_3_point_map_config,
    create_photos_config,
    create_table_config,
    create_custom_config,
    create_sub_element_only_config
)
from .models import RegConstruccion, AvanceComponente, AvanceComponenteComentarios, Objetivo
from .forms import AvanceComponenteForm, AvanceComponenteComentariosForm, ObjetivoForm
from core.models.sites import Site

table_avance_componente = create_table_config(
    table_title="COMPONENTES",
    table_template='components/sub_elemento_table.html',
    data_source="avance_componente_data",
    fields_to_show=['componente', 'incidencia', 'ejec_anterior', 'ejec_actual', 'ejec_acumulada', 'ejecucion_total'],
    table_model_class=AvanceComponente,
    table_form_class=AvanceComponenteForm
)
# Configuración de pasos
PASOS_CONFIG = {
    'objetivo': create_custom_config(
        model_class=Objetivo,
        form_class=ObjetivoForm,
        title='Objetivo',
        description='Objetivo del registro de construcción.',
        template_form='components/elemento_form.html'
    ),
    'avance_componente': create_custom_config(
        model_class=AvanceComponenteComentarios,
        form_class=AvanceComponenteComentariosForm,
        title='Avance',
        description='Tabla de avances por componente de la estructura.',
        template_form='components/elemento_form.html',
        sub_elementos=[
            table_avance_componente
        ]
    ),
    'imagenes': create_sub_element_only_config(
        title='Imágenes',
        description='Fotografías del avance de construcción.',
        sub_elementos=[
            create_photos_config(
                photo_min=6,
                photos_template='widgets/camera_widget_page.html'
            )
        ]
    ),
}

# Configuración completa del registro
REGISTRO_CONFIG = create_registro_config(
    registro_model=RegConstruccion,
    pasos_config=PASOS_CONFIG,
    title='Reporte de construcción',
    app_namespace='reg_construccion',
    list_template='components/generic_tables2_template.html',
    steps_template='pages/steps_generic.html',
    allow_multiple_per_site=True,  # Permite múltiples registros por sitio (uno por día)
    project=True  # Muestra campo de estructura/grupo de proyectos
)