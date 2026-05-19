from django.urls import path, include
from .views import (
    ListRegistrosView,
    StepsRegistroView,
    ElementoRegistroView,
    ActivarRegistroView,
    TableOnlyView,
    guardar_ejecucion,
    actualizar_ejecucion_ajax,
    RegConstruccionCreateView,
    RegConstruccionUpdateView,
    RegConstruccionDeleteView,
    dashboard_construccion,
    update_contratista,
    update_ito,
    update_estado,
    get_contractors,
    get_users_ito,
)
def _pdf_view(request, *args, **kwargs):
    from .pdf_views import RegConstruccionPDFView
    return RegConstruccionPDFView.as_view()(request, *args, **kwargs)

app_name = 'reg_construccion'

urlpatterns = [
    path('', ListRegistrosView.as_view(), name='list'),
    # path('dashboard/', dashboard_construccion, name='dashboard'),  # NO USADO
    path('activar/', ActivarRegistroView.as_view(), name='activar'),  # NO USADO
    path('crear/', RegConstruccionCreateView.as_view(), name='create'),
    path('guardar-ejecucion/<int:registro_id>/', guardar_ejecucion, name='guardar_ejecucion'),
    path('pdf/<int:registro_id>/', _pdf_view, name='pdf'),
    # path('preview/<int:registro_id>/', preview_reg_construccion_individual, name='preview'),  # NO USADO
    
    # APIs
    path('api/v1/contractors/', get_contractors, name='api_contractors'),
    path('api/v1/users_ito/', get_users_ito, name='api_users_ito'),
    path('api/v1/registros/<int:registro_id>/update_constructor/', update_contratista, name='api_update_constructor'),
    path('api/v1/registros/<int:registro_id>/update_ito/', update_ito, name='api_update_ito'),
    path('api/v1/registros/<int:registro_id>/update_estado/', update_estado, name='api_update_estado'),
    
    # Rutas con parámetros dinámicos (al final para evitar conflictos)
    path('<int:registro_id>/', StepsRegistroView.as_view(), name='steps'),
    path('<int:registro_id>/editar/', RegConstruccionUpdateView.as_view(), name='update'),
    # path('<int:registro_id>/eliminar/', RegConstruccionDeleteView.as_view(), name='delete'),  # NO USADO
    # path('<int:registro_id>/update-contratista/', update_contratista, name='update_contratista'),  # NO USADO
    path('<int:registro_id>/<str:paso_nombre>/', ElementoRegistroView.as_view(), name='elemento'),
    path('<int:registro_id>/<str:paso_nombre>/tabla/', TableOnlyView.as_view(), name='elemento_tabla'),
    # path('actualizar-ejecucion/<int:registro_id>/', actualizar_ejecucion_ajax, name='actualizar_ejecucion_ajax'),  # NO USADO
    
    # URLs de photos específicas para reg_construccion
    path('<int:registro_id>/<str:step_name>/photos/', include('photos.urls')),  # NO USADO
]