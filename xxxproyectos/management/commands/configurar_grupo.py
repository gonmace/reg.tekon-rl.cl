#!/usr/bin/env python3
"""
Comando para configurar grupos de componentes con sus incidencias.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from proyectos.models import Componente, GrupoComponentes, ComponenteGrupo
from django.db.models import Sum


class Command(BaseCommand):
    help = 'Configura un grupo de componentes con sus incidencias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grupo',
            type=str,
            required=True,
            help='Nombre del grupo a crear o modificar'
        )
        parser.add_argument(
            '--componentes',
            nargs='+',
            type=str,
            required=True,
            help='Lista de componentes con sus incidencias (formato: "Componente:Incidencia")'
        )
        parser.add_argument(
            '--crear-componentes',
            action='store_true',
            help='Crear componentes automáticamente si no existen'
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar la configuración sin validar que la suma sea 100%'
        )

    def handle(self, *args, **options):
        grupo_nombre = options['grupo']
        componentes_data = options['componentes']
        crear_componentes = options['crear_componentes']
        forzar = options['forzar']

        self.stdout.write(f"🔧 Configurando grupo: {grupo_nombre}")
        
        # Crear o obtener el grupo
        grupo, created = GrupoComponentes.objects.get_or_create(nombre=grupo_nombre)
        if created:
            self.stdout.write(f"✅ Grupo creado: {grupo_nombre}")
        else:
            self.stdout.write(f"📝 Grupo existente: {grupo_nombre}")

        # Procesar componentes e incidencias
        componentes_config = []
        total_incidencia = 0
        
        for componente_data in componentes_data:
            try:
                if ':' in componente_data:
                    nombre, incidencia_str = componente_data.split(':', 1)
                    incidencia = float(incidencia_str)
                else:
                    nombre = componente_data
                    incidencia = 0
                
                nombre = nombre.strip()
                componentes_config.append((nombre, incidencia))
                total_incidencia += incidencia
                
            except ValueError:
                raise CommandError(f'Formato inválido: {componente_data}. Use "Componente:Incidencia"')

        # Validar suma de incidencias
        if not forzar and abs(total_incidencia - 100) > 0.01:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  La suma de incidencias es {total_incidencia:.1f}%, no 100%'
                )
            )
            if not self.confirm_continue():
                return

        # Configurar componentes
        with transaction.atomic():
            # Limpiar componentes existentes del grupo
            grupo.componentes.all().delete()
            
            for nombre, incidencia in componentes_config:
                # Obtener o crear componente
                componente, created = Componente.objects.get_or_create(nombre=nombre)
                if created and not crear_componentes:
                    raise CommandError(
                        f'Componente "{nombre}" no existe. Use --crear-componentes para crearlo automáticamente.'
                    )
                elif created:
                    self.stdout.write(f"✅ Componente creado: {nombre}")
                
                # Crear relación con incidencia
                ComponenteGrupo.objects.create(
                    grupo=grupo,
                    componente=componente,
                    incidencia=incidencia
                )
                self.stdout.write(f"  • {nombre}: {incidencia}%")

        # Mostrar resumen
        self.stdout.write(f"\n📊 Resumen del grupo '{grupo_nombre}':")
        for cg in grupo.componentes.all():
            self.stdout.write(f"  • {cg.componente.nombre}: {cg.incidencia}%")
        
        total_final = grupo.componentes.aggregate(total=Sum('incidencia'))['total'] or 0
        self.stdout.write(f"📈 Total: {total_final}%")
        
        if total_final == 100:
            self.stdout.write(self.style.SUCCESS("✅ Grupo configurado correctamente"))
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Total no es 100% ({total_final}%)")
            )

    def confirm_continue(self):
        """Preguntar al usuario si continuar"""
        answer = input('\n¿Desea continuar de todas formas? (y/N): ')
        return answer.lower() in ['y', 'yes', 'sí', 'si']
