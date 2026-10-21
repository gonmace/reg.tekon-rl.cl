from widgets.base import WidgetBase
from widgets.registry import register_widget


class FormWidget(WidgetBase):
    def validate_config(self, config):
        errors = []
        if "max_length" in config and not isinstance(config["max_length"], int):
            errors.append("max_length debe ser un entero")
        if "opcional" in config and not isinstance(config["opcional"], bool):
            errors.append("opcional debe ser verdadero o falso")
        return errors

    def validate_data(self, data):
        text = data.get("text", "")
        if not isinstance(text, str):
            return ["El campo text debe ser una cadena de texto"]
        return []

    @staticmethod
    def _texto(data, config=None):
        """Texto guardado: el campo se llama como `config['name']` (default «comentario»); `text` es el nombre antiguo."""
        campo = (config or {}).get("name", "comentario")
        return str(data.get(campo) or data.get("text") or "")

    def completeness(self, data):
        return self.completeness_with_config(data, {})

    def completeness_with_config(self, data, config):
        return 3 if self._texto(data, config).strip() else 1

    def to_display(self, data, config):
        text = self._texto(data, config)
        return {
            "label": config.get("label", "Comentario"),
            "text": text,
            "is_empty": not text.strip(),
        }


@register_widget
class ComentarioWidget(FormWidget):
    slug = "comentario_widget"
    nombre = "Comentario"
    icon = "fa-solid fa-comment-dots"
