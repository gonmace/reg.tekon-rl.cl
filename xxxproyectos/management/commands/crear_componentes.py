"""
Comando para crear los 13 componentes básicos.
"""

from django.core.management.base import BaseCommand
from proyectos.models import Componente


class Command(BaseCommand):
    help = 'Crea los 13 componentes básicos del sistema'

    def handle(self, *args, **options):
        self.stdout.write('Creando componentes básicos...')
        
        # Lista de los 13 componentes
        componentes_data = [
            {'nombre': 'Instalación de faenas', 'descripcion': 'Preparación del área de trabajo y organización del sitio'},
            {'nombre': 'Replanteo y Trazado', 'descripcion': 'Marcado de ubicaciones en el terreno según planos'},
            {'nombre': 'Excavación para la fundación', 'descripcion': 'Excavación del terreno para fundaciones'},
            {'nombre': 'Enferradura de la fundación', 'descripcion': 'Construcción de la estructura de fundación'},
            {'nombre': 'Hormigonado de la fundación', 'descripcion': 'Vertido de hormigón en fundaciones'},
            {'nombre': 'Relleno y compactado', 'descripcion': 'Relleno del terreno excavado y compactación'},
            {'nombre': 'Montaje de la Torre', 'descripcion': 'Ensamblaje de la estructura de la torre'},
            {'nombre': 'Losa Radier de Equipos', 'descripcion': 'Construcción de losa para equipos'},
            {'nombre': 'Cierre perimetral', 'descripcion': 'Construcción de muros perimetrales'},
            {'nombre': 'Sistema puesta a tierra', 'descripcion': 'Instalación del sistema de tierra'},
            {'nombre': 'Sistema Eléctrico', 'descripcion': 'Instalación de sistemas eléctricos'},
            {'nombre': 'Linea Electica definitiva', 'descripcion': 'Conexión eléctrica definitiva'},
            {'nombre': 'Trabajos Finales / Adicionales', 'descripcion': 'Trabajos de terminación y adicionales'},
        ]
        
        componentes_creados = 0
        for comp_data in componentes_data:
            componente, created = Componente.objects.get_or_create(
                nombre=comp_data['nombre'],
                defaults=comp_data
            )
            if created:
                self.stdout.write(f'✓ Componente creado: {componente.nombre}')
                componentes_creados += 1
            else:
                self.stdout.write(f'⚠ Componente ya existe: {componente.nombre}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado!\n'
                f'• {componentes_creados} componentes nuevos creados\n'
                f'• {len(componentes_data) - componentes_creados} componentes ya existían\n'
                f'• Total de componentes: {Componente.objects.count()}'
            )
        ) 