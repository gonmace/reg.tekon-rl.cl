"""
Admin para registros TX/TSS.
"""

from django.contrib import admin
from .models import RegTxtss


@admin.register(RegTxtss)
class RegistrosAdmin(admin.ModelAdmin):
    list_display = ['sitio', 'user', 'alternativa', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['sitio__name', 'user__username']
    list_per_page = 10
    list_display_links = ['sitio']
    list_select_related = ['sitio', 'user']
