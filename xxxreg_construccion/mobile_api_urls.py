"""
URLs específicas para las APIs móviles de reg_construccion.
"""

from django.urls import path
from .mobile_api_views import (
    sitios_activos_por_usuario,
    crear_nueva_fecha,
    llenar_objetivo,
    llenar_avance,
    llenar_tabla,
    subir_imagenes,
    obtener_imagenes,
    editar_imagen,
    eliminar_imagen,
    obtener_registro_completo,
    login,
    fechas_por_usuario,
    obtener_objetivo,
    obtener_avance,
    obtener_tabla
)

app_name = 'mobile_api'

urlpatterns = [
    path('sitios-activos/', sitios_activos_por_usuario, name='sitios_activos'),

    path('fechas-por-usuario/', fechas_por_usuario, name='fechas_por_usuario'),

    path('crear-fecha/', crear_nueva_fecha, name='crear_fecha'),

    path('llenar-objetivo/', llenar_objetivo, name='llenar_objetivo'),
    path("obtener-objetivo/<int:registro_id>/", obtener_objetivo, name="obtener_objetivo"),
    path('llenar-avance/', llenar_avance, name='llenar_avance'),

    path("obtener-avance/<int:registro_id>/", obtener_avance, name="obtener_avance"),

    path('llenar-tabla/', llenar_tabla, name='llenar_tabla'),

    path("obtener-tabla/<int:registro_id>/", obtener_tabla, name="obtener_tabla"),

    path('subir-imagenes/', subir_imagenes, name='subir_imagenes'),

    path("editar-imagen/<int:imagen_id>/", editar_imagen, name="editar_imagen"),

    path("eliminar-imagen/<int:imagen_id>/", eliminar_imagen, name="eliminar_imagen"),

    path('obtener-imagenes/<int:registro_id>/', obtener_imagenes, name='obtener_imagenes'),

    path('registro-completo/<int:registro_id>/',
         obtener_registro_completo, name='registro_completo'),

    path('login/', login, name='login'),
]
