from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Prueba la Google Maps API key configurada en GOOGLE_MAPS_API_KEY (.env)'

    def handle(self, *args, **options):
        api_key = settings.GOOGLE_MAPS_API_KEY

        if not api_key:
            self.stdout.write(
                self.style.ERROR(
                    'GOOGLE_MAPS_API_KEY no está configurada en .env.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'Para obtener una Google Maps API key:\n'
                    '1. Ir a https://console.cloud.google.com/\n'
                    '2. Crear o seleccionar un proyecto\n'
                    '3. Habilitar "Maps Static API"\n'
                    '4. Crear credenciales (API key)\n'
                    '5. Restringir la API key a Maps Static API\n'
                    '6. Agregar GOOGLE_MAPS_API_KEY=<tu-api-key> al archivo .env'
                )
            )
            return

        self.stdout.write(self.style.WARNING('Probando Google Maps API key...'))

        from core.utils.coordenadas import obtener_imagen_google_maps

        test_coords = [{
            'lat': -33.4567,
            'lon': -70.6483,
            'color': '#3b82f6',
            'label': 'T',
            'size': 'large',
        }]

        result = obtener_imagen_google_maps(
            coordenadas=test_coords,
            zoom=15,
            maptype='hybrid',
            scale=1,
            tamano='400x300',
        )

        if result:
            self.stdout.write(self.style.SUCCESS('✓ Google Maps API key funciona correctamente'))
        else:
            self.stdout.write(
                self.style.ERROR(
                    '✗ La prueba falló. Verifica la API key y que Maps Static API esté habilitada.'
                )
            )
