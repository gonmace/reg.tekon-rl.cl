# Sistema Flexible de Pasos

## Descripción General

El nuevo sistema flexible de pasos permite crear configuraciones donde cada paso puede contener múltiples tipos de elementos combinados de forma flexible. Esto reemplaza el sistema anterior donde cada paso tenía un tipo específico (formulario, tabla, mapa, etc.) y ahora permite cualquier combinación.

## Características Principales

- ✅ **Múltiples elementos por paso**: Cada paso puede contener formularios, tablas, mapas, fotos, información y elementos personalizados
- ✅ **Configuración declarativa**: Todo se define mediante funciones de configuración
- ✅ **Elementos opcionales**: Cada elemento puede ser marcado como requerido u opcional
- ✅ **Validación automática**: El sistema valida la completitud de todos los elementos requeridos
- ✅ **Templates flexibles**: Cada tipo de elemento tiene su propio template
- ✅ **Compatibilidad**: Mantiene compatibilidad con el sistema anterior

## Tipos de Elementos Disponibles

### 1. **Formulario** (`form`)
Elemento para capturar datos mediante formularios Django.

```python
create_form_element(
    model_class=MiModelo,
    form_class=MiFormulario,
    title="Información General",
    description="Complete los datos básicos",
    required=True
)
```

### 2. **Tabla** (`table`)
Elemento para gestionar datos en formato de tabla editable.

```python
create_table_element(
    model_class=MiTablaModel,
    title="Lista de Materiales",
    description="Gestione los materiales",
    columns=[
        {'name': 'nombre', 'title': 'Nombre', 'type': 'text', 'required': True},
        {'name': 'cantidad', 'title': 'Cantidad', 'type': 'number', 'required': True}
    ],
    min_rows=1,
    max_rows=20,
    required=True
)
```

### 3. **Mapa** (`map`)
Elemento para mostrar ubicaciones geográficas.

```python
create_map_element(
    map_type="single_point",
    title="Ubicación del Sitio",
    description="Seleccione la ubicación",
    lat_field="latitud",
    lon_field="longitud",
    name_field="nombre",
    zoom=15,
    icon_color="red",
    required=True
)
```

### 4. **Fotos** (`photos`)
Elemento para gestionar fotografías.

```python
create_photos_element(
    title="Fotos del Sitio",
    description="Suba al menos 4 fotos",
    min_count=4,
    max_count=10,
    required=True
)
```

### 5. **Información** (`info`)
Elemento para mostrar información estática.

```python
create_info_element(
    title="Información Importante",
    content="<p>Recuerde verificar todos los datos antes de continuar.</p>",
    icon="warning",
    color="warning"
)
```

### 6. **Personalizado** (`custom`)
Elemento para funcionalidades específicas.

```python
create_custom_element(
    config={
        'title': 'Mi Elemento',
        'template': 'mi_template.html',
        'data': {...}
    },
    template_name='components/custom_element.html'
)
```

## Configuración de Pasos

### Función Principal: `create_flexible_step_config()`

```python
from registros.config import create_flexible_step_config, create_form_element, create_map_element

paso = create_flexible_step_config(
    title="Información del Sitio",
    description="Complete toda la información del sitio",
    elements=[
        create_form_element(
            model_class=RSitio,
            form_class=RSitioForm,
            title="Datos del Sitio",
            required=True
        ),
        create_map_element(
            title="Ubicación",
            lat_field="lat",
            lon_field="lon",
            required=True
        ),
        create_photos_element(
            title="Fotos del Sitio",
            min_count=4,
            required=True
        )
    ],
    order=1
)
```

## Ejemplos de Uso

### Ejemplo 1: Paso Completo
```python
def crear_paso_sitio():
    elementos = [
        create_form_element(
            model_class=RSitio,
            form_class=RSitioForm,
            title="Datos del Sitio",
            required=True
        ),
        create_map_element(
            title="Ubicación",
            required=True
        ),
        create_photos_element(
            title="Fotos",
            min_count=4,
            required=True
        )
    ]
    
    return create_flexible_step_config(
        title="Sitio",
        description="Información completa del sitio",
        elements=elementos
    )
```

### Ejemplo 2: Paso Solo con Tabla
```python
def crear_paso_materiales():
    elementos = [
        create_table_element(
            model_class=Material,
            title="Materiales",
            columns=[
                {'name': 'nombre', 'title': 'Nombre', 'type': 'text', 'required': True},
                {'name': 'cantidad', 'title': 'Cantidad', 'type': 'number', 'required': True}
            ],
            required=True
        )
    ]
    
    return create_flexible_step_config(
        title="Materiales",
        description="Gestione los materiales",
        elements=elementos
    )
```

### Ejemplo 3: Paso Informativo
```python
def crear_paso_mandato():
    elementos = [
        create_info_element(
            title="Información del Mandato",
            content="<p>Revise la información del mandato antes de continuar.</p>",
            icon="info"
        ),
        create_map_element(
            title="Ubicación del Mandato",
            required=False
        )
    ]
    
    return create_flexible_step_config(
        title="Mandato",
        description="Información de referencia",
        elements=elementos
    )
```

## Configuración Completa de Registro

```python
from registros.config import create_registro_config

# Definir todos los pasos
PASOS_CONFIG = {
    'mandato': crear_paso_mandato(),
    'sitio': crear_paso_sitio(),
    'materiales': crear_paso_materiales(),
    'empalme': crear_paso_empalme(),
}

# Crear configuración del registro
REGISTRO_CONFIG = create_registro_config(
    registro_model=RVisita,
    pasos_config=PASOS_CONFIG,
    title="Registro de Visita",
    app_namespace="reg_visita"
)
```

## Validación y Completitud

El sistema valida automáticamente la completitud de cada paso:

- **Formularios**: Verifica que todos los campos requeridos estén llenos
- **Tablas**: Verifica el número mínimo y máximo de filas
- **Mapas**: Verifica que las coordenadas estén definidas
- **Fotos**: Verifica el número mínimo y máximo de fotos

### Estado de Completitud
```python
completeness = elemento.validate_completeness()
# Retorna:
{
    'is_complete': True/False,
    'missing_elements': ['form', 'photos'],
    'total_elements': 3,
    'completed_elements': 1
}
```

## Templates

### Template Principal: `flexible_step.html`
Maneja la renderización de todos los elementos del paso.

### Templates de Elementos
- `form_element.html`: Para formularios
- `table_element.html`: Para tablas
- `info_element.html`: Para información
- `custom_element.html`: Para elementos personalizados

## Migración desde el Sistema Anterior

### Antes (Sistema Anterior)
```python
# Cada paso tenía un tipo específico
paso = create_photo_map_config(
    model_class=RSitio,
    form_class=RSitioForm,
    title="Sitio",
    photo_min=4
)
```

### Ahora (Sistema Flexible)
```python
# Cada paso puede tener múltiples elementos
paso = create_flexible_step_config(
    title="Sitio",
    elements=[
        create_form_element(
            model_class=RSitio,
            form_class=RSitioForm,
            title="Datos del Sitio"
        ),
        create_map_element(title="Ubicación"),
        create_photos_element(title="Fotos", min_count=4)
    ]
)
```

## Ventajas del Nuevo Sistema

1. **Flexibilidad**: Cada paso puede contener cualquier combinación de elementos
2. **Reutilización**: Los elementos se pueden reutilizar en diferentes pasos
3. **Mantenibilidad**: Configuración más clara y organizada
4. **Escalabilidad**: Fácil agregar nuevos tipos de elementos
5. **Validación**: Validación automática de completitud
6. **UX**: Mejor experiencia de usuario con elementos organizados

## Consideraciones

- Los elementos se renderizan en el orden en que se definen
- Cada elemento puede tener su propio estado de validación
- Los templates son responsivos y usan DaisyUI
- El sistema mantiene compatibilidad con el código existente 