"""
Tablas django-tables2 para la app core.
"""

import django_tables2 as tables
from django.utils.html import format_html

from core.models.contractors import Contractor
from core.models.sites import Site
from users.models import User


CUPERTINO_TEMPLATE = "django_tables2/cupertino.html"


class SiteTable(tables.Table):
    pti_cell_id = tables.Column(
        verbose_name='PTI ID',
        attrs={'th': {'class': 'text-left'}, 'td': {'class': 'text-left py-1 md:px-4'}},
    )
    operator_id = tables.Column(
        verbose_name='Operador ID',
        attrs={'th': {'class': 'text-left'}, 'td': {'class': 'text-left py-1 md:px-4'}},
    )
    name = tables.Column(verbose_name='Nombre Sitio', attrs={'td': {'class': 'py-1 md:px-4'}})
    tipo_sitio = tables.TemplateColumn(
        template_name='partials/site_tipo_sitio_badge.html',
        verbose_name='Tipo',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    region = tables.Column(verbose_name='Región', attrs={'td': {'class': 'py-1 md:px-4'}})
    comuna = tables.Column(verbose_name='Comuna', attrs={'td': {'class': 'py-1 md:px-4'}})
    acciones = tables.TemplateColumn(
        template_name='partials/site_actions.html',
        verbose_name='Acciones',
        orderable=False,
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )

    class Meta:
        model = Site
        template_name = CUPERTINO_TEMPLATE
        attrs = {'class': 'table w-full'}
        row_attrs = {'class': 'pt-2'}
        fields = ('pti_cell_id', 'operator_id', 'name', 'tipo_sitio', 'region', 'comuna', 'acciones')
        sequence = ('pti_cell_id', 'operator_id', 'name', 'tipo_sitio', 'region', 'comuna', 'acciones')
        order_by = ('pti_cell_id',)
        empty_text = 'No hay sitios para mostrar.'

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not (self.user and self.user.is_superuser):
            self.exclude = ('acciones',)


class ContractorTable(tables.Table):
    name = tables.Column(verbose_name='Nombre', attrs={'td': {'class': 'py-1 md:px-4'}})
    code = tables.Column(
        verbose_name='Código',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    is_active = tables.Column(
        verbose_name='Estado',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    acciones = tables.TemplateColumn(
        template_name='partials/contractor_actions.html',
        verbose_name='Acciones',
        orderable=False,
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )

    class Meta:
        model = Contractor
        template_name = CUPERTINO_TEMPLATE
        attrs = {'class': 'table w-full contractors-table'}
        row_attrs = {'class': 'pt-2'}
        fields = ('name', 'code', 'is_active', 'acciones')
        sequence = ('name', 'code', 'is_active', 'acciones')
        order_by = ('name',)
        empty_text = 'No hay contratistas para mostrar.'

    def render_is_active(self, value):
        if value:
            return format_html('<span class="badge badge-success badge-outline">Activo</span>')
        return format_html('<span class="badge badge-error badge-outline">Inactivo</span>')


class UserTable(tables.Table):
    get_full_name = tables.Column(
        verbose_name='Nombre',
        attrs={'td': {'class': 'py-1 md:px-4'}},
        orderable=False,
    )
    username = tables.Column(
        verbose_name='Correo',
        attrs={'td': {'class': 'py-1 md:px-4'}},
    )
    contractor = tables.Column(
        verbose_name='Empresa',
        attrs={'td': {'class': 'py-1 md:px-4'}},
        orderable=False,
    )
    user_type = tables.Column(
        verbose_name='Rol',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    is_active = tables.Column(
        verbose_name='Estado',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    acciones = tables.TemplateColumn(
        template_name='partials/user_actions.html',
        verbose_name='Acciones',
        orderable=False,
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )

    class Meta:
        model = User
        template_name = CUPERTINO_TEMPLATE
        attrs = {'class': 'table w-full'}
        row_attrs = {'class': 'pt-2'}
        fields = ('get_full_name', 'username', 'contractor', 'user_type', 'is_active', 'acciones')
        sequence = ('get_full_name', 'username', 'contractor', 'user_type', 'is_active', 'acciones')
        order_by = ('user_type', 'first_name', 'last_name')
        empty_text = 'No hay usuarios para mostrar.'

    def render_contractor(self, value, record):
        if not record.contractor_id:
            return format_html('<span class="text-base-content/40 text-xs">—</span>')
        return format_html('<span class="text-sm">{}</span>', record.contractor.code)

    def render_user_type(self, value, record):
        if not record.user_type:
            return format_html('<span class="badge badge-primary text-xs">Superusuario</span>')
        badge_classes = {
            User.GERENCIA:  'badge-error',
            User.COORD:     'badge-warning',
            User.ITO:       'badge-info',
            User.SEARCHER:  'badge-accent',
            User.VISITA:    'badge-neutral',
        }
        cls = badge_classes.get(record.user_type, 'badge-ghost')
        return format_html('<span class="badge {} text-xs">{}</span>', cls, record.get_user_type)

    def render_is_active(self, value):
        if value:
            return format_html('<span class="badge badge-success badge-outline">Activo</span>')
        return format_html('<span class="badge badge-error badge-outline">Inactivo</span>')
