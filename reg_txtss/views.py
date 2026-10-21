"""
Vistas para registros TX/TSS.
"""

import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST, require_GET

from registros.views.steps_views import (
    GenericRegistroStepsView,
    GenericRegistroTableListView,
)
from registros.views.activation_views import GenericActivarRegistroView
from registros.views.dynamic_steps import (
    DynamicPasoViewBase, MapaSaveViewBase, get_dynamic_steps,
    make_formatear_registro, make_resumen_formatear, make_toggle_concluido,
)
from registros.config import RegistroConfig
from .config import REGISTRO_CONFIG
from .models import RegTxtss, ALTERNATIVA_CHOICES
from core.permissions import (
    not_visita, superuser_required, NotVisitaMixin, SuperuserRequiredMixin, ItoLikeMixin,
    can_access_registro, registro_access_denied, registro_bloqueado_response,
)


class ListRegistrosView(GenericRegistroTableListView):
    """Vista para listar registros TX/TSS usando tabla genérica."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .tables import RegTxtssTable
        self.table_class = RegTxtssTable

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def get_queryset(self):
        return super().get_queryset().with_estado().order_by('orden_estado', '-fecha')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        if self.request.user.is_supermanager:
            table.columns.show('ito')
            table.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'tipo_sitio', 'ito', 'acciones')
        return table

    def get_page_title(self):
        return 'Registros'

    def get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'TX/TSS'},
        ]


class ListRegistrosPostesView(ListRegistrosView):
    """Vista para listar registros TX/TSS de Postes."""

    def get_queryset(self):
        return super().get_queryset().filter(sitio__tipo_sitio='POSTE')

    def get_sitio_queryset(self):
        from core.models.sites import Site
        return Site.get_actives().filter(tipo_sitio='POSTE')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.columns.hide('tipo_sitio')
        if self.request.user.is_supermanager:
            table.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'ito', 'acciones')
        return table

    def get_page_title(self):
        return 'Postes'

    def get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'TX/TSS de Postes'},
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_supermanager:
            ctx['pasos_config_url'] = reverse('reg_txtss:pasos_postes')
        # Un solo aggregate en vez de 3 .count() que reejecutaban el queryset
        # anotado (con sus subconsultas EXISTS) tres veces.
        from django.db.models import Count, Q
        counts = self.get_queryset().aggregate(
            verde=Count('id', filter=Q(concluido=True)),
            amarillo=Count('id', filter=Q(concluido=False, has_widgets=True)),
            rojo=Count('id', filter=Q(concluido=False, has_widgets=False)),
        )
        ctx['count_verde'] = counts['verde']
        ctx['count_amarillo'] = counts['amarillo']
        ctx['count_rojo'] = counts['rojo']
        return ctx


class ListRegistrosTorresView(ListRegistrosView):
    """Vista para listar registros TX/TSS Ingenieria (sitios tipo TORRE)."""

    def get_queryset(self):
        return super().get_queryset().filter(sitio__tipo_sitio='TORRE')

    def get_sitio_queryset(self):
        from core.models.sites import Site
        return Site.get_actives().filter(tipo_sitio='TORRE')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.columns.hide('tipo_sitio')
        if self.request.user.is_supermanager:
            table.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'ito', 'acciones')
        return table

    def get_page_title(self):
        return 'Ingenieria'

    def get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'TX/TSS Ingenieria'},
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_supermanager:
            ctx['pasos_config_url'] = reverse('reg_txtss:pasos_torres')
        return ctx


class StepsRegistroView(GenericRegistroStepsView):
    """Vista para mostrar los pasos de un registro TX/TSS."""

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def _generate_steps_context(self, registro):
        return []

    def get_context_data(self, **kwargs):
        from django.core.exceptions import PermissionDenied
        registro_id = self.kwargs.get('registro_id')
        self.registro = get_object_or_404(self.registro_config.registro_model, id=registro_id)
        if not can_access_registro(self.request.user, self.registro):
            raise PermissionDenied('No tienes acceso a este registro.')
        context = super().get_context_data(**kwargs)

        title = context.get('header_title')
        if isinstance(title, tuple):
            context['header_title'] = title[0]
            context['header_subtitle'] = title[1]

        context['steps'] = _get_dynamic_steps(self.registro)

        tipo = getattr(getattr(self.registro, 'sitio', None), 'tipo_sitio', None)
        if tipo == 'POSTE':
            context['back_url'] = reverse('reg_txtss:list_postes')
        else:
            context['back_url'] = reverse('reg_txtss:list_torres')

        context['concluido'] = self.registro.concluido
        context['toggle_concluido_url'] = reverse('reg_txtss:api_toggle_concluido', kwargs={'registro_id': self.registro.id})
        if self.request.user.is_supermanager:
            context['formatear_url'] = reverse('reg_txtss:api_formatear', kwargs={'registro_id': self.registro.id})

        return context

    def get_header_title(self):
        if hasattr(self, 'registro') and self.registro and self.registro.alternativa:
            return f'Alternativa {self.registro.alternativa}'
        return super().get_header_title()

    def get_pdf_url(self, registro_id):
        return reverse('reg_txtss:pdf', kwargs={'registro_id': registro_id})


class ActivarRegistroView(GenericActivarRegistroView):
    """Vista para activar registros TX/TSS."""

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def get_success_url_after_activation(self, registro):
        tipo = getattr(getattr(registro, 'sitio', None), 'tipo_sitio', None)
        if tipo == 'POSTE':
            return reverse('reg_txtss:list_postes')
        return reverse('reg_txtss:list_torres')


# ── Configuración de Pasos ────────────────────────────────────────────────────

from django.http import HttpResponseRedirect
from urllib.parse import urlencode


class _PasosConfigRedirectView(LoginRequiredMixin, SuperuserRequiredMixin, View):
    """Redirige directo a los pasos del TipoActividad (auto-creando si no existe)."""
    _app_namespace = None
    _nombre = None
    _tipo_sitio = None
    _back_label = None
    _back_url_name = None

    def get(self, request):
        from actividades.models import TipoActividad
        tipo, _ = TipoActividad.objects.get_or_create(
            app_namespace=self._app_namespace,
            defaults={
                'nombre': self._nombre,
                'tipo_sitio': self._tipo_sitio,
                'activo': True,
            },
        )
        params = urlencode({
            'back_url': reverse(self._back_url_name),
            'back_label': self._back_label,
        })
        return HttpResponseRedirect(
            f"{reverse('actividades:tipo_pasos', kwargs={'pk': tipo.pk})}?{params}"
        )


class PasosPostesView(_PasosConfigRedirectView):
    _app_namespace = 'reg_txtss_postes'
    _nombre = 'TX/TSS Postes'
    _tipo_sitio = 'POSTE'
    _back_label = 'TX/TSS Postes'
    _back_url_name = 'reg_txtss:list_postes'


class PasosTorresView(_PasosConfigRedirectView):
    _app_namespace = 'reg_txtss_torres'
    _nombre = 'TX/TSS Ingenieria'
    _tipo_sitio = 'TORRE'
    _back_label = 'TX/TSS Ingenieria'
    _back_url_name = 'reg_txtss:list_torres'


# ── API views ──────────────────────────────────────────────────────────────────

@login_required
@not_visita
@require_POST
def copy_registro(request, registro_id):
    """Crea una copia del registro con la siguiente alternativa (A→B→C→D→E)."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_supermanager and registro.user != request.user:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)

    orden = [c[0] for c in ALTERNATIVA_CHOICES]
    actual = registro.alternativa or 'A'
    if actual not in orden or orden.index(actual) >= len(orden) - 1:
        return JsonResponse(
            {'success': False, 'message': f'No hay alternativa después de {actual}'},
            status=400,
        )

    siguiente = orden[orden.index(actual) + 1]

    if RegTxtss.objects.filter(
        sitio=registro.sitio,
        user=registro.user,
        fecha=registro.fecha,
        alternativa=siguiente,
    ).exists():
        return JsonResponse(
            {'success': False, 'message': f'Ya existe un registro con alternativa {siguiente} para este sitio y fecha'},
            status=400,
        )

    try:
        nuevo = RegTxtss.objects.create(
            sitio=registro.sitio,
            user=registro.user,
            fecha=registro.fecha,
            alternativa=siguiente,
            is_active=True,
            is_deleted=False,
        )
        return JsonResponse({
            'success': True,
            'message': f'Registro copiado con alternativa {siguiente}',
            'nuevo_id': nuevo.id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

def _puede_editar_registro(user):
    """Cambiar el ITO/Buscador y la alternativa: superusuario y ADMINISTRADOR."""
    return user.is_supermanager or user.is_administrador


@login_required
@require_GET
def get_edit_form(request, registro_id):
    """Devuelve el HTML del formulario de edición de un registro."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not _puede_editar_registro(request.user):
        return JsonResponse({'error': 'Sin permisos'}, status=403)

    from users.models import User
    users = User.objects.filter(
        user_type__in=User.ITO_LIKE_ROLES, is_active=True, is_deleted=False
    ).order_by('first_name', 'last_name', 'username')

    return render(request, 'reg_txtss/edit_form_partial.html', {
        'registro': registro,
        'users': users,
        'alternativa_choices': ALTERNATIVA_CHOICES,
    })


@login_required
@require_POST
def update_registro(request, registro_id):
    """Actualiza buscador y alternativa de un registro (superusuario y ADMINISTRADOR)."""
    from .forms import RegTxtssAdminEditForm
    if not _puede_editar_registro(request.user):
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    bloqueado = registro_bloqueado_response(get_object_or_404(RegTxtss, pk=registro_id))
    if bloqueado:
        return bloqueado

    form = RegTxtssAdminEditForm({
        'user': request.POST.get('user_id') or '',
        'alternativa': request.POST.get('alternativa') or '',
    })
    if not form.is_valid():
        return JsonResponse(
            {'success': False, 'message': 'Datos inválidos', 'errors': form.errors},
            status=400,
        )

    # Se persiste con .update() a propósito (evita full_clean y el registro de
    # history en una edición administrativa). alternativa vacía → None.
    update_fields = {'alternativa': form.cleaned_data['alternativa'] or None}
    if 'user_id' in request.POST:
        update_fields['user'] = form.cleaned_data['user']  # instancia User o None
    RegTxtss.objects.filter(pk=registro_id).update(**update_fields)
    return JsonResponse({'success': True, 'message': 'Registro actualizado'})


@login_required
@superuser_required
@require_POST
def delete_registro(request, registro_id):
    """Soft-delete de un registro TX/TSS."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    try:
        registro.soft_delete()
        return JsonResponse({'success': True, 'message': 'Registro eliminado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def _tipo_namespace(registro):
    """TipoActividad de TX/TSS según el tipo de sitio del registro."""
    tipo_sitio = getattr(getattr(registro, 'sitio', None), 'tipo_sitio', None)
    if tipo_sitio == 'POSTE':
        return 'reg_txtss_postes'
    if tipo_sitio == 'TORRE':
        return 'reg_txtss_torres'
    return None


def _get_dynamic_steps(registro):
    return get_dynamic_steps(
        registro, model=RegTxtss, url_namespace='reg_txtss',
        tipo_namespace=_tipo_namespace(registro),
    )


@login_required
@require_POST
def update_fecha(request, registro_id):
    """Actualiza la fecha de inspección. Solo ITO y Buscador (y supermanager)."""
    if not (request.user.is_supermanager or request.user.is_ito_like):
        return JsonResponse({'success': False, 'message': 'Solo ITO y Buscador pueden cambiar la fecha'}, status=403)
    from datetime import date as date_type
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    denied = registro_access_denied(request, registro) or registro_bloqueado_response(registro)
    if denied:
        return denied
    try:
        data = json.loads(request.body)
        fecha_iso = data.get('fecha', '')
        fecha = date_type.fromisoformat(fecha_iso)
        registro.fecha = fecha
        registro.save()
        return JsonResponse({'success': True, 'fecha': fecha.strftime('%d/%m/%Y')})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@superuser_required
@require_POST
def update_alternativa(request, registro_id):
    """Actualiza el campo alternativa de un registro."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    bloqueado = registro_bloqueado_response(registro)
    if bloqueado:
        return bloqueado
    try:
        data = json.loads(request.body)
        alternativa = data.get('alternativa') or None
        valid = [c[0] for c in ALTERNATIVA_CHOICES]
        if alternativa and alternativa not in valid:
            return JsonResponse({'success': False, 'message': 'Valor inválido'}, status=400)
        registro.alternativa = alternativa
        registro.save()
        return JsonResponse({'success': True, 'message': 'Alternativa actualizada', 'alternativa': alternativa or ''})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


class DynamicPasoView(DynamicPasoViewBase):
    """Pasos dinámicos (configurados en actividades) de RegTxtss."""
    registro_model = RegTxtss
    url_namespace = 'reg_txtss'

    def get_tipo_namespace(self, registro):
        # Compatibilidad: todo lo que no es POSTE usa la config de torres.
        return _tipo_namespace(registro) or 'reg_txtss_torres'


class MapaSaveView(MapaSaveViewBase):
    registro_model = RegTxtss


toggle_concluido = make_toggle_concluido(RegTxtss)
formatear_registro = make_formatear_registro(RegTxtss)
resumen_formatear = make_resumen_formatear(RegTxtss)


@login_required
@require_GET
def locate_registro(request, registro_id):
    """Devuelve el número de página donde aparece el registro en la lista."""
    registro = get_object_or_404(RegTxtss, pk=registro_id, is_deleted=False)
    list_path = request.GET.get('list_path', '')
    tipo = 'TORRE' if 'torres' in list_path else 'POSTE'

    qs = (
        RegTxtss.objects.filter(is_deleted=False, sitio__tipo_sitio=tipo)
        .with_estado()
        .order_by('orden_estado', '-fecha')
    )

    if not request.user.is_supermanager and not request.user.is_visita:
        qs = qs.filter(user=request.user)

    ids = list(qs.values_list('id', flat=True))
    try:
        position = ids.index(registro_id)
    except ValueError:
        return JsonResponse({'page': 1})

    per_page = 25
    page = position // per_page + 1
    return JsonResponse({'page': page})


@login_required
@require_GET
def mapa_registros_geojson(request):
    """GeoJSON con todos los registros que tienen coordenadas, para el mapa Leaflet."""
    from django.contrib.contenttypes.models import ContentType
    from actividades.models import ContextoRegistro

    ct = ContentType.objects.get_for_model(RegTxtss)
    qs = RegTxtss.objects.filter(is_deleted=False).with_estado().select_related('sitio')

    contextos = {
        c.object_id: c.contexto
        for c in ContextoRegistro.objects.filter(content_type=ct)
    }

    features = []
    for reg in qs:
        lat, lon = None, None
        flat = (contextos.get(reg.id) or {}).get('flat', {})
        for key, val in flat.items():
            if key.endswith('.lat') and val:
                paso_prefix = key[:-4]
                lon_candidate = flat.get(f'{paso_prefix}.lon')
                if lon_candidate:
                    try:
                        lat = float(val)
                        lon = float(lon_candidate)
                        break
                    except (ValueError, TypeError):
                        pass

        if lat is None and reg.sitio:
            try:
                if reg.sitio.lat_man and reg.sitio.lon_man:
                    lat = float(reg.sitio.lat_man)
                    lon = float(reg.sitio.lon_man)
            except (ValueError, TypeError):
                pass

        if lat is None or lon is None:
            continue

        estado = 'verde' if reg.concluido else ('amarillo' if reg.has_widgets else 'rojo')
        sitio = reg.sitio
        lat_man, lon_man = None, None
        if sitio:
            try:
                if sitio.lat_man and sitio.lon_man:
                    lat_man = float(sitio.lat_man)
                    lon_man = float(sitio.lon_man)
            except (ValueError, TypeError):
                pass
        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
            'properties': {
                'id': reg.id,
                'pti_id': sitio.pti_cell_id if sitio else '',
                'operador_id': sitio.operator_id if sitio else '',
                'nombre': sitio.name if sitio else '',
                'alternativa': reg.alternativa or '',
                'fecha': reg.fecha.strftime('%d/%m/%Y') if reg.fecha else '',
                'estado': estado,
                'url': f'/reg_txtss/{reg.id}/',
                'lat_man': lat_man,
                'lon_man': lon_man,
            },
        })

    return JsonResponse({'type': 'FeatureCollection', 'features': features})
