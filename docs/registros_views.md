# Vista Genérica para Registros

Esta vista genérica permite crear vistas para cualquier modelo de registro de manera consistente y reutilizable, manteniendo formularios específicos para cada modelo.

## Características

- ✅ **Reutilización de código**: Una sola implementación para la lógica común
- ✅ **Consistencia**: Mismo comportamiento base en todas las vistas
- ✅ **Mantenimiento**: Cambios en la lógica común se aplican automáticamente
- ✅ **Flexibilidad**: Cada modelo puede tener su propio formulario personalizado
- ✅ **Escalabilidad**: Fácil agregar nuevos modelos
- ✅ **URLs genéricas**: Templatetags para generar URLs dinámicamente

## Uso Básico

### ⚠️ **Método Obsoleto - Usar Comando Automático**

**En lugar de crear manualmente, usar el comando:**
```bash
python manage.py create_registro_app reg_nombre --pasos mi_modelo
```

### Método Manual (Solo para casos especiales)

### 1. Crear un formulario específico

```python
# reg_nombre/forms.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML
from .models import MiModelo

class MiModeloForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        # Configurar crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = "pb-4"
        
        # Layout específico para este modelo
        self.helper.layout = Layout(
            HTML('<div class="header">Mi Modelo</div>'),
            Field('registro'),
            Field('campo_especifico_1'),
            Field('campo_especifico_2'),
            Submit('submit', 'Guardar', css_class='btn btn-success')
        )
    
    class Meta:
        model = MiModelo
        fields = ['registro', 'campo_especifico_1', 'campo_especifico_2']
        labels = {
            'campo_especifico_1': 'Mi Campo 1',
            'campo_especifico_2': 'Mi Campo 2',
        }
```

### 2. Crear una vista específica

```python
# reg_nombre/views.py
from registros.views.generic_registro_views import GenericElementoView
from .models import MiModelo
from .forms import MiModeloForm

class MiModeloView(GenericElementoView):
    form_class = MiModeloForm
    
    def get_registro_config(self):
        return REGISTRO_CONFIG
```

### 3. Configurar en config.py

```python
# reg_nombre/config.py
from registros.config import create_custom_config

PASOS_CONFIG = {
    'mi_modelo': create_custom_config(
        model_class=MiModelo,
        form_class=MiModeloForm,
        title='Mi Modelo',
        description='Descripción del modelo',
        template_form='components/elemento_form.html'
    )
}
```

### 4. Registrar el modelo en admin (opcional)

```python
# reg_nombre/admin.py
from django.contrib import admin
from .models import MiModelo

admin.site.register(MiModelo)
```

## URLs Genéricas con Templatetags

### Cargar los Templatetags

```html
{% load registro_urls %}
```

### Generar URLs Dinámicamente

```html
<!-- URL para formulario de cualquier etapa -->
<a href="{% get_registro_url 'sitio' registro_id %}">Editar Sitio</a>
<a href="{% get_registro_url 'acceso' registro_id %}">Editar Acceso</a>
<a href="{% get_registro_url 'equipamiento' registro_id %}">Editar Equipamiento</a>

<!-- URL para fotos -->
<a href="{% get_registro_photos_url 'sitio' registro_id %}">Fotos del Sitio</a>

<!-- URL para otros tipos -->
<a href="{% get_registro_url 'sitio' registro_id 'edit' %}">Editar</a>
<a href="{% get_registro_url 'sitio' registro_id 'delete' %}">Eliminar</a>
```

### En Componentes Reutilizables

```html
{% load registro_urls %}

<div class="etapa-card">
    <h3>{{ etapa|title }}</h3>
    <div class="actions">
        <a href="{% get_registro_url etapa registro_id %}" class="btn btn-form">
            {% if is_complete %}Editar{% else %}Crear{% endif %}
        </a>
        <a href="{% get_registro_photos_url etapa registro_id %}" class="btn btn-photos">
            Fotos ({{ photo_count }})
        </a>
    </div>
</div>
```

## Funcionalidades Automáticas de la Vista Genérica

### Lógica Común

La vista genérica maneja automáticamente:

- ✅ Validación de formularios
- ✅ Pre-llenado de datos del sitio
- ✅ Manejo de edición vs creación
- ✅ Redirección automática
- ✅ Manejo de errores
- ✅ Breadcrumbs automáticos
- ✅ Interfaz consistente
- ✅ Contexto automático

### Formularios Específicos

Cada modelo debe tener su propio formulario con:

- Layout personalizado con crispy forms
- Campos específicos del modelo
- Validaciones específicas
- Help text personalizado
- Estilos específicos

## Personalización

### Personalizar Campos del Formulario

```python
class RMiModeloForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.registro_id = kwargs.pop('registro_id', None)
        super().__init__(*args, **kwargs)
        
        # Configurar campos específicos
        self.fields['campo_especifico'].help_text = 'Ayuda específica'
        self.fields['campo_especifico'].widget.attrs['placeholder'] = 'Placeholder específico'
        
        # Layout personalizado
        self.helper.layout = Layout(
            # Tu layout específico aquí
        )
```

### Personalizar Contexto de la Vista

```python
class RMiModeloView(GenericRegistroView):
    form_class = RMiModeloForm
    
    def setup(self, request, *args, **kwargs):
        kwargs['model_class'] = RMiModelo
        kwargs['etapa'] = 'mi_etapa'
        super().setup(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar datos específicos
        context['datos_especificos'] = 'valor'
        return context
```

### Personalizar Lógica de Guardado

```python
def form_valid(self, form):
    # Lógica específica antes de guardar
    instance = form.save(commit=False)
    instance.campo_calculado = self.calcular_valor()
    instance.save()
    return super().form_valid(form)
```

## Ejemplos de Uso

### Modelo de Sitio

```python
# registrostxtss/r_sitio/views.py
from registrostxtss.views.generic_views import GenericRegistroView
from registrostxtss.r_sitio.models import RSitio
from registrostxtss.r_sitio.form import RSitioForm

class RSitioView(GenericRegistroView):
    form_class = RSitioForm
    
    def setup(self, request, *args, **kwargs):
        kwargs['model_class'] = RSitio
        kwargs['etapa'] = 'sitio'
        super().setup(request, *args, **kwargs)
```

### Modelo de Acceso

```python
# registrostxtss/r_acceso/views.py
from registrostxtss.views.generic_views import GenericRegistroView
from registrostxtss.r_acceso.models import RAcceso
from registrostxtss.r_acceso.form import RAccesoForm

class RAccesoView(GenericRegistroView):
    form_class = RAccesoForm
    
    def setup(self, request, *args, **kwargs):
        kwargs['model_class'] = RAcceso
        kwargs['etapa'] = 'acceso'
        super().setup(request, *args, **kwargs)
```

## Estructura de Archivos

```
registrostxtss/
├── views/
│   ├── __init__.py
│   ├── generic_views.py          # Vista genérica principal
│   ├── example_usage.py          # Ejemplos de uso
│   └── README.md                 # Esta documentación
├── templatetags/
│   ├── __init__.py
│   ├── registro_urls.py          # Templatetags genéricos
│   └── example_usage.md          # Ejemplos de templatetags
├── r_sitio/
│   ├── models.py
│   ├── form.py                   # Formulario específico para sitio
│   └── views.py                  # Vista específica para sitio
├── r_acceso/
│   ├── models.py
│   ├── form.py                   # Formulario específico para acceso
│   └── views.py                  # Vista específica para acceso
└── r_mi_modelo/                  # Nuevo modelo
    ├── models.py
    ├── form.py                   # Formulario específico para mi modelo
    └── views.py                  # Vista específica para mi modelo
```

## Ventajas

1. **DRY (Don't Repeat Yourself)**: No repites la lógica común
2. **Consistencia**: Todas las vistas tienen el mismo comportamiento base
3. **Mantenimiento**: Cambios centralizados en la lógica común
4. **Escalabilidad**: Fácil agregar nuevos modelos
5. **Flexibilidad**: Formularios completamente personalizables
6. **URLs Genéricas**: Sistema de URLs dinámicas y reutilizables

## Consideraciones

- Asegúrate de que tu modelo herede de `BaseModel`
- El modelo debe tener un campo `registro` que sea una ForeignKey a `RegistrosTxTss`
- Cada modelo debe tener su propio formulario con crispy forms
- Puedes personalizar cualquier aspecto de la vista si es necesario
- La vista genérica maneja la lógica común, los formularios manejan la presentación específica
- Los templatetags genéricos manejan la generación de URLs de manera dinámica 