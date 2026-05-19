# API Móvil de RegConstruccion

Esta documentación describe los endpoints específicos de la API móvil para la aplicación `reg_construccion`.

## Autenticación

Todos los endpoints requieren autenticación. Debes incluir el token de autenticación en el header de las peticiones:

```
Authorization: Token <tu_token_aqui>
```

## Base URL

```
http://localhost:8000/api/v1/mobile/
```

## Endpoints

### 1. Listar Sitios Activos por Usuario

**GET** `/api/v1/mobile/sitios-activos/?user_id=<id>`

Obtiene todos los sitios que tienen registros activos de un usuario específico.

**Parámetros requeridos:**
- `user_id`: ID del usuario

**Ejemplo de respuesta:**
```json
{
    "sitios": [
        {
            "id": 1,
            "name": "Sitio A",
            "pti_cell_id": "PTI001",
            "operator_id": "OP001"
        },
        {
            "id": 2,
            "name": "Sitio B",
            "pti_cell_id": "PTI002",
            "operator_id": "OP002"
        }
    ],
    "total": 2
}
```

**Ejemplo de uso:**
```bash
curl -H "Authorization: Token <tu_token>" \
     "http://localhost:8000/api/v1/mobile/sitios-activos/?user_id=1"
```

### 2. Crear Nueva Fecha

**POST** `/api/v1/mobile/crear-fecha/`

Crea un nuevo registro de construcción para una fecha específica.

**Datos requeridos:**
```json
{
    "sitio_id": 1,
    "title": "Registro de Construcción",
    "fecha": "2024-01-15"
}
```

**Datos opcionales:**
```json
{
    "description": "Descripción del registro",
    "estado": "construccion",
    "contratista_id": 1,
    "estructura_id": 1
}
```

**Ejemplo de respuesta:**
```json
{
    "message": "Registro creado exitosamente",
    "registro": {
        "id": 1,
        "estado": "construccion",
        "sitio": {...},
        "user": {...},
        "title": "Registro de Construcción",
        "description": "Descripción del registro",
        "fecha": "2024-01-15",
        "is_active": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
}
```

**Ejemplo de uso:**
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "sitio_id": 1,
       "title": "Nuevo Registro",
       "fecha": "2024-01-15",
       "description": "Descripción del proyecto"
     }' \
     "http://localhost:8000/api/v1/mobile/crear-fecha/"
```

### 3. Llenar Objetivo

**POST** `/api/v1/mobile/llenar-objetivo/`

Guarda o actualiza el objetivo de un registro específico.

**Datos requeridos:**
```json
{
    "registro_id": 1,
    "objetivo": "Objetivo del proyecto de construcción"
}
```

**Ejemplo de respuesta:**
```json
{
    "message": "Objetivo guardado exitosamente",
    "objetivo": {
        "id": 1,
        "objetivo": "Objetivo del proyecto de construcción",
        "is_active": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
}
```

**Ejemplo de uso:**
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "registro_id": 1,
       "objetivo": "Completar la construcción del edificio principal"
     }' \
     "http://localhost:8000/api/v1/mobile/llenar-objetivo/"
```

### 4. Llenar Avance

**POST** `/api/v1/mobile/llenar-avance/`

Guarda o actualiza el avance de un componente específico.

**Datos requeridos:**
```json
{
    "registro_id": 1,
    "componente_id": 1,
    "porcentaje_actual": 25
}
```

**Datos opcionales:**
```json
{
    "porcentaje_acumulado": 30,
    "comentarios": "Comentarios sobre el avance",
    "fecha": "2024-01-15"
}
```

**Ejemplo de respuesta:**
```json
{
    "message": "Avance guardado exitosamente",
    "avance": {
        "id": 1,
        "fecha": "2024-01-15",
        "componente": {
            "id": 1,
            "nombre": "Cimientos"
        },
        "porcentaje_actual": 25,
        "porcentaje_acumulado": 30,
        "comentarios": "Comentarios sobre el avance",
        "is_active": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
}
```

**Ejemplo de uso:**
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "registro_id": 1,
       "componente_id": 1,
       "porcentaje_actual": 25,
       "porcentaje_acumulado": 30,
       "comentarios": "Los cimientos están completos"
     }' \
     "http://localhost:8000/api/v1/mobile/llenar-avance/"
```

### 5. Llenar Tabla

**POST** `/api/v1/mobile/llenar-tabla/`

Guarda o actualiza los comentarios generales de avance por componente.

**Datos requeridos:**
```json
{
    "registro_id": 1,
    "comentarios": "Comentarios generales sobre el avance de todos los componentes"
}
```

**Ejemplo de respuesta:**
```json
{
    "message": "Comentarios guardados exitosamente",
    "comentarios": {
        "id": 1,
        "comentarios": "Comentarios generales sobre el avance de todos los componentes",
        "is_active": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    }
}
```

**Ejemplo de uso:**
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "registro_id": 1,
       "comentarios": "El proyecto avanza según lo planificado"
     }' \
     "http://localhost:8000/api/v1/mobile/llenar-tabla/"
```

### 6. Subir Imágenes

**POST** `/api/v1/mobile/subir-imagenes/`

Sube una o múltiples imágenes para un registro específico.

**Datos requeridos:**
- `registro_id`: ID del registro
- `imagenes`: Archivos de imagen (multipart/form-data)

**Datos opcionales:**
- `caption`: Descripción de las imágenes

**Ejemplo de respuesta:**
```json
{
    "message": "2 imágenes subidas exitosamente",
    "imagenes": [
        {
            "id": 1,
            "image_url": "/media/photos/imagen1.jpg",
            "caption": "Vista frontal del proyecto",
            "uploaded_at": "2024-01-15T10:00:00Z"
        },
        {
            "id": 2,
            "image_url": "/media/photos/imagen2.jpg",
            "caption": "Vista lateral del proyecto",
            "uploaded_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

**Ejemplo de uso:**
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -F "registro_id=1" \
     -F "caption=Vistas del proyecto" \
     -F "imagenes=@imagen1.jpg" \
     -F "imagenes=@imagen2.jpg" \
     "http://localhost:8000/api/v1/mobile/subir-imagenes/"
```

### 7. Obtener Registro Completo

**GET** `/api/v1/mobile/registro-completo/{registro_id}/`

Obtiene un registro completo con todos sus datos relacionados.

**Ejemplo de respuesta:**
```json
{
    "id": 1,
    "estado": "construccion",
    "sitio": {...},
    "user": {...},
    "contratista": {...},
    "estructura": {...},
    "title": "Registro de Construcción",
    "description": "Descripción del registro",
    "fecha": "2024-01-15",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "objetivos": [...],
    "avances_componente": [...],
    "avance_componente_comentarios": [...],
    "ejecucion_porcentajes": [...]
}
```

**Ejemplo de uso:**
```bash
curl -H "Authorization: Token <tu_token>" \
     "http://localhost:8000/api/v1/mobile/registro-completo/1/"
```

## Códigos de Estado HTTP

- `200 OK`: Petición exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Datos de entrada inválidos
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: No autorizado
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Flujo de Trabajo Típico

1. **Obtener sitios activos**: `GET /api/v1/mobile/sitios-activos/?user_id=1`
2. **Crear nueva fecha**: `POST /api/v1/mobile/crear-fecha/`
3. **Llenar objetivo**: `POST /api/v1/mobile/llenar-objetivo/`
4. **Llenar avances**: `POST /api/v1/mobile/llenar-avance/` (múltiples veces)
5. **Llenar tabla**: `POST /api/v1/mobile/llenar-tabla/`
6. **Subir imágenes**: `POST /api/v1/mobile/subir-imagenes/`

## Notas Importantes

- Todos los endpoints verifican que el usuario autenticado sea el propietario del registro
- No se pueden crear registros duplicados para la misma fecha, sitio y usuario
- Las imágenes se almacenan en el directorio de medios configurado
- Los porcentajes de avance deben estar entre 0 y 100
- Todos los registros se marcan como activos por defecto
