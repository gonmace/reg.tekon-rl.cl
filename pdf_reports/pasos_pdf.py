"""
Construye la sección genérica de "pasos" del PDF (Sitio, Acceso, Eléctrico,
Adicionales, etc.) a partir de ContextoRegistro — NO de widget.to_display().

Por qué desde ContextoRegistro y no desde to_display():
- to_display() recibe DatoPaso.datos[widget_slug] (lookup anidado), pero los
  datos se guardan PLANOS en DatoPaso.datos (ver reg_txtss/views.py). Con eso
  todo widget recibe {} y sale vacío.
- to_contexto() SÍ recibe el dict plano correcto (actividades/context_builder.py)
  y además resuelve fotos (Photos) y mapas (GoogleMapsImage), cosa que
  to_display() no puede hacer porque su firma (data, config) no tiene
  acceso a registro/paso_nombre.
- ContextoRegistro.contexto ya es la salida persistida de to_contexto(), y es
  la misma fuente que usan hoy las secciones hardcodeadas de "postes" en
  pdf_reports/views.py.

Las fotos y la resolución de URLs de imagen (file:// para WeasyPrint) NO se
hacen acá: este módulo es puro (solo lee reg_contexto + config de BD). La
vista (pdf_reports/views.py::_resolve_pasos_media) las completa después.
"""
from actividades.context_builder import get_tipo_actividad
from core.utils.coordenadas import convert_lat_to_dms, convert_lon_to_dms

# Widgets cuyas fotos se resuelven aparte (Photos por etapa=paso_nombre) y que
# no deben listarse como "widget" de datos.
_WIDGETS_FOTO = {'camera_widget', 'imgs_desc_widget'}

# Claves de metadata que agrega to_contexto() (base en widgets/base.py) y que
# no son parte del display en sí.
_META = ('raw', 'display', 'computed', 'level')

_DEFAULT_COLOR_1 = '#3b82f6'
_DEFAULT_COLOR_2 = '#e74c3c'
_FORM_DINAMICO_TEMPLATE = 'reportes_txtss/partials/widgets/form_dinamico_widget.html'


def _normalize(ctx: dict) -> dict:
    """Aplana la salida heterogénea de to_contexto() a un solo dict `data`.

    Widgets que overridean to_contexto (camera, imgs_desc, mapa_1p, mapa_2p)
    devuelven un dict plano sin clave 'display'. Widgets que usan la base
    (form_dinamico, ubicacion, comentario, distancia, poste_form) anidan el
    resultado de to_display() bajo 'display'. Se normaliza a un solo shape
    para que los partials siempre reciban `display` con las mismas claves
    que hoy produce to_display() (o su equivalente).
    """
    if isinstance(ctx.get('display'), dict):
        data = dict(ctx['display'])
    else:
        data = {k: v for k, v in ctx.items() if k not in _META}
    data['computed'] = ctx.get('computed') or {}
    return data


def _numero_legible(v):
    """Evita que floatformat/locale 'es' convierta 135.0 en '135,0' en el PDF."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return v


def _postprocesar_form_dinamico(data: dict, pw) -> dict:
    campos = [
        {**c, 'valor': _numero_legible(c['valor'])}
        for c in data.get('campos', [])
        if c.get('valor') not in (None, '', 'Sin responder')
    ]
    data['campos'] = campos
    data['label_explicito'] = 'label' in (pw.config or {})
    return data


def _postprocesar_ubicacion(data: dict) -> dict:
    """Agrega la representación en grados-minutos-segundos con hemisferio,
    para mostrarla debajo de las coordenadas decimales (mismo par de formatos
    que ya se usa en la sección de postes)."""
    data['lat_dms'] = convert_lat_to_dms(data.get('lat'))
    data['lon_dms'] = convert_lon_to_dms(data.get('lon'))
    return data


def _postprocesar_mapa(data: dict, pw, titulos_por_paso: dict) -> dict:
    config = pw.config or {}

    def _titulo(paso_slug):
        if not paso_slug:
            return None
        return titulos_por_paso.get(str(paso_slug).lower()) or str(paso_slug).capitalize()

    leyenda = []
    if pw.widget_slug == 'mapa_2_puntos':
        n1 = _titulo(config.get('paso1'))
        n2 = _titulo(config.get('paso2'))
        if n1:
            leyenda.append({'icon_color': config.get('color1') or _DEFAULT_COLOR_1, 'name': n1})
        if n2:
            leyenda.append({'icon_color': config.get('color2') or _DEFAULT_COLOR_2, 'name': n2})
    else:  # mapa_1p
        leyenda.append({'icon_color': config.get('color1') or _DEFAULT_COLOR_1, 'name': config.get('label') or 'Ubicación'})

    data['leyenda'] = leyenda

    metros = data.get('distancia_total_metros')
    if metros is not None:
        data['distancia_str'] = f'{metros / 1000:.2f} km' if metros >= 1000 else f'{metros:.0f} m'
    else:
        data['distancia_str'] = None
    return data


def _a_shape_generico(nombre_widget: str, data: dict) -> dict:
    """Mapea un dict arbitrario al shape {label, campos} de form_dinamico_widget.html,
    para que un widget futuro sin partial propio caiga en una tabla label/valor
    en vez de no mostrar nada."""
    campos = [
        {'label': k.replace('_', ' ').capitalize(), 'valor': _numero_legible(v), 'tipo': 'text'}
        for k, v in data.items()
        if k not in ('computed', 'is_empty', 'label') and v not in (None, '', [], {})
    ]
    return {'label': data.get('label') or nombre_widget, 'campos': campos, 'label_explicito': True}


def _is_empty(slug: str, data: dict) -> bool:
    if slug == 'form_dinamico_widget':
        return not data.get('campos')
    if slug in ('ubicacion_widget', 'comentario_widget', 'distancia_widget'):
        return data.get('is_empty', True)
    if slug in ('mapa_1p', 'mapa_2_puntos'):
        return not data.get('imagen_url')
    return not data


def build_pasos_pdf(registro, reg_contexto, excluir=frozenset()) -> list[dict]:
    """
    Retorna la lista de pasos (excluyendo `excluir`) con sus widgets de datos
    listos para el template, y un flag de fotos a resolver por la vista.

    [
      {
        "nombre": "sitio", "titulo": "Sitio", "orden": 10,
        "widgets": [{"slug","nombre","level","template","data"}],
        "tiene_fotos": bool, "fotos_label": str, "fotos": [],
      },
      ...
    ]
    """
    from widgets.registry import get_widget

    actividad = get_tipo_actividad(registro)
    if not actividad:
        return []

    config_pasos = (
        actividad.config_pasos
        .select_related('pasodef')
        .prefetch_related('pasodef__paso_widgets')
        .order_by('orden')
    )
    config_pasos = list(config_pasos)

    titulos_por_paso = {cp.pasodef.nombre.lower(): cp.pasodef.titulo for cp in config_pasos}
    pasos_ctx = (reg_contexto or {}).get('pasos', {})

    result = []
    for cp in config_pasos:
        paso_nombre = cp.pasodef.nombre
        if paso_nombre in excluir:
            continue

        widget_ctx = pasos_ctx.get(paso_nombre, {})
        widgets_data = []
        tiene_fotos = False
        fotos_label = None

        for pw in cp.pasodef.paso_widgets.order_by('orden'):
            ctx = widget_ctx.get(pw.widget_slug)
            if not ctx:
                continue

            if pw.widget_slug in _WIDGETS_FOTO:
                if ctx.get('count', 0) > 0:
                    tiene_fotos = True
                    fotos_label = (pw.config or {}).get('label') or fotos_label
                continue

            widget = get_widget(pw.widget_slug)
            if not widget:
                continue

            data = _normalize(ctx)
            if pw.widget_slug == 'form_dinamico_widget':
                data = _postprocesar_form_dinamico(data, pw)
            elif pw.widget_slug == 'ubicacion_widget':
                data = _postprocesar_ubicacion(data)
            elif pw.widget_slug in ('mapa_1p', 'mapa_2_puntos'):
                data = _postprocesar_mapa(data, pw, titulos_por_paso)

            if _is_empty(pw.widget_slug, data):
                continue

            template = _template_for(pw.widget_slug)
            if template == _FORM_DINAMICO_TEMPLATE and pw.widget_slug != 'form_dinamico_widget':
                # Slug sin partial propio: cae al fallback genérico de
                # form_dinamico_widget.html, así que hay que darle su shape
                # (label/campos) en vez de dejarlo sin contenido.
                data = _a_shape_generico(widget.nombre, data)
                if _is_empty('form_dinamico_widget', data):
                    continue

            widgets_data.append({
                'slug': pw.widget_slug,
                'nombre': widget.nombre,
                'level': ctx.get('level', 0),
                'template': template,
                'data': data,
            })

        if not widgets_data and not tiene_fotos:
            continue

        result.append({
            'nombre': paso_nombre,
            'titulo': cp.pasodef.titulo,
            'orden': cp.orden,
            'widgets': widgets_data,
            'tiene_fotos': tiene_fotos,
            'fotos_label': fotos_label or 'Registro Fotográfico',
            'fotos': [],
        })

    return result


def _template_for(slug: str) -> str:
    """Resuelve el partial de PDF para un slug, con fallback genérico.

    Nunca lanza TemplateDoesNotExist: si no hay partial específico, usa el
    de form_dinamico_widget (tabla label/valor) como fallback razonable.
    """
    from django.template.loader import select_template

    return select_template([
        f'reportes_txtss/partials/widgets/{slug}.html',
        'reportes_txtss/partials/widgets/form_dinamico_widget.html',
    ]).template.name
