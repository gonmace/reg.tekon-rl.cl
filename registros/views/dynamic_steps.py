"""
Motor de pasos dinámicos (configurados en `actividades`) reutilizable por cualquier
modelo de registro (RegTxtss, RegConstruccion, ...).

Convención: el namespace de URLs de la app coincide con su prefijo en config/urls.py
(p. ej. 'reg_txtss' → /reg_txtss/), y publica las rutas `steps`, `paso_dinamico`
y `mapa_save`. Cada app subclasea las vistas base fijando `registro_model`,
`url_namespace` y `get_tipo_namespace()`.
"""

import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from django.contrib import messages

from core.permissions import (
    MENSAJE_BLOQUEADO, MENSAJE_SOLO_ADMIN_REABRE, ItoLikeMixin, can_access_registro, puede_cambiar_concluido,
    registro_access_denied, registro_bloqueado, registro_bloqueado_response, superuser_required,
)


def get_dynamic_steps(registro, *, model, url_namespace, tipo_namespace):
    """Arma las entradas de `steps` para el TipoActividad `tipo_namespace` del registro."""
    from actividades.models import TipoActividad
    from actividades.views import (
        _compute_camera_extra_info, _compute_camera_info, _compute_form_widgets, _compute_map_info,
        _compute_paso_derived,
    )

    if not tipo_namespace:
        return []
    try:
        tipo = TipoActividad.objects.get(app_namespace=tipo_namespace)
    except TipoActividad.DoesNotExist:
        return []

    ct = ContentType.objects.get_for_model(model)
    steps = []
    for cp in tipo.config_pasos.order_by('orden').select_related('pasodef'):
        paso = cp.pasodef
        paso_url = reverse(f'{url_namespace}:paso_dinamico',
                           kwargs={'registro_id': registro.id, 'paso_nombre': paso.nombre})
        photos_url = f'/{url_namespace}/{registro.id}/{paso.nombre}/photos/'

        form_widgets = _compute_form_widgets(paso, registro, ct, paso_url)
        camera_info = _compute_camera_info(paso, registro, ct, photos_url, paso_url)
        photos_extra = _compute_camera_extra_info(paso, registro, ct, paso_url)
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
                'photos_extra': photos_extra,
                'map': map_info,
                'table': None,
            },
            'datos_clave_template': None,
            'sub_elementos_data': {},
            'computed': computed,
        }))
    return steps


class DynamicPasoViewBase(LoginRequiredMixin, View):
    """GET/POST de un paso dinámico. Subclasear fijando registro_model y url_namespace."""

    registro_model = None
    url_namespace = None

    def puede_escribir(self, user):
        """Quién puede hacer POST. Por defecto ITO, Buscador y supermanager."""
        return user.is_supermanager or user.is_ito_like

    def puede_escribir_widget(self, user, widget_slug):
        """Si los controles de guardado del widget van habilitados para `user` (por defecto, `puede_escribir`)."""
        return self.puede_escribir(user)

    def puede_acceder(self, user, registro):
        """Quién puede ver/editar este registro. Por defecto: dueño, supermanager o visita."""
        return can_access_registro(user, registro)

    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated and request.method not in ('GET', 'HEAD', 'OPTIONS')
                and not self.puede_escribir(request.user)):
            return JsonResponse({'success': False, 'message': 'Sin permisos para esta acción'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_tipo_namespace(self, registro):
        raise NotImplementedError

    def _get_objects(self, registro_id, paso_nombre):
        from actividades.models import PasoDefinicion, TipoActividad
        from django.core.exceptions import PermissionDenied
        registro = get_object_or_404(self.registro_model, pk=registro_id, is_deleted=False)
        if not self.puede_acceder(self.request.user, registro):
            raise PermissionDenied('No tienes acceso a este registro.')
        tipo = get_object_or_404(TipoActividad, app_namespace=self.get_tipo_namespace(registro))
        paso = get_object_or_404(PasoDefinicion, nombre=paso_nombre, asignaciones__tipo=tipo)
        return registro, paso

    def _render(self, request, registro, paso, form, datos=None):
        from actividades.views import (
            _enrich_widgets, _get_campos_form, camera_etapa, resolve_paso_template, _get_sitio_lat_lon,
        )
        from actividades.models import DatoPaso
        from core.models.google_maps import GoogleMapsImage
        from photos.models import Photos
        ns = self.url_namespace
        widgets = _enrich_widgets(paso, registro, form)
        widget_slug = request.GET.get('widget')
        if widget_slug:
            widgets = [w for w in widgets if w.widget_slug == widget_slug]
        campos_form = _get_campos_form(paso, form)
        has_map = any(w.widget_tipo in ('MAP_1', 'MAP_2', 'MAP_3') for w in widgets)
        # La cámara mostrada fija la etapa de las fotos: la del paso o, en cámaras extra, la de su config.
        camera_pw = next((w for w in widgets if w.widget_slug in ('camera_widget', 'camera_libro_widget')), None)
        has_camera = camera_pw is not None
        # Título de la página de una cámara: «<Paso> - <Widget>» (Imágenes / Libro de obras).
        widget_titulo = None
        if camera_pw and widget_slug:
            from widgets.registry import get_widget
            widget_obj = get_widget(camera_pw.widget_slug)
            widget_titulo = widget_obj.nombre if widget_obj else None
        etapa_fotos = camera_etapa(camera_pw, paso) if camera_pw else paso.nombre
        sitio = registro.sitio
        lat, lon = _get_sitio_lat_lon(sitio, paso.nombre)
        upload_url = f'/{ns}/{registro.id}/paso/{etapa_fotos}/photos/upload/'
        save_url = reverse(f'{ns}:mapa_save', kwargs={'registro_id': registro.id, 'paso_nombre': paso.nombre})
        ct = ContentType.objects.get_for_model(self.registro_model)
        imagen_guardada = has_map and GoogleMapsImage.objects.filter(
            content_type=ct, object_id=registro.id, etapa=paso.nombre
        ).exists()
        foto_count = 0
        foto_min = 0
        if has_camera:
            foto_count = Photos.objects.filter(
                content_type=ct, object_id=registro.id, etapa=etapa_fotos
            ).count()
            foto_min = camera_pw.config.get('foto_min', 4)

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
            'widget_titulo': widget_titulo,
            'back_url': reverse(f'{ns}:steps', kwargs={'registro_id': registro.id}),
            'app_namespace': ns,
            'registro_contexto_flat': registro_contexto_flat,
            'bloqueado': registro_bloqueado(registro),
            'puede_escribir': self.puede_escribir_widget(request.user, request.GET.get('widget')),
        })

    def get(self, request, registro_id, paso_nombre):
        from actividades.models import DatoPaso
        from actividades.forms import build_dynamic_form
        registro, paso = self._get_objects(registro_id, paso_nombre)
        ct = ContentType.objects.get_for_model(self.registro_model)
        dato = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso_nombre).first()
        datos = dato.datos if dato else {}
        widget_slug = request.GET.get('widget')
        form = build_dynamic_form(paso, initial=datos, widget_slug=widget_slug)
        return self._render(request, registro, paso, form, datos=datos)

    def post(self, request, registro_id, paso_nombre):
        from actividades.models import DatoPaso
        from actividades.forms import build_dynamic_form
        registro, paso = self._get_objects(registro_id, paso_nombre)
        if registro_bloqueado(registro):
            messages.error(request, MENSAJE_BLOQUEADO)
            return redirect(f'{self.url_namespace}:steps', registro_id=registro_id)
        widget_slug = request.GET.get('widget')
        form = build_dynamic_form(paso, data=request.POST, widget_slug=widget_slug)
        if form.is_valid():
            from widgets.registry import get_widget
            ct = ContentType.objects.get_for_model(self.registro_model)
            dato, _ = DatoPaso.objects.get_or_create(
                content_type=ct,
                object_id=registro.id,
                paso_nombre=paso_nombre,
                defaults={'datos': {}},
            )
            cleaned = dict(form.cleaned_data)
            for pw in paso.paso_widgets.all():
                widget = get_widget(pw.widget_slug)
                if widget:
                    widget.before_save(cleaned, dato.datos, request, registro, paso, pw.config)
            dato.datos = {**dato.datos, **cleaned}
            dato.save()
            from actividades.context_builder import rebuild_contexto
            rebuild_contexto(registro)
            from actividades.views import regenerar_mapas_2_puntos_afectados
            regenerar_mapas_2_puntos_afectados(registro, ct, paso_nombre)
            return redirect(f'{self.url_namespace}:steps', registro_id=registro_id)
        return self._render(request, registro, paso, form)


class MapaSaveViewBase(LoginRequiredMixin, ItoLikeMixin, View):
    """Guarda la imagen estática del mapa de un paso dinámico."""

    registro_model = None

    def post(self, request, registro_id, paso_nombre):
        from django.core.files.base import ContentFile
        from core.models.google_maps import GoogleMapsImage
        from core.utils.coordenadas import obtener_imagen_google_maps, calcular_zoom_optimo

        registro = get_object_or_404(self.registro_model, pk=registro_id, is_deleted=False)
        denied = registro_access_denied(request, registro) or registro_bloqueado_response(registro)
        if denied:
            return denied

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
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
            # Zoom máximo que garantiza que TODOS los puntos queden visibles:
            # se ignora el zoom del body (vista Leaflet) porque si el usuario
            # zoomea de más, la imagen estática (centrada en el punto medio)
            # cortaría puntos en los bordes.
            zoom = calcular_zoom_optimo(coordenadas, tamano='640x640')
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

        ct = ContentType.objects.get_for_model(self.registro_model)
        obj, _ = GoogleMapsImage.objects.update_or_create(
            content_type=ct,
            object_id=registro.id,
            etapa=paso_nombre,
            defaults={
                'zoom': zoom,
                'maptype': 'hybrid',
                'scale': 2,
                'tamano': '640x640',
                'coordenadas_json': json.dumps(coordenadas),
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


# ── Vistas función: se generan por modelo ─────────────────────────────────────

def make_toggle_concluido(model):
    @login_required
    @require_POST
    def toggle_concluido(request, registro_id):
        """Concluir (ITO/Buscador/superusuario) o reabrir (solo superusuario y ADMINISTRADOR)."""
        registro = get_object_or_404(model, id=registro_id, is_deleted=False)
        denied = registro_access_denied(request, registro)
        if denied:
            return denied
        if not puede_cambiar_concluido(request.user, registro):
            mensaje = (MENSAJE_SOLO_ADMIN_REABRE if registro.concluido
                       else 'Solo ITO y Buscador pueden concluir un registro.')
            return JsonResponse({'success': False, 'message': mensaje}, status=403)
        registro.concluido = not registro.concluido
        registro.save()
        return JsonResponse({'concluido': registro.concluido})
    return toggle_concluido


def make_formatear_registro(model):
    @login_required
    @superuser_required
    @require_POST
    def formatear_registro(request, registro_id):
        from actividades.models import DatoPaso, ContextoRegistro
        from photos.models import Photos
        from core.models.google_maps import GoogleMapsImage

        registro = get_object_or_404(model, id=registro_id)
        ct = ContentType.objects.get_for_model(model)

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

        # Borrar datos de widgets (formularios) y contexto acumulado
        DatoPaso.objects.filter(content_type=ct, object_id=registro.id).delete()
        ContextoRegistro.objects.filter(content_type=ct, object_id=registro.id).delete()

        registro.concluido = False
        registro.save()
        return JsonResponse({'success': True})
    return formatear_registro


def make_resumen_formatear(model):
    @login_required
    @superuser_required
    def resumen_formatear(request, registro_id):
        from actividades.models import ContextoRegistro
        from photos.models import Photos
        from core.models.google_maps import GoogleMapsImage

        registro = get_object_or_404(model, id=registro_id)
        ct = ContentType.objects.get_for_model(model)

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
    return resumen_formatear
