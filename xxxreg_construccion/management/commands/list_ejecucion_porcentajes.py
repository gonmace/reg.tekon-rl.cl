from django.core.management.base import BaseCommand
from reg_construccion.models import EjecucionPorcentajes, RegConstruccion
from django.db.models import Q


class Command(BaseCommand):
    help = 'Lista los porcentajes de ejecución guardados en el modelo EjecucionPorcentajes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--registro-id',
            type=int,
            help='ID del registro específico para filtrar'
        )
        parser.add_argument(
            '--componente',
            type=str,
            help='Nombre del componente para filtrar'
        )

    def handle(self, *args, **options):
        queryset = EjecucionPorcentajes.objects.select_related(
            'registro', 'componente'
        ).order_by('-fecha_calculo')
        
        # Aplicar filtros si se proporcionan
        if options['registro_id']:
            queryset = queryset.filter(registro_id=options['registro_id'])
            self.stdout.write(f"Filtrando por registro ID: {options['registro_id']}")
        
        if options['componente']:
            queryset = queryset.filter(componente__nombre__icontains=options['componente'])
            self.stdout.write(f"Filtrando por componente: {options['componente']}")
        
        if not queryset.exists():
            self.stdout.write(
                self.style.WARNING('No se encontraron registros de porcentajes de ejecución.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Se encontraron {queryset.count()} registros de porcentajes:')
        )
        self.stdout.write('=' * 80)
        
        for porcentaje in queryset:
            self.stdout.write(
                f"ID: {porcentaje.id} | "
                f"Registro: {porcentaje.registro.title} (ID: {porcentaje.registro.id}) | "
                f"Componente: {porcentaje.componente.nombre} | "
                f"Ejec. Actual: {porcentaje.porcentaje_ejec_actual}% | "
                f"Ejec. Anterior: {porcentaje.porcentaje_ejec_anterior}% | "
                f"Fecha: {porcentaje.fecha_calculo.strftime('%d/%m/%Y %H:%M')}"
            )
        
        self.stdout.write('=' * 80)
        
        # Mostrar estadísticas
        total_registros = queryset.count()
        registros_unicos = queryset.values('registro').distinct().count()
        componentes_unicos = queryset.values('componente').distinct().count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Estadísticas: {total_registros} registros, '
                f'{registros_unicos} registros únicos, '
                f'{componentes_unicos} componentes únicos'
            )
        ) 