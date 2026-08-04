from geopy.distance import geodesic
import requests
import math
import re as _re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def calcular_distancia_geopy(lat_1, lon_1, lat_2, lon_2):
    """Calcula la distancia entre dos puntos usando geopy."""
    if lat_1 is not None and lon_1 is not None and lat_2 is not None and lon_2 is not None:
        try:
            lat_1, lon_1, lat_2, lon_2 = float(lat_1), float(lon_1), float(lat_2), float(lon_2)
            if not (-90 <= lat_1 <= 90) or not (-90 <= lat_2 <= 90):
                return None
            if not (-180 <= lon_1 <= 180) or not (-180 <= lon_2 <= 180):
                return None
            return geodesic((lat_1, lon_1), (lat_2, lon_2)).meters
        except (ValueError, TypeError):
            return None
    return None


def calcular_distancia_entre_puntos(lat_1, lon_1, lat_2, lon_2):
    """Alias para calcular_distancia_geopy para compatibilidad."""
    return calcular_distancia_geopy(lat_1, lon_1, lat_2, lon_2)


def convert_lat_to_dms(lat):
    if lat is None:
        return 'N/A'
    lat = float(lat)
    direction = 'N' if lat >= 0 else 'S'
    deg_abs = abs(lat)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"


def convert_lon_to_dms(lon):
    if lon is None:
        return 'N/A'
    lon = float(lon)
    direction = 'E' if lon >= 0 else 'W'
    deg_abs = abs(lon)
    degrees = int(deg_abs)
    minutes_full = (deg_abs - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60, 2)
    return f"{direction} {degrees}° {minutes}' {seconds}''"


def _to_api_color(color_str):
    """Convierte '#RRGGBB' a '0xRRGGBB' para el parámetro markers de la Static Maps API."""
    s = str(color_str or '').strip()
    if s.startswith('#'):
        return '0x' + s[1:].upper()
    if _re.match(r'^0x', s, _re.IGNORECASE):
        return '0x' + s[2:].upper()
    return s  # color nombrado ('red', 'blue', etc.)


def obtener_imagen_google_maps(coordenadas, zoom=None, maptype="hybrid", scale=2, tamano="400x400"):
    """
    Solicita una imagen estática de Google Maps usando los marcadores nativos de la API.
    Los colores se pasan directamente como parámetro markers (0xRRGGBB o nombre).
    """
    base_url = "https://maps.googleapis.com/maps/api/staticmap"

    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY no está configurada en .env")
        return None

    valid_coords = []
    for coord in coordenadas:
        lat = coord.get('lat')
        lon = coord.get('lon')
        if lat is None or lon is None:
            continue
        try:
            lat_f, lon_f = float(lat), float(lon)
            if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
                continue
            valid_coords.append({
                'lat': lat_f,
                'lon': lon_f,
                'color': _to_api_color(coord.get('color', '#3b82f6')),
                'label': (str(coord.get('label', '') or '').strip()[:1] or 'M').upper(),
                'size': coord.get('size', 'mid'),
            })
        except (ValueError, TypeError):
            continue

    if not valid_coords:
        return None

    # ── Calcular centro y zoom ────────────────────────────────────────────────
    def _lat_rad(lat):
        s = math.sin(lat * math.pi / 180)
        r = math.log((1 + s) / (1 - s)) / 2
        return max(min(r, math.pi), -math.pi) / 2

    def _zoom_fit(map_px, world_px, fraction):
        if fraction == 0:
            return 21
        return math.floor(math.log(map_px / world_px / fraction) / math.log(2))

    lats = [c['lat'] for c in valid_coords]
    lons = [c['lon'] for c in valid_coords]
    centro_lat = (min(lats) + max(lats)) / 2
    centro_lon = (min(lons) + max(lons)) / 2

    if zoom is None:
        if len(valid_coords) == 1:
            zoom = 20
        else:
            try:
                iw, ih = [int(x) for x in tamano.lower().split('x')]
            except Exception:
                iw, ih = 640, 640
            lat_frac = (_lat_rad(max(lats)) - _lat_rad(min(lats))) / math.pi
            lon_frac = (max(lons) - min(lons)) / 360.0
            zoom = max(1, min(
                _zoom_fit(ih, 256, lat_frac) if lat_frac else 21,
                _zoom_fit(iw, 256, lon_frac) if lon_frac else 21,
                21,
            ))

    # ── Construir params con múltiples markers ────────────────────────────────
    params = [
        ('center', f'{centro_lat},{centro_lon}'),
        ('zoom', str(zoom)),
        ('size', tamano),
        ('maptype', maptype),
        ('scale', str(scale)),
        ('key', api_key),
    ]

    for coord in valid_coords:
        marker = f'color:{coord["color"]}|size:{coord["size"]}|label:{coord["label"]}|{coord["lat"]},{coord["lon"]}'
        params.append(('markers', marker))

    try:
        response = requests.get(base_url, params=params, timeout=30)
        if response.status_code != 200:
            logger.error("Error Google Maps API: %s - %s", response.status_code, response.text[:200])
            return None
        return response.content
    except requests.exceptions.RequestException:
        logger.exception("Error de conexión con Google Maps API")
        return None
