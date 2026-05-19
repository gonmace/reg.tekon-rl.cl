"""
Configuración de la aplicación Reporte de visita.
"""

from django.apps import AppConfig


class RegConstruccionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reg_construccion'
    verbose_name = 'Reporte de construcción'
    description = 'Aplicación para reporte de construcción'
