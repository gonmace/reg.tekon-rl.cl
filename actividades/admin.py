import json

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html

from .models import TipoActividad, PasoDefinicion, ConfigPaso, ContextoRegistro

_ACTIVIDADES_ORDER = [
    'TipoActividad',
    'PasoDefinicion',
    'ConfigPaso',
    'ContextoRegistro',
]

_original_get_app_list = AdminSite.get_app_list


def _get_app_list_ordered(self, request, app_label=None):
    app_list = _original_get_app_list(self, request, app_label)
    for app in app_list:
        if app['app_label'] == 'actividades':
            app['models'].sort(
                key=lambda m: _ACTIVIDADES_ORDER.index(m['object_name'])
                if m['object_name'] in _ACTIVIDADES_ORDER else 99
            )
    return app_list


AdminSite.get_app_list = _get_app_list_ordered


class ConfigPasoInline(admin.TabularInline):
    model = ConfigPaso
    extra = 1
    fields = ('orden', 'pasodef')
    ordering = ('orden',)


@admin.register(TipoActividad)
class TipoActividadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'app_namespace', 'tipo_sitio', 'activo')
    list_filter = ('activo', 'tipo_sitio')
    prepopulated_fields = {'app_namespace': ('nombre',)}
    inlines = [ConfigPasoInline]


@admin.register(ContextoRegistro)
class ContextoRegistroAdmin(admin.ModelAdmin):
    list_display = ('registro_str', 'content_type', 'object_id', 'completion_pct', 'pasos_completos', 'updated_at')
    list_filter = ('content_type',)
    readonly_fields = ('content_type', 'object_id', 'updated_at', 'contexto_pretty')
    fields = ('content_type', 'object_id', 'updated_at', 'contexto_pretty')

    def registro_str(self, obj):
        try:
            registro = obj.registro
            return str(registro)
        except Exception:
            return f'{obj.content_type}/{obj.object_id}'
    registro_str.short_description = 'Registro'

    def completion_pct(self, obj):
        pct = obj.contexto.get('stats', {}).get('completion_pct', 0)
        color = '#22c55e' if pct == 100 else '#f59e0b' if pct > 0 else '#ef4444'
        return format_html('<span style="color:{}; font-weight:bold">{}%</span>', color, pct)
    completion_pct.short_description = 'Completitud'

    def pasos_completos(self, obj):
        stats = obj.contexto.get('stats', {})
        return f"{stats.get('pasos_completos', 0)} / {stats.get('pasos_total', 0)}"
    pasos_completos.short_description = 'Pasos'

    def contexto_pretty(self, obj):
        pretty = json.dumps(obj.contexto, indent=2, ensure_ascii=False, default=str)
        return format_html('<pre style="font-size:12px; max-height:600px; overflow:auto">{}</pre>', pretty)
    contexto_pretty.short_description = 'Contexto (JSON)'


@admin.register(PasoDefinicion)
class PasoDefinicionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'titulo', 'usos')
    ordering = ('titulo',)

    def usos(self, obj):
        return obj.asignaciones.count()
    usos.short_description = 'Usos'


