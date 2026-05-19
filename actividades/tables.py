from django.utils.html import format_html
import django_tables2 as tables

from .models import PasoDefinicion


class PasoDefinicionTable(tables.Table):
    titulo = tables.Column(verbose_name='Título', attrs={'td': {'class': 'py-1 md:px-4'}})
    nombre = tables.Column(verbose_name='Slug', attrs={'td': {'class': 'py-1 md:px-4 font-mono text-sm'}})
    usos = tables.Column(verbose_name='Usos', orderable=False, accessor='pk',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}})
    acciones = tables.TemplateColumn(
        template_name='actividades/paso_actions.html',
        verbose_name='', orderable=False,
        attrs={'td': {'class': 'text-center py-1 md:px-4'}},
    )

    class Meta:
        model = PasoDefinicion
        template_name = 'django_tables2/cupertino.html'
        attrs = {'class': 'table w-full'}
        row_attrs = {'class': 'pt-2'}
        fields = ('titulo', 'nombre', 'usos', 'acciones')

    def render_usos(self, record):
        count = record.asignaciones.count()
        if count == 0:
            return format_html('<span class="text-base-content/40 text-xs">Sin asignar</span>')
        return format_html('<span class="badge badge-sm badge-ghost">{}</span>', count)
