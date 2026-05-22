import django_tables2 as tables
from django.utils.html import format_html
from registros.tables import GenericRegistrosTable
from .models import RegTxtss


class RegTxtssTable(GenericRegistrosTable):
    ito = tables.Column(
        accessor='user.username',
        verbose_name='Buscador',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
        empty_values=(),
    )
    alternativa = tables.Column(
        accessor='alternativa',
        verbose_name='Alt.',
        attrs={
            'td': {'class': 'text-center py-1 md:px-4'},
            'th': {'class': 'text-center'},
        },
    )
    tipo_sitio = tables.Column(
        accessor='sitio.tipo_sitio',
        verbose_name='Tipo',
        attrs={
            'td': {'class': 'text-center py-1 md:px-4'},
            'th': {'class': 'text-center'},
        },
        orderable=False,
    )
    fecha = tables.Column(
        accessor='fecha',
        verbose_name='Fecha Inspección',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
    )
    acciones = tables.TemplateColumn(
        template_name='components/reg_txtss_registro_actions.html',
        verbose_name='Acciones',
        attrs={'td': {'class': 'text-center py-1 md:px-4'}, 'th': {'class': 'text-center'}},
        orderable=False,
    )

    class Meta(GenericRegistrosTable.Meta):
        model = RegTxtss
        fields = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'tipo_sitio', 'fecha')
        sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'tipo_sitio', 'fecha')
        row_attrs = {
            'class': lambda record: (
                'pt-2 row-concluido'
                if getattr(record, 'concluido', False)
                else 'pt-2 row-parcial'
                if getattr(record, 'has_widgets', False)
                else 'pt-2 row-vacio'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns.hide('estado')
        self.columns.hide('constructor')
        self.columns.hide('ito')
        self.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'tipo_sitio', 'fecha', 'acciones')

    ALT_BADGE_CLASS = {
        'A': 'badge-accent',
        'B': 'badge-accent opacity-70',
        'C': 'badge-accent opacity-50',
        'D': 'badge-accent opacity-35',
        'E': 'badge-accent opacity-20',
    }

    def render_alternativa(self, value, record):
        choices = ['A', 'B', 'C', 'D', 'E']
        display = value or '—'
        badge_cls = self.ALT_BADGE_CLASS.get(value, 'badge-neutral')

        if self.user and self.user.is_superuser:
            options = ''.join(
                f'<option value="{c}"{"selected" if c == value else ""}>{c}</option>'
                for c in choices
            )
            return format_html(
                '<div class="alternativa-cell-container">'
                '<span class="alternativa-text" style="cursor:pointer;" data-registro-id="{}">'
                '<span class="badge {} badge-sm">{}</span>'
                '</span>'
                '<select class="alternativa-select select select-warning select-sm select-bordered w-full max-w-xs"'
                ' style="display:none;" data-registro-id="{}">'
                '<option value="">—</option>{}'
                '</select>'
                '</div>',
                record.id, badge_cls, display, record.id, options,
            )
        return format_html('<span class="badge {} badge-sm">{}</span>', badge_cls, display)

    def render_fecha(self, value, record):
        fecha_str = value.strftime('%d/%m/%Y') if value else '—'
        fecha_iso = value.isoformat() if value else ''
        user = getattr(self, 'user', None)
        can_edit = user and (user.is_supermanager or user.is_ito_like)
        if can_edit:
            return format_html(
                '<div class="fecha-cell-container flex items-center justify-center gap-1">'
                '<span class="fecha-text text-sm">{}</span>'
                '<button type="button" class="btn btn-xs btn-ghost btn-circle fecha-edit-btn"'
                ' data-registro-id="{}" title="Editar fecha">'
                '<i class="fa-regular fa-calendar text-xs"></i>'
                '</button>'
                '<input type="date" class="fecha-input input input-warning input-sm w-28"'
                ' style="display:none;" data-registro-id="{}" value="{}">'
                '</div>',
                fecha_str, record.id, record.id, fecha_iso,
            )
        return format_html('<span class="text-sm">{}</span>', fecha_str)

    def render_ito(self, value, record):
        user = getattr(record, 'user', None)
        if user:
            return user.get_full_name or user.username or '—'
        return '—'

    def render_tipo_sitio(self, value, record):
        sitio = getattr(record, 'sitio', None)
        tipo = getattr(sitio, 'tipo_sitio', None) if sitio else None
        if tipo == 'TORRE':
            return format_html('<span class="badge badge-outline badge-accent badge-sm">Torre</span>')
        elif tipo == 'POSTE':
            return format_html('<span class="badge badge-outline badge-info badge-sm">Poste</span>')
        return format_html('<span class="badge badge-outline badge-sm">—</span>')
