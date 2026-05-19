import math

from widgets.registry import register_widget
from widgets.widget_types.comentario import FormWidget


@register_widget
class UbicacionWidget(FormWidget):
    slug = "ubicacion_widget"
    nombre = "Ubicación GPS"
    icon = "fa-solid fa-map-marker-alt"

    def validate_data(self, data):
        errors = []
        for field in ("lat", "lon"):
            val = data.get(field)
            if val is not None:
                try:
                    float(val)
                except (ValueError, TypeError):
                    errors.append(f"{field} inválido")
        return errors

    def completeness(self, data):
        lat = data.get("lat") or data.get("latitud")
        lon = data.get("lon") or data.get("longitud")
        return 3 if (lat and lon) else 1

    def to_display(self, data, config):
        lat = data.get("lat") or data.get("latitud")
        lon = data.get("lon") or data.get("longitud")
        accuracy = data.get("accuracy")
        coords_str = f"{float(lat):.6f}, {float(lon):.6f}" if (lat and lon) else "Sin capturar"
        maps_url = f"https://maps.google.com/?q={lat},{lon}" if (lat and lon) else None
        return {
            "label": config.get("label", "Ubicación GPS"),
            "lat": lat,
            "lon": lon,
            "accuracy": accuracy,
            "coords_str": coords_str,
            "maps_url": maps_url,
            "is_empty": not (lat and lon),
        }

    def compute_derived(self, paso_datos, registro):
        lat = paso_datos.get("lat") or paso_datos.get("latitud")
        lon = paso_datos.get("lon") or paso_datos.get("longitud")
        sitio = getattr(registro, "sitio", None)
        lat_man = getattr(sitio, "lat_man", None) if sitio else None
        lon_man = getattr(sitio, "lon_man", None) if sitio else None
        if not (lat and lon and lat_man and lon_man):
            return {}
        try:
            lat, lon = float(lat), float(lon)
            lat_man, lon_man = float(lat_man), float(lon_man)
        except (ValueError, TypeError):
            return {}
        R = 6371000
        f1, f2 = math.radians(lat_man), math.radians(lat)
        df = math.radians(lat - lat_man)
        dl = math.radians(lon - lon_man)
        a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
        d = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d_rounded = round(d, 1)
        dist_str = f"{d:.0f} m" if d < 1000 else f"{d / 1000:.3f} km ({d:.0f} m)"
        paso_titulo = paso_datos.get("_paso_titulo", "Ubicación")
        return {
            "distancia_mandato_metros": d_rounded,
            "distancia_mandato_str": dist_str,
            "distancia_mandato_label": f"Mandato → {paso_titulo}",
        }
