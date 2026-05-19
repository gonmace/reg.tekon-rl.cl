"""
Tablas genéricas para registros.
"""

import django_tables2 as tables
from django_tables2 import A
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from registros.models.base import RegistroBase

User = get_user_model()

class GenericRegistrosTable(tables.Table):
    """
    Tabla genérica para mostrar registros.
    Puede ser configurada para cualquier aplicación que herede de RegistroBase.
    """
    
    # Columnas básicas
    pti_id = tables.Column(
        accessor='sitio.pti_cell_id',
        verbose_name='PTI ID',
        attrs={'td': {'class': 'text-left py-1 md:px-4'}, 'th': {'class': 'text-left'}}
    )

    operador_id = tables.Column(
        accessor='sitio.operator_id',
        verbose_name='Operador ID',
        attrs={'td': {'class': 'text-left py-1 md:px-4'}, 'th': {'class': 'text-left'}}
    )

    nombre_sitio = tables.Column(
        accessor='sitio.name',
        verbose_name='Nombre Sitio',
        attrs={'td': {'class': 'w-fit max-w-40 py-1 md:px-4'}}
    )

    estado = tables.Column(
        accessor='estado',
        verbose_name='Estado',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}}
    )

    # Columna ITO (solo para superusuarios)
    ito = tables.Column(
        accessor='user.username',
        verbose_name='ITO',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
        empty_values=()
    )

    # Columna Constructor (solo para superusuarios)
    constructor = tables.Column(
        accessor='contratista.name',
        verbose_name='Constructor',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
        empty_values=()
    )

    # Columna de acciones
    acciones = tables.TemplateColumn(
        template_name='components/registro_actions.html',
        verbose_name='Acciones',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
        orderable=False
    )

    class Meta:
        template_name = "django_tables2/cupertino.html"
        attrs = {
            'class': 'table w-full',
        }
        row_attrs = {'class': 'pt-2'}
        fields = ('pti_id', 'operador_id', 'nombre_sitio', 'estado')
        sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'estado')
        orderable = True
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.app_namespace = kwargs.pop('app_namespace', 'registros')
        super().__init__(*args, **kwargs)
        
        # Agregar columnas adicionales para superusuarios
        if self.user and self.user.is_superuser:
            # Las columnas ya están definidas en la clase, solo necesitamos actualizar la secuencia
            self.Meta.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'estado', 'ito', 'constructor', 'acciones')
    
    def render_estado(self, value, record):
        """Renderizar el estado del proyecto con funcionalidad de edición para superusuarios."""
        # Debug: imprimir el valor que se está recibiendo
        print(f"DEBUG - Valor de estado recibido: '{value}' (tipo: {type(value)}) para registro {record.id}")
        
        # Mapeo de estados unificado - debe coincidir con changeStatus.js
        estado_map = {
            'Construcción': ('Construcción', 'badge badge-success'),
            'Paralizado': ('Paralizado', 'badge badge-warning'),
            'Cancelado': ('Cancelado', 'badge badge-error'),
            'Concluido': ('Concluido', 'badge badge-info'),
        }
        
        # Normalizar el valor para la búsqueda
        if value:
            value_str = str(value).lower().strip()
            print(f"DEBUG - Valor normalizado: '{value_str}'")
            
            # Buscar en el mapeo - primero por valor normalizado, luego por valor original
            if value_str in estado_map:
                display_text, badge_class = estado_map[value_str]
            elif str(value) in estado_map:
                display_text, badge_class = estado_map[str(value)]
            else:
                display_text, badge_class = (str(value), 'badge badge-neutral')
            
            print(f"DEBUG - Mapeo encontrado: '{value_str}' -> '{display_text}' con clase '{badge_class}'")
        else:
            display_text, badge_class = ('Sin estado', 'badge badge-neutral')
            print(f"DEBUG - Valor vacío, usando: '{display_text}' con clase '{badge_class}'")
        
        if self.user and self.user.is_superuser:
            return format_html(
                '<div class="estado-cell-container">'
                '<span class="estado-text" style="cursor: pointer;" data-registro-id="{}">'
                '<span class="{}">{}</span></span>'
                '<select class="estado-select select select-warning select-sm select-bordered w-full max-w-full" '
                'style="display: none;" data-registro-id="{}">'
                '<option value="">Seleccionar Estado</option>'
                '</select></div>',
                record.id,
                badge_class,
                display_text,
                record.id
            )
        
        # Para usuarios no superusuarios, mostrar solo el badge
        return format_html('<span class="{}">{}</span>', badge_class, display_text)
    
    def render_ito(self, value, record):
        """Renderizar la columna ITO con funcionalidad de edición para superusuarios."""
        if self.user and self.user.is_superuser:
            return format_html(
                '<div class="ito-cell-container">'
                '<span class="ito-text" style="cursor: pointer;" data-registro-id="{}">'
                '{}</span>'
                '<select class="ito-select select select-warning select-sm select-bordered w-full max-w-full" '
                'style="display: none;" data-registro-id="{}">'
                '<option value="">Seleccionar ITO</option>'
                '</select></div>',
                record.id,
                value or "Sin asignar",
                record.id
            )
        return value or "Sin asignar"
    
    def render_constructor(self, value, record):
        """Renderizar la columna Constructor con funcionalidad de edición para superusuarios."""
        if self.user and self.user.is_superuser:
            return format_html(
                '<div class="constructor-cell-container">'
                '<span class="constructor-text" style="cursor: pointer;" data-registro-id="{}">'
                '{}</span>'
                '<select class="constructor-select select select-warning select-sm select-bordered w-full max-w-full" '
                'style="display: none;" data-registro-id="{}">'
                '<option value="">Seleccionar Constructor</option>'
                '</select></div>',
                record.id,
                value or "Sin asignar",
                record.id
            )
        return value or "Sin asignar"


def create_registros_table(model_class, app_namespace='registros'):
    """
    Factory function para crear una tabla específica para un modelo de registro.
    
    Args:
        model_class: Clase del modelo que hereda de RegistroBase
        app_namespace: Namespace de la aplicación para las URLs
    
    Returns:
        Clase de tabla configurada
    """
    class SpecificRegistrosTable(GenericRegistrosTable):
        class Meta(GenericRegistrosTable.Meta):
            model = model_class
    
    return SpecificRegistrosTable 