from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class PosteFormWidget(WidgetBase):
    slug = "poste_form_widget"
    nombre = "Datos del Poste"
    icon = "fa-brands fa-wpforms"

    def validate_data(self, data):
        errors = []
        for field in ("tipo_estructura", "altura", "tension"):
            if not str(data.get(field, "")).strip():
                errors.append(f"{field.replace('_', ' ').title()} es requerido")
        return errors

    def completeness(self, data):
        checkable = ["tipo_estructura", "altura", "tension", "placa_poste", "obstaculos", "empresa_energia", "comentario"]
        filled = sum(1 for f in checkable if str(data.get(f, "")).strip())
        if filled == 0:
            return 1
        return 3 if filled == len(checkable) else 2

    def to_display(self, data, config):
        return {
            "tipo_estructura": data.get("tipo_estructura") or config.get("default_tipo_estructura", ""),
            "altura": data.get("altura") or config.get("default_altura", ""),
            "placa_poste": data.get("placa_poste", ""),
            "obstaculos": data.get("obstaculos", ""),
            "luminaria": data.get("luminaria", False),
            "red_protegida": data.get("red_protegida", False),
            "acceso_camion_grua": data.get("acceso_camion_grua", bool(config.get("default_acceso_camion_grua"))),
            "vegetacion": data.get("vegetacion", False),
            "antena_microondas": data.get("antena_microondas", False),
            "tension": data.get("tension") or config.get("default_tension", ""),
            "empresa_energia": data.get("empresa_energia", ""),
            "comentario": data.get("comentario", ""),
        }
