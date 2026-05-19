# Registros Views - Estructura de Archivos

Este directorio contiene las vistas genéricas y base para el sistema de registros.

## Estructura de Archivos

### 📁 `base_views.py`
**Propósito:** Vistas base que definen la funcionalidad común para todos los registros.

**Clases principales:**
- `RegistroListView` - Vista base para listar registros
- `RegistroStepsView` - Vista base para mostrar pasos de registros
- `ElementoView` - Vista base para elementos de registros

### 📁 `activation_views.py`
**Propósito:** Vistas para activar y crear nuevos registros.

**Clases principales:**
- `GenericActivarRegistroView` - Vista genérica para activar registros

### 📁 `steps_views.py`
**Propósito:** Vistas para manejar los pasos/steps de los registros.

**Clases principales:**
- `GenericRegistroStepsView` - Vista genérica para mostrar pasos de registros
- `GenericRegistroTableListView` - Vista genérica para listar registros con tabla
- `GenericElementoView` - Vista genérica para elementos de registros





### 📁 `api_views.py`
**Propósito:** ViewSets de API REST para operaciones CRUD de registros.

**Clases principales:**
- `RegistrosViewSet` - ViewSet completo para manejar registros via API

## Convenciones de Nomenclatura

- **Base:** Archivos que contienen clases base abstractas
- **Generic:** Archivos que contienen implementaciones genéricas reutilizables
- **Specific:** Archivos que contienen implementaciones específicas
- **API:** Archivos que contienen ViewSets y endpoints de API REST

## Uso

### Para crear una nueva aplicación de registros:

```python
from registros.views.steps_views import (
    GenericRegistroStepsView,
    GenericElementoView,
    GenericRegistroTableListView
)
from registros.views.activation_views import GenericActivarRegistroView

class ListRegistrosView(GenericRegistroTableListView):
    """Vista para listar registros de mi aplicación."""
    
class StepsRegistroView(GenericRegistroStepsView):
    """Vista para mostrar pasos de registros de mi aplicación."""
    
class ElementoRegistroView(GenericElementoView):
    """Vista para elementos de registros de mi aplicación."""
    
class ActivarRegistroView(GenericActivarRegistroView):
    """Vista para activar registros de mi aplicación."""
```

## Migración desde la Estructura Anterior

| Archivo Anterior | Archivo Nuevo | Propósito |
|------------------|---------------|-----------|
| `base.py` | `base_views.py` | Vistas base |
| `generic_views.py` | `activation_views.py` | Vistas de activación |
| `generic_registro_views.py` | `steps_views.py` | Vistas de pasos |


| `registros.py` | `api_views.py` | ViewSets de API | 