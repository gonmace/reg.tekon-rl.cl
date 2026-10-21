from widgets.base import WidgetBase
from widgets.registry import register_widget

FIELD_NAME = 'entradas'


@register_widget
class ListaWidget(WidgetBase):
    slug = "lista_widget"
    nombre = "Lista numerada"
    icon = "fa-solid fa-list-ol"

    def validate_config(self, config):
        errors = []
        if "max_items" in config and not isinstance(config["max_items"], int):
            errors.append("max_items debe ser un entero")
        for clave in ("multilinea", "numerada"):
            if clave in config and not isinstance(config[clave], bool):
                errors.append(f"{clave} debe ser verdadero o falso")
        return errors

    def validate_data(self, data):
        if not isinstance(data.get(FIELD_NAME, []), list):
            return ["entradas debe ser una lista"]
        return []

    def completeness(self, data):
        items = data.get(FIELD_NAME) or []
        return 3 if any(str(i).strip() for i in items) else 1

    def to_display(self, data, config):
        items = [str(i).strip() for i in (data.get(FIELD_NAME) or []) if str(i).strip()]
        return {
            "label": config.get("label", "Lista"),
            "items": items,
            "is_empty": not items,
        }
