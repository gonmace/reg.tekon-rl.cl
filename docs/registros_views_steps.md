# Vista de Pasos Genérica - BaseStepsView

## Descripción

La clase `BaseStepsView` es una vista base abstracta que permite crear vistas de pasos de registro de manera genérica y reutilizable. Maneja automáticamente diferentes tipos de contextos (con y sin fotos) y proporciona una estructura consistente para todas las vistas de pasos.

## Características Principales

- ✅ **Manejo automático de fotos**: Algunos pasos pueden tener fotos, otros no
- ✅ **Configuración flexible**: Cada paso puede tener diferentes configuraciones
- ✅ **Reutilización de código**: Lógica común centralizada
- ✅ **Fácil extensión**: Agregar nuevos pasos es muy simple
- ✅ **Consistencia**: Todas las vistas tienen el mismo comportamiento base

## Estructura de la Clase Base

### BaseStepsView (Clase Abstracta)

```python
class BaseStepsView(BreadcrumbsMixin, TemplateView, ABC):
    @abstractmethod
    def get_steps_config(self):
        """Define la configuración de los pasos"""
        pass
    
    def generate_step_context(self, registro_txtss, model_class, has_photos, min_photo_count=4):
        """Genera el contexto para un paso específico"""
        # Lógica común para generar contexto
```

### StepsRegistroView (Implementación Específica)

```python
class StepsRegistroView(BaseStepsView):
    template_name = 'pages/steps_txtss.html'
    
    def get_steps_config(self):
        return {
            'sitio': {
                'model_class': RSitio,
                'has_photos': True,
                'min_photo_count': 4
            },
            'acceso': {
                'model_class': RAcceso,
                'has_photos': False
            }
        }
```

## Cómo Crear una Nueva Vista de Pasos

### 1. Crear la Vista Específica

### ⚠️ **Método Obsoleto - Usar Comando Automático**

**En lugar de crear manualmente, usar el comando:**
```bash
python manage.py create_registro_app reg_nombre --pasos paso1 paso2 paso3
```

### Método Manual (Solo para casos especiales)

```python
# reg_nombre/views.py
from registros.views.generic_registro_views import GenericRegistroStepsView
from django.shortcuts import get_object_or_404
from .models import RegNombre

class MiVistaPasosView(GenericRegistroStepsView):
    template_name = 'reg_nombre/steps.html'
    
    def get_breadcrumbs(self):
        """Breadcrumbs específicos para esta vista"""
        breadcrumbs = [
            {'label': 'Inicio', 'url_name': 'dashboard:dashboard'},
            {'label': 'Mi Sección', 'url_name': 'mi_seccion:list'}
        ]
        
        # Agregar breadcrumb del sitio
        registro_id = self.kwargs.get('registro_id')
        if registro_id:
            registro = get_object_or_404(RegNombre, id=registro_id)
            sitio_cod = registro.sitio.pti_cell_id or registro.sitio.operator_id
            breadcrumbs.append({'label': sitio_cod})
        
        return self._resolve_breadcrumbs(breadcrumbs)
    
    def get_registro_config(self):
        """Configuración de los pasos para esta vista"""
        from .config import REGISTRO_CONFIG
        return REGISTRO_CONFIG
```

### 2. Configurar en config.py

```python
# reg_nombre/config.py
from registros.config import create_custom_config

PASOS_CONFIG = {
    'paso1': create_custom_config(
        model_class=Paso1,
        form_class=Paso1Form,
        title='Paso 1',
        description='Descripción del paso 1'
    ),
    'paso2': create_custom_config(
        model_class=Paso2,
        form_class=Paso2Form,
        title='Paso 2',
        description='Descripción del paso 2'
    ),
    'paso3': create_custom_config(
        model_class=Paso3,
        form_class=Paso3Form,
        title='Paso 3',
        description='Descripción del paso 3'
    )
}
```

### 3. Crear el Template

```html
<!-- templates/pages/mi_vista_pasos.html -->
{% extends "base.html" %}
{% load static %} 

{% block pre_content %}
    {% include 'components/common/breadcrumbs.html' %}
{% endblock pre_content %}

{% block content %}
<ul class="timeline timeline-vertical">
    {% include 'components/step&photo.html' with 
        registro_id=paso1.registro_id 
        title="paso1" 
        photo_count=paso1.photo.count 
        color_form=paso1.completeness_info.color  
        color_photo=paso1.photo.color 
        first=True %}
        
    {% include 'components/step.html' with 
        registro_id=paso2.registro_id 
        title="paso2" 
        color_form=paso2.completeness_info.color %}

    {% include 'components/step&photo.html' with 
        registro_id=paso3.registro_id 
        title="paso3" 
        photo_count=paso3.photo.count 
        color_form=paso3.completeness_info.color  
        color_photo=paso3.photo.color 
        last=True %}
</ul>
{% endblock %}
```

## Configuración de Pasos

### Estructura de Configuración

```python
{
    'nombre_paso': {
        'model_class': ModelClass,      # Clase del modelo Django
        'has_photos': bool,             # Si el paso tiene fotos
        'min_photo_count': int          # Mínimo de fotos (opcional, default: 4)
    }
}
```

### Ejemplos de Configuración

#### Paso con Fotos
```python
'sitio': {
    'model_class': RSitio,
    'has_photos': True,
    'min_photo_count': 4
}
```

#### Paso sin Fotos
```python
'acceso': {
    'model_class': RAcceso,
    'has_photos': False
}
```

#### Paso con Fotos Personalizadas
```python
'empalme': {
    'model_class': REmpalme,
    'has_photos': True,
    'min_photo_count': 3  # Solo requiere 3 fotos
}
```

## Contexto Generado

### Para Pasos con Fotos
```python
{
    'registro_id': 123,
    'completeness_info': {
        'color': 'success',
        'is_complete': True,
        'missing_fields': [],
        'total_fields': 5,
        'filled_fields': 5
    },
    'photo': {
        'count': 4,
        'color': 'success'
    }
}
```

### Para Pasos sin Fotos
```python
{
    'registro_id': 123,
    'completeness_info': {
        'color': 'warning',
        'is_complete': False,
        'missing_fields': ['campo1'],
        'total_fields': 3,
        'filled_fields': 2
    }
}
```

## Requisitos de los Modelos

Para que un modelo funcione con `BaseStepsView`, debe tener estos métodos estáticos:

### 1. get_etapa()
```python
@staticmethod
def get_etapa():
    return 'nombre_etapa'
```

### 2. check_completeness()
```python
@staticmethod
def check_completeness(instance_id):
    """
    Verifica la completitud del registro.
    
    Returns:
        dict: {
            'color': str,
            'is_complete': bool,
            'missing_fields': list,
            'total_fields': int,
            'filled_fields': int
        }
    """
```

## Personalización Avanzada

### Sobrescribir Métodos Específicos

```python
class MiVistaPersonalizada(BaseStepsView):
    def generate_step_context(self, registro_txtss, model_class, has_photos, min_photo_count=4):
        # Llamar al método base
        context = super().generate_step_context(registro_txtss, model_class, has_photos, min_photo_count)
        
        # Agregar lógica personalizada
        if has_photos:
            context['photo']['custom_field'] = 'valor_personalizado'
        
        return context
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar contexto adicional
        context['datos_adicionales'] = self.obtener_datos_adicionales()
        
        return context
```

### Agregar Validaciones Personalizadas

```python
def get_steps_config(self):
    config = super().get_steps_config()
    
    # Validar que todos los modelos tengan los métodos requeridos
    for step_name, step_config in config.items():
        model_class = step_config['model_class']
        
        if not hasattr(model_class, 'get_etapa'):
            raise ValueError(f"Modelo {model_class.__name__} debe tener método get_etapa()")
        
        if not hasattr(model_class, 'check_completeness'):
            raise ValueError(f"Modelo {model_class.__name__} debe tener método check_completeness()")
    
    return config
```

## Ventajas de la Nueva Estructura

### 1. Reutilización de Código
- Lógica común centralizada en `BaseStepsView`
- No duplicación de código entre vistas similares

### 2. Consistencia
- Todas las vistas de pasos tienen el mismo comportamiento
- Interfaz uniforme para el usuario

### 3. Mantenibilidad
- Cambios en la lógica común se aplican automáticamente
- Fácil de debuggear y mantener

### 4. Escalabilidad
- Agregar nuevos pasos es muy simple
- Crear nuevas vistas de pasos es rápido

### 5. Flexibilidad
- Cada vista puede tener su propia configuración
- Personalización específica cuando sea necesario

## Ejemplos de Uso Completo

### Vista Simple
```python
class VistaSimple(BaseStepsView):
    template_name = 'pages/simple.html'
    
    def get_steps_config(self):
        return {
            'paso1': {'model_class': Modelo1, 'has_photos': True},
            'paso2': {'model_class': Modelo2, 'has_photos': False}
        }
```

### Vista Compleja
```python
class VistaCompleja(BaseStepsView):
    template_name = 'pages/compleja.html'
    
    def get_breadcrumbs(self):
        # Breadcrumbs personalizados
        pass
    
    def get_steps_config(self):
        # Configuración compleja con múltiples pasos
        pass
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Contexto adicional
        return context
```

## Migración desde el Código Anterior

### Antes (Código Duplicado)
```python
def get_context_data(self, **kwargs):
    # Lógica específica para sitio
    # Lógica específica para acceso
    # Código duplicado para cada paso
```

### Después (Código Reutilizable)
```python
def get_steps_config(self):
    return {
        'sitio': {'model_class': RSitio, 'has_photos': True},
        'acceso': {'model_class': RAcceso, 'has_photos': False}
    }
```

La nueva estructura es más limpia, mantenible y escalable. 