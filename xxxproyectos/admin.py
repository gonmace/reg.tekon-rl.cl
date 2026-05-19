"""
Configuración del admin para la aplicación de proyectos.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Avg
from django.core.exceptions import ValidationError
from django import forms
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase
from .models import Componente, GrupoComponentes, ComponenteGrupo


class ComponenteGrupoInline(SortableInlineAdminMixin, admin.TabularInline):
    model = ComponenteGrupo
    extra = 0
    fields = ['orden_display', 'componente', 'incidencia']
    readonly_fields = ['orden', 'orden_display']
    
    def get_queryset(self, request):
        """Asegurar que los componentes se muestren en el orden correcto"""
        qs = super().get_queryset(request)
        return qs.order_by('orden', 'id')
    
    def orden_display(self, obj):
        """Mostrar el orden de manera visual"""
        if obj.orden is not None:
            return f"#{obj.orden + 1}"
        return "-"
    orden_display.short_description = "Orden"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        class CustomForm(formset.form):
            def clean(self):
                cleaned_data = super().clean()
                # Validar que la incidencia esté entre 0 y 100
                incidencia = cleaned_data.get('incidencia')
                if incidencia is not None and (incidencia < 0 or incidencia > 100):
                    raise ValidationError('La incidencia debe estar entre 0% y 100%')
                return cleaned_data
        
        formset.form = CustomForm
        return formset


@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'num_grupos', 'total_incidencia']
    search_fields = ['nombre']
    ordering = ['nombre']
    
    def num_grupos(self, obj):
        return obj.componentegrupo_set.count()
    num_grupos.short_description = 'Grupos'
    
    def total_incidencia(self, obj):
        total = obj.componentegrupo_set.aggregate(total=Sum('incidencia'))['total'] or 0
        return f"{total}%"
    total_incidencia.short_description = 'Total Incidencia'


@admin.register(GrupoComponentes)
class GrupoComponentesAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ['nombre', 'num_componentes', 'porcentaje_incidencia_total', 'estado_balance']
    search_fields = ['nombre']
    ordering = ['nombre']
    inlines = [ComponenteGrupoInline]
    
    def num_componentes(self, obj):
        return obj.componentes.count()
    num_componentes.short_description = 'Componentes'
    
    def porcentaje_incidencia_total(self, obj):
        total = obj.componentes.aggregate(total=Sum('incidencia'))['total'] or 0
        return f"{total}%"
    porcentaje_incidencia_total.short_description = '% Incidencia Total'
    
    def estado_balance(self, obj):
        total = obj.componentes.aggregate(total=Sum('incidencia'))['total'] or 0
        if total == 100:
            return format_html('<span style="color: green;">✓ Balanceado (100%)</span>')
        elif total > 100:
            return format_html('<span style="color: red;">✗ Excede 100% ({:.1f}%)</span>', total)
        else:
            return format_html('<span style="color: orange;">⚠ Incompleto ({:.1f}%)</span>', total)
    estado_balance.short_description = 'Estado del Balance'
    
    def save_formset(self, request, form, formset, change):
        """Validar que la suma de incidencias sea 100% al guardar y asignar orden"""
        instances = formset.save(commit=False)
        
        # Asignar orden automáticamente a nuevos componentes
        existing_orders = set()
        for instance in instances:
            if instance.id:  # Componente existente
                existing_orders.add(instance.orden)
            else:  # Nuevo componente
                # Encontrar el siguiente orden disponible
                next_order = 0
                while next_order in existing_orders:
                    next_order += 1
                instance.orden = next_order
                existing_orders.add(next_order)
        
        # Calcular total de incidencias
        total_incidencia = sum(
            instance.incidencia for instance in instances 
            if instance.incidencia is not None
        )
        
        # Agregar incidencias existentes que no se están editando
        existing_incidencias = form.instance.componentes.exclude(
            id__in=[instance.id for instance in instances if instance.id]
        ).aggregate(total=Sum('incidencia'))['total'] or 0
        
        total_final = total_incidencia + existing_incidencias
        
        if total_final != 100:
            raise ValidationError(
                f'La suma total de incidencias debe ser 100%. '
                f'Actualmente suma {total_final:.1f}%'
            )
        
        super().save_formset(request, form, formset, change)


@admin.register(ComponenteGrupo)
class ComponenteGrupoAdmin(admin.ModelAdmin):
    list_display = ['grupo', 'componente', 'incidencia', 'porcentaje_formato']
    list_filter = ['grupo', 'componente']
    search_fields = ['grupo__nombre', 'componente__nombre']
    ordering = ['grupo', 'componente']
    
    def incidencia(self, obj):
        return f"{obj.incidencia}%"
    incidencia.short_description = '% Incidencia'
    
    def porcentaje_formato(self, obj):
        return f"{obj.incidencia:.1f}%"
    porcentaje_formato.short_description = 'Incidencia'
