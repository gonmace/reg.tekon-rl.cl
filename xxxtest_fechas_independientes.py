#!/usr/bin/env python3
"""
Script de prueba para verificar que cada fecha tiene valores independientes.
"""

import os
import django
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from reg_construccion.models import RegConstruccion, AvanceComponente
from proyectos.models import GrupoComponentes
from core.models.sites import Site
from users.models import User

def test_fechas_independientes():
    """Prueba que cada fecha tiene valores independientes."""
    
    print("🧪 Prueba: Fechas independientes")
    print("=" * 70)
    
    sitio = Site.objects.first()
    user = User.objects.filter(user_type=User.ITO).first()
    grupo = GrupoComponentes.objects.get(nombre="Torres Completas")
    
    if sitio and user and grupo:
        # 1. Crear primera fecha con datos
        print(f"\n1️⃣ Creando primera fecha...")
        fecha_1 = date.today() - timedelta(days=10)
        
        registro_1 = RegConstruccion.objects.create(
            title="Primera Fecha - Test",
            sitio=sitio,
            user=user,
            estructura=grupo,
            fecha=fecha_1,
            is_active=True
        )
        
        # Crear avances para la primera fecha
        componentes = grupo.componentes.all()[:3]
        for i, gc in enumerate(componentes):
            avance = AvanceComponente.objects.create(
                registro=registro_1,
                componente=gc.componente,
                fecha=fecha_1,
                porcentaje_actual=20 + (i * 5),
                porcentaje_acumulado=25 + (i * 5),
                comentarios=f"Avance primera fecha {i+1}"
            )
            print(f"   ✅ {gc.componente.nombre}: {avance.porcentaje_actual}% actual, {avance.porcentaje_acumulado}% acumulado")
        
        # 2. Crear segunda fecha (independiente)
        print(f"\n2️⃣ Creando segunda fecha (independiente)...")
        fecha_2 = date.today() - timedelta(days=5)
        
        registro_2 = RegConstruccion.objects.create(
            title="Segunda Fecha - Test",
            sitio=sitio,
            user=user,
            estructura=grupo,
            fecha=fecha_2,
            is_active=True
        )
        
        # Crear avances independientes para la segunda fecha
        for i, gc in enumerate(componentes):
            avance = AvanceComponente.objects.create(
                registro=registro_2,
                componente=gc.componente,
                fecha=fecha_2,
                porcentaje_actual=30 + (i * 5),
                porcentaje_acumulado=35 + (i * 5),  # Valores independientes
                comentarios=f"Avance segunda fecha {i+1}"
            )
            print(f"   ✅ {gc.componente.nombre}: {avance.porcentaje_actual}% actual, {avance.porcentaje_acumulado}% acumulado")
        
        # 3. Verificar independencia
        print(f"\n3️⃣ Verificando independencia...")
        
        print(f"   📋 Primera fecha ({fecha_1}):")
        avances_1 = AvanceComponente.objects.filter(registro=registro_1)
        for avance in avances_1:
            print(f"      - {avance.componente.nombre}: {avance.porcentaje_actual}% actual, {avance.porcentaje_acumulado}% acumulado")
        
        print(f"   📋 Segunda fecha ({fecha_2}):")
        avances_2 = AvanceComponente.objects.filter(registro=registro_2)
        for avance in avances_2:
            print(f"      - {avance.componente.nombre}: {avance.porcentaje_actual}% actual, {avance.porcentaje_acumulado}% acumulado")
        
        # 4. Simular cálculo de tabla para cada fecha
        print(f"\n4️⃣ Simulando cálculo de tabla...")
        
        for registro in [registro_1, registro_2]:
            print(f"   📋 Tabla para {registro.title} ({registro.fecha}):")
            
            for gc in componentes:
                componente = gc.componente
                avance = AvanceComponente.objects.get(
                    registro=registro,
                    componente=componente
                )
                
                # Cálculo independiente para cada fecha
                ejec_actual = avance.porcentaje_actual
                ejec_anterior = avance.porcentaje_acumulado - avance.porcentaje_actual
                if ejec_anterior < 0:
                    ejec_anterior = 0
                ejec_acumulada = ejec_anterior + ejec_actual
                
                print(f"      - {componente.nombre}:")
                print(f"        * Ejec anterior: {ejec_anterior}%")
                print(f"        * Ejec actual: {ejec_actual}%")
                print(f"        * Ejec acumulada: {ejec_acumulada}%")
        
        # 5. Verificar que los valores son independientes
        print(f"\n5️⃣ Verificando independencia de valores...")
        
        # Comparar valores entre fechas
        for i, gc in enumerate(componentes):
            avance_1 = AvanceComponente.objects.get(registro=registro_1, componente=gc.componente)
            avance_2 = AvanceComponente.objects.get(registro=registro_2, componente=gc.componente)
            
            if (avance_1.porcentaje_actual != avance_2.porcentaje_actual and 
                avance_1.porcentaje_acumulado != avance_2.porcentaje_acumulado):
                print(f"   ✅ {gc.componente.nombre}: Valores independientes")
                print(f"      - Fecha 1: {avance_1.porcentaje_actual}% actual, {avance_1.porcentaje_acumulado}% acumulado")
                print(f"      - Fecha 2: {avance_2.porcentaje_actual}% actual, {avance_2.porcentaje_acumulado}% acumulado")
            else:
                print(f"   ❌ {gc.componente.nombre}: Valores no independientes")
        
        # Limpiar registros de prueba
        registro_2.delete()
        registro_1.delete()
        print(f"\n🧹 Registros de prueba eliminados")
    
    print(f"\n🎉 Prueba completada!")

if __name__ == "__main__":
    test_fechas_independientes()
