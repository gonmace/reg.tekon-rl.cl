from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class DistanciaWidget(WidgetBase):
    slug = "distancia_widget"
    nombre = "Distancia entre puntos"
    icon = "fa-solid fa-ruler"

    def validate_data(self, data):
        errors = []
        for key, label in [('lat1', 'Lat A'), ('lon1', 'Lon A'), ('lat2', 'Lat B'), ('lon2', 'Lon B')]:
            val = data.get(key)
            if val is None:
                continue
            try:
                v = float(val)
            except (ValueError, TypeError):
                errors.append(f"{label}: valor inválido")
                continue
            if 'lat' in key and not (-90 <= v <= 90):
                errors.append(f"{label}: fuera de rango (-90 a 90)")
            if 'lon' in key and not (-180 <= v <= 180):
                errors.append(f"{label}: fuera de rango (-180 a 180)")
        return errors

    def completeness(self, data):
        if data.get('distancia_metros') is not None:
            return 3
        punto_a = data.get('lat1') is not None and data.get('lon1') is not None
        punto_b = data.get('lat2') is not None and data.get('lon2') is not None
        if punto_a and punto_b:
            return 2
        return 1

    def to_display(self, data, config):
        d = data.get('distancia_metros')
        if d is not None:
            d = float(d)
            distancia_str = f"{d:.1f} m" if d < 1000 else f"{d / 1000:.3f} km ({d:.0f} m)"
        else:
            distancia_str = "Sin calcular"
        return {
            "label":          config.get("label", "Distancia"),
            "label_punto1":   config.get("label_punto1", "Punto A"),
            "label_punto2":   config.get("label_punto2", "Punto B"),
            "lat1":           data.get("lat1"),
            "lon1":           data.get("lon1"),
            "lat2":           data.get("lat2"),
            "lon2":           data.get("lon2"),
            "distancia_str":  distancia_str,
            "is_empty":       d is None,
        }
