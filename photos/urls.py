from django.urls import path, include
from .views import ListPhotosView, UploadPhotosView, UpdatePhotoView, ReorderPhotosView, DeletePhotoView

app_name = "photos"

urlpatterns = [
    path("", ListPhotosView.as_view(), name="list"),
    path("upload/", UploadPhotosView.as_view(), name="upload"),
    path("update/", UpdatePhotoView.as_view(), name="update"),
    path("reorder/", ReorderPhotosView.as_view(), name="reorder"),
    path("delete/<int:photo_id>/", DeletePhotoView.as_view(), name="delete"),
]
