from django.urls import path, include
from .views import (
    ListPhotosView, UploadPhotosView, UpdatePhotoView, ReorderPhotosView, DeletePhotoView,
    PhotoGalleryView, BulkDeletePhotosView, BulkDownloadPhotosView, CompressPhotosView,
)

app_name = "photos"

urlpatterns = [
    path("", ListPhotosView.as_view(), name="list"),
    path("upload/", UploadPhotosView.as_view(), name="upload"),
    path("update/", UpdatePhotoView.as_view(), name="update"),
    path("reorder/", ReorderPhotosView.as_view(), name="reorder"),
    path("delete/<int:photo_id>/", DeletePhotoView.as_view(), name="delete"),
    path("imagenes/", PhotoGalleryView.as_view(), name="gallery"),
    path("imagenes/bulk-delete/", BulkDeletePhotosView.as_view(), name="bulk_delete"),
    path("imagenes/bulk-download/", BulkDownloadPhotosView.as_view(), name="bulk_download"),
    path("imagenes/compress/", CompressPhotosView.as_view(), name="compress"),
]
