from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class CameraWidget(WidgetBase):
    slug = "camera_widget"
    nombre = "Fotos"
    icon = "fa-solid fa-camera"

    def validate_config(self, config):
        errors = []
        for key in ("min_photos", "max_photos", "foto_min"):
            if key in config and not isinstance(config[key], int):
                errors.append(f"{key} debe ser un entero")
        return errors

    def validate_data(self, data):
        if not isinstance(data.get("photo_ids", []), list):
            return ["photo_ids debe ser una lista"]
        return []

    def completeness(self, data):
        # photo_ids se sincroniza desde el modelo Photos al guardar
        min_required = data.get("min_photos", 1)
        count = len(data.get("photo_ids", []))
        if count == 0:
            return 1
        if count < min_required:
            return 2
        return 3

    def to_contexto(self, datos, config, registro, paso_nombre, ct=None):
        from photos.models import Photos
        from django.contrib.contenttypes.models import ContentType
        if ct is None:
            ct = ContentType.objects.get_for_model(type(registro))
        min_count = int(config.get('foto_min', config.get('min_photos', 1)))
        count = Photos.objects.filter(content_type=ct, object_id=registro.id, etapa=paso_nombre).count()
        level = 1 if count == 0 else (2 if count < min_count else 3)
        return {"count": count, "min_count": min_count, "level": level}

    def to_display(self, data, config):
        from photos.models import Photos
        photo_ids = data.get("photo_ids", [])
        photos = []
        if photo_ids:
            for p in Photos.objects.filter(id__in=photo_ids).order_by('orden', '-created_at'):
                photos.append({"id": p.id, "url": p.imagen.url, "descripcion": p.descripcion or ""})
        return {
            "label": config.get("label", "Fotos"),
            "count": len(photo_ids),
            "min_photos": config.get("min_photos", config.get("foto_min", 1)),
            "photos": photos,
            "is_empty": len(photo_ids) == 0,
        }
