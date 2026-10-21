from django.apps import AppConfig


class RegTxtssConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reg_txtss'

    def ready(self):
        from registros.registry import register_registro_model
        from .models import RegTxtss
        register_registro_model('reg_txtss', RegTxtss)
