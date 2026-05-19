"""
Comando para poblar automáticamente los componentes del proyecto.
Basado en las fases estándar de construcción de infraestructura.
"""

from django.core.management.base import BaseCommand
from proyectos.models import Componente


class Command(BaseCommand):
    help = 'Pobla automáticamente los componentes del proyecto con las fases estándar de construcción'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando población de componentes...')
        
        # Lista de componentes basada en las fases de construcción
        componentes_data = [
            {
                'nombre': 'Instalación de faenas',
                'descripcion': 'Preparación e instalación de las instalaciones de obra y faenas necesarias para el proyecto'
            },
            {
                'nombre': 'Replanteo y Trazado',
                'descripcion': 'Trabajos de replanteo y trazado de la obra según los planos de proyecto'
            },
            {
                'nombre': 'Excavación para la fundación',
                'descripcion': 'Excavación de zanjas y pozos para las fundaciones de la estructura'
            },
            {
                'nombre': 'Enferradura de la fundación',
                'descripcion': 'Instalación de armadura y encofrado para las fundaciones'
            },
            {
                'nombre': 'Hormigonado de la fundación',
                'descripcion': 'Vertido y curado del hormigón para las fundaciones'
            },
            {
                'nombre': 'Relleno y compactado',
                'descripcion': 'Relleno de excavaciones y compactación del terreno'
            },
            {
                'nombre': 'Montaje de la Torre',
                'descripcion': 'Montaje y ensamblaje de la estructura de la torre'
            },
            {
                'nombre': 'Losa Radier de Equipos',
                'descripcion': 'Construcción de la losa radier para el soporte de equipos'
            },
            {
                'nombre': 'Cierre perimetral',
                'descripcion': 'Instalación del cerco perimetral de seguridad'
            },
            {
                'nombre': 'Sistema puesta a tierra',
                'descripcion': 'Instalación del sistema de puesta a tierra para seguridad eléctrica'
            },
            {
                'nombre': 'Sistema Eléctrico',
                'descripcion': 'Instalación del sistema eléctrico principal de la obra'
            },
            {
                'nombre': 'Linea Electrica Provisorias',
                'descripcion': 'Instalación de líneas eléctricas provisionales para la obra'
            },
            {
                'nombre': 'Linea Electica definitiva',
                'descripcion': 'Instalación de las líneas eléctricas definitivas del proyecto'
            },
            {
                'nombre': 'Trabajos Finales / Adicionales',
                'descripcion': 'Trabajos finales de terminación y trabajos adicionales no contemplados inicialmente'
            }
        ]

        # Crear los componentes
        created_count = 0
        skipped_count = 0

        for componente_data in componentes_data:
            componente, created = Componente.objects.get_or_create(
                nombre=componente_data['nombre'],
                defaults={
                    'descripcion': componente_data['descripcion'],
                    'activo': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {componente.nombre}')
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⚠ Existente: {componente.nombre}')
                )

        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'Resumen: {created_count} componentes creados, {skipped_count} existentes'
            )
        )
        
        total_count = Componente.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'Total de componentes en la base de datos: {total_count}')
        ) 