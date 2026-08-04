"""
Importa un JSON generado por `export_pasos_actividad`, aplicando la
configuración de Pasos + Widgets en este ambiente.

Idempotente y seguro de re-correr: matchea TipoActividad por app_namespace,
PasoDefinicion por (nombre, TipoActividad) vía ConfigPaso, y PasoWidget por
(pasodef, widget_slug) — nunca por ID de fila, que difiere entre ambientes.
No borra pasos/widgets que existan acá pero no vengan en el JSON (no hay
--prune); solo crea o actualiza.

Uso:
    python manage.py import_pasos_actividad --input pasos_torres.json --dry-run
    python manage.py import_pasos_actividad --input pasos_torres.json
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from actividades.models import ConfigPaso, PasoDefinicion, PasoWidget, TipoActividad


class Command(BaseCommand):
    help = 'Importa Pasos + Widgets de un TipoActividad desde un JSON de export_pasos_actividad'

    def add_arguments(self, parser):
        parser.add_argument('--input', type=str, required=True, help='Archivo JSON a importar')
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Muestra qué se crearía/actualizaría sin escribir en la base de datos',
        )

    def handle(self, *args, **options):
        input_file = options['input']
        dry_run = options['dry_run']

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"No existe el archivo '{input_file}'")
        except json.JSONDecodeError as e:
            raise CommandError(f"JSON inválido en '{input_file}': {e}")

        tipo_data = data['tipo_actividad']
        namespace = tipo_data['app_namespace']

        summary = {'tipo_creado': False, 'pasos_creados': [], 'pasos_actualizados': [],
                   'widgets_creados': [], 'widgets_actualizados': []}

        with transaction.atomic():
            tipo, tipo_created = TipoActividad.objects.get_or_create(
                app_namespace=namespace,
                defaults={
                    'nombre': tipo_data['nombre'],
                    'descripcion': tipo_data['descripcion'],
                    'tipo_sitio': tipo_data['tipo_sitio'],
                    'activo': tipo_data['activo'],
                },
            )
            summary['tipo_creado'] = tipo_created
            if not tipo_created:
                tipo.nombre = tipo_data['nombre']
                tipo.descripcion = tipo_data['descripcion']
                tipo.tipo_sitio = tipo_data['tipo_sitio']
                tipo.activo = tipo_data['activo']
                tipo.save()

            for step in data['pasos']:
                pasodef = PasoDefinicion.objects.filter(
                    nombre=step['nombre'], asignaciones__tipo=tipo
                ).first()
                if pasodef is None:
                    pasodef = PasoDefinicion(nombre=step['nombre'])
                    creating_paso = True
                else:
                    creating_paso = False
                pasodef.titulo = step['titulo']
                pasodef.descripcion = step['descripcion']
                pasodef.save()
                (summary['pasos_creados'] if creating_paso else summary['pasos_actualizados']).append(step['nombre'])

                ConfigPaso.objects.update_or_create(
                    tipo=tipo, pasodef=pasodef, defaults={'orden': step['orden']},
                )

                for w in step['widgets']:
                    pw, w_created = PasoWidget.objects.update_or_create(
                        pasodef=pasodef, widget_slug=w['widget_slug'],
                        defaults={'orden': w['orden'], 'config': w['config']},
                    )
                    label = f"{step['nombre']}/{w['widget_slug']}"
                    (summary['widgets_creados'] if w_created else summary['widgets_actualizados']).append(label)

            if dry_run:
                transaction.set_rollback(True)

        self._print_summary(namespace, summary, dry_run)

    def _print_summary(self, namespace, summary, dry_run):
        prefix = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write(f"{prefix}TipoActividad '{namespace}': {'creado' if summary['tipo_creado'] else 'ya existía (actualizado)'}")
        if summary['pasos_creados']:
            self.stdout.write(self.style.SUCCESS(f"{prefix}Pasos creados: {', '.join(summary['pasos_creados'])}"))
        if summary['pasos_actualizados']:
            self.stdout.write(f"{prefix}Pasos actualizados: {', '.join(summary['pasos_actualizados'])}")
        if summary['widgets_creados']:
            self.stdout.write(self.style.SUCCESS(f"{prefix}Widgets creados: {', '.join(summary['widgets_creados'])}"))
        if summary['widgets_actualizados']:
            self.stdout.write(f"{prefix}Widgets actualizados: {', '.join(summary['widgets_actualizados'])}")
        if dry_run:
            self.stdout.write(self.style.WARNING('Dry-run: no se escribió nada en la base de datos.'))
        else:
            self.stdout.write(self.style.SUCCESS('Import aplicado correctamente.'))
