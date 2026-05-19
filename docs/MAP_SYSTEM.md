# Sistema de Mapas Genérico

## Descripción General

El sistema de mapas genérico permite mostrar ubicaciones geográficas en mapas interactivos usando Leaflet.js y generar imágenes estáticas usando Google Maps API. El sistema es completamente configurable y puede manejar desde 1 hasta 9 puntos diferentes en un mismo mapa.

## Características Principales

- **Múltiples Puntos**: Soporte para 1-9 coordenadas en un mismo mapa
- **Marcadores Personalizables**: Colores, tamaños y etiquetas únicas para cada punto
- **Líneas Conectivas**: Conexión automática entre puntos consecutivos
- **Leyenda Dinámica**: Muestra automáticamente todos los puntos con sus colores y etiquetas
- **Zoom Inteligente**: Ajuste automático del zoom según la distribución de puntos
- **Cálculo de Distancias**: Distancia total entre puntos consecutivos
- **Configuración Flexible**: Modelos y campos de coordenadas configurables

## Configuración de Pasos

### Propiedades de Configuración

| Propiedad | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `model_class` | Class | Sí | Clase del modelo Django |
| `has_photos` | bool | No | Si el paso tiene fotos (default: False) |
| `min_photo_count` | int | No | Mínimo de fotos requeridas (default: 4) |
| `desfase` | bool | No | Si calcular desfase entre puntos |
| `map` | dict | No | Configuración del mapa |

### Configuración de Mapas

#### Estructura Básica
```python
'map': {
    'coordinates_1': { ... },  # Requerido
    'coordinates_2': { ... },  # Opcional
    'coordinates_3': { ... },  # Opcional
    # ... hasta coordinates_9
}
```

#### Configuración de Coordenadas
```python
'coordinates_N': {
    'model': str,      # 'site', 'current', o nombre del modelo
    'lat': str,        # nombre del campo de latitud
    'lon': str,        # nombre del campo de longitud
    'label': str,      # etiqueta para mostrar
    'color': str,      # color del marcador (opcional)
    'size': str        # tamaño del marcador (opcional)
}
```

### Fuentes de Coordenadas

| Valor | Descripción |
|-------|-------------|
| `'site'` | Coordenadas del sitio base (lat_base, lon_base) |
| `'current'` | Coordenadas del modelo actual del paso |
| `'rsitio'` | Coordenadas del modelo RSitio |
| `'racceso'` | Coordenadas del modelo RAcceso |
| `'rempalme'` | Coordenadas del modelo REmpalme |

### Colores Disponibles

- `#3B82F6` - Azul (default para coord1)
- `#10B981` - Verde (default para coord2)
- `#8B5CF6` - Púrpura (default para coord3)
- `#F59E0B` - Naranja
- `#EF4444` - Rojo
- `#6B7280` - Gris
- `#e60000` - Rojo intenso

### Tamaños Disponibles

- `'small'` - 16x16px
- `'mid'` - 20x20px (default para coord2)
- `'large'` - 24x24px (default para coord1)
- `'xlarge'` - 28x28px

## Ejemplos de Configuración

### Configuración con Un Solo Punto
```python
'acceso': {
    'model_class': RAcceso,
    'map': {
        'coordinates_1': {
            'model': 'current',
            'lat': 'lat',
            'lon': 'lon',
            'label': 'Acceso',
            'color': '#8B5CF6',
            'size': 'large',
        },
        # No se especifica coordinates_2 - solo se muestra un punto
    }
}
```

### Configuración con Dos Puntos
```python
'sitio': {
    'model_class': RSitio,
    'has_photos': True,
    'min_photo_count': 4,
    'desfase': True,
    'map': {
        'coordinates_1': {
            'model': 'site',
            'lat': 'lat_base',
            'lon': 'lon_base',
            'label': 'Mandato',
            'color': '#3B82F6',
            'size': 'large',
        },
        'coordinates_2': {
            'model': 'current',
            'lat': 'lat',
            'lon': 'lon',
            'label': 'Inspección',
            'color': '#F59E0B',
            'size': 'mid',
        },
    }
}
```

### Configuración con Tres Puntos
```python
'empalme': {
    'model_class': REmpalme,
    'has_photos': True,
    'min_photo_count': 3,
    'map': {
        'coordinates_1': {
            'model': 'rsitio',
            'lat': 'lat',
            'lon': 'lon',
            'label': 'Sitio',
            'color': '#F59E0B',
            'size': 'large',
        },
        'coordinates_2': {
            'model': 'current',
            'lat': 'lat',
            'lon': 'lon',
            'label': 'Empalme',
            'color': '#e60000',
            'size': 'mid',
        },
        'coordinates_3': {
            'model': 'site',
            'lat': 'lat_base',
            'lon': 'lon_base',
            'label': 'Mandato',
            'color': '#3B82F6',
            'size': 'large',
        },
    }
}
```

## Funcionalidades del Frontend

### Mapa Interactivo
- **Marcadores Personalizados**: Cada punto tiene su propio color, tamaño y letra
- **Popups Informativos**: Muestran etiqueta y coordenadas exactas
- **Líneas Conectivas**: Conectan puntos consecutivos con línea punteada
- **Zoom Automático**: Se ajusta para mostrar todos los puntos
- **Leyenda Dinámica**: Se genera automáticamente según los puntos disponibles

### Generación de Imágenes
- **API Flexible**: Acepta 1-9 coordenadas
- **Zoom Inteligente**: Calculado según la distribución de puntos
- **Cálculo de Distancias**: Distancia total entre puntos consecutivos
- **Nombres Únicos**: Archivos nombrados con código PTI y operador

## API de Google Maps

### Endpoint
```
POST /api/v1/google-maps/
```

### Estructura de Request
```json
{
    "registro_id": 123,
    "coordenada_1": {
        "lat": -33.4567,
        "lon": -70.6483,
        "label": "M",
        "color": "#3B82F6",
        "size": "large"
    },
    "coordenada_2": {
        "lat": -33.4568,
        "lon": -70.6484,
        "label": "I",
        "color": "#EF4444",
        "size": "mid"
    },
    "coordenada_3": {
        "lat": -33.4569,
        "lon": -70.6485,
        "label": "P",
        "color": "#8B5CF6",
        "size": "large"
    },
    "zoom": 15,
    "maptype": "hybrid",
    "scale": 2,
    "tamano": "1200x600"
}
```

### Estructura de Response
```json
{
    "success": true,
    "message": "Imagen guardada exitosamente",
    "mapa_id": 456,
    "file_path": "google_maps/PTI001_OPERADOR_empalme.png",
    "file_url": "/media/google_maps/PTI001_OPERADOR_empalme.png",
    "distancia_total_metros": 150.25,
    "was_created": true,
    "parameters": {
        "zoom": 15,
        "maptype": "hybrid",
        "scale": 2,
        "tamano": "1200x600",
        "coordenadas": [...]
    }
}
```

## Ventajas del Sistema

1. **Escalabilidad**: Fácil agregar nuevos modelos y configuraciones
2. **Flexibilidad**: Soporte para 1-9 puntos con configuraciones únicas
3. **Reutilización**: Componente genérico para todos los pasos
4. **Mantenibilidad**: Código centralizado y bien documentado
5. **Experiencia de Usuario**: Interfaz consistente y intuitiva
6. **Rendimiento**: Carga dinámica de Leaflet y optimización de zoom

## Extensibilidad

### Agregar Nuevos Modelos
Para agregar soporte para nuevos modelos, actualizar el método `_get_model_class_by_name`:

```python
model_mapping = {
    'rsitio': 'reg_nombre.models.RSitio',
'racceso': 'reg_nombre.models.RAcceso',
'rempalme': 'reg_nombre.models.REmpalme',
'nuevo_modelo': 'reg_nombre.models.NuevoModelo',
}
```

### Agregar Nuevos Colores/Tamaños
Los colores y tamaños se pueden personalizar en cualquier configuración de coordenadas sin modificar el código base. 