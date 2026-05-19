from django.apps import AppConfig


class ActividadesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actividades'
    verbose_name = 'Actividades'

    def ready(self):
        import actividades.signals  # noqa: F401
