from django.urls import path
from . import views

app_name = 'executive_dashboard'

urlpatterns = [
    path('sitios/', views.dashboard_sitios, name='sitios'),
    path('txtss/', views.dashboard_txtss, name='txtss'),
    path('api/stats/', views.api_dashboard_stats, name='api_stats'),
    path('api/sitio/<int:sitio_id>/', views.api_sitio_detail, name='api_sitio_detail'),
]
