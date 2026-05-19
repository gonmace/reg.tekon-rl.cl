"""
Comando para crear datos de ejemplo para los nuevos modelos simplificados.
"""

from django.core.management.base import BaseCommand
from proyectos.models import Componente, GrupoComponentes, ComponenteGrupo


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para probar los nuevos modelos simplificados'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de ejemplo...')
        
        # Crear componentes
        componentes_data = [
            'Instalación de faenas',
            'Replanteo y Trazado',
            'Excavación para la fundación',
            'Enferradura de la fundación',
            'Hormigonado de la fundación',
            'Relleno y compactado',
            'Montaje de la Torre',
            'Losa Radier de Equipos',
            'Cierre perimetral',
            'Sistema puesta a tierra',
            'Sistema Eléctrico',
            'Linea Electica definitiva',
            'Trabajos Finales / Adicionales',
        ]
        
        componentes_creados = 0
        for nombre in componentes_data:
            componente, created = Componente.objects.get_or_create(nombre=nombre)
            if created:
                self.stdout.write(f'✓ Componente creado: {nombre}')
                componentes_creados += 1
            else:
                self.stdout.write(f'⚠ Componente ya existe: {nombre}')
        
        # Crear grupos de componentes
        grupos_data = [
            {
                'nombre': 'Torres Completas',
                'componentes': [
                    ('Instalación de faenas', 5.0),
                    ('Replanteo y Trazado', 5.0),
                    ('Excavación para la fundación', 5.0),
                    ('Enferradura de la fundación', 15.0),
                    ('Hormigonado de la fundación', 15.0),
                    ('Relleno y compactado', 5.0),
                    ('Montaje de la Torre', 15.0),
                    ('Losa Radier de Equipos', 5.0),
                    ('Cierre perimetral', 5.0),
                    ('Sistema puesta a tierra', 5.0),
                    ('Sistema Eléctrico', 5.0),
                    ('Linea Electica definitiva', 10.0),
                    ('Trabajos Finales / Adicionales', 5.0),
                ]
            },
            {
                'nombre': 'Torres Pequeñas',
                'componentes': [
                    ('Instalación de faenas', 10.0),
                    ('Replanteo y Trazado', 10.0),
                    ('Excavación para la fundación', 15.0),
                    ('Enferradura de la fundación', 20.0),
                    ('Hormigonado de la fundación', 20.0),
                    ('Montaje de la Torre', 15.0),
                    ('Sistema Eléctrico', 10.0),
                ]
            },
            {
                'nombre': 'Fundaciones',
                'componentes': [
                    ('Replanteo y Trazado', 10.0),
                    ('Excavación para la fundación', 25.0),
                    ('Enferradura de la fundación', 35.0),
                    ('Hormigonado de la fundación', 30.0),
                ]
            },
            {
                'nombre': 'Sistemas Eléctricos',
                'componentes': [
                    ('Sistema puesta a tierra', 30.0),
                    ('Sistema Eléctrico', 40.0),
                    ('Linea Electica definitiva', 30.0),
                ]
            }
        ]
        
        grupos_creados = 0
        total_componentes_asignados = 0
        
        for grupo_data in grupos_data:
            grupo, created = GrupoComponentes.objects.get_or_create(
                nombre=grupo_data['nombre']
            )
            if created:
                self.stdout.write(f'✓ Grupo creado: {grupo.nombre}')
                grupos_creados += 1
            else:
                self.stdout.write(f'⚠ Grupo ya existe: {grupo.nombre}')
            
            # Asignar componentes al grupo con sus incidencias
            componentes_asignados = 0
            for nombre_componente, incidencia in grupo_data['componentes']:
                componente = Componente.objects.filter(nombre=nombre_componente).first()
                if componente:
                    cg, created = ComponenteGrupo.objects.get_or_create(
                        grupo=grupo,
                        componente=componente,
                        defaults={'incidencia': incidencia}
                    )
                    if created:
                        self.stdout.write(f'  ✓ Componente asignado: {componente.nombre} (Incidencia: {incidencia}%)')
                        componentes_asignados += 1
                        total_componentes_asignados += 1
                    else:
                        # Actualizar la incidencia si ya existe
                        cg.incidencia = incidencia
                        cg.save()
                        self.stdout.write(f'  ⚠ Componente ya asignado, incidencia actualizada: {componente.nombre} (Incidencia: {incidencia}%)')
                else:
                    self.stdout.write(f'  ❌ Componente no encontrado: {nombre_componente}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado!\n'
                f'• {componentes_creados} componentes nuevos creados\n'
                f'• {grupos_creados} grupos nuevos creados\n'
                f'• Total de componentes: {Componente.objects.count()}\n'
                f'• Total de grupos: {GrupoComponentes.objects.count()}\n'
                f'• Total de componentes asignados: {total_componentes_asignados}'
            )
        )
