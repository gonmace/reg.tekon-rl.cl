"""
Admin configuration for registros Reporte de construcción.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import RegConstruccion, AvanceComponente, AvanceComponenteComentarios, Objetivo, EjecucionPorcentajes


@admin.register(RegConstruccion)
class RegConstruccionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'fecha', 'title', 'sitio_link', 'estructura_link', 'user_link',
        'created_at', 'avance_status', 'actions_links'
    ]
    list_filter = [
        'sitio', 'estructura', 'user', 'created_at',
        ('created_at', admin.DateFieldListFilter)
    ]
    search_fields = ['title', 'description', 'sitio__name',
                     'estructura__name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    list_per_page = 25
    list_select_related = ['sitio', 'estructura', 'user']

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'fecha', 'description', 'sitio', 'estructura', 'user')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sitio_link(self, obj):
        if obj.sitio:
            url = reverse('admin:core_site_change', args=[obj.sitio.id])
            return format_html('<a href="{}">{}</a>', url, obj.sitio.name)
        return "Sin sitio"

    sitio_link.short_description = 'Sitio'
    sitio_link.admin_order_field = 'sitio__name'

    def estructura_link(self, obj):
        if obj.estructura:
            url = reverse('admin:proyectos_grupocomponentes_change',
                          args=[obj.estructura.id])
            return format_html('<a href="{}">{}</a>', url, obj.estructura.nombre)
        return "Sin estructura"

    estructura_link.short_description = 'Estructura'
    estructura_link.admin_order_field = 'estructura__name'

    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "Sin usuario"

    user_link.short_description = 'Usuario'
    user_link.admin_order_field = 'user__username'

    def avance_status(self, obj):
        avances = obj.avancecomponente_set.count()
        if avances > 0:
            return format_html(
                '<span style="color: green;">✓ {} avances</span>',
                avances
            )
        return format_html('<span style="color: orange;">⚠ Sin avances</span>')

    avance_status.short_description = 'Estado'

    def actions_links(self, obj):
        steps_url = reverse('reg_construccion:steps', args=[obj.id])
        pdf_url = reverse('reg_construccion:pdf', args=[obj.id])

        return format_html(
            '<a href="{}" class="button" style="margin-right: 5px;">Ver Pasos</a>'
            '<a href="{}" class="button">PDF</a>',
            steps_url, pdf_url
        )

    actions_links.short_description = 'Acciones'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sitio', 'estructura', 'user')


@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ['id', 'registro_link', 'objetivo_preview', 'created_at']
    list_filter = ['created_at', 'registro__sitio', 'registro__estructura']
    search_fields = ['objetivo', 'registro__title']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25

    def registro_link(self, obj):
        url = reverse('admin:reg_construccion_regconstruccion_change', args=[
            obj.registro.id])
        return format_html('<a href="{}">{}</a>', url, obj.registro.title)

    registro_link.short_description = 'Registro'
    registro_link.admin_order_field = 'registro__title'

    def objetivo_preview(self, obj):
        if obj.objetivo:
            return obj.objetivo[:100] + '...' if len(obj.objetivo) > 100 else obj.objetivo
        return "Sin objetivo"

    objetivo_preview.short_description = 'Objetivo'


@admin.register(AvanceComponenteComentarios)
class AvanceComponenteComentariosAdmin(admin.ModelAdmin):
    list_display = ['id', 'registro_link', 'comentarios_preview', 'created_at']
    list_filter = ['created_at', 'registro__sitio', 'registro__estructura']
    search_fields = ['comentarios', 'registro__title']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25

    def registro_link(self, obj):
        url = reverse('admin:reg_construccion_regconstruccion_change', args=[
            obj.registro.id])
        return format_html('<a href="{}">{}</a>', url, obj.registro.title)

    registro_link.short_description = 'Registro'
    registro_link.admin_order_field = 'registro__title'

    def comentarios_preview(self, obj):
        if obj.comentarios:
            return obj.comentarios[:100] + '...' if len(obj.comentarios) > 100 else obj.comentarios
        return "Sin comentarios"

    comentarios_preview.short_description = 'Comentarios'


@admin.register(AvanceComponente)
class AvanceComponenteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'registro_link', 'componente_link', 'fecha', 'porcentaje_anterior',
        'porcentaje_actual', 'porcentaje_acumulado', 'created_at'
    ]
    list_filter = [
        'fecha', 'created_at', 'registro__sitio', 'registro__estructura',
        'componente'
    ]
    search_fields = [
        'comentarios', 'registro__title', 'componente__nombre'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'fecha'
    list_per_page = 25
    list_select_related = ['registro', 'componente']

    fieldsets = (
        ('Información del Registro', {
            'fields': ('registro', 'componente')
        }),
        ('Avance', {
            'fields': ('fecha', 'porcentaje_anterior', 'porcentaje_actual', 'porcentaje_acumulado')
        }),
        ('Comentarios', {
            'fields': ('comentarios',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def registro_link(self, obj):
        url = reverse('admin:reg_construccion_regconstruccion_change', args=[
            obj.registro.id])
        return format_html('<a href="{}">{}</a>', url, obj.registro.title)

    registro_link.short_description = 'Registro'
    registro_link.admin_order_field = 'registro__title'

    def componente_link(self, obj):
        url = reverse('admin:proyectos_componente_change',
                      args=[obj.componente.id])
        return format_html('<a href="{}">{}</a>', url, obj.componente.nombre)

    componente_link.short_description = 'Componente'
    componente_link.admin_order_field = 'componente__nombre'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('registro', 'componente')


@admin.register(EjecucionPorcentajes)
class EjecucionPorcentajesAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'registro_link', 'componente_link',
        'porcentaje_ejec_actual', 'porcentaje_ejec_anterior', 'fecha_calculo'
    ]
    list_filter = [
        'fecha_calculo', 'registro__sitio', 'registro__estructura',
        'componente'
    ]
    search_fields = [
        'registro__title', 'componente__nombre'
    ]
    readonly_fields = ['fecha_calculo']
    date_hierarchy = 'fecha_calculo'
    list_per_page = 25
    list_select_related = ['registro', 'componente']

    fieldsets = (
        ('Información del Registro', {
            'fields': ('registro', 'componente')
        }),
        ('Porcentajes de Ejecución', {
            'fields': ('porcentaje_ejec_actual', 'porcentaje_ejec_anterior')
        }),
        ('Información del Cálculo', {
            'fields': ('fecha_calculo',),
            'classes': ('collapse',)
        }),
    )

    def registro_link(self, obj):
        url = reverse('admin:reg_construccion_regconstruccion_change', args=[
            obj.registro.id])
        return format_html('<a href="{}">{}</a>', url, obj.registro.title)

    registro_link.short_description = 'Registro'
    registro_link.admin_order_field = 'registro__title'

    def componente_link(self, obj):
        url = reverse('admin:proyectos_componente_change',
                      args=[obj.componente.id])
        return format_html('<a href="{}">{}</a>', url, obj.componente.nombre)

    componente_link.short_description = 'Componente'
    componente_link.admin_order_field = 'componente__nombre'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('registro', 'componente')


# Configuración del sitio admin
admin.site.site_header = "Administración de Reportes de Construcción"
admin.site.site_title = "Reportes de Construcción"
admin.site.index_title = "Panel de Administración"
