"""
Comando de prueba simple para verificar que funciona.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Comando de prueba simple'

    def handle(self, *args, **options):
        self.stdout.write('¡Comando de prueba funcionando!')
        self.stdout.write(self.style.SUCCESS('✓ Comando ejecutado correctamente')) 