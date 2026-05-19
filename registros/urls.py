from django.urls import path, include

app_name = "registros"

urlpatterns = [
    path("registros/", include("photos.urls"), name="photos"),
]
