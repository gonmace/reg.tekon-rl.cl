"""
Exporta la configuración de Pasos + Widgets de un TipoActividad (ej. "TX/TSS
Torres") a un JSON portable entre ambientes.

Se exporta por NOMBRE/NAMESPACE, nunca por ID de fila — los IDs de
TipoActividad/PasoDefinicion/PasoWidget difieren entre este ambiente y
producción (y ni siquiera son estables entre dos lecturas acá: cada edición
en el admin borra y recrea la fila). El import (`import_pasos_actividad`)
matchea por esas claves naturales, así que el export/import es idempotente y
seguro de re-correr.

Uso:
    python manage.py export_pasos_actividad --namespace reg_txtss_torres --output pasos_torres.json
    python manage.py export_pasos_actividad --namespace reg_txtss_torres   # imprime a stdout
"""
import json

from django.core.management.base import BaseCommand, CommandError

from actividades.models import TipoActividad


class Command(BaseCommand):
    help = 'Exporta Pasos + Widgets de un TipoActividad a JSON (portable entre ambientes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--namespace', type=str, required=True,
            help='app_namespace del TipoActividad a exportar (ej. reg_txtss_torres)',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='Archivo de salida. Si se omite, imprime el JSON a stdout.',
        )

    def handle(self, *args, **options):
        namespace = options['namespace']
        try:
            tipo = TipoActividad.objects.get(app_namespace=namespace)
        except TipoActividad.DoesNotExist:
            raise CommandError(f"No existe un TipoActividad con app_namespace='{namespace}'")

        config_pasos = (
            tipo.config_pasos
            .select_related('pasodef')
            .prefetch_related('pasodef__paso_widgets')
            .order_by('orden')
        )

        data = {
            'tipo_actividad': {
                'app_namespace': tipo.app_namespace,
                'nombre': tipo.nombre,
                'descripcion': tipo.descripcion,
                'tipo_sitio': tipo.tipo_sitio,
                'activo': tipo.activo,
            },
            'pasos': [
                {
                    'nombre': cp.pasodef.nombre,
                    'titulo': cp.pasodef.titulo,
                    'descripcion': cp.pasodef.descripcion,
                    'orden': cp.orden,
                    'widgets': [
                        {'widget_slug': pw.widget_slug, 'orden': pw.orden, 'config': pw.config}
                        for pw in cp.pasodef.paso_widgets.order_by('orden')
                    ],
                }
                for cp in config_pasos
            ],
        }

        payload = json.dumps(data, ensure_ascii=False, indent=2)

        output = options['output']
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(payload)
            n_pasos = len(data['pasos'])
            n_widgets = sum(len(p['widgets']) for p in data['pasos'])
            self.stdout.write(self.style.SUCCESS(
                f"Exportado '{namespace}': {n_pasos} pasos, {n_widgets} widgets → {output}"
            ))
        else:
            self.stdout.write(payload)
