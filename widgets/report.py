"""
Helpers para extraer datos de todos los pasos/widgets de un registro,
formateados para renderizar en un informe PDF.
"""
from django.contrib.contenttypes.models import ContentType

from actividades.models import DatoPaso, TipoActividad
from widgets.registry import get_widget


def get_registro_report_data(registro) -> list[dict]:
    """
    Retorna la lista de pasos de un registro con los datos de cada widget
    formateados para el template PDF.

    Estructura retornada:
    [
      {
        "titulo": str,
        "orden": int,
        "completeness": int,  # min de todos sus widgets
        "widgets": [
          {
            "nombre": str,
            "icon": str,
            "display": dict,  # from widget.to_display()
            "level": int,
          }
        ]
      },
      ...
    ]
    """
    ct = ContentType.objects.get_for_model(registro)
    datos_pasos = {
        dp.paso_nombre: dp
        for dp in DatoPaso.objects.filter(content_type=ct, object_id=registro.id)
    }

    app_namespace = _get_app_namespace(registro)
    try:
        actividad = TipoActividad.objects.get(app_namespace=app_namespace)
    except TipoActividad.DoesNotExist:
        return []

    config_pasos = (
        actividad.config_pasos
        .select_related("pasodef")
        .prefetch_related("pasodef__paso_widgets")
        .order_by("orden")
    )

    result = []
    for cp in config_pasos:
        dato_paso = datos_pasos.get(cp.pasodef.nombre)
        widgets_data = []

        for pw in cp.pasodef.paso_widgets.order_by("orden"):
            widget = get_widget(pw.widget_slug)
            if not widget:
                continue
            raw = dato_paso.get_widget_data(pw.widget_slug) if dato_paso else {}
            level = widget.completeness(raw)
            widgets_data.append({
                "slug": widget.slug,
                "nombre": widget.nombre,
                "icon": widget.icon,
                "display": widget.to_display(raw, pw.config),
                "level": level,
            })

        result.append({
            "titulo": cp.pasodef.titulo,
            "orden": cp.orden,
            "widgets": widgets_data,
            "completeness": min((w["level"] for w in widgets_data), default=0),
        })

    return result


def _get_app_namespace(registro) -> str:
    """
    Obtiene el app_namespace del registro.
    Primero busca el método get_app_namespace(), luego infiere desde el app_label.
    """
    if hasattr(registro, "get_app_namespace"):
        return registro.get_app_namespace()
    return registro._meta.app_label
