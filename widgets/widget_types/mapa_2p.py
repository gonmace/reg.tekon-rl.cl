from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class Mapa2pWidget(WidgetBase):
    slug = "mapa_2_puntos"
    nombre = "Mapa 2 Puntos"
    icon = "fa-solid fa-map-location-dot"

    def validate_config(self, config):
        errors = []
        if not config.get('paso1'):
            errors.append("paso1 requerido: nombre del paso del primer punto")
        if not config.get('paso2'):
            errors.append("paso2 requerido: nombre del paso del segundo punto")
        return errors

    def validate_data(self, data):
        return []

    def completeness(self, data):
        return 1

    def to_contexto(self, datos, config, registro, paso_nombre, ct=None):
        from core.models.google_maps import GoogleMapsImage
        from django.contrib.contenttypes.models import ContentType
        if ct is None:
            ct = ContentType.objects.get_for_model(type(registro))
        img = GoogleMapsImage.objects.filter(
            content_type=ct, object_id=registro.id, etapa=paso_nombre
        ).first()
        if img and img.imagen:
            return {
                "imagen_url": img.imagen.url,
                "imagen_abs_path": img.imagen.path,
                "distancia_total_metros": img.distancia_total_metros,
                "desfase_metros": img.desfase_metros,
                "level": 3,
            }
        return {"imagen_url": None, "imagen_abs_path": None, "distancia_total_metros": None, "desfase_metros": None, "level": 1}

    def to_display(self, data, config):
        return {
            "label": config.get("label", "Mapa 2 Puntos"),
            "paso1": config.get("paso1"),
            "paso2": config.get("paso2"),
        }
