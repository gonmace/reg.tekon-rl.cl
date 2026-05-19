# Iconos Diferentes para Pasos de Tablas Editables

## Descripción

El sistema ahora detecta automáticamente cuando un paso es una tabla editable y muestra un icono diferente (icono de tabla) en lugar del icono tradicional de formulario (notas).

## Funcionalidad

### ✅ **Detección Automática**
- El sistema detecta automáticamente si un paso es una tabla editable
- Se basa en la configuración del paso (`template_name` o `sub_elementos`)

### ✅ **Iconos Diferentes**
- **Formularios tradicionales**: Icono de notas (📝)
- **Tablas editables**: Icono de tabla (📊)

### ✅ **Tooltips Personalizados**
- **Formularios**: "Editar [Título del Paso]"
- **Tablas**: "Gestionar tabla de [Título del Paso]"

## Cómo Funciona

### 1. **Detección en la Vista**
En `registros/views/steps_views.py`, la vista `GenericRegistroStepsView` detecta si un paso es una tabla editable:

```python
# Verificar si es una tabla editable
is_table = (elemento_config.template_name == 'components/editable_table.html' or 
           any(sub.tipo == 'editable_table' for sub in elemento_config.sub_elementos))

# Agregar al contexto del paso
step_data = {
    'title': paso_config.title,
    'step_name': step_name,
    'registro_id': registro.id,
    'is_table': is_table,  # ← Nueva propiedad
    # ... resto del contexto
}
```

### 2. **Renderizado en el Template**
En `registros/templates/pages/step_generic.html`, el template usa la propiedad `is_table`:

```html
<a href="{{step.elements.form.url}}"
   class="btn btn-{{step.elements.form.color}} btn-circle p-1 sombra"
   title="{% if step.is_table %}Gestionar tabla de {{step.title}}{% else %}Editar {{step.title}}{% endif %}">
  {% if step.is_table %}
    {% include 'svgs/table.svg' %}
  {% else %}
    {% include 'svgs/notes.svg' %}
  {% endif %}
</a>
```

## Configuración

### **Para Pasos de Tabla Editable**
```python
# En config.py
PASOS_CONFIG = {
    'visita': create_table_only_config(
        title='Visitas',
        description='Administre las visitas realizadas.',
        columns=visitas_columns,
        model_class=Visita,
        template_name='components/editable_table.html',  # ← Esto activa el icono de tabla
        api_url='/reg_visita/api/visitas/',
        allow_create=True,
        allow_edit=True,
        allow_delete=True,
        page_length=10
    ),
}
```

### **Para Pasos Tradicionales**
```python
# En config.py
PASOS_CONFIG = {
    'sitio': create_custom_config(
        model_class=RSitio,
        form_class=RSitioForm,
        title='Sitio',
        description='Información general del sitio.',
        template_form='components/elemento_form.html',  # ← Esto mantiene el icono de notas
        sub_elementos=[sitio_mapa_component, sitio_fotos_component]
    ),
}
```

## Archivos Modificados

### **Nuevos Archivos**
- `templates/svgs/table.svg` - Icono de tabla para pasos editables

### **Archivos Modificados**
- `registros/views/steps_views.py` - Agregada detección de tablas editables
- `registros/templates/pages/step_generic.html` - Agregada lógica de iconos condicionales

## Ejemplos Visuales

### **Paso de Formulario Tradicional**
```
┌─────────────────┐
│   📝 Sitio      │  ← Icono de notas
└─────────────────┘
```

### **Paso de Tabla Editable**
```
┌─────────────────┐
│   📊 Visitas    │  ← Icono de tabla
└─────────────────┘
```

## Ventajas

1. **Identificación Visual Clara**: Los usuarios pueden identificar rápidamente qué pasos son tablas editables
2. **Experiencia de Usuario Mejorada**: Tooltips específicos para cada tipo de paso
3. **Consistencia**: Mantiene la coherencia visual del sistema
4. **Escalabilidad**: Fácil de extender para otros tipos de pasos en el futuro

## Casos de Uso

### **Tablas Editables**
- Gestión de visitas
- Gestión de avances
- Listas de elementos
- Datos tabulares

### **Formularios Tradicionales**
- Información de sitio
- Datos de acceso
- Configuraciones
- Información general

## Extensibilidad

El sistema está diseñado para ser fácilmente extensible. Para agregar nuevos tipos de iconos:

1. **Crear el SVG**: Agregar nuevo archivo en `templates/svgs/`
2. **Modificar la detección**: Agregar lógica en `steps_views.py`
3. **Actualizar el template**: Agregar condición en `step_generic.html`

## Compatibilidad

- ✅ **Retrocompatible**: No afecta pasos existentes
- ✅ **Opcional**: Solo se activa cuando se detecta tabla editable
- ✅ **Configurable**: Se puede personalizar por paso 