from django.urls import path
from . import views

app_name = 'widgets'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('preview/<slug:slug>/', views.preview, name='preview'),
    path('icon/<slug:slug>/', views.icon_view, name='icon'),

    # Endpoints de fotos para pruebas del catálogo (solo dev)
    path('dev/photos/', views.DevPhotoListView.as_view(), name='dev_photo_list'),
    path('dev/photos/upload/', views.DevPhotoUploadView.as_view(), name='dev_photo_upload'),
    path('dev/photos/update/', views.DevPhotoUpdateView.as_view(), name='dev_photo_update'),
    path('dev/photos/delete/<int:photo_id>/', views.DevPhotoDeleteView.as_view(), name='dev_photo_delete'),
]
