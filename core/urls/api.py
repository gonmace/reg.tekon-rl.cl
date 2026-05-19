"""
URLs para las APIs del core.
"""

from django.urls import path
from core.views.google_maps import GoogleMapsAPIView

app_name = 'core_api'

urlpatterns = [
    path('v1/google-maps/', GoogleMapsAPIView.as_view(), name='google_maps_api'),
] 