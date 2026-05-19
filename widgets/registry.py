from widgets.base import WidgetBase

WIDGET_REGISTRY: dict[str, WidgetBase] = {}


def register_widget(cls):
    """Decorador para registrar una clase de widget en el registry global."""
    instance = cls()
    WIDGET_REGISTRY[instance.slug] = instance
    return cls


def get_widget(slug: str) -> WidgetBase | None:
    """Retorna la instancia del widget registrado con ese slug, o None."""
    _ensure_loaded()
    return WIDGET_REGISTRY.get(slug)


def _ensure_loaded():
    """Importa todos los tipos de widget si el registry aún está vacío."""
    if not WIDGET_REGISTRY:
        import widgets.widget_types  # noqa: F401
