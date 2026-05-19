from django.core.management.base import BaseCommand
from core.models.app_settings import AppSettings


class Command(BaseCommand):
    help = 'Set up initial application settings including Google Maps API key'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-key',
            type=str,
            help='Google Maps API key to configure',
        )
        parser.add_argument(
            '--app-name',
            type=str,
            default='Reportes Tekon',
            help='Application name (default: Reportes Tekon)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing settings',
        )

    def handle(self, *args, **options):
        api_key = options['api_key']
        app_name = options['app_name']
        force = options['force']

        # Check if settings already exist
        existing_settings = AppSettings.objects.first()
        
        if existing_settings and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'AppSettings already exists (ID: {existing_settings.id}). '
                    'Use --force to update existing settings.'
                )
            )
            self.stdout.write(
                f'Current Google Maps API key: {"✓ Set" if existing_settings.google_maps_api_key else "✗ Not set"}'
            )
            return

        if not api_key:
            self.stdout.write(
                self.style.ERROR(
                    'Google Maps API key is required. Please provide it with --api-key option.'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    'To get a Google Maps API key:\n'
                    '1. Go to https://console.cloud.google.com/\n'
                    '2. Create a new project or select existing one\n'
                    '3. Enable the "Maps Static API"\n'
                    '4. Create credentials (API key)\n'
                    '5. Restrict the API key to Maps Static API only\n'
                    '6. Use the API key with this command: python manage.py setup_app_settings --api-key YOUR_API_KEY'
                )
            )
            return

        # Create or update settings
        if existing_settings and force:
            existing_settings.app_name = app_name
            existing_settings.google_maps_api_key = api_key
            existing_settings.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated AppSettings (ID: {existing_settings.id}) with new configuration'
                )
            )
        else:
            new_settings = AppSettings.objects.create(
                app_name=app_name,
                google_maps_api_key=api_key
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created new AppSettings (ID: {new_settings.id}) with configuration'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Application name: {app_name}\n'
                f'✓ Google Maps API key: {"✓ Set" if api_key else "✗ Not set"}'
            )
        )
        
        # Test the API key
        if api_key:
            self.stdout.write(
                self.style.WARNING(
                    'Testing Google Maps API key...'
                )
            )
            
            try:
                from core.utils.coordenadas import obtener_imagen_google_maps
                
                # Test with a simple coordinate
                test_coords = [{
                    'lat': -33.4567,
                    'lon': -70.6483,
                    'color': '#3B82F6',
                    'label': 'T',
                    'size': 'large'
                }]
                
                result = obtener_imagen_google_maps(
                    coordenadas=test_coords,
                    zoom=15,
                    maptype='hybrid',
                    scale=1,
                    tamano='400x300'
                )
                
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            '✓ Google Maps API key is working correctly!'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            '✗ Google Maps API key test failed. Please check your API key and ensure Maps Static API is enabled.'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error testing Google Maps API key: {str(e)}'
                    )
                ) 