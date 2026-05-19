from django.urls import path

app_name = 'pdf_reports'

def _pdf_view(request, *args, **kwargs):
    from .views import RegistroPDFView
    return RegistroPDFView.as_view()(request, *args, **kwargs)

def _preview_view(request, *args, **kwargs):
    from .views import preview_registro_individual
    return preview_registro_individual(request, *args, **kwargs)

urlpatterns = [
    path('pdf/<int:registro_id>/', _pdf_view, name='registro_pdf'),
    path('preview/<int:registro_id>/', _preview_view, name='preview_registro_individual'),
]