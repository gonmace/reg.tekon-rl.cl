from django.contrib import admin
from .models import DashboardMetric, SitioDashboard


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'last_updated']
    list_filter = ['metric_type', 'last_updated']
    readonly_fields = ['last_updated']
    search_fields = ['metric_type']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('metric_type',)
        return self.readonly_fields


@admin.register(SitioDashboard)
class SitioDashboardAdmin(admin.ModelAdmin):
    list_display = ['sitio', 'total_registros_txtss', 'ultimo_registro_txtss', 'last_updated']
    list_filter = ['last_updated', 'sitio__region']
    readonly_fields = ['last_updated']
    search_fields = ['sitio__name', 'sitio__pti_cell_id']
    list_select_related = ['sitio']

    actions = ['update_metrics']

    def update_metrics(self, request, queryset):
        updated = 0
        for sitio_dashboard in queryset:
            sitio_dashboard.update_metrics()
            updated += 1
        self.message_user(request, f'Se actualizaron las métricas de {updated} sitio(s).')

    update_metrics.short_description = 'Actualizar métricas de sitios seleccionados'
