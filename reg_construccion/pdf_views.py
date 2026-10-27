"""
PDF "Reporte de avance" de una visita de Construcción Sitios.
Se importa de forma perezosa desde urls.py (weasyprint tarda ~11 s en importarse).
"""
import re
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django_weasyprint.views import WeasyTemplateView

from actividades.models import DatoPaso
from .permissions import puede_ver
from pdf_reports.views import _cols_from_request, _get_fotos_pdf
from widgets.widget_types.tabla_avance import avance_sitio, redondear, serializar

from .models import PASO_AVANCE, RegConstruccion

# Paso «Actividades». La clave interna conserva su nombre original
# (obra_objetivos) para no migrar los datos ya guardados.
PASO_ACTIVIDADES = 'obra_objetivos'
PASO_LIBRO = 'obra_libro'  # etapa de las imágenes del libro de obras (segunda cámara de Actividades)
PASO_ELECTRICO = 'obra_electrico'
PASO_COMENTARIOS = 'obra_comentarios'
# Secciones con fotos: clave del selector «1/2 por fila» → paso (etapa) de las fotos.
SECCIONES_FOTOS = (('actividades', PASO_ACTIVIDADES, 'Actividades'),
                   ('libro', PASO_LIBRO, 'Libro de obras'),
                   ('electrico', PASO_ELECTRICO, 'Eléctrico'))


def _lista(registro, ct, paso_nombre):
    dato = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso_nombre).first()
    return [str(i) for i in ((dato.datos.get('entradas') if dato else None) or []) if str(i).strip()]


def _texto(registro, ct, paso_nombre, campo='comentario'):
    dato = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso_nombre).first()
    return str((dato.datos.get(campo) if dato else '') or '').strip()


def _dms(valor, positivo, negativo):
    """41° 52′ 03,4″ S — segundos con 1 decimal y coma decimal."""
    if valor is None:
        return '—'
    absoluto = abs(valor)
    grados = int(absoluto)
    minutos_total = (absoluto - grados) * 60
    minutos = int(minutos_total)
    segundos = round((minutos_total - minutos) * 60, 1)
    if segundos >= 60:
        segundos, minutos = 0.0, minutos + 1
    if minutos >= 60:
        minutos, grados = 0, grados + 1
    return f"{grados}° {minutos:02d}′ {segundos:04.1f}″ {positivo if valor >= 0 else negativo}".replace('.', ',')


def _decimal(valor):
    return f'{valor:.6f}'.replace('.', ',') if valor is not None else '—'


def _fmt(d, decimales=1):
    return f'{redondear(d, decimales):.{decimales}f}'.replace('.', ',')


class RegConstruccionPDFView(LoginRequiredMixin, WeasyTemplateView):
    template_name = 'reportes_construccion/construccion.html'
    pdf_attachment = False
    pdf_options = {
        'default-font-family': 'Arial',
        'default-font-size': 12,
        'enable-local-file-access': True,
    }
    pdf_stylesheets = [str(Path(settings.BASE_DIR) / 'static/css/weasyprint.css')]

    def _registro(self):
        return get_object_or_404(
            RegConstruccion.objects.select_related('sitio', 'user', 'contratista'),
            id=self.kwargs.get('registro_id'), is_deleted=False,
        )

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not puede_ver(request.user, self._registro()):
                raise PermissionDenied('No tienes acceso a este registro.')
        return super().dispatch(request, *args, **kwargs)

    def get_pdf_filename(self):
        def limpio(s):
            return re.sub(r'[\\/:*?"<>|]', '', str(s or '')).strip()
        reg = self._registro()
        partes = [limpio(reg.sitio.pti_cell_id), limpio(reg.sitio.operator_id),
                  f'reporte{reg.numero_visita}', reg.fecha.strftime('%Y%m%d')]
        if not reg.concluido:
            partes.append('BORRADOR')
        return '-'.join(p for p in partes if p) + '.pdf'

    @staticmethod
    def _fotos_numeradas(registro, ct, paso, desde=1):
        """Fotos de un paso; la numeración continúa entre secciones (parte en `desde`)."""
        fotos = _get_fotos_pdf(registro, paso, ct)
        for n, foto in enumerate(fotos, start=desde):
            leyenda = foto['descripcion'].strip()
            foto['descripcion'] = f'Imagen {n}: {leyenda}' if leyenda else f'Imagen {n}'
        return fotos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        registro = self._registro()
        sitio = registro.sitio
        ct = ContentType.objects.get_for_model(RegConstruccion)

        serie = avance_sitio(RegConstruccion, registro.sitio_id, PASO_AVANCE, hasta=registro)
        actual = serializar(serie[-1][1])
        anterior_total = serie[-2][1]['total'] if len(serie) > 1 else None
        filas = []
        for f in serie[-1][1]['filas']:
            filas.append({
                'nombre': f['nombre'],
                'incidencia': _fmt(f['incidencia'], 0 if f['incidencia'] == int(f['incidencia']) else 1),
                'anterior': _fmt(f['anterior'], 0),
                'actual': _fmt(f['actual'], 0),
                'acumulada': _fmt(f['acumulada'], 0),
                'total': _fmt(f['total'], 1),
                'w_anterior': float(f['anterior']),
                'w_actual': float(f['acumulada'] - f['anterior']),
            })

        fecha_inicio = (RegConstruccion.objects.filter(sitio=sitio, is_deleted=False)
                        .order_by('fecha').values_list('fecha', flat=True).first())
        lat, lon = registro.coordenadas
        fotos_actividades = self._fotos_numeradas(registro, ct, PASO_ACTIVIDADES)
        fotos_libro = self._fotos_numeradas(registro, ct, PASO_LIBRO, desde=len(fotos_actividades) + 1)
        fotos_electrico = self._fotos_numeradas(
            registro, ct, PASO_ELECTRICO, desde=len(fotos_actividades) + len(fotos_libro) + 1)
        supervisor = registro.ito_nombre
        context.update({
            'registro': registro,
            # Sin concluir → el PDF lleva la marca de agua «BORRADOR».
            'borrador': not registro.concluido,
            'sitio': sitio,
            'supervisor': supervisor,
            # Inicio de obra = primera visita registrada del sitio (día cero).
            'fecha_inicio': fecha_inicio,
            'dias_transcurridos': (registro.fecha - fecha_inicio).days if fecha_inicio else None,
            'coord_lat': _dms(lat, 'N', 'S'),
            'coord_lon': _dms(lon, 'E', 'O'),
            'coord_lat_deg': _decimal(lat),
            'coord_lon_deg': _decimal(lon),
            'actividades': _lista(registro, ct, PASO_ACTIVIDADES),
            'comentarios': _lista(registro, ct, PASO_COMENTARIOS),
            'electrico_texto': _texto(registro, ct, PASO_ELECTRICO),
            'partidas': filas,
            'total_general': _fmt(serie[-1][1]['total'], 1),
            'suma_incidencia': _fmt(sum((f['incidencia'] for f in serie[-1][1]['filas']), Decimal('0')), 0),
            'numero_visita': registro.numero_visita,
            'total_anterior': _fmt(anterior_total, 1) if anterior_total is not None else None,
            'delta': _fmt(serie[-1][1]['total'] - anterior_total, 1) if anterior_total is not None else None,
            'delta_positivo': anterior_total is not None and serie[-1][1]['total'] >= anterior_total,
            'fotos_actividades': fotos_actividades,
            'fotos_actividades_cols': _cols_from_request(self.request, 'actividades'),
            'fotos_libro': fotos_libro,
            'fotos_libro_cols': _cols_from_request(self.request, 'libro'),
            'fotos_electrico': fotos_electrico,
            'fotos_electrico_cols': _cols_from_request(self.request, 'electrico'),
            'w_total': float(serie[-1][1]['total']),
            'tekon_logo_src': Path(settings.BASE_DIR, 'templates', 'svgs', 'tekon_logo.png').as_uri(),
            'avance_total_num': actual['total'],
        })
        return context


def pdf_secciones_fotos(request, registro_id):
    """Secciones con fotos, para el modal de opciones del PDF (selector 1/2 por fila)."""
    from photos.models import Photos
    if not request.user.is_authenticated:
        raise PermissionDenied
    registro = get_object_or_404(RegConstruccion, id=registro_id, is_deleted=False)
    if not puede_ver(request.user, registro):
        raise PermissionDenied('No tienes acceso a este registro.')
    ct = ContentType.objects.get_for_model(RegConstruccion)
    secciones = [{'key': key, 'label': label} for key, paso, label in SECCIONES_FOTOS
                 if Photos.objects.filter(content_type=ct, object_id=registro.id, etapa=paso).exists()]
    return JsonResponse({'secciones': secciones})
