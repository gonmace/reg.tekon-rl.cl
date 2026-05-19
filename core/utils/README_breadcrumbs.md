# BreadcrumbsMixin - Guía de Uso Simplificada

El `BreadcrumbsMixin` es una herramienta simple para manejar breadcrumbs y títulos de página en tus vistas Django.

## Uso Básico

### 1. Vista Simple
```python
from django.views.generic import TemplateView
from core.utils.breadcrumbs import BreadcrumbsMixin

class MiVistaView(BreadcrumbsMixin, TemplateView):
    template_name = 'mi_template.html'
    
    class Meta:
        title = 'Mi Página'
        header_title = 'Gestión de Mi Página'
```

### 2. Vista con Breadcrumbs Personalizados
```python
class DetalleSitioView(BreadcrumbsMixin, DetailView):
    model = Site
    template_name = 'sitios/detalle.html'
    
    class Meta:
        title = 'Detalle del Sitio'
        header_title = 'Información del Sitio'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Sitios', 'url_name': 'core:sitios'},
            {'label': 'Detalle'}  # Sin url_name = página actual
        ]
```

## Opciones Disponibles

### En la clase Meta:

- **`title`**: Título de la página (para breadcrumbs)
- **`header_title`**: Título que aparece en el header
- **`breadcrumbs`**: Lista de breadcrumbs personalizados

### Estructura de breadcrumbs:
```python
breadcrumbs = [
    {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
    {'label': 'Sección', 'url_name': 'app:seccion'},
    {'label': 'Página Actual'}  # Sin url_name = página actual
]
```

## Variables Disponibles en Templates

Cuando usas `BreadcrumbsMixin`, tienes acceso a:

- `{{ page_title }}`: Título de la página
- `{{ header_title }}`: Título del header
- `{{ breadcrumbs }}`: Array de breadcrumbs

## Ejemplos Prácticos

### Dashboard
```python
class DashboardView(BreadcrumbsMixin, TemplateView):
    template_name = 'pages/dashboard.html'
    
    class Meta:
        title = 'Dashboard'
        header_title = 'Panel Principal'
```

### Lista de Registros
```python
class ListRegistrosView(BreadcrumbsMixin, TemplateView):
    template_name = 'pages/registros.html'
    
    class Meta:
        title = 'Registros Tx/Tss'
        header_title = 'Registros Tx/Tss'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Registros Tx/Tss'}
        ]
```

### Formulario de Registro
```python
class RegistroFormView(BreadcrumbsMixin, FormView):
    template_name = 'pages/registro_form.html'
    
    class Meta:
        title = 'Nuevo Registro'
        header_title = 'Crear Registro'
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Registros', 'url_name': 'registros:list'},
            {'label': 'Nuevo Registro'}
        ]
```

## Fallbacks Automáticos

Si no defines algo en `Meta`, el mixin usa valores por defecto:

- **Sin `title`**: Usa el nombre de la clase sin "View"
- **Sin `header_title`**: Usa el `title`
- **Sin `breadcrumbs`**: Genera "Inicio > Título actual"

## Migración desde la Versión Anterior

### Antes (complejo):
```python
class MiVistaView(BreadcrumbsMixin, TemplateView):
    template_name = 'mi_template.html'
    
    def get_parent_breadcrumbs(self):
        return [{"label": "Padre", "url": reverse("app:padre")}]
```

### Ahora (simple):
```python
class MiVistaView(BreadcrumbsMixin, TemplateView):
    template_name = 'mi_template.html'
    
    class Meta:
        title = 'Mi Página'
        breadcrumbs = [
            {'label': 'Padre', 'url_name': 'app:padre'},
            {'label': 'Mi Página'}
        ]
```

## Ventajas de la Nueva Versión

✅ **Más simple**: Solo necesitas definir `Meta`  
✅ **Más claro**: Todo está en un solo lugar  
✅ **Más flexible**: Puedes personalizar exactamente lo que necesitas  
✅ **Menos código**: No más métodos complejos de auto-detección  
✅ **Más mantenible**: Fácil de entender y modificar 