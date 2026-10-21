from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import RegConstruccion


@admin.register(RegConstruccion)
class RegConstruccionAdmin(SimpleHistoryAdmin):
    list_display = ('sitio', 'fecha', 'user', 'contratista', 'estado_obra', 'avance_pct', 'concluido', 'is_deleted')
    list_filter = ('estado_obra', 'concluido', 'is_deleted', 'contratista')
    search_fields = ('sitio__pti_cell_id', 'sitio__name', 'proyecto')
    autocomplete_fields = ()
    raw_id_fields = ('sitio', 'user')
