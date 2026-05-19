"""
Construcción genérica del ContextoRegistro.

Funciona para cualquier tipo de registro (RegTxtss, futuros) con cualquier
configuración de pasos/widgets en TipoActividad. Llama widget.to_contexto()
en cada widget, que tiene implementación base para cualquier widget form y
overrides específicos para mapa, cámara e imgs_desc.
"""
from django.contrib.contenttypes.models import ContentType


def rebuild_contexto(registro):
    """
    Reconstruye el ContextoRegistro para el registro dado.
    Se puede llamar desde cualquier punto donde se guarden datos de widgets o imágenes.
    """
    from actividades.models import TipoActividad, DatoPaso, ContextoRegistro
    from widgets.registry import get_widget

    tipo = _get_tipo_actividad(registro)
    if not tipo:
        return

    ct = ContentType.objects.get_for_model(type(registro))

    pasos = {}
    flat = {}
    foto_counts = {}

    for cp in (
        tipo.config_pasos
        .order_by('orden')
        .select_related('pasodef')
        .prefetch_related('pasodef__paso_widgets')
    ):
        paso = cp.pasodef
        dato = DatoPaso.objects.filter(
            content_type=ct, object_id=registro.id, paso_nombre=paso.nombre
        ).first()
        datos_paso = dato.datos if dato else {}

        widgets_ctx = {}
        for pw in paso.paso_widgets.order_by('orden'):
            widget = get_widget(pw.widget_slug)
            if not widget:
                continue
            ctx = widget.to_contexto(datos_paso, pw.config, registro, paso.nombre, ct=ct)
            widgets_ctx[pw.widget_slug] = ctx
            _update_flat(flat, paso.nombre, pw.widget_slug, ctx)
            if 'count' in ctx:
                foto_counts[paso.nombre] = ctx['count']

        pasos[paso.nombre] = widgets_ctx

    pasos_total = len(pasos)
    pasos_completos = sum(
        1 for p_data in pasos.values()
        if p_data and all(w.get('level', 0) >= 3 for w in p_data.values())
    )
    stats = {
        'pasos_total': pasos_total,
        'pasos_completos': pasos_completos,
        'completion_pct': int(pasos_completos / pasos_total * 100) if pasos_total else 0,
        'foto_counts': foto_counts,
    }

    ContextoRegistro.objects.update_or_create(
        content_type=ct,
        object_id=registro.id,
        defaults={'contexto': {'pasos': pasos, 'flat': flat, 'stats': stats}},
    )


def _get_tipo_actividad(registro):
    """
    Resuelve el TipoActividad para cualquier tipo de registro.
    Soporta registros con tipo_sitio (como RegTxtss) usando namespace específico.
    """
    from actividades.models import TipoActividad

    base_namespace = _get_base_namespace(registro)
    tipo_sitio = _get_tipo_sitio(registro)

    if tipo_sitio:
        namespace = f'{base_namespace}_{tipo_sitio.lower()}s'
        try:
            return TipoActividad.objects.get(app_namespace=namespace)
        except TipoActividad.DoesNotExist:
            pass

    try:
        return TipoActividad.objects.get(app_namespace=base_namespace)
    except TipoActividad.DoesNotExist:
        return None


def _get_base_namespace(registro):
    if hasattr(registro, 'get_reg_app_name'):
        return registro.get_reg_app_name()
    if hasattr(registro, 'get_app_namespace'):
        return registro.get_app_namespace()
    return registro._meta.app_label


def _get_tipo_sitio(registro):
    sitio = getattr(registro, 'sitio', None)
    if sitio:
        return getattr(sitio, 'tipo_sitio', None)
    return None


def _update_flat(flat, paso_nombre, widget_slug, ctx):
    """
    Puebla el dict flat con claves "paso.campo": valor.
    Extrae valores escalares del contexto del widget.
    """
    scalar_keys = {
        'lat', 'lon', 'accuracy',
        'distancia_mandato_metros', 'distancia_total_metros', 'desfase_metros',
        'imagen_url', 'imagen_abs_path',
        'count', 'min_count', 'level',
    }
    for key, val in ctx.items():
        if key in scalar_keys and val is not None:
            flat[f'{paso_nombre}.{key}'] = val

    raw = ctx.get('raw', {})
    if isinstance(raw, dict):
        for key in ('lat', 'lon', 'accuracy'):
            if raw.get(key) is not None:
                flat[f'{paso_nombre}.{key}'] = raw[key]

    computed = ctx.get('computed', {})
    if isinstance(computed, dict):
        for key, val in computed.items():
            if val is not None:
                flat[f'{paso_nombre}.{key}'] = val
