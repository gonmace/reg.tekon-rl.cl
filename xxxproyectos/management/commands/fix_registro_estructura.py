#!/usr/bin/env python3
"""
Comando para arreglar registros que no tienen estructura asignada.
"""

from django.core.management.base import BaseCommand
from reg_construccion.models import RegConstruccion
from proyectos.models import GrupoComponentes


class Command(BaseCommand):
    help = 'Arregla registros que no tienen estructura asignada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--registro-id',
            type=int,
            help='ID específico del registro a arreglar'
        )
        parser.add_argument(
            '--estructura',
            type=str,
            help='Nombre de la estructura a asignar'
        )
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Listar registros sin estructura'
        )
        parser.add_argument(
            '--auto-fix',
            action='store_true',
            help='Arreglar automáticamente todos los registros sin estructura'
        )

    def handle(self, *args, **options):
        registro_id = options['registro_id']
        estructura_nombre = options['estructura']
        listar = options['listar']
        auto_fix = options['auto_fix']

        if listar:
            self.listar_registros_sin_estructura()
            return

        if registro_id:
            self.arreglar_registro_especifico(registro_id, estructura_nombre)
        elif auto_fix:
            self.auto_fix_registros()
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Use --listar para ver registros sin estructura, '
                    '--registro-id para arreglar uno específico, '
                    'o --auto-fix para arreglar todos automáticamente'
                )
            )

    def listar_registros_sin_estructura(self):
        """Lista registros que no tienen estructura asignada."""
        registros_sin_estructura = RegConstruccion.objects.filter(
            estructura__isnull=True
        ).order_by('-fecha')
        
        self.stdout.write(f"📋 Registros sin estructura: {registros_sin_estructura.count()}")
        self.stdout.write("=" * 60)
        
        for registro in registros_sin_estructura:
            self.stdout.write(f"• ID: {registro.id}")
            self.stdout.write(f"  - Título: {registro.title}")
            self.stdout.write(f"  - Fecha: {registro.fecha}")
            self.stdout.write(f"  - Sitio: {registro.sitio.name}")
            self.stdout.write(f"  - Usuario: {registro.user.username}")
            self.stdout.write("")

    def arreglar_registro_especifico(self, registro_id, estructura_nombre):
        """Arregla un registro específico."""
        try:
            registro = RegConstruccion.objects.get(id=registro_id)
        except RegConstruccion.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Registro con ID {registro_id} no encontrado")
            )
            return

        if registro.estructura:
            self.stdout.write(
                self.style.WARNING(f"⚠️  El registro {registro_id} ya tiene estructura: {registro.estructura.nombre}")
            )
            return

        # Buscar estructura
        if estructura_nombre:
            try:
                estructura = GrupoComponentes.objects.get(nombre=estructura_nombre)
            except GrupoComponentes.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Estructura '{estructura_nombre}' no encontrada")
                )
                return
        else:
            # Usar la primera estructura disponible
            estructura = GrupoComponentes.objects.first()
            if not estructura:
                self.stdout.write(
                    self.style.ERROR("❌ No hay estructuras disponibles")
                )
                return
            estructura_nombre = estructura.nombre

        # Asignar estructura
        registro.estructura = estructura
        registro.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Registro {registro_id} arreglado: estructura '{estructura_nombre}' asignada"
            )
        )

    def auto_fix_registros(self):
        """Arregla automáticamente todos los registros sin estructura."""
        registros_sin_estructura = RegConstruccion.objects.filter(
            estructura__isnull=True
        )
        
        if not registros_sin_estructura.exists():
            self.stdout.write(
                self.style.SUCCESS("✅ No hay registros sin estructura para arreglar")
            )
            return

        # Obtener la estructura más común o la primera disponible
        estructura = GrupoComponentes.objects.first()
        if not estructura:
            self.stdout.write(
                self.style.ERROR("❌ No hay estructuras disponibles")
            )
            return

        self.stdout.write(f"🔧 Arreglando registros con estructura: {estructura.nombre}")
        
        for registro in registros_sin_estructura:
            registro.estructura = estructura
            registro.save()
            self.stdout.write(f"  ✅ Registro {registro.id} arreglado")

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Se arreglaron {registros_sin_estructura.count()} registros"
            )
        )
