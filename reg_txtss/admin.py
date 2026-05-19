"""
Admin para registros TX/TSS.
"""

from django.contrib import admin
from .models import RegTxtss, RSitio, RAcceso, REmpalme


@admin.register(RegTxtss)
class RegistrosAdmin(admin.ModelAdmin):
    list_display = ['sitio', 'user', 'alternativa', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['sitio__name', 'user__username']
    list_per_page = 10
    list_display_links = ['sitio']
    list_select_related = ['sitio', 'user']


@admin.register(RSitio)
class RSitioAdmin(admin.ModelAdmin):
    list_display = ['registro', 'lat', 'lon', 'altura', 'created_at']
    list_filter = ['created_at']
    search_fields = ['registro__sitio__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RAcceso)
class RAccesoAdmin(admin.ModelAdmin):
    list_display = ['registro', 'tipo_suelo', 'distancia', 'created_at']
    list_filter = ['created_at']
    search_fields = ['registro__sitio__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(REmpalme)
class REmpalmeAdmin(admin.ModelAdmin):
    list_display = ['registro', 'proveedor', 'capacidad', 'created_at']
    list_filter = ['created_at']
    search_fields = ['registro__sitio__name']
    readonly_fields = ['created_at', 'updated_at']
