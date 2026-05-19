#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reg_construccion.config import PASOS_CONFIG
from reg_construccion.models import RegConstruccion
from registros.views.steps_views import GenericRegistroStepsView

# Obtener el registro
registro = RegConstruccion.objects.get(id=61)
print(f"Registro encontrado: {registro.id}")

# Crear una instancia de la vista
from reg_construccion.config import REGISTRO_CONFIG

class TestView(GenericRegistroStepsView):
    def get_registro_config(self):
        return REGISTRO_CONFIG

view = TestView()

# Probar la función
elemento_config = PASOS_CONFIG['avance_componente'].elemento
print(f"Subelementos del paso avance_componente: {[sub.tipo for sub in elemento_config.sub_elementos]}")

# Probar la función _process_table_config
table_config = view._process_table_config(registro, elemento_config, None, 'avance_componente')
print(f"Configuración de tabla: {table_config}")

# Probar la función _get_table_data_for_step
table_data = view._get_table_data_for_step(registro, elemento_config, None)
print(f"Datos de tabla: {table_data}") 