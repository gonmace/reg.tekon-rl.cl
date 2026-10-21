"""
URLs de Construcción Sitios (prefijo /reg_construccion/ y namespace 'reg_construccion':
el motor genérico de pasos asume que ambos coinciden).
"""
from django.urls import include, path

from .views import (
    ActivarRegistroView, DynamicPasoView, ListSitiosView, MapaSaveView, StepsRegistroView,
    delete_registro, formatear_registro, get_edit_form, mapa_dashboard, nueva_visita, pasos_config,
    resumen_formatear, toggle_concluido, update_registro, visitas_sitio,
)


# Imports pesados (weasyprint) perezosos: ver CLAUDE.md
def _pdf_view(request, *args, **kwargs):
    from .pdf_views import RegConstruccionPDFView
    return RegConstruccionPDFView.as_view()(request, *args, **kwargs)


def _pdf_secciones_fotos_view(request, *args, **kwargs):
    from .pdf_views import pdf_secciones_fotos
    return pdf_secciones_fotos(request, *args, **kwargs)


app_name = 'reg_construccion'

urlpatterns = [
    path('', ListSitiosView.as_view(), name='list'),
    path('sitio/<int:sitio_id>/visitas/', visitas_sitio, name='visitas_sitio'),
    path('api/mapa-dashboard/', mapa_dashboard, name='api_mapa_dashboard'),
    path('pasos/', pasos_config, name='pasos'),
    path('activar/', ActivarRegistroView.as_view(), name='activar'),

    path('api/registros/<int:registro_id>/nueva-visita/', nueva_visita, name='api_nueva_visita'),
    path('api/registros/<int:registro_id>/edit-form/', get_edit_form, name='api_edit_form'),
    path('api/registros/<int:registro_id>/update/', update_registro, name='api_update'),
    path('api/registros/<int:registro_id>/delete/', delete_registro, name='api_delete'),
    path('api/registros/<int:registro_id>/toggle-concluido/', toggle_concluido, name='api_toggle_concluido'),
    path('api/registros/<int:registro_id>/formatear/', formatear_registro, name='api_formatear'),
    path('api/registros/<int:registro_id>/resumen-formatear/', resumen_formatear, name='api_resumen_formatear'),
    path('api/registros/<int:registro_id>/pdf-secciones-fotos/', _pdf_secciones_fotos_view,
         name='api_pdf_secciones_fotos'),

    path('<int:registro_id>/paso/<str:paso_nombre>/', DynamicPasoView.as_view(), name='paso_dinamico'),
    path('<int:registro_id>/paso/<str:paso_nombre>/mapa/save/', MapaSaveView.as_view(), name='mapa_save'),
    path('<int:registro_id>/paso/<str:paso_nombre>/photos/',
         include(('photos.urls', 'photos'), namespace='photos_paso')),
    path('<int:registro_id>/<str:paso_nombre>/photos/',
         include(('photos.urls', 'photos'), namespace='photos')),

    path('<int:registro_id>/', StepsRegistroView.as_view(), name='steps'),

    path('pdf/<int:registro_id>/', _pdf_view, name='pdf'),
]
