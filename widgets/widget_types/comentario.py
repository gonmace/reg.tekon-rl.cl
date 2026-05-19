from widgets.base import WidgetBase
from widgets.registry import register_widget


class FormWidget(WidgetBase):
    def validate_config(self, config):
        errors = []
        if "max_length" in config and not isinstance(config["max_length"], int):
            errors.append("max_length debe ser un entero")
        return errors

    def validate_data(self, data):
        text = data.get("text", "")
        if not isinstance(text, str):
            return ["El campo text debe ser una cadena de texto"]
        return []

    def completeness(self, data):
        return 3 if str(data.get("text", "")).strip() else 1

    def to_display(self, data, config):
        text = data.get("text", "")
        return {
            "label": config.get("label", "Comentario"),
            "text": text,
            "is_empty": not str(text).strip(),
        }


@register_widget
class ComentarioWidget(FormWidget):
    slug = "comentario_widget"
    nombre = "Comentario"
    icon = "fa-solid fa-comment-dots"
