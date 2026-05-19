#!/usr/bin/env python3
"""
Script de prueba para las APIs móviles de reg_construccion.
"""

import os
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from reg_construccion.models import RegConstruccion
from core.models.sites import Site
from core.models.contractors import Contractor
from proyectos.models import GrupoComponentes, Componente

User = get_user_model()

def test_mobile_apis():
    """Prueba las APIs móviles de reg_construccion."""
    print("🧪 Probando APIs móviles de reg_construccion...")
    
    # Crear cliente de prueba
    client = APIClient()
    
    # Crear datos de prueba
    try:
        # Crear usuario de prueba o usar uno existente
        try:
            user = User.objects.get(username='testuser')
            print("✅ Usuario de prueba ya existe")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
            print("✅ Usuario de prueba creado")
        
        # Crear sitio de prueba o usar uno existente
        try:
            site = Site.objects.get(pti_cell_id='PTI001')
            print("✅ Sitio de prueba ya existe")
        except Site.DoesNotExist:
            site = Site.objects.create(
                name='Sitio de Prueba',
                pti_cell_id='PTI001',
                operator_id='OP001'
            )
            print("✅ Sitio de prueba creado")
        
        # Crear contratista de prueba o usar uno existente
        try:
            contractor = Contractor.objects.get(code='CON001')
            print("✅ Contratista de prueba ya existe")
        except Contractor.DoesNotExist:
            contractor = Contractor.objects.create(
                name='Contratista de Prueba',
                code='CON001'
            )
            print("✅ Contratista de prueba creado")
        
        # Crear estructura de prueba o usar una existente
        try:
            estructura = GrupoComponentes.objects.get(nombre='Estructura de Prueba')
            print("✅ Estructura de prueba ya existe")
        except GrupoComponentes.DoesNotExist:
            estructura = GrupoComponentes.objects.create(
                nombre='Estructura de Prueba'
            )
            print("✅ Estructura de prueba creada")
        
        # Crear componente de prueba o usar uno existente
        try:
            componente = Componente.objects.get(nombre='Componente de Prueba')
            print("✅ Componente de prueba ya existe")
        except Componente.DoesNotExist:
            componente = Componente.objects.create(
                nombre='Componente de Prueba'
            )
            print("✅ Componente de prueba creado")
        
        # Autenticar al cliente
        client.force_authenticate(user=user)
        
        print(f"\n📋 Datos de prueba:")
        print(f"   - Usuario: {user.username}")
        print(f"   - Sitio: {site.name}")
        print(f"   - Contratista: {contractor.name}")
        print(f"   - Estructura: {estructura.nombre}")
        print(f"   - Componente: {componente.nombre}")
        
        # 1. Probar API de sitios activos por usuario
        print("\n🔍 1. Probando API de sitios activos por usuario...")
        response = client.get(f'/api/v1/mobile/sitios-activos/?user_id={user.id}')
        if response.status_code == 200:
            print("✅ API de sitios activos funciona correctamente")
            data = response.json()
            print(f"   - Total de sitios: {data.get('total', 0)}")
        else:
            print(f"❌ Error en API de sitios activos: {response.status_code}")
        
        # 2. Probar API de crear nueva fecha
        print("\n🔍 2. Probando API de crear nueva fecha...")
        fecha_data = {
            'sitio_id': site.id,
            'title': 'Registro de Prueba Móvil',
            'fecha': '2024-01-23',
            'description': 'Descripción de prueba para móvil',
            'contratista_id': contractor.id,
            'estructura_id': estructura.id
        }
        response = client.post('/api/v1/mobile/crear-fecha/', fecha_data, format='json')
        if response.status_code == 201:
            print("✅ API de crear fecha funciona correctamente")
            data = response.json()
            registro_id = data['registro']['id']
            print(f"   - Registro creado con ID: {registro_id}")
        else:
            print(f"❌ Error en API de crear fecha: {response.status_code}")
            print(f"   - Respuesta: {response.json()}")
            return
        
        # 3. Probar API de llenar objetivo
        print("\n🔍 3. Probando API de llenar objetivo...")
        objetivo_data = {
            'registro_id': registro_id,
            'objetivo': 'Objetivo de prueba para la aplicación móvil'
        }
        response = client.post('/api/v1/mobile/llenar-objetivo/', objetivo_data, format='json')
        if response.status_code == 200:
            print("✅ API de llenar objetivo funciona correctamente")
            data = response.json()
            print(f"   - Objetivo guardado: {data['objetivo']['objetivo'][:50]}...")
        else:
            print(f"❌ Error en API de llenar objetivo: {response.status_code}")
        
        # 4. Probar API de llenar avance
        print("\n🔍 4. Probando API de llenar avance...")
        avance_data = {
            'registro_id': registro_id,
            'componente_id': componente.id,
            'porcentaje_actual': 25,
            'porcentaje_acumulado': 30,
            'comentarios': 'Avance de prueba para móvil'
        }
        response = client.post('/api/v1/mobile/llenar-avance/', avance_data, format='json')
        if response.status_code == 200:
            print("✅ API de llenar avance funciona correctamente")
            data = response.json()
            print(f"   - Avance guardado: {data['avance']['porcentaje_actual']}%")
        else:
            print(f"❌ Error en API de llenar avance: {response.status_code}")
        
        # 5. Probar API de llenar tabla
        print("\n🔍 5. Probando API de llenar tabla...")
        tabla_data = {
            'registro_id': registro_id,
            'comentarios': 'Comentarios generales de prueba para móvil'
        }
        response = client.post('/api/v1/mobile/llenar-tabla/', tabla_data, format='json')
        if response.status_code == 200:
            print("✅ API de llenar tabla funciona correctamente")
            data = response.json()
            print(f"   - Comentarios guardados: {data['comentarios']['comentarios'][:50]}...")
        else:
            print(f"❌ Error en API de llenar tabla: {response.status_code}")
        
        # 6. Probar API de obtener registro completo
        print("\n🔍 6. Probando API de obtener registro completo...")
        response = client.get(f'/api/v1/mobile/registro-completo/{registro_id}/')
        if response.status_code == 200:
            print("✅ API de obtener registro completo funciona correctamente")
            data = response.json()
            print(f"   - Título del registro: {data.get('title')}")
            print(f"   - Objetivos: {len(data.get('objetivos', []))}")
            print(f"   - Avances: {len(data.get('avances_componente', []))}")
        else:
            print(f"❌ Error en API de obtener registro completo: {response.status_code}")
        
        print("\n🎉 Todas las APIs móviles funcionan correctamente!")
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_mobile_apis()
