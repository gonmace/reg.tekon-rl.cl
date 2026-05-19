#!/usr/bin/env python3
"""
Comando para listar y gestionar grupos de componentes.
"""

from django.core.management.base import BaseCommand
from django.db.models import Sum
from proyectos.models import GrupoComponentes, Componente


class Command(BaseCommand):
    help = 'Lista grupos de componentes con sus incidencias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grupo',
            type=str,
            help='Nombre específico del grupo a mostrar'
        )
        parser.add_argument(
            '--detallado',
            action='store_true',
            help='Mostrar información detallada de cada grupo'
        )
        parser.add_argument(
            '--componentes',
            action='store_true',
            help='Mostrar todos los componentes disponibles'
        )

    def handle(self, *args, **options):
        grupo_nombre = options['grupo']
        detallado = options['detallado']
        mostrar_componentes = options['componentes']

        if mostrar_componentes:
            self.mostrar_componentes()
            return

        if grupo_nombre:
            self.mostrar_grupo_especifico(grupo_nombre, detallado)
        else:
            self.mostrar_todos_grupos(detallado)

    def mostrar_componentes(self):
        """Mostrar todos los componentes disponibles"""
        self.stdout.write("📋 Componentes disponibles:")
        self.stdout.write("=" * 50)
        
        componentes = Componente.objects.all().order_by('nombre')
        if not componentes:
            self.stdout.write("❌ No hay componentes creados")
            return
        
        for componente in componentes:
            grupos_count = componente.componentegrupo_set.count()
            self.stdout.write(f"• {componente.nombre} (usado en {grupos_count} grupos)")
        
        self.stdout.write(f"\n📊 Total: {componentes.count()} componentes")

    def mostrar_grupo_especifico(self, nombre, detallado):
        """Mostrar un grupo específico"""
        try:
            grupo = GrupoComponentes.objects.get(nombre=nombre)
            self.mostrar_grupo(grupo, detallado)
        except GrupoComponentes.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Grupo '{nombre}' no encontrado")
            )

    def mostrar_todos_grupos(self, detallado):
        """Mostrar todos los grupos"""
        grupos = GrupoComponentes.objects.all().order_by('nombre')
        
        if not grupos:
            self.stdout.write("❌ No hay grupos creados")
            return
        
        self.stdout.write(f"📊 Grupos de componentes ({grupos.count()} grupos):")
        self.stdout.write("=" * 60)
        
        for grupo in grupos:
            self.mostrar_grupo(grupo, detallado)
            if not detallado:
                self.stdout.write("-" * 40)

    def mostrar_grupo(self, grupo, detallado):
        """Mostrar información de un grupo específico"""
        componentes = grupo.componentes.all().order_by('orden', 'id')
        total_incidencia = componentes.aggregate(total=Sum('incidencia'))['total'] or 0
        
        # Estado del balance
        if total_incidencia == 100:
            estado = "✅ Balanceado"
            color = self.style.SUCCESS
        elif total_incidencia > 100:
            estado = f"❌ Excede 100% ({total_incidencia:.1f}%)"
            color = self.style.ERROR
        else:
            estado = f"⚠️  Incompleto ({total_incidencia:.1f}%)"
            color = self.style.WARNING
        
        self.stdout.write(f"\n🏷️  Grupo: {grupo.nombre}")
        self.stdout.write(f"📈 Total incidencia: {total_incidencia}%")
        self.stdout.write(color(estado))
        
        if detallado or componentes.count() > 0:
            self.stdout.write("\n📋 Componentes:")
            for cg in componentes:
                self.stdout.write(f"  • {cg.componente.nombre}: {cg.incidencia}%")
        
        if detallado:
            self.stdout.write(f"\n🔗 ID del grupo: {grupo.id}")

    def mostrar_resumen(self):
        """Mostrar resumen general"""
        grupos = GrupoComponentes.objects.all()
        componentes = Componente.objects.all()
        
        grupos_balanceados = sum(
            1 for grupo in grupos 
            if grupo.componentes.aggregate(total=Sum('incidencia'))['total'] == 100
        )
        
        self.stdout.write(f"\n📊 Resumen general:")
        self.stdout.write(f"  • Grupos: {grupos.count()}")
        self.stdout.write(f"  • Componentes: {componentes.count()}")
        self.stdout.write(f"  • Grupos balanceados: {grupos_balanceados}/{grupos.count()}")
