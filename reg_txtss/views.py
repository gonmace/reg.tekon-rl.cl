"""
Vistas para registros TX/TSS.
"""

import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
from registros.config import RegistroConfig
from .config import REGISTRO_CONFIG
from .models import RegTxtss, ALTERNATIVA_CHOICES


class ListRegistrosView(GenericRegistroTableListView):
    """Vista para listar registros TX/TSS usando tabla genérica."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .tables import RegTxtssTable
        self.table_class = RegTxtssTable

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def get_queryset(self):
        from django.db.models import Exists, OuterRef, Case, When, IntegerField, Value
        from django.contrib.contenttypes.models import ContentType
        from actividades.models import DatoPaso
        from photos.models import Photos
        from core.models.google_maps import GoogleMapsImage

        ct = ContentType.objects.get_for_model(RegTxtss)
        # DatoPaso con al menos un valor no vacío (filtra dicts como {'lat': '', 'lon': ''})
        datopaso_con_datos = DatoPaso.objects.filter(
            content_type=ct,
            object_id=OuterRef('pk'),
        ).extra(where=["EXISTS(SELECT 1 FROM jsonb_each_text(datos) j WHERE j.value != '')"])
        has_widgets_qs = (
            Exists(datopaso_con_datos)
            | Exists(Photos.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
            | Exists(GoogleMapsImage.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
        )
        return super().get_queryset().annotate(
            has_widgets=has_widgets_qs,
            orden_estado=Case(
                When(concluido=False, has_widgets=True,  then=Value(1)),  # amarillo
                When(concluido=True,                     then=Value(2)),  # verde
                default=Value(3),                                          # rojo
                output_field=IntegerField(),
            )
        ).order_by('orden_estado', '-fecha')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        if self.request.user.is_superuser:
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
        if self.request.user.is_superuser:
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
        if self.request.user.is_superuser:
            ctx['pasos_config_url'] = reverse('reg_txtss:pasos_postes')
        qs = self.get_queryset()
        ctx['count_verde']   = qs.filter(concluido=True).count()
        ctx['count_amarillo'] = qs.filter(concluido=False, has_widgets=True).count()
        ctx['count_rojo']    = qs.filter(concluido=False, has_widgets=False).count()
        return ctx


class ListRegistrosTorresView(ListRegistrosView):
    """Vista para listar registros TX/TSS de Torres."""

    def get_queryset(self):
        return super().get_queryset().filter(sitio__tipo_sitio='TORRE')

    def get_sitio_queryset(self):
        from core.models.sites import Site
        return Site.get_actives().filter(tipo_sitio='TORRE')

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        table.columns.hide('tipo_sitio')
        if self.request.user.is_superuser:
            table.sequence = ('pti_id', 'operador_id', 'nombre_sitio', 'alternativa', 'ito', 'acciones')
        return table

    def get_page_title(self):
        return 'Torres'

    def get_breadcrumbs(self):
        return [
            {'label': 'Inicio', 'url': reverse('dashboard:dashboard')},
            {'label': 'TX/TSS de Torres'},
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            ctx['pasos_config_url'] = reverse('reg_txtss:pasos_torres')
        return ctx


class StepsRegistroView(GenericRegistroStepsView):
    """Vista para mostrar los pasos de un registro TX/TSS."""

    def get_registro_config(self):
        return REGISTRO_CONFIG

    def _generate_steps_context(self, registro):
        return []

    def get_context_data(self, **kwargs):
        registro_id = self.kwargs.get('registro_id')
        self.registro = get_object_or_404(self.registro_config.registro_model, id=registro_id)
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
        if self.request.user.is_superuser:
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

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from urllib.parse import urlencode


class _PasosConfigRedirectView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Redirige directo a los pasos del TipoActividad (auto-creando si no existe)."""
    raise_exception = True
    _app_namespace = None
    _nombre = None
    _tipo_sitio = None
    _back_label = None
    _back_url_name = None

    def test_func(self):
        return self.request.user.is_superuser

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
    _nombre = 'TX/TSS Torres'
    _tipo_sitio = 'TORRE'
    _back_label = 'TX/TSS Torres'
    _back_url_name = 'reg_txtss:list_torres'


# ── API views ──────────────────────────────────────────────────────────────────

@login_required
@require_POST
def copy_registro(request, registro_id):
    """Crea una copia del registro con la siguiente alternativa (A→B→C→D→E)."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_superuser and registro.user != request.user:
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

@login_required
@require_GET
def get_edit_form(request, registro_id):
    """Devuelve el HTML del formulario de edición de un registro."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_superuser and registro.user != request.user:
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
    """Actualiza buscador y alternativa de un registro."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_superuser and registro.user != request.user:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)

    try:
        from users.models import User
        user_id = request.POST.get('user_id')
        alternativa = request.POST.get('alternativa') or None

        update_fields = {}

        if user_id:
            user = get_object_or_404(User, pk=user_id)
            update_fields['user'] = user
        elif user_id == '':
            update_fields['user'] = None

        valid_alternativas = [c[0] for c in ALTERNATIVA_CHOICES]
        if alternativa and alternativa in valid_alternativas:
            update_fields['alternativa'] = alternativa
        else:
            update_fields['alternativa'] = None

        RegTxtss.objects.filter(pk=registro_id).update(**update_fields)
        return JsonResponse({'success': True, 'message': 'Registro actualizado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required
@require_POST
def delete_registro(request, registro_id):
    """Soft-delete de un registro TX/TSS."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_superuser and registro.user != request.user:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
    try:
        registro.soft_delete()
        return JsonResponse({'success': True, 'message': 'Registro eliminado'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def _get_dynamic_steps(registro):
    """Builds step_data entries for the TipoActividad configured for this registro's site type."""
    from actividades.models import TipoActividad
    from actividades.views import _compute_form_widgets, _compute_camera_info, _compute_map_info, _compute_paso_derived
    from django.contrib.contenttypes.models import ContentType

    tipo_sitio = getattr(getattr(registro, 'sitio', None), 'tipo_sitio', None)
    if tipo_sitio == 'POSTE':
        namespace = 'reg_txtss_postes'
    elif tipo_sitio == 'TORRE':
        namespace = 'reg_txtss_torres'
    else:
        return []

    try:
        tipo = TipoActividad.objects.get(app_namespace=namespace)
    except TipoActividad.DoesNotExist:
        return []

    ct = ContentType.objects.get_for_model(RegTxtss)
    steps = []
    for cp in tipo.config_pasos.order_by('orden').select_related('pasodef'):
        paso = cp.pasodef
        paso_url = reverse('reg_txtss:paso_dinamico', kwargs={'registro_id': registro.id, 'paso_nombre': paso.nombre})
        photos_url = f'/reg_txtss/{registro.id}/{paso.nombre}/photos/'

        form_widgets = _compute_form_widgets(paso, registro, ct, paso_url)
        camera_info = _compute_camera_info(paso, registro, ct, photos_url, paso_url)
        map_info = _compute_map_info(paso, registro, ct, paso_url)
        computed = _compute_paso_derived(paso, registro, ct)

        steps.append((paso.nombre, {
            'title': paso.titulo,
            'step_name': paso.nombre,
            'registro_id': registro.id,
            'is_table': False,
            'elements': {
                'form_widgets': form_widgets,
                'photos': camera_info,
                'map': map_info,
                'table': None,
            },
            'datos_clave_template': None,
            'sub_elementos_data': {},
            'computed': computed,
        }))
    return steps


@login_required
@require_POST
@require_POST
@login_required
def update_fecha(request, registro_id):
    """Actualiza la fecha de inspección de un registro. Editable por cualquier usuario."""
    from datetime import date as date_type
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    try:
        data = json.loads(request.body)
        fecha_iso = data.get('fecha', '')
        fecha = date_type.fromisoformat(fecha_iso)
        registro.fecha = fecha
        registro.save()
        return JsonResponse({'success': True, 'fecha': fecha.strftime('%d/%m/%Y')})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def update_alternativa(request, registro_id):
    """Actualiza el campo alternativa de un registro."""
    registro = get_object_or_404(RegTxtss, pk=registro_id)
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)
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


class DynamicPasoView(LoginRequiredMixin, View):
    """Vista GET/POST para pasos dinámicos (configurados en actividades) de RegTxtss."""

    def _get_objects(self, registro_id, paso_nombre):
        from actividades.models import PasoDefinicion, TipoActividad
        registro = get_object_or_404(RegTxtss, pk=registro_id)
        tipo_sitio = getattr(getattr(registro, 'sitio', None), 'tipo_sitio', None)
        namespace = 'reg_txtss_postes' if tipo_sitio == 'POSTE' else 'reg_txtss_torres'
        tipo = get_object_or_404(TipoActividad, app_namespace=namespace)
        paso = get_object_or_404(PasoDefinicion, nombre=paso_nombre, asignaciones__tipo=tipo)
        return registro, paso

    def _render(self, request, registro, paso, form, datos=None):
        from actividades.views import _enrich_widgets, _get_campos_form, resolve_paso_template, _get_sitio_lat_lon
        from actividades.models import PasoWidget, DatoPaso
        from core.models.google_maps import GoogleMapsImage
        from django.contrib.contenttypes.models import ContentType
        from photos.models import Photos
        widgets = _enrich_widgets(paso, registro, form)
        widget_slug = request.GET.get('widget')
        if widget_slug:
            widgets = [w for w in widgets if w.widget_slug == widget_slug]
        campos_form = _get_campos_form(paso, form)
        has_map = any(w.widget_tipo in ('MAP_1', 'MAP_2', 'MAP_3') for w in widgets)
        has_camera = any(w.widget_slug == 'camera_widget' for w in widgets)
        sitio = registro.sitio
        lat, lon = _get_sitio_lat_lon(sitio, paso.nombre)
        upload_url = f'/reg_txtss/{registro.id}/paso/{paso.nombre}/photos/upload/'
        save_url = reverse('reg_txtss:mapa_save', kwargs={'registro_id': registro.id, 'paso_nombre': paso.nombre})
        ct = ContentType.objects.get_for_model(RegTxtss)
        imagen_guardada = has_map and GoogleMapsImage.objects.filter(
            content_type=ct, object_id=registro.id, etapa=paso.nombre
        ).exists()
        foto_count = 0
        foto_min = 0
        if has_camera:
            foto_count = Photos.objects.filter(
                content_type=ct, object_id=registro.id, etapa=paso.nombre
            ).count()
            camera_pw = paso.paso_widgets.filter(widget_slug='camera_widget').first()
            foto_min = camera_pw.config.get('foto_min', 4) if camera_pw else 4

        lat1 = lon1 = lat2 = lon2 = label1 = label2 = color1 = color2 = None
        map2_pw = paso.paso_widgets.filter(widget_slug='mapa_2_puntos').first()
        if map2_pw:
            cfg = map2_pw.config
            label1 = cfg.get('label1', 'A')
            color1 = cfg.get('color1', '#e74c3c')
            label2 = cfg.get('label2', 'B')
            color2 = cfg.get('color2', '#0054ff')
            for paso_clave, lat_key, lon_key in [('paso1', 'lat1', 'lon1'), ('paso2', 'lat2', 'lon2')]:
                paso_n = (cfg.get(paso_clave) or '').strip().lower()
                if not paso_n:
                    continue
                d = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso_n).first()
                datos_n = d.datos if d else {}
                lat_v = datos_n.get('lat') or datos_n.get('latitud')
                lon_v = datos_n.get('lon') or datos_n.get('longitud')
                if not (lat_v and lon_v):
                    lat_v, lon_v = _get_sitio_lat_lon(sitio, paso_n)
                if lat_key == 'lat1':
                    lat1, lon1 = lat_v, lon_v
                else:
                    lat2, lon2 = lat_v, lon_v

        from actividades.models import ContextoRegistro
        ctx_obj = ContextoRegistro.objects.filter(content_type=ct, object_id=registro.id).first()
        registro_contexto_flat = ctx_obj.contexto.get('flat', {}) if ctx_obj else {}

        return render(request, resolve_paso_template(paso), {
            'registro': registro,
            'paso': paso,
            'sitio': sitio,
            'form': form,
            'datos': datos or {},
            'widgets': widgets,
            'has_form_widgets': any(w.is_form for w in widgets),
            'campos_form': campos_form,
            'has_map_widget': has_map,
            'imagen_guardada': imagen_guardada,
            'foto_count': foto_count,
            'foto_min': foto_min,
            'lat': lat,
            'lon': lon,
            'lat1': lat1, 'lon1': lon1,
            'lat2': lat2, 'lon2': lon2,
            'label1': label1, 'color1': color1,
            'label2': label2, 'color2': color2,
            'upload_url': upload_url,
            'save_url': save_url,
            'header_title': paso.titulo,
            'back_url': reverse('reg_txtss:steps', kwargs={'registro_id': registro.id}),
            'app_namespace': 'reg_txtss',
            'registro_contexto_flat': registro_contexto_flat,
        })

    def get(self, request, registro_id, paso_nombre):
        from actividades.models import DatoPaso
        from actividades.forms import build_dynamic_form
        from django.contrib.contenttypes.models import ContentType
        registro, paso = self._get_objects(registro_id, paso_nombre)
        ct = ContentType.objects.get_for_model(RegTxtss)
        dato = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso_nombre).first()
        datos = dato.datos if dato else {}
        widget_slug = request.GET.get('widget')
        form = build_dynamic_form(paso, initial=datos, widget_slug=widget_slug)
        return self._render(request, registro, paso, form, datos=datos)

    def post(self, request, registro_id, paso_nombre):
        if request.user.is_visita:
            return HttpResponseForbidden()
        from actividades.models import DatoPaso
        from actividades.forms import build_dynamic_form
        from django.contrib.contenttypes.models import ContentType
        registro, paso = self._get_objects(registro_id, paso_nombre)
        widget_slug = request.GET.get('widget')
        form = build_dynamic_form(paso, data=request.POST, widget_slug=widget_slug)
        if form.is_valid():
            ct = ContentType.objects.get_for_model(RegTxtss)
            dato, _ = DatoPaso.objects.get_or_create(
                content_type=ct,
                object_id=registro.id,
                paso_nombre=paso_nombre,
                defaults={'datos': {}},
            )
            dato.datos = {**dato.datos, **form.cleaned_data}
            dato.save()
            from actividades.context_builder import rebuild_contexto
            rebuild_contexto(registro)
            return redirect('reg_txtss:steps', registro_id=registro_id)
        return self._render(request, registro, paso, form)


class MapaSaveView(LoginRequiredMixin, View):
    """Guarda imagen estática del mapa para un paso dinámico de RegTxtss."""

    def post(self, request, registro_id, paso_nombre):
        if request.user.is_visita:
            return JsonResponse({"error": "Acceso de solo lectura"}, status=403)
        import json as _json
        from django.core.files.base import ContentFile
        from django.contrib.contenttypes.models import ContentType
        from core.models.google_maps import GoogleMapsImage
        from core.utils.coordenadas import obtener_imagen_google_maps

        registro = get_object_or_404(RegTxtss, pk=registro_id)

        try:
            body = _json.loads(request.body) if request.body else {}
        except _json.JSONDecodeError:
            body = {}

        coordenadas_body = body.get('coordenadas')
        if coordenadas_body and isinstance(coordenadas_body, list):
            coordenadas = [
                {'lat': float(c['lat']), 'lon': float(c['lon']),
                 'label': (c.get('label') or 'M')[0].upper(),
                 'color': c.get('color', '#3b82f6'), 'size': 'mid'}
                for c in coordenadas_body if c.get('lat') is not None and c.get('lon') is not None
            ]
            if not coordenadas:
                return JsonResponse({'success': False, 'error': 'Sin coordenadas válidas'}, status=400)
            zoom = int(body.get('zoom', 17))
        else:
            lat = body.get('lat')
            lon = body.get('lon')
            if lat is None or lon is None:
                return JsonResponse({'success': False, 'error': 'Sin coordenadas'}, status=400)
            zoom = int(body.get('zoom', 20))
            color = body.get('color', '#3b82f6')
            label = (body.get('label', 'M') or 'M')[0].upper()
            coordenadas = [{'lat': float(lat), 'lon': float(lon), 'label': label, 'color': color, 'size': 'mid'}]

        imagen_bytes = obtener_imagen_google_maps(
            coordenadas=coordenadas, zoom=zoom, maptype='hybrid', scale=2, tamano='640x640'
        )
        if not imagen_bytes:
            return JsonResponse({'success': False, 'error': 'Error al generar la imagen'}, status=500)

        sitio = registro.sitio
        sitio_codigo = getattr(sitio, 'pti_cell_id', 'SIN_CODIGO') if sitio else 'SIN_CODIGO'
        operador = getattr(sitio, 'operator_id', 'SIN_OPERADOR') if sitio else 'SIN_OPERADOR'
        filename = '{}_{}_{}.png'.format(sitio_codigo, operador, paso_nombre)

        ct = ContentType.objects.get_for_model(RegTxtss)
        obj, _ = GoogleMapsImage.objects.update_or_create(
            content_type=ct,
            object_id=registro.id,
            etapa=paso_nombre,
            defaults={
                'zoom': zoom,
                'maptype': 'hybrid',
                'scale': 2,
                'tamano': '640x640',
                'coordenadas_json': _json.dumps(coordenadas),
                'was_created': True,
            }
        )
        # Borrar archivo anterior ANTES de guardar el nuevo para que el
        # nombre quede siempre limpio (sin sufijos aleatorios de Django).
        if obj.imagen:
            obj.imagen.delete(save=False)
        obj.imagen.save(filename, ContentFile(imagen_bytes), save=True)

        from actividades.context_builder import rebuild_contexto
        rebuild_contexto(registro)

        return JsonResponse({'success': True, 'image_url': obj.imagen.url})


@login_required
@require_POST
def toggle_concluido(request, registro_id):
    registro = get_object_or_404(RegTxtss, id=registro_id)
    registro.concluido = not registro.concluido
    registro.save()
    return JsonResponse({'concluido': registro.concluido})


@login_required
@require_POST
def formatear_registro(request, registro_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Sin permisos'}, status=403)

    from django.contrib.contenttypes.models import ContentType
    from actividades.models import DatoPaso, ContextoRegistro
    from photos.models import Photos
    from core.models.google_maps import GoogleMapsImage

    registro = get_object_or_404(RegTxtss, id=registro_id)
    ct = ContentType.objects.get_for_model(RegTxtss)

    # Borrar fotos (archivos incluidos)
    fotos = Photos.objects.filter(content_type=ct, object_id=registro.id)
    for foto in fotos:
        if foto.imagen:
            foto.imagen.delete(save=False)
    fotos.delete()

    # Borrar imágenes de mapas (archivos incluidos)
    mapas = GoogleMapsImage.objects.filter(content_type=ct, object_id=registro.id)
    for mapa in mapas:
        if mapa.imagen:
            mapa.imagen.delete(save=False)
    mapas.delete()

    # Borrar datos de widgets (formularios)
    DatoPaso.objects.filter(content_type=ct, object_id=registro.id).delete()

    # Borrar contexto acumulado
    ContextoRegistro.objects.filter(content_type=ct, object_id=registro.id).delete()

    # Resetear concluido
    registro.concluido = False
    registro.save()

    return JsonResponse({'success': True})


@login_required
def resumen_formatear(request, registro_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False}, status=403)

    from django.contrib.contenttypes.models import ContentType
    from actividades.models import DatoPaso, ContextoRegistro
    from photos.models import Photos
    from core.models.google_maps import GoogleMapsImage

    registro = get_object_or_404(RegTxtss, id=registro_id)
    ct = ContentType.objects.get_for_model(RegTxtss)

    fotos = Photos.objects.filter(content_type=ct, object_id=registro.id, is_deleted=False).count()
    mapas = GoogleMapsImage.objects.filter(content_type=ct, object_id=registro.id, is_deleted=False).count()

    # Contar widgets de formulario con datos reales desde el contexto
    widgets = 0
    try:
        ctx_obj = ContextoRegistro.objects.get(content_type=ct, object_id=registro.id)
        pasos = ctx_obj.contexto.get('pasos', {})
        for paso_data in pasos.values():
            if isinstance(paso_data, dict):
                for widget_data in paso_data.values():
                    if isinstance(widget_data, dict) and widget_data.get('level', 1) > 1:
                        widgets += 1
    except ContextoRegistro.DoesNotExist:
        pass

    return JsonResponse({'fotos': fotos, 'mapas': mapas, 'widgets': widgets})


@login_required
@require_GET
def locate_registro(request, registro_id):
    """Devuelve el número de página donde aparece el registro en la lista."""
    from django.db.models import Exists, OuterRef, Case, When, IntegerField, Value
    from django.contrib.contenttypes.models import ContentType
    from actividades.models import DatoPaso
    from photos.models import Photos
    from core.models.google_maps import GoogleMapsImage

    registro = get_object_or_404(RegTxtss, pk=registro_id, is_deleted=False)
    list_path = request.GET.get('list_path', '')
    tipo = 'TORRE' if 'torres' in list_path else 'POSTE'

    ct = ContentType.objects.get_for_model(RegTxtss)
    datopaso_con_datos = DatoPaso.objects.filter(
        content_type=ct, object_id=OuterRef('pk'),
    ).extra(where=["EXISTS(SELECT 1 FROM jsonb_each_text(datos) j WHERE j.value != '')"])
    has_widgets_qs = (
        Exists(datopaso_con_datos)
        | Exists(Photos.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
        | Exists(GoogleMapsImage.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
    )
    qs = RegTxtss.objects.filter(is_deleted=False, sitio__tipo_sitio=tipo).annotate(
        has_widgets=has_widgets_qs,
        orden_estado=Case(
            When(concluido=False, has_widgets=True,  then=Value(1)),
            When(concluido=True,                     then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).order_by('orden_estado', '-fecha')

    if not request.user.is_superuser and not request.user.is_visita:
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
    from django.db.models import Exists, OuterRef, Case, When, IntegerField, Value
    from django.contrib.contenttypes.models import ContentType
    from actividades.models import DatoPaso, ContextoRegistro
    from photos.models import Photos
    from core.models.google_maps import GoogleMapsImage

    ct = ContentType.objects.get_for_model(RegTxtss)
    datopaso_con_datos = DatoPaso.objects.filter(
        content_type=ct, object_id=OuterRef('pk'),
    ).extra(where=["EXISTS(SELECT 1 FROM jsonb_each_text(datos) j WHERE j.value != '')"])
    has_widgets_qs = (
        Exists(datopaso_con_datos)
        | Exists(Photos.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
        | Exists(GoogleMapsImage.objects.filter(content_type=ct, object_id=OuterRef('pk'), is_deleted=False))
    )
    qs = RegTxtss.objects.filter(is_deleted=False).annotate(
        has_widgets=has_widgets_qs,
        orden_estado=Case(
            When(concluido=False, has_widgets=True, then=Value(1)),
            When(concluido=True,                    then=Value(2)),
            default=Value(3),
            output_field=IntegerField(),
        )
    ).select_related('sitio')

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
