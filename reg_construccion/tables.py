import django_tables2 as tables
from django.utils.html import format_html

from core.models.sites import Site
from registros.tables import GenericRegistrosTable
from .models import RegConstruccion

def _barra_avance(value):
    pct = float(value or 0)
    texto = f'{pct:.1f}'.replace('.', ',')
    # Barra arriba y porcentaje debajo (ocupa poco ancho). Azul: el rojo se lee como alarma.
    return format_html(
        '<div class="flex flex-col items-center gap-0.5 w-16 mx-auto" title="{}% de avance acumulado">'
        '<progress class="progress progress-info h-1.5 w-full" value="{}" max="100"></progress>'
        '<span class="text-xs leading-none tabular-nums">{}%</span></div>',
        texto, pct, texto,
    )


class SitiosObraTable(tables.Table):
    """Tabla superior: una fila por sitio, con el resumen de su última visita."""

    pti_id = tables.Column(
        accessor='pti_cell_id', verbose_name='PTI ID', empty_values=(),
        attrs={'td': {'class': 'text-left py-1 md:px-4'}, 'th': {'class': 'text-left min-w-32'}},
    )
    operador_id = tables.Column(
        accessor='operator_id', verbose_name='Ope.ID', empty_values=(),
        attrs={'td': {'class': 'text-left py-1 md:px-4'}, 'th': {'class': 'text-left'}},
    )
    nombre = tables.Column(
        accessor='name', verbose_name='Sitio',
        attrs={'td': {'class': 'w-fit max-w-48 py-1 md:px-4'}},
    )
    contratista = tables.Column(
        accessor='ultimo_contratista', verbose_name='Con.', empty_values=(),
        attrs={'td': {'class': 'py-1 md:px-4'}},
    )
    n_visitas = tables.Column(
        verbose_name='Reportes', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    ultima_fecha = tables.Column(
        verbose_name='Último reporte', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    avance = tables.Column(
        accessor='ultimo_avance', verbose_name='Avance', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    acciones = tables.TemplateColumn(
        template_name='components/reg_construccion_sitio_actions.html',
        verbose_name='Acciones', orderable=False,
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )

    class Meta:
        model = Site
        template_name = 'django_tables2/cupertino.html'
        attrs = {'class': 'table w-full reg-obra-sitios-table'}
        fields = ()
        sequence = ('pti_id', 'operador_id', 'nombre', 'contratista', 'n_visitas',
                    'ultima_fecha', 'avance', 'acciones')
        row_attrs = {
            # cursor-pointer: la fila entera es clicable (abre el panel de visitas del sitio).
            # Color según la última visita: verde concluida o con todos los pasos obligatorios completos ·
            # amarillo con datos · rojo sin datos.
            'class': lambda record: (
                'pt-2 cursor-pointer row-concluido' if (getattr(record, 'ultimo_concluido', False)
                                                        or getattr(record, 'ultimo_completo', False))
                else 'pt-2 cursor-pointer row-parcial' if getattr(record, 'ultimo_con_datos', False)
                else 'pt-2 cursor-pointer row-vacio'
            ),
        }

    def render_pti_id(self, value):
        return value or '—'

    def render_operador_id(self, value):
        return value or '—'

    def render_contratista(self, value):
        return value or '—'

    def render_n_visitas(self, value):
        return format_html('<span class="badge badge-outline badge-sm">{}</span>', value or 0)

    def render_ultima_fecha(self, value):
        return value.strftime('%d/%m/%Y') if value else '—'

    def render_avance(self, value):
        return _barra_avance(value)


class RegConstruccionTable(GenericRegistrosTable):
    """Tabla inferior: visitas (reportes) de un sitio. PTI y nombre ya están en la tabla de sitios."""

    n_visita = tables.Column(
        verbose_name='Reporte', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    fecha = tables.Column(
        verbose_name='Fecha reporte',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    # Días desde la primera visita del sitio (día cero) hasta la fecha de esta visita; lo calcula la vista.
    dias = tables.Column(
        verbose_name='Días', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    contratista = tables.Column(
        accessor='contratista.code', verbose_name='Con.', empty_values=(),
        attrs={'td': {'class': 'py-1 md:px-4'}},
    )
    avance = tables.Column(
        accessor='avance_pct', verbose_name='Avance',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    ito = tables.Column(
        accessor='user.username', verbose_name='ITO', empty_values=(),
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    acciones = tables.TemplateColumn(
        template_name='components/reg_construccion_actions.html',
        verbose_name='Acciones', orderable=False,
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )

    class Meta(GenericRegistrosTable.Meta):
        attrs = {'class': 'table w-full reg-obra-visitas-table'}
        model = RegConstruccion
        orderable = False
        fields = ('n_visita', 'fecha')
        sequence = ('n_visita', 'fecha', 'dias', 'contratista', 'avance', 'ito', 'acciones')
        row_attrs = {
            # cursor-pointer: la fila entera es clicable (abre la visita)
            'class': lambda record: (
                'pt-2 cursor-pointer row-concluido' if (getattr(record, 'concluido', False)
                                                        or getattr(record, 'completo', False))
                else 'pt-2 cursor-pointer row-parcial' if getattr(record, 'has_widgets', False)
                else 'pt-2 cursor-pointer row-vacio'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for col in ('estado', 'constructor', 'pti_id', 'operador_id', 'nombre_sitio'):
            self.columns.hide(col)
        self.sequence = self.Meta.sequence

    def render_n_visita(self, value):
        return format_html('<span class="badge badge-outline badge-sm">N° {}</span>', value or '—')

    def render_fecha(self, value):
        return value.strftime('%d/%m/%Y') if value else '—'

    def render_dias(self, value):
        return value if value is not None else '—'

    def render_avance(self, value):
        return _barra_avance(value)

    def render_ito(self, value, record):
        return record.ito_nombre
