
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('core.urls.dashboard')),
    path('', include('core.urls.sitios')),
    path('', include('core.urls.contractors')),
    path('reg_txtss/', include('reg_txtss.urls')),
    path('photos/', include('photos.urls')),
    path('', include('pdf_reports.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('core.urls.api')),
    path('', include('users.urls')),
    path('actividades/', include('actividades.urls')),
    path('widgets/', include('widgets.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
