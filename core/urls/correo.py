"""URLs de la configuración de correo (solo superusuario)."""
from django.urls import path

from core.views.correo import CorreoConexionView, CorreoConfigView, CorreoGuardarView, CorreoProbarView

app_name = 'correo'

urlpatterns = [
    path('configuracion/correo/', CorreoConfigView.as_view(), name='config'),
    path('configuracion/correo/guardar/', CorreoGuardarView.as_view(), name='guardar'),
    path('configuracion/correo/conexion/', CorreoConexionView.as_view(), name='conexion'),
    path('configuracion/correo/probar/', CorreoProbarView.as_view(), name='probar'),
]
