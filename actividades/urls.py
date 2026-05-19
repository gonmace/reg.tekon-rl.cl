from django.urls import path

from .views import save_widget_data
from .views_catalogo import (
    PasoDefinicionCloneView,
    PasoDefinicionDeleteView,
    PasoDefinicionListView,
    PasoDefinicionModalView,
    PasoWidgetsSetView,
    TipoActividadListView,
    TipoPasoAddView,
    TipoPasoCreateView,
    TipoPasoRemoveView,
    TipoPasosExportView,
    TipoPasosImportView,
    TipoPasosView,
)

app_name = 'actividades'

urlpatterns = [
    # Catálogo de pasos (solo superusuarios)
    path('pasos/', PasoDefinicionListView.as_view(), name='paso_list'),
    path('pasos/modal/', PasoDefinicionModalView.as_view(), name='paso_create_modal'),
    path('pasos/<int:pk>/modal/', PasoDefinicionModalView.as_view(), name='paso_edit_modal'),
    path('pasos/<int:pk>/eliminar/', PasoDefinicionDeleteView.as_view(), name='paso_delete'),
    path('pasos/<int:pk>/clonar/', PasoDefinicionCloneView.as_view(), name='paso_clone'),
    path('pasos/<int:pk>/widgets/', PasoWidgetsSetView.as_view(), name='paso_widgets_set'),

    # API de widgets
    path('api/pasos/<str:paso_nombre>/widgets/<str:widget_slug>/', save_widget_data, name='save_widget_data'),

    # Tipos de Actividad — asignación de pasos
    path('tipos/', TipoActividadListView.as_view(), name='tipo_list'),
    path('tipos/<int:pk>/pasos/', TipoPasosView.as_view(), name='tipo_pasos'),
    path('tipos/<int:pk>/pasos/crear/', TipoPasoCreateView.as_view(), name='tipo_paso_crear'),
    path('tipos/<int:pk>/pasos/agregar/', TipoPasoAddView.as_view(), name='tipo_paso_add'),
    path('tipos/<int:pk>/pasos/<int:cp_pk>/quitar/', TipoPasoRemoveView.as_view(), name='tipo_paso_remove'),
    path('tipos/<int:pk>/pasos/exportar/', TipoPasosExportView.as_view(), name='tipo_pasos_exportar'),
    path('tipos/<int:pk>/pasos/importar/', TipoPasosImportView.as_view(), name='tipo_pasos_importar'),
]
