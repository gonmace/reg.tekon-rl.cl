from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class Mapa1pWidget(WidgetBase):
    slug = "mapa_1p"
    nombre = "Mapa 1 punto"
    icon = "fa-solid fa-map-location-dot"

    def validate_data(self, data):
        errors = []
        lat, lon = data.get("lat"), data.get("lon")
        if lat is not None:
            try:
                v = float(lat)
                if not (-90 <= v <= 90):
                    errors.append("Latitud fuera de rango (-90 a 90)")
            except (ValueError, TypeError):
                errors.append("Latitud inválida")
        if lon is not None:
            try:
                v = float(lon)
                if not (-180 <= v <= 180):
                    errors.append("Longitud fuera de rango (-180 a 180)")
            except (ValueError, TypeError):
                errors.append("Longitud inválida")
        return errors

    def completeness(self, data):
        lat, lon = data.get("lat"), data.get("lon")
        return 3 if (lat is not None and lon is not None) else 1

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
        lat = data.get("lat") or data.get("latitud")
        lon = data.get("lon") or data.get("longitud")
        coords_str = f"{float(lat):.6f}, {float(lon):.6f}" if (lat and lon) else "Sin capturar"
        maps_url = f"https://maps.google.com/?q={lat},{lon}" if (lat and lon) else None
        return {
            "label": config.get("label", "Ubicación"),
            "lat": lat,
            "lon": lon,
            "coords_str": coords_str,
            "maps_url": maps_url,
            "is_empty": not (lat and lon),
        }
