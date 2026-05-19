#!/usr/bin/env python3
"""
Script de prueba para verificar que al guardar la tabla NO se modifica porcentaje_acumulado.
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

def test_guardar_sin_modificar_acumulado():
    """Prueba que al guardar NO se modifica porcentaje_acumulado."""
    
    print("🧪 Prueba: Guardar sin modificar porcentaje_acumulado")
    print("=" * 70)
    
    sitio = Site.objects.first()
    user = User.objects.filter(user_type=User.ITO).first()
    grupo = GrupoComponentes.objects.get(nombre="Torres Completas")
    
    if sitio and user and grupo:
        # 1. Crear registro con datos iniciales
        print(f"\n1️⃣ Creando registro con datos iniciales...")
        fecha_1 = date.today() - timedelta(days=5)
        
        registro = RegConstruccion.objects.create(
            title="Registro Test - Guardar",
            sitio=sitio,
            user=user,
            estructura=grupo,
            fecha=fecha_1,
            is_active=True
        )
        
        # Crear avances iniciales
        componentes = grupo.componentes.all()[:3]
        for i, gc in enumerate(componentes):
            avance = AvanceComponente.objects.create(
                registro=registro,
                componente=gc.componente,
                fecha=fecha_1,
                porcentaje_actual=20 + (i * 5),
                porcentaje_acumulado=30 + (i * 5),  # Valor inicial del acumulado
                comentarios=f"Avance inicial {i+1}"
            )
            print(f"   ✅ {gc.componente.nombre}: {avance.porcentaje_actual}% actual, {avance.porcentaje_acumulado}% acumulado")
        
        # 2. Simular guardado de tabla (como lo haría la vista)
        print(f"\n2️⃣ Simulando guardado de tabla...")
        
        componente_test = componentes[0].componente
        avance_test = AvanceComponente.objects.get(
            registro=registro,
            componente=componente_test
        )
        
        print(f"   📋 Antes de guardar:")
        print(f"      - Componente: {componente_test.nombre}")
        print(f"      - Ejec actual: {avance_test.porcentaje_actual}%")
        print(f"      - Ejec acumulado: {avance_test.porcentaje_acumulado}%")
        
        # Simular actualización (como lo haría la vista guardar_ejecucion)
        nuevo_valor = 40
        avance_test.porcentaje_actual = nuevo_valor
        # NO modificar porcentaje_acumulado
        avance_test.save()
        
        print(f"   📋 Después de guardar:")
        print(f"      - Ejec actual: {avance_test.porcentaje_actual}% (actualizado)")
        print(f"      - Ejec acumulado: {avance_test.porcentaje_acumulado}% (mantenido)")
        
        # 3. Verificar que el acumulado NO cambió
        print(f"\n3️⃣ Verificando que el acumulado NO cambió...")
        
        avance_actualizado = AvanceComponente.objects.get(
            registro=registro,
            componente=componente_test
        )
        
        valor_acumulado_original = 30  # Valor inicial
        valor_acumulado_actual = avance_actualizado.porcentaje_acumulado
        
        if valor_acumulado_actual == valor_acumulado_original:
            print(f"   ✅ porcentaje_acumulado se mantuvo correctamente: {valor_acumulado_actual}%")
            print(f"   ✅ Solo se modificó porcentaje_actual: {avance_actualizado.porcentaje_actual}%")
        else:
            print(f"   ❌ porcentaje_acumulado cambió incorrectamente:")
            print(f"      - Original: {valor_acumulado_original}%")
            print(f"      - Actual: {valor_acumulado_actual}%")
        
        # 4. Verificar todos los componentes
        print(f"\n4️⃣ Verificando todos los componentes...")
        
        for gc in componentes:
            avance = AvanceComponente.objects.get(
                registro=registro,
                componente=gc.componente
            )
            valor_original = 30 + (componentes.index(gc) * 5)
            
            if avance.porcentaje_acumulado == valor_original:
                print(f"   ✅ {gc.componente.nombre}: acumulado correcto ({avance.porcentaje_acumulado}%)")
            else:
                print(f"   ❌ {gc.componente.nombre}: acumulado incorrecto ({avance.porcentaje_acumulado}% vs {valor_original}%)")
        
        # Limpiar registro de prueba
        registro.delete()
        print(f"\n🧹 Registro de prueba eliminado")
    
    print(f"\n🎉 Prueba completada!")

if __name__ == "__main__":
    test_guardar_sin_modificar_acumulado()
