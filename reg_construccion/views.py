"""
Vistas de Construcción Sitios. Un sitio activado acumula varias visitas (una por fecha).
El timeline de pasos usa el motor genérico de registros.views.dynamic_steps.
"""
import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Exists, F, Min, OuterRef, Q, Subquery
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from core.models.sites import Site
from core.permissions import not_visita, registro_bloqueado_response, superuser_required
from .permissions import (
    MENSAJE_POSTERIOR_CONCLUIDA, hay_posterior_concluida, puede_cambiar_ito, puede_gestionar, puede_ver,
)
from registros.views.activation_views import GenericActivarRegistroView
from registros.views.dynamic_steps import (
    DynamicPasoViewBase, MapaSaveViewBase, get_dynamic_steps,
    make_formatear_registro, make_resumen_formatear, make_toggle_concluido,
)
from registros.views.steps_views import GenericRegistroStepsView, GenericRegistroTableListView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin  # noqa: F401  (documenta el contrato)

from .config import REGISTRO_CONFIG
from .dashboard import mapa_geojson, sitios_con_ultima_visita, visitas_del_alcance
from .dashboard import cached as dashboard_cached
from .forms import RegConstruccionEditForm
from .models import RegConstruccion

TIPO_NAMESPACE = 'reg_construccion_torres'
URL_NAMESPACE = 'reg_construccion'
VISITAS_POR_PAGINA = 10


def _visitas_del_alcance(user):
    """Visitas (no eliminadas) que `user` puede ver."""
    return visitas_del_alcance(user)


def _fecha_o_none(valor):
    try:
        return date.fromisoformat(valor) if valor else None
    except ValueError:
        return None


def _panel_context(request, sitio_id, desde=None, hasta=None, page=None):
    """Contexto del panel inferior (visitas de un sitio), o None si el sitio no tiene visitas visibles."""
    visitas = _visitas_del_alcance(request.user).filter(sitio_id=sitio_id)
    if not visitas.exists():
        return None
    from .tables import RegConstruccionTable
    sitio = Site.objects.get(pk=sitio_id)
    total = visitas.count()

    d, h = _fecha_o_none(desde), _fecha_o_none(hasta)
    if d:
        visitas = visitas.filter(fecha__gte=d)
    if h:
        visitas = visitas.filter(fecha__lte=h)

    # N° de visita = posición entre TODAS las visitas del sitio (no solo las filtradas).
    anteriores = (
        RegConstruccion.objects.filter(sitio_id=sitio_id, is_deleted=False)
        .filter(Q(fecha__lt=OuterRef('fecha')) | Q(fecha=OuterRef('fecha'), id__lte=OuterRef('id')))
        .order_by().values('sitio').annotate(c=Count('id')).values('c')
    )
    # Solo la última visita del sitio (sobre todas, no solo las filtradas) puede crear una nueva.
    posteriores = RegConstruccion.objects.filter(sitio_id=sitio_id, is_deleted=False).filter(
        Q(fecha__gt=OuterRef('fecha')) | Q(fecha=OuterRef('fecha'), id__gt=OuterRef('id')))
    visitas = (
        visitas.with_estado().select_related('sitio', 'user', 'contratista')
        .annotate(n_visita=Subquery(anteriores), es_ultima=~Exists(posteriores)).order_by('-fecha', '-id')
    )
    page_obj = Paginator(visitas, VISITAS_POR_PAGINA).get_page(page)
    registros = list(page_obj.object_list)
    # Día cero = primera visita del sitio (entre todas, no solo las filtradas).
    inicio = RegConstruccion.objects.filter(sitio_id=sitio_id, is_deleted=False).aggregate(m=Min('fecha'))['m']
    for r in registros:
        r.dias = (r.fecha - inicio).days if inicio else None
    table = RegConstruccionTable(registros)
    table.user = request.user
    table.app_namespace = URL_NAMESPACE
    return {
        'panel_sitio': sitio,
        'panel_total': total,
        'panel_table': table,
        'panel_page': page_obj,
        'panel_desde': desde or '',
        'panel_hasta': hasta or '',
        'panel_url': reverse('reg_construccion:visitas_sitio', kwargs={'sitio_id': sitio_id}),
    }


class ListSitiosView(GenericRegistroTableListView):
    """Listado maestro: una fila por sitio en construcción. Sus visitas se ven en el panel inferior."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .tables import SitiosObraTable
        self.table_class = SitiosObraTable

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def get_queryset(self):
        visitas = _visitas_del_alcance(self.request.user)
        qs = sitios_con_ultima_visita(self.request.user)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(pti_cell_id__icontains=q) | Q(operator_id__icontains=q) | Q(name__icontains=q)
                | Q(pk__in=visitas.filter(
                    Q(contratista__name__icontains=q) | Q(contratista__code__icontains=q)).values('sitio_id'))
            )
        return qs.order_by(F('ultima_fecha').desc(nulls_last=True), 'name')

    def get_sitio_queryset(self):
        return Site.get_actives().filter(tipo_sitio=Site.TORRE)

    def get_page_title(self):
        return 'Construcción Sitios'

    def get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'Construcción Sitios'},
        ]

    def _sitio_seleccionado(self):
        """?sitio=ID si es visible para el usuario; si no viene y hay un solo sitio, ese."""
        # order_by() vacío: el Meta.ordering del modelo haría que distinct() repita el sitio por visita.
        visibles = list(
            _visitas_del_alcance(self.request.user).order_by().values_list('sitio_id', flat=True).distinct()
        )
        try:
            pedido = int(self.request.GET.get('sitio', ''))
        except ValueError:
            pedido = None
        if pedido in visibles:
            return pedido
        return visibles[0] if len(visibles) == 1 else None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Sitios en construcción'
        ctx['activate_button_text'] = 'Activar sitio'
        sitio_id = self._sitio_seleccionado()
        ctx['sitio_sel'] = sitio_id
        if sitio_id:
            ctx.update(_panel_context(self.request, sitio_id) or {})
        if self.request.user.is_supermanager:
            ctx['pasos_config_url'] = reverse('reg_construccion:pasos')
        return ctx


@login_required
@require_GET
def mapa_dashboard(request):
    """GeoJSON de las torres con obra para el mapa del dashboard (respeta el alcance por rol)."""
    if not request.user.has_report_access('construccion'):
        raise PermissionDenied
    return JsonResponse(dashboard_cached('mapa', request.user, lambda: mapa_geojson(request.user)))


@login_required
@require_GET
def visitas_sitio(request, sitio_id):
    """Panel inferior (HTMX): visitas de un sitio. Sin HTMX, vuelve al listado con el sitio elegido."""
    if not request.headers.get('HX-Request'):
        return redirect(f"{reverse('reg_construccion:list')}?sitio={sitio_id}")
    ctx = _panel_context(
        request, sitio_id,
        desde=request.GET.get('desde'), hasta=request.GET.get('hasta'), page=request.GET.get('page'),
    )
    if ctx is None:
        raise Http404('Sitio sin reportes')
    return render(request, 'reg_construccion/partials/visitas_sitio.html', ctx)


class StepsRegistroView(GenericRegistroStepsView):
    """Timeline de pasos de una visita."""

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def _generate_steps_context(self, registro):
        return []

    def get_registros_sitio(self, registro):
        return RegConstruccion.objects.filter(
            sitio_id=registro.sitio_id, is_deleted=False,
        ).order_by('-fecha', '-id')

    def get_context_data(self, **kwargs):
        registro_id = self.kwargs.get('registro_id')
        self.registro = get_object_or_404(RegConstruccion, id=registro_id, is_deleted=False)
        if not puede_ver(self.request.user, self.registro):
            raise PermissionDenied('No tienes acceso a este registro.')
        context = super().get_context_data(**kwargs)
        registro = self.registro
        context['header_title'] = f'Reporte N° {registro.numero_visita} · {registro.fecha:%d/%m/%Y}'
        context['steps'] = get_dynamic_steps(
            registro, model=RegConstruccion, url_namespace=URL_NAMESPACE, tipo_namespace=TIPO_NAMESPACE)
        # «Atrás» vuelve al listado con el sitio de esta visita ya seleccionado.
        context['back_url'] = f"{reverse('reg_construccion:list')}?sitio={registro.sitio_id}"
        context['concluido'] = registro.concluido
        context['toggle_concluido_url'] = reverse(
            'reg_construccion:api_toggle_concluido', kwargs={'registro_id': registro.id})
        if self.request.user.is_supermanager:
            context['formatear_url'] = reverse(
                'reg_construccion:api_formatear', kwargs={'registro_id': registro.id})
        context['registro_header_template'] = 'reg_construccion/partials/cabecera.html'
        context['puede_gestionar'] = puede_gestionar(self.request.user, registro)
        context['visitas'] = context['registros_sitio']
        # «Nueva visita» solo se ofrece desde la última visita del sitio (la lista va de la más reciente a la más antigua).
        context['es_ultima_visita'] = registro.pk == self.get_registros_sitio(registro).values_list('pk', flat=True).first()
        context['ito_nombre'] = registro.ito_nombre
        from core.utils.coordenadas import convert_lat_to_dms, convert_lon_to_dms
        lat, lon = registro.coordenadas
        context['coord_lat_dms'] = convert_lat_to_dms(lat) if lat is not None else '—'
        context['coord_lon_dms'] = convert_lon_to_dms(lon) if lon is not None else '—'
        return context

    def get_pdf_url(self, registro_id):
        return reverse('reg_construccion:pdf', kwargs={'registro_id': registro_id})


class ActivarRegistroView(GenericActivarRegistroView):
    """Activa un sitio: crea su primera visita (las siguientes con «Nueva visita»)."""

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def get_success_url_after_activation(self, registro):
        return reverse('reg_construccion:steps', kwargs={'registro_id': registro.id})

    def form_valid(self, form):
        sitio = form.cleaned_data['sitio']
        hoy = date.today()
        existente = RegConstruccion.objects.filter(sitio=sitio, fecha=hoy, is_deleted=False).first()
        if existente:
            msg = (f'El sitio {sitio.name} ya tiene un reporte con fecha {hoy:%d/%m/%Y}. '
                   'Usa «Nuevo reporte» para otra fecha.')
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            return super().form_invalid(form)
        return super().form_valid(form)


class DynamicPasoView(DynamicPasoViewBase):
    registro_model = RegConstruccion
    url_namespace = URL_NAMESPACE

    def get_tipo_namespace(self, registro):
        return TIPO_NAMESPACE

    def puede_escribir(self, user):
        # Coordinación completa la visita; el ADMINISTRADOR solo define la estructura de ítems (ver `post`).
        return user.is_supermanager or user.is_ito_like or user.is_coord or user.is_administrador

    def puede_escribir_widget(self, user, widget_slug):
        if user.is_administrador:
            return widget_slug == 'tabla_avance_widget'
        return self.puede_escribir(user)

    def post(self, request, *args, **kwargs):
        if request.user.is_administrador and request.GET.get('widget') != 'tabla_avance_widget':
            return _json_error('El administrador solo puede definir los ítems del avance', 403)
        if request.GET.get('widget') == 'tabla_avance_widget':
            registro = RegConstruccion.objects.filter(pk=kwargs.get('registro_id'), is_deleted=False).first()
            if registro and hay_posterior_concluida(registro):
                return _json_error(MENSAJE_POSTERIOR_CONCLUIDA, 403)
        return super().post(request, *args, **kwargs)

    def puede_acceder(self, user, registro):
        return puede_ver(user, registro)


class MapaSaveView(MapaSaveViewBase):
    registro_model = RegConstruccion


toggle_concluido = make_toggle_concluido(RegConstruccion)
formatear_registro = make_formatear_registro(RegConstruccion)
resumen_formatear = make_resumen_formatear(RegConstruccion)


def _pasos_redirect(request):
    from actividades.models import TipoActividad
    from django.http import HttpResponseRedirect
    from urllib.parse import urlencode
    if not request.user.is_supermanager:
        raise PermissionDenied
    tipo, _ = TipoActividad.objects.get_or_create(
        app_namespace=TIPO_NAMESPACE,
        defaults={'nombre': 'Construcción Sitios', 'tipo_sitio': 'TORRE', 'activo': True},
    )
    params = urlencode({'back_url': reverse('reg_construccion:list'), 'back_label': 'Construcción Sitios'})
    return HttpResponseRedirect(f"{reverse('actividades:tipo_pasos', kwargs={'pk': tipo.pk})}?{params}")


@login_required
def pasos_config(request):
    return _pasos_redirect(request)


# ── API ───────────────────────────────────────────────────────────────────────

def _json_error(message, status=400):
    return JsonResponse({'success': False, 'message': message}, status=status)


@login_required
@not_visita
@require_POST
def nueva_visita(request, registro_id):
    """Crea otra visita del mismo sitio (fecha distinta) copiando la cabecera de la visita base."""
    base = get_object_or_404(RegConstruccion, pk=registro_id, is_deleted=False)
    if not puede_gestionar(request.user, base):
        return _json_error('Sin permisos', 403)
    try:
        body = json.loads(request.body) if request.body else {}
        fecha = date.fromisoformat(body.get('fecha') or date.today().isoformat())
    except (ValueError, TypeError):
        return _json_error('Fecha inválida')

    if hay_posterior_concluida(base, fecha):
        return _json_error(MENSAJE_POSTERIOR_CONCLUIDA, 403)

    ultima = RegConstruccion.objects.filter(sitio_id=base.sitio_id, is_deleted=False).order_by('-fecha', '-id').first()
    user = request.user if request.user.is_ito_like else base.user
    try:
        nueva = RegConstruccion.objects.create(
            sitio=base.sitio, user=user, fecha=fecha, contratista=ultima.contratista,
            proyecto=ultima.proyecto, descripcion=ultima.descripcion, revision=ultima.revision,
            estado_obra=ultima.estado_obra, is_active=True,
        )
    except ValidationError as e:
        return _json_error(' '.join(e.messages))
    return JsonResponse({
        'success': True,
        'message': f'Reporte del {fecha:%d/%m/%Y} creado',
        'redirect_url': reverse('reg_construccion:steps', kwargs={'registro_id': nueva.id}),
    })


def _form_edicion(user, registro, data=None):
    """Superusuario y ADMINISTRADOR pueden cambiar el ITO; el ADMINISTRADOR solo eso."""
    return RegConstruccionEditForm(
        data, instance=registro,
        cambiar_ito=puede_cambiar_ito(user),
        solo_ito=not puede_gestionar(user, registro),
    )


@login_required
@require_GET
def get_edit_form(request, registro_id):
    registro = get_object_or_404(RegConstruccion, pk=registro_id, is_deleted=False)
    if not (puede_gestionar(request.user, registro) or puede_cambiar_ito(request.user)):
        return _json_error('Sin permisos', 403)
    form = _form_edicion(request.user, registro)
    return render(request, 'reg_construccion/partials/edit_form.html', {'form': form, 'registro': registro})


@login_required
@not_visita
@require_POST
def update_registro(request, registro_id):
    registro = get_object_or_404(RegConstruccion, pk=registro_id, is_deleted=False)
    if not (puede_gestionar(request.user, registro) or puede_cambiar_ito(request.user)):
        return _json_error('Sin permisos', 403)
    bloqueado = registro_bloqueado_response(registro)
    if bloqueado:
        return bloqueado
    fecha_original = registro.fecha
    form = _form_edicion(request.user, registro, request.POST)
    if not form.is_valid():
        errores = ' '.join(m for msgs in form.errors.values() for m in msgs)
        return _json_error(errores or 'Datos inválidos')
    fecha_nueva = form.cleaned_data.get('fecha')
    if fecha_nueva and fecha_nueva != fecha_original and (
        hay_posterior_concluida(registro, fecha_original) or hay_posterior_concluida(registro, fecha_nueva)
    ):
        return _json_error(MENSAJE_POSTERIOR_CONCLUIDA, 403)
    try:
        form.save()
    except ValidationError as e:
        return _json_error(' '.join(e.messages))
    return JsonResponse({'success': True, 'message': 'Reporte actualizado'})


@login_required
@superuser_required
@require_POST
def delete_registro(request, registro_id):
    registro = get_object_or_404(RegConstruccion, pk=registro_id)
    if registro.concluido:
        return _json_error('Un reporte concluido no se puede eliminar; reábrelo primero', 403)
    if hay_posterior_concluida(registro):
        return _json_error(MENSAJE_POSTERIOR_CONCLUIDA, 403)
    registro.soft_delete()
    return JsonResponse({'success': True, 'message': 'Reporte eliminado'})
