"""
Configuración del registro Construcción Sitios.
"""
from registros.config import create_registro_config
from .models import RegConstruccion

REGISTRO_CONFIG = create_registro_config(
    registro_model=RegConstruccion,
    pasos_config={},
    title='Construcción Sitios',
    app_namespace='reg_construccion',
    list_template='reg_construccion/list.html',
    steps_template='pages/steps_generic.html',
    # Cada sitio tiene VARIAS visitas (una por fecha): el listado muestra todas.
    allow_multiple_per_site=False,
    project=False,
)
