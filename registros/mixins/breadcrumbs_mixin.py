"""
Mixin genérico para manejar breadcrumbs en vistas de registro.
"""

from registros.utils.breadcrumbs import generate_registro_breadcrumbs


class RegistroBreadcrumbsMixin:
    """
    Mixin para generar breadcrumbs automáticamente en vistas de registro.
    
    Requiere que la vista tenga:
    - self.registro_config: Configuración del registro
    - self.kwargs.get('registro_id'): ID del registro
    - self.kwargs.get('paso_nombre'): Nombre del paso (opcional)
    """
    
    def get_breadcrumbs(self):
        """Genera breadcrumbs dinámicos usando la función genérica."""
        registro_id = self.kwargs.get('registro_id')
        paso_nombre = self.kwargs.get('paso_nombre')
        
        return generate_registro_breadcrumbs(
            registro_id=registro_id,
            paso_nombre=paso_nombre,
            registro_model=self.registro_config.registro_model if hasattr(self, 'registro_config') else None,
            registro_config=self.registro_config if hasattr(self, 'registro_config') else None
        ) 