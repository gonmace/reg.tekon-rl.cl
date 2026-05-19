import json

from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from photos.models import Photos

from .models import DatoPaso, PasoDefinicion


# ── Helpers for dynamic steps (used by reg_txtss and similar apps) ─────────────

_WIDGET_TIPO_MAP = {
    'mapa_1p': 'MAP_1',
    'mapa_2_puntos': 'MAP_2',
    'mapa_3_puntos': 'MAP_3',
    'camera_widget': 'CAMERA',
    'ubicacion_widget': 'LOCATION',
    'comentario_widget': 'TEXT',
}

_CAMERA_SLUGS = {'camera_widget'}
_MAP_SLUGS = {'mapa_1p', 'mapa_2_puntos', 'mapa_3_puntos'}
_FORM_SLUGS = {'comentario_widget', 'ubicacion_widget'}

_WIDGET_ICON_MAP = {
    'comentario_widget':  'fa-solid fa-comment-dots',
    'ubicacion_widget':   'fa-solid fa-map-marker-alt',
    'distancia_widget':   'fa-solid fa-ruler',
    'mapa_1p':            'fa-solid fa-map-location-dot',
    'mapa_2_puntos':      'fa-solid fa-map-location-dot',
    'mapa_3_puntos':      'fa-solid fa-map-location-dot',
    'camera_widget':      'fa-solid fa-camera',
}

# Mapeo de nombre de paso → campos de coordenadas en el modelo Site
_PASO_COORD_FIELDS = {
    'mandato':     ('lat_man', 'lon_man'),
    'ingenieria':  ('lat_ing', 'lon_ing'),
    'construccion':('lat_con', 'lon_con'),
}


def _get_sitio_lat_lon(sitio, paso_nombre):
    """Returns (lat, lon) as dot-notation strings for the given paso, or (None, None).

    Strings avoid Django locale formatting (es → commas) breaking JS parseFloat().
    """
    lat_field, lon_field = _PASO_COORD_FIELDS.get(paso_nombre, (None, None))
    if lat_field and sitio:
        lat = getattr(sitio, lat_field, None)
        lon = getattr(sitio, lon_field, None)
        return (str(lat) if lat is not None else None,
                str(lon) if lon is not None else None)
    return None, None


class _EnrichedWidget:
    def __init__(self, pw):
        from widgets.views import get_widget_meta
        meta = get_widget_meta(pw.widget_slug)
        self.widget_slug = pw.widget_slug
        self.tipo = meta.get('tipo', 'ajax')             # 'form' | 'ajax'
        self.widget_tipo = _WIDGET_TIPO_MAP.get(pw.widget_slug, pw.widget_slug.upper())
        self.orden = pw.orden
        self.config = pw.config
        self.template_path = f'widgets/{pw.widget_slug}.html'

    @property
    def is_form(self):
        return self.tipo == 'form'

    def __repr__(self):
        return f'<Widget {self.widget_slug} tipo={self.tipo}>'


def _enrich_widgets(paso, registro, form):
    """Returns enriched widget list for a paso (used to detect MAP/CAMERA widgets)."""
    return [_EnrichedWidget(pw) for pw in paso.paso_widgets.order_by('orden')]


def _get_campos_form(paso, form):
    """Returns the visible form fields for a dynamic paso form."""
    if form is None:
        return []
    return [form[name] for name in form.fields]


def _widget_has_data(slug, datos, config):
    """Returns True if the widget has meaningful saved data."""
    if slug == 'comentario_widget':
        field = config.get('name', 'comentario')
        return bool(str(datos.get(field, '')).strip())
    if slug == 'ubicacion_widget':
        return bool(datos.get('lat')) and bool(datos.get('lon'))
    if slug == 'poste_form_widget':
        return bool(datos.get('tipo_estructura'))
    return bool(datos)


_LEVEL_COLOR = {1: 'paso-rojo', 2: 'paso-amarillo', 3: 'paso-verde'}
_IMGS_DESC_SLUGS = {'imgs_desc_widget'}


def _compute_imgs_desc_info(pw, registro, ct):
    """Returns (level, filled, total) for imgs_desc_widget by querying Photos."""
    from widgets.widget_types.imgs_desc import _parse_descripciones
    descripciones = _parse_descripciones(pw.config.get('descripciones', ''))
    qs = Photos.objects.filter(content_type=ct, object_id=registro.id, etapa=pw.pasodef.nombre)
    photo_count = qs.count()
    if not descripciones:
        foto_min = int(pw.config.get('foto_min', 0) or 0)
        if foto_min == 0:
            return 0, photo_count, 0
        level = 1 if photo_count == 0 else (2 if photo_count < foto_min else 3)
        return level, photo_count, foto_min
    existing = set(qs.values_list('descripcion', flat=True))
    total = len(descripciones)
    filled = sum(1 for d in descripciones if d in existing)
    level = 1 if filled == 0 else (2 if filled < total else 3)
    return level, photo_count, total


def _compute_imgs_desc_level(pw, registro, ct):
    level, _, _ = _compute_imgs_desc_info(pw, registro, ct)
    return level


def _compute_form_widgets(paso, registro, ct, paso_url):
    """Returns a list of per-widget dicts for all non-map, non-camera widgets in this paso."""
    from widgets.registry import get_widget
    excluded = _MAP_SLUGS | _CAMERA_SLUGS
    form_pws = [pw for pw in paso.paso_widgets.order_by('orden')
                if pw.widget_slug not in excluded]
    if not form_pws:
        return []
    dato = DatoPaso.objects.filter(
        content_type=ct, object_id=registro.id, paso_nombre=paso.nombre
    ).first()
    datos = dato.datos if dato else {}
    result = []
    for pw in form_pws:
        widget = get_widget(pw.widget_slug)
        icon = widget.icon if (widget and widget.icon) else 'fa-solid fa-pen-to-square'
        extra = {}
        if pw.widget_slug in _IMGS_DESC_SLUGS:
            level, filled, total = _compute_imgs_desc_info(pw, registro, ct)
            extra = {'count': filled, 'count_total': total}
        else:
            level = widget.completeness(datos) if widget else (3 if _widget_has_data(pw.widget_slug, datos, pw.config) else 1)
        result.append({
            'url': f'{paso_url}?widget={pw.widget_slug}',
            'color': _LEVEL_COLOR.get(level, 'paso-rojo'),
            'icon': icon,
            'slug': pw.widget_slug,
            'boton_template': f'widgets/{pw.widget_slug}_boton.html',
            **extra,
        })
    return result


def _compute_camera_info(paso, registro, ct, photos_url, paso_url=None):
    """Returns the photos element dict for a dynamic paso step."""
    camera_pws = list(paso.paso_widgets.filter(widget_slug__in=_CAMERA_SLUGS).order_by('orden'))
    if not camera_pws:
        return {'enabled': False}
    min_count = camera_pws[0].config.get('foto_min', 4)
    count = Photos.objects.filter(content_type=ct, object_id=registro.id, etapa=paso.nombre).count()
    color = 'paso-verde' if count >= min_count else ('paso-amarillo' if count > 0 else 'paso-rojo')
    slug = camera_pws[0].widget_slug
    nav_url = f'{paso_url}?widget={slug}' if paso_url else photos_url
    return {
        'enabled': True,
        'url': nav_url,
        'color': color,
        'count': count,
        'required': True,
        'min_count': min_count,
        'slug': slug,
        'boton_template': f'widgets/{slug}_boton.html',
        'icon': 'fa-solid fa-camera',
    }


def _compute_map_info(paso, registro, ct, paso_url=None):
    """Returns the map element dict for a dynamic paso step."""
    map_pws = list(paso.paso_widgets.filter(widget_slug__in=_MAP_SLUGS).order_by('orden'))
    if not map_pws:
        return {'enabled': False, 'status': 'paso-ghost', 'coordinates': {}, 'etapa': paso.nombre}
    from core.models.google_maps import GoogleMapsImage
    exists = GoogleMapsImage.objects.filter(
        content_type=ct, object_id=registro.id, etapa=paso.nombre
    ).exists()
    slug = map_pws[0].widget_slug
    sitio = getattr(registro, 'sitio', None)

    def _resolve_coord(paso_nombre_raw):
        """Busca lat/lon en DatoPaso; si no hay, cae en coordenadas del sitio."""
        nombre = (paso_nombre_raw or '').strip().lower()
        if not nombre:
            return None, None
        d = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=nombre).first()
        datos_d = d.datos if d else {}
        lat_v = datos_d.get('lat') or datos_d.get('latitud')
        lon_v = datos_d.get('lon') or datos_d.get('longitud')
        if not (lat_v and lon_v):
            lat_v, lon_v = _get_sitio_lat_lon(sitio, nombre)
        return lat_v, lon_v

    if slug == 'mapa_2_puntos':
        cfg = map_pws[0].config
        lat, lon = _resolve_coord(cfg.get('paso1'))
        lat2, lon2 = _resolve_coord(cfg.get('paso2'))
    else:
        dato = DatoPaso.objects.filter(content_type=ct, object_id=registro.id, paso_nombre=paso.nombre).first()
        datos = dato.datos if dato else {}
        lat = datos.get('lat') or datos.get('latitud')
        lon = datos.get('lon') or datos.get('longitud')
        if not (lat and lon):
            lat, lon = _get_sitio_lat_lon(sitio, paso.nombre)
        lat2 = lon2 = None

    coordinates = {}
    if lat and lon:
        label1 = map_pws[0].config.get('label1', paso.titulo[:1]) if slug == 'mapa_2_puntos' else map_pws[0].config.get('label', paso.titulo[:1])
        color1 = map_pws[0].config.get('color1', '#e74c3c') if slug == 'mapa_2_puntos' else map_pws[0].config.get('color', '#3b82f6')
        coordinates['coord1'] = {'lat': lat, 'lon': lon, 'label': label1, 'color': color1, 'size': 'mid'}

    if slug == 'mapa_2_puntos' and lat2 and lon2:
        label2 = map_pws[0].config.get('label2', 'B')
        color2 = map_pws[0].config.get('color2', '#0054ff')
        coordinates['coord2'] = {'lat': lat2, 'lon': lon2, 'label': label2, 'color': color2, 'size': 'mid'}

    color = 'paso-verde' if exists else 'paso-rojo'
    return {
        'enabled': True,
        'status': color,
        'color': color,
        'url': f'{paso_url}?widget={slug}' if paso_url else None,
        'coordinates': coordinates,
        'etapa': paso.nombre,
        'slug': slug,
        'boton_template': f'widgets/{slug}_boton.html',
        'step_name': paso.nombre,
        'registro_id': registro.id,
        'title': paso.titulo,
    }



@require_POST
def save_widget_data(request, paso_nombre, widget_slug):
    """
    Endpoint genérico para guardar los datos de un widget en DatoPaso.

    Espera JSON: {"registro_ct": "app_label.model", "registro_id": 42, "data": {...}}
    Retorna: {"level": N} o {"errors": [...]}
    """
    if request.user.is_visita:
        return JsonResponse({"error": "Acceso de solo lectura"}, status=403)
    from widgets.registry import get_widget
    widget = get_widget(widget_slug)
    if not widget:
        return JsonResponse({"error": f"Widget '{widget_slug}' no registrado"}, status=404)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "JSON inválido"}, status=400)

    data = body.get("data", {})
    errors = widget.validate_data(data)
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    ct_str = body.get("registro_ct", "")
    registro_id = body.get("registro_id")
    if not ct_str or not registro_id:
        return JsonResponse({"error": "registro_ct y registro_id son requeridos"}, status=400)

    try:
        app_label, model_name = ct_str.split(".")
        ct = ContentType.objects.get(app_label=app_label, model=model_name)
    except (ValueError, ContentType.DoesNotExist):
        return JsonResponse({"error": f"content_type inválido: {ct_str}"}, status=400)

    dato_paso, _ = DatoPaso.objects.get_or_create(
        content_type=ct,
        object_id=registro_id,
        paso_nombre=paso_nombre,
        defaults={"datos": {}}
    )
    dato_paso.set_widget_data(widget_slug, data)

    registro = ct.get_object_for_this_type(id=registro_id)
    from actividades.context_builder import rebuild_contexto
    rebuild_contexto(registro)

    level = widget.completeness(data)
    return JsonResponse({"level": level})


def _compute_paso_derived(paso, registro, ct):
    """Calls compute_derived on all widgets of a paso and merges the results."""
    from widgets.registry import get_widget
    dato = DatoPaso.objects.filter(
        content_type=ct, object_id=registro.id, paso_nombre=paso.nombre
    ).first()
    paso_datos = dict(dato.datos) if dato else {}
    paso_datos['_paso_titulo'] = paso.titulo
    computed = {}
    for pw in paso.paso_widgets.all():
        widget = get_widget(pw.widget_slug)
        if widget:
            computed.update(widget.compute_derived(paso_datos, registro))
    return computed


def resolve_paso_template(paso):
    """
    Returns the page template for a paso.

    Resolution order:
      1. actividades/pasos/<slug>.html  — custom override for this paso
      2. actividades/elemento.html      — generic: renders widgets when present, placeholder otherwise
    """
    from django.template import TemplateDoesNotExist
    from django.template.loader import get_template

    custom = f'actividades/pasos/{paso.nombre}.html'
    try:
        get_template(custom)
        return custom
    except TemplateDoesNotExist:
        return 'actividades/elemento.html'


