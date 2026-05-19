# Configuración Genérica de Registros

Este módulo proporciona una estructura modular y flexible para crear configuraciones de registros en Django. **`create_simple_config`** es la función base que permite agregar componentes (mapa, fotos, etc.) de manera modular.

## 🎯 **Enfoque Modular**

### **`create_simple_config()` - Función Base**
Esta es la función principal que permite crear configuraciones flexibles:

```python
from registros.config import create_simple_config

# Configuración básica
paso = create_simple_config(
    model_class=MiModelo,
    form_class=MiFormulario,
    title="Mi Paso",
    description="Descripción del paso"
)
```

## 🔧 **Componentes Modulares**

### 1. **Componente de Mapa**
```python
from registros.config import create_map_component

mapa_component = create_map_component(
    lat_field='latitud',
    lon_field='longitud',
    name_field='nombre',
    zoom=15
)

# Agregar a create_simple_config
paso = create_simple_config(
    model_class=MiModelo,
    form_class=MiFormulario,
    title="Paso con Mapa",
    description="Descripción",
    sub_elementos=[mapa_component]
)
```

### 2. **Componente de Fotos**
```python
from registros.config import create_photos_component

fotos_component = create_photos_component(
    photo_min=4,
    allowed_types=['image/jpeg', 'image/png'],
    photos_template='photos/photos_main.html'
)

# Agregar a create_simple_config
paso = create_simple_config(
    model_class=MiModelo,
    form_class=MiFormulario,
    title="Paso con Fotos",
    description="Descripción",
    sub_elementos=[fotos_component]
)
```

## 🚀 **Funciones de Ayuda Rápidas**

### 1. **`create_config_with_map()`**
Crea configuración con mapa agregado automáticamente:

```python
from registros.config import create_config_with_map

paso = create_config_with_map(
    model_class=Sitio,
    form_class=SitioForm,
    title="Ubicación",
    description="Seleccione ubicación en el mapa",
    lat_field='latitud',
    lon_field='longitud',
    name_field='nombre',
    zoom=12
)
```

### 2. **`create_config_with_photos()`**
Crea configuración con fotos agregadas automáticamente:

```python
from registros.config import create_config_with_photos

paso = create_config_with_photos(
    model_class=Documentacion,
    form_class=DocumentacionForm,
    title="Documentación",
    description="Suba las fotos",
    photo_min=6
)
```

### 3. **`create_config_with_map_and_photos()`**
Crea configuración con mapa y fotos:

```python
from registros.config import create_config_with_map_and_photos

paso = create_config_with_map_and_photos(
    model_class=Sitio,
    form_class=SitioForm,
    title="Sitio con Fotos",
    description="Configure sitio y suba fotos",
    photo_min=4,
    lat_field='latitud',
    lon_field='longitud'
)
```

### 4. **`create_config_with_multi_point_map()`**
Crea configuración con mapa de múltiples puntos:

```python
from registros.config import create_config_with_multi_point_map

paso = create_config_with_multi_point_map(
    model_class=Sitio,
    form_class=SitioForm,
    title="Sitio con Puntos de Referencia",
    description="Configure sitio y puntos de referencia",
    lat_field='latitud',
    lon_field='longitud',
    second_model_class=PuntoReferencia,
    second_model_relation_field='sitio'
)
```

## 🎛️ **Función Flexible**

### **`create_flexible_config()`**
Crea configuraciones especificando qué componentes incluir:

```python
from registros.config import create_flexible_config

# Solo formulario
config1 = create_flexible_config(
    MiModelo, MiFormulario, "Paso 1", "Solo formulario",
    components=[]
)

# Formulario con mapa
config2 = create_flexible_config(
    MiModelo, MiFormulario, "Paso 2", "Con mapa",
    components=['map'],
    lat_field='latitud', lon_field='longitud'
)

# Formulario con fotos
config3 = create_flexible_config(
    MiModelo, MiFormulario, "Paso 3", "Con fotos",
    components=['photos'],
    photo_min=6
)

# Formulario con mapa y fotos
config4 = create_flexible_config(
    MiModelo, MiFormulario, "Paso 4", "Con mapa y fotos",
    components=['map', 'photos'],
    photo_min=4, lat_field='latitud', lon_field='longitud'
)

# Formulario con mapa múltiple
config5 = create_flexible_config(
    MiModelo, MiFormulario, "Paso 5", "Con mapa múltiple",
    components=['multi_map'],
    second_model_class=PuntoReferencia
)
```

## 🔧 **Configuración Personalizada Avanzada**

### Combinando Componentes Manualmente
```python
from registros.config import create_simple_config, create_map_component, create_photos_component

# Crear componentes personalizados
mapa_personalizado = create_map_component(
    lat_field='coordenada_lat',
    lon_field='coordenada_lon',
    name_field='titulo',
    zoom=18,
    template_name='components/mapa_personalizado.html',
    css_classes='mi-mapa-container'
)

fotos_personalizadas = create_photos_component(
    photo_min=8,
    allowed_types=['image/jpeg', 'image/png', 'image/webp'],
    photos_template='photos/photos_avanzado.html',
    css_classes='mis-fotos-container'
)

# Crear configuración personalizada
paso = create_simple_config(
    model_class=MiModelo,
    form_class=MiFormulario,
    title="Configuración Personalizada",
    description="Ejemplo avanzado",
    template_form='components/formulario_personalizado.html',
    success_message="¡Guardado con éxito!",
    error_message="Error al guardar",
    sub_elementos=[mapa_personalizado, fotos_personalizadas]
)
```

## 📋 **Configuración Completa de Registro**

```python
from registros.config import create_registro_config

# Definir pasos usando cualquier método
pasos_config = {
    'informacion': create_simple_config(...),
    'ubicacion': create_config_with_map(...),
    'documentacion': create_config_with_photos(...),
    'evaluacion': create_config_with_map_and_photos(...)
}

# Crear configuración completa
registro_config = create_registro_config(
    registro_model=RegistroPrincipal,
    pasos_config=pasos_config,
    title="Mi Registro",
    app_namespace="mi_app"
)
```

## 🛠️ **Función de Ayuda Rápida**

```python
from registros.config_examples import crear_configuracion_rapida

# Solo formulario
config1 = crear_configuracion_rapida(
    MiModelo, MiFormulario, "Paso 1", "Descripción 1"
)

# Formulario con mapa
config2 = crear_configuracion_rapida(
    MiModelo, MiFormulario, "Paso 2", "Descripción 2",
    incluir_mapa=True, lat_field='latitud', lon_field='longitud'
)

# Formulario con fotos
config3 = crear_configuracion_rapida(
    MiModelo, MiFormulario, "Paso 3", "Descripción 3",
    incluir_fotos=True, photo_min=6
)

# Formulario con mapa y fotos
config4 = crear_configuracion_rapida(
    MiModelo, MiFormulario, "Paso 4", "Descripción 4",
    incluir_mapa=True, incluir_fotos=True
)

# Formulario con mapa múltiple
config5 = crear_configuracion_rapida(
    MiModelo, MiFormulario, "Paso 5", "Descripción 5",
    incluir_multi_mapa=True, second_model_class=PuntoReferencia
)
```

## 🎯 **Ventajas del Nuevo Enfoque**

1. **Flexibilidad Total**: `create_simple_config` es la base para todo
2. **Modularidad**: Componentes se pueden agregar/remover fácilmente
3. **Reutilización**: Componentes se pueden usar en diferentes configuraciones
4. **Simplicidad**: Funciones de ayuda para casos comunes
5. **Personalización**: Control total sobre cada componente
6. **Escalabilidad**: Fácil agregar nuevos tipos de componentes

## 📚 **Ejemplos Completos**

Ver el archivo `config_examples.py` para ejemplos detallados de uso.

### Ejemplo: Registro Completo con Diferentes Tipos de Pasos

```python
from registros.config import (
    create_simple_config,
    create_config_with_map,
    create_config_with_photos,
    create_config_with_map_and_photos,
    create_registro_config
)

# Paso 1: Información básica
paso1 = create_simple_config(
    model_class=RegistroPrincipal,
    form_class=RegistroForm,
    title="Información General",
    description="Datos básicos del registro"
)

# Paso 2: Ubicación con mapa
paso2 = create_config_with_map(
    model_class=Sitio,
    form_class=SitioForm,
    title="Ubicación",
    description="Seleccione la ubicación en el mapa",
    lat_field='latitud',
    lon_field='longitud'
)

# Paso 3: Documentación fotográfica
paso3 = create_config_with_photos(
    model_class=Documentacion,
    form_class=DocumentacionForm,
    title="Documentación",
    description="Suba las fotos de documentación",
    photo_min=6
)

# Paso 4: Evaluación con mapa y fotos
paso4 = create_config_with_map_and_photos(
    model_class=Evaluacion,
    form_class=EvaluacionForm,
    title="Evaluación Final",
    description="Complete la evaluación y suba fotos",
    photo_min=4
)

# Configuración completa
registro_config = create_registro_config(
    registro_model=RegistroPrincipal,
    pasos_config={
        'informacion': paso1,
        'ubicacion': paso2,
        'documentacion': paso3,
        'evaluacion': paso4
    },
    title="Registro Completo",
    app_namespace="mi_app"
)
```

## 🔄 **Migración desde la Versión Anterior**

La nueva estructura es compatible con la anterior. Los cambios principales son:

- **`create_simple_config()`** es ahora la función base principal
- **Componentes modulares** (`create_map_component`, `create_photos_component`)
- **Funciones de ayuda** para casos comunes
- **`create_flexible_config()`** para configuraciones dinámicas
- **Mejor organización** y más opciones de personalización

## 🎯 **Configuración Solo con Componentes**

### **`create_sub_element_only_config()` - Sin Formulario**
Esta función permite crear pasos que solo muestran componentes (mapa, fotos, etc.) sin formulario:

```python
from registros.config import create_sub_element_only_config, create_1_point_map_config

# Crear componente de mapa
mandato_mapa = create_1_point_map_config(
    model_class1=Site,
    lat1='lat_base',
    lon1='lon_base',
    name1='Mandato',
    icon1_color='blue'
)

# Configuración solo con componente (sin formulario)
paso = create_sub_element_only_config(
    title='Información del Mandato',
    description='Visualice la ubicación del mandato en el mapa.',
    sub_elementos=[mandato_mapa]  # Solo un componente
)
```

### **Características de `create_sub_element_only_config()`**
- ✅ **Sin formulario**: No requiere modelo ni formulario
- ✅ **Un solo componente**: Solo acepta un sub_elemento
- ✅ **Template personalizable**: Usa `components/component_only.html` por defecto
- ✅ **Validación**: Lanza error si se proporcionan múltiples componentes
- ✅ **Navegación**: Incluye botones de navegación automáticamente

### **Casos de Uso Comunes**
1. **Visualización de mapas**: Mostrar ubicaciones sin edición
2. **Galerías de fotos**: Visualizar fotos existentes
3. **Información de referencia**: Mostrar datos del mandato
4. **Dashboards**: Visualizaciones informativas

### **Ejemplo Completo**
```python
from registros.config import (
    create_sub_element_only_config,
    create_1_point_map_config,
    create_photos_config,
    create_registro_config
)

# Paso 1: Información básica (con formulario)
paso1 = create_simple_config(
    model_class=RegistroPrincipal,
    form_class=RegistroForm,
    title="Información General",
    description="Datos básicos del registro"
)

# Paso 2: Visualización del mandato (solo componente)
mandato_mapa = create_1_point_map_config(
    model_class1=Site,
    lat1='lat_base',
    lon1='lon_base',
    name1='Mandato',
    icon1_color='blue'
)

paso2 = create_sub_element_only_config(
    title="Ubicación del Mandato",
    description="Visualice la ubicación del mandato en el mapa",
    sub_elementos=[mandato_mapa]
)

# Paso 3: Documentación (con formulario)
paso3 = create_simple_config(
    model_class=Documentacion,
    form_class=DocumentacionForm,
    title="Documentación",
    description="Suba la documentación requerida"
)

# Configuración completa
registro_config = create_registro_config(
    registro_model=RegistroPrincipal,
    pasos_config={
        'informacion': paso1,
        'mandato': paso2,  # Paso solo con componente
        'documentacion': paso3
    },
    title="Registro con Componente Only",
    app_namespace="mi_app"
)
```

### **Template Personalizado**
El template `components/component_only.html` incluye:
- Título y descripción del paso
- Renderizado automático de sub-elementos
- Botones de navegación (Atrás, Actualizar)
- Estilos responsivos con DaisyUI
- Soporte para diferentes tipos de componentes

### **Validaciones**
```python
# ✅ Correcto - Un solo componente
paso = create_sub_element_only_config(
    title='Título',
    description='Descripción',
    sub_elementos=[mi_componente]
)

# ❌ Error - Múltiples componentes
paso = create_sub_element_only_config(
    title='Título',
    description='Descripción',
    sub_elementos=[componente1, componente2]  # ValueError
)
```

### **Integración con Funciones de Ayuda**
```python
from registros.config_examples import crear_configuracion_rapida_actualizada

# Solo componente de mapa
config = crear_configuracion_rapida_actualizada(
    title="Visualización de Mapa",
    description="Descripción del mapa",
    tipo_config="component_only",
    incluir_mapa=True,
    lat_field='latitud',
    lon_field='longitud'
)

# Solo componente de fotos
config = crear_configuracion_rapida_actualizada(
    title="Galería de Fotos",
    description="Descripción de la galería",
    tipo_config="component_only",
    incluir_fotos=True,
    photo_min=0
)
``` 