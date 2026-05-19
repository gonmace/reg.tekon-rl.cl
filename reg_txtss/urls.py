"""
URLs simplificadas para registros TX/TSS usando el sistema genérico.
"""

from django.urls import path, include
from .views import (
    ListRegistrosView,
    ListRegistrosPostesView,
    ListRegistrosTorresView,
    PasosPostesView,
    PasosTorresView,
    StepsRegistroView,
    ActivarRegistroView,
    DynamicPasoView,
    MapaSaveView,
    get_edit_form,
    update_registro,
    delete_registro,
    update_alternativa,
    update_fecha,
    copy_registro,
)


def _pdf_view(request, *args, **kwargs):
    from .pdf_views import RegTxtssPDFView
    return RegTxtssPDFView.as_view()(request, *args, **kwargs)


def _preview_view(request, *args, **kwargs):
    from .pdf_views import preview_reg_txtss_individual
    return preview_reg_txtss_individual(request, *args, **kwargs)


app_name = 'reg_txtss'

urlpatterns = [
    # Lista de registros
    path('', ListRegistrosView.as_view(), name='list'),
    path('postes/', ListRegistrosPostesView.as_view(), name='list_postes'),
    path('postes/pasos/', PasosPostesView.as_view(), name='pasos_postes'),
    path('torres/', ListRegistrosTorresView.as_view(), name='list_torres'),
    path('torres/pasos/', PasosTorresView.as_view(), name='pasos_torres'),

    # Activar registro
    path('activar/', ActivarRegistroView.as_view(), name='activar'),

    # API de registros
    path('api/registros/<int:registro_id>/edit-form/', get_edit_form, name='api_edit_form'),
    path('api/registros/<int:registro_id>/update/', update_registro, name='api_update'),
    path('api/registros/<int:registro_id>/delete/', delete_registro, name='api_delete'),
    path('api/registros/<int:registro_id>/update-alternativa/', update_alternativa, name='api_update_alternativa'),
    path('api/registros/<int:registro_id>/update-fecha/', update_fecha, name='api_update_fecha'),
    path('api/registros/<int:registro_id>/copy/', copy_registro, name='api_copy'),

    # Pasos dinámicos (configurados en actividades)
    path('<int:registro_id>/paso/<str:paso_nombre>/', DynamicPasoView.as_view(), name='paso_dinamico'),
    path('<int:registro_id>/paso/<str:paso_nombre>/mapa/save/', MapaSaveView.as_view(), name='mapa_save'),
    path('<int:registro_id>/paso/<str:paso_nombre>/photos/', include('photos.urls')),
    path('<int:registro_id>/<str:paso_nombre>/photos/', include('photos.urls')),

    # Pasos del registro
    path('<int:registro_id>/', StepsRegistroView.as_view(), name='steps'),

    # PDF
    path('pdf/<int:registro_id>/', _pdf_view, name='pdf'),
    path('preview/<int:registro_id>/', _preview_view, name='preview'),

]
