from django.apps import AppConfig


class RegConstruccionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reg_construccion'
    verbose_name = 'Construcción Sitios'

    def ready(self):
        from registros.registry import register_registro_model
        from . import signals  # noqa: F401
        from .models import RegConstruccion
        register_registro_model('reg_construccion', RegConstruccion)
