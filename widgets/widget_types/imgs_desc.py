from widgets.base import WidgetBase
from widgets.registry import register_widget


def _parse_descripciones(value):
    """Acepta string CSV o lista; retorna lista de strings no vacíos."""
    if isinstance(value, str):
        return [d.strip() for d in value.split(',') if d.strip()]
    if isinstance(value, list):
        return [str(d).strip() for d in value if str(d).strip()]
    return []


@register_widget
class ImgsDescWidget(WidgetBase):
    slug = "imgs_desc_widget"
    nombre = "Fotos con descripción"
    icon = "fa-solid fa-camera"

    def validate_config(self, config):
        parsed = _parse_descripciones(config.get("descripciones", ""))
        if not parsed:
            return ["Se requiere el campo 'descripciones' con al menos un valor (separados por coma)"]
        return []

    def validate_data(self, data):
        return []

    def completeness(self, data):
        # Las fotos están en el modelo Photos, no en DatoPaso.datos.
        # El nivel real se calcula en _compute_imgs_desc_level (actividades/views.py).
        return 1

    def to_contexto(self, datos, config, registro, paso_nombre, ct=None):
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        if ct is None:
            ct = ContentType.objects.get_for_model(type(registro))
        descripciones = _parse_descripciones(config.get("descripciones", ""))
        min_count = int(config.get('foto_min', len(descripciones) or 1))
        qs = Photos.objects.filter(
            content_type=ct, object_id=registro.id, etapa=paso_nombre
        ).order_by('orden', '-created_at')
        fotos = [{"descripcion": p.descripcion or "", "url": p.imagen.url} for p in qs]
        count = len(fotos)
        if descripciones:
            filled_descs = {f["descripcion"] for f in fotos}
            filled = sum(1 for d in descripciones if d in filled_descs)
            level = 1 if filled == 0 else (2 if filled < len(descripciones) else 3)
        else:
            level = 1 if count == 0 else (2 if count < min_count else 3)
        return {"count": count, "min_count": min_count, "fotos": fotos, "level": level}

    def to_display(self, data, config):
        from photos.models import Photos
        descripciones = _parse_descripciones(config.get("descripciones", ""))
        slots = data.get("slots", {})
        items = []
        for desc in descripciones:
            slot = slots.get(desc, {})
            photo_id = slot.get("photo_id")
            photo = None
            if photo_id:
                p = Photos.objects.filter(id=photo_id).first()
                if p:
                    photo = {"id": p.id, "url": p.imagen.url, "descripcion": p.descripcion or ""}
            items.append({"descripcion": desc, "photo": photo})
        filled = sum(1 for i in items if i["photo"])
        return {
            "label": config.get("label", "Fotos"),
            "items": items,
            "total": len(descripciones),
            "filled": filled,
        }
