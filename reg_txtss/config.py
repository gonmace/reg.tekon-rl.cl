"""
Configuración del registro TX/TSS.
"""
from registros.config import create_registro_config
from .models import RegTxtss

REGISTRO_CONFIG = create_registro_config(
    registro_model=RegTxtss,
    pasos_config={},
    title='TX/TSS',
    app_namespace='reg_txtss',
    list_template='reg_txtss/list.html',
    steps_template='pages/steps_generic.html',
    allow_multiple_per_site=False,
    project=False,
)
