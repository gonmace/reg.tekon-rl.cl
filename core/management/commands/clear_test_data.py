"""
Borra los datos de prueba creados por seed_test_data (todo lo marcado con TEST_).

Uso:
    python manage.py clear_test_data
    python manage.py clear_test_data --yes   (sin prompt de confirmación)
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models.sites import Site
from core.models.contractors import Contractor
from users.models import User


class Command(BaseCommand):
    help = 'Borra todos los datos generados por seed_test_data'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Confirma sin preguntar')

    @transaction.atomic
    def handle(self, *args, **opts):
        sites = Site.objects.filter(name__startswith='TEST_')
        contractors = Contractor.objects.filter(code__startswith='TEST')
        users = User.objects.filter(username__startswith='test_user_')

        counts = {
            'Sitios': sites.count(),
            'Contratistas': contractors.count(),
            'Usuarios': users.count(),
        }
        total = sum(counts.values())

        if total == 0:
            self.stdout.write(self.style.WARNING('No hay datos de prueba para borrar.'))
            return

        self.stdout.write('Se borrarán:')
        for label, n in counts.items():
            self.stdout.write(f'  {label}: {n}')

        if not opts['yes']:
            confirm = input('\n¿Continuar? [y/N]: ').strip().lower()
            if confirm not in ('y', 'yes', 's', 'si'):
                self.stdout.write(self.style.WARNING('Cancelado.'))
                return

        sites.delete()
        contractors.delete()
        users.delete()

        self.stdout.write(self.style.SUCCESS(f'Borrados {total} registros.'))
