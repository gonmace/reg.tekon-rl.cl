class WidgetBase:
    """
    Contrato base para todos los widgets del sistema.

    Para crear un nuevo widget: subclasear, definir slug/nombre/icon e implementar
    validate_data, completeness y to_display. Decorar con @register_widget.
    """
    slug: str = ""
    nombre: str = ""
    icon: str = ""

    def validate_config(self, config: dict) -> list:
        """Valida la config de PasoWidget.config al crear/editar en admin."""
        return []

    def validate_data(self, data: dict) -> list:
        """Valida los datos al guardar. Retorna lista de strings de error."""
        return []

    def completeness(self, data: dict) -> int:
        """
        Retorna nivel 0-3 que representa el estado del widget:
          0 — sin configuración / widget no operativo
          1 — sin datos / vacío
          2 — datos parciales
          3 — completo / datos válidos
        """
        return 0 if not data else 3

    def to_display(self, data: dict, config: dict) -> dict:
        """
        Convierte datos guardados en DatoPaso a formato legible para PDF/informe.
        Recibe los datos crudos del widget y la config del PasoWidget.
        """
        return {"raw": data}

    def compute_derived(self, paso_datos: dict, registro) -> dict:
        """
        Calcula valores derivados a partir del dict completo de DatoPaso.datos y
        el registro (para acceder a sitio, fechas, etc.).
        Se llama una vez por paso al construir el contexto del overview.
        Retorna un dict con claves descriptivas; los valores llegan a step.computed.
        """
        return {}

    def to_contexto(self, datos: dict, config: dict, registro, paso_nombre: str, ct=None) -> dict:
        """
        Construye la entrada de contexto para este widget en ContextoRegistro.
        La implementación base cubre cualquier widget que guarde datos en DatoPaso.
        Widgets que leen modelos externos (Photos, GoogleMapsImage) sobreescriben este método.
        """
        return {
            "raw": datos,
            "display": self.to_display(datos, config),
            "computed": self.compute_derived(datos, registro),
            "level": self.completeness(datos),
        }
