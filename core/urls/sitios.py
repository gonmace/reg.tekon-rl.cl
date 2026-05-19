from django.urls import path, include
from rest_framework.routers import DefaultRouter
from core.views.sitios import (
    SitiosView,
    SiteViewSet,
    SiteEditModalView,
    SiteCreateModalView,
    SiteImportView,
    SiteImportTemplateView,
)

app_name = "sitios"

router = DefaultRouter()
router.register(r'sitios', SiteViewSet, basename='sitios')

urlpatterns = [
    path("sitios/", SitiosView.as_view(), name="sitios_list"),
    # Rutas específicas ANTES del router DRF (cuyo <pk> capturaría 'create-modal' como id)
    path('api/v1/sitios/create-modal/', SiteCreateModalView.as_view(), name='site_create_modal'),
    path('api/v1/sitios/import/', SiteImportView.as_view(), name='site_import'),
    path('api/v1/sitios/import-template/', SiteImportTemplateView.as_view(), name='site_import_template'),
    path('api/v1/sitios/<int:site_id>/edit-modal/', SiteEditModalView.as_view(), name='site_edit_modal'),
    path('api/v1/', include(router.urls)),
]
