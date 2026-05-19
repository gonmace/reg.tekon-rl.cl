#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reg_construccion.models import RegConstruccion

# Verificar los valores de estado en la base de datos
registros = RegConstruccion.objects.all()[:10]

print("=== VALORES DE ESTADO EN LA BASE DE DATOS ===")
for registro in registros:
    print(f"ID: {registro.id}, Estado: '{registro.estado}' (tipo: {type(registro.estado)})")

print("\n=== OPCIONES VÁLIDAS DEL MODELO ===")
from reg_construccion.models import RegConstruccion
for choice in RegConstruccion.ESTADO_CHOICES:
    print(f"'{choice[0]}' -> '{choice[1]}'")
