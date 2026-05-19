# API de RegConstruccion

Esta documentación describe los endpoints de la API para la aplicación `reg_construccion`.

## Autenticación

Todos los endpoints requieren autenticación. Debes incluir el token de autenticación en el header de las peticiones:

```
Authorization: Token <tu_token_aqui>
```

## Endpoints Principales

### 1. Listar Registros de Construcción

**GET** `/api/reg-construccion/`

Obtiene todos los registros de construcción activos del usuario autenticado.

**Parámetros de consulta:**
- `estado`: Filtra por estado del proyecto (construccion, paralizado, cancelado, concluido)
- `sitio`: Filtra por ID del sitio
- `contratista`: Filtra por ID del contratista
- `estructura`: Filtra por ID de la estructura
- `fecha`: Filtra por fecha
- `search`: Búsqueda en título y descripción
- `ordering`: Ordenamiento (created_at, updated_at, fecha, title)
- `page`: Número de página para paginación

**Ejemplo de respuesta:**
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "estado": "construccion",
            "sitio": {
                "id": 1,
                "name": "Sitio A",
                "pti_cell_id": "PTI001",
                "operator_id": "OP001"
            },
            "user": {
                "id": 1,
                "username": "usuario1",
                "first_name": "Juan",
                "last_name": "Pérez",
                "email": "juan@example.com"
            },
            "contratista": {
                "id": 1,
                "name": "Contratista A",
                "code": "CON001"
            },
            "estructura": {
                "id": 1,
                "name": "Estructura Principal",
                "description": "Descripción de la estructura"
            },
            "title": "Registro de Construcción 1",
            "description": "Descripción del registro",
            "fecha": "2024-01-15",
            "is_active": true,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

### 2. Registros Activos por Usuario

**GET** `/api/reg-construccion/activos-por-usuario/?user_id=<id>`

Obtiene todos los registros activos de un usuario específico.

**Parámetros requeridos:**
- `user_id`: ID del usuario

**Ejemplo:**
```
GET /api/reg-construccion/activos-por-usuario/?user_id=1
```

### 3. Mis Registros

**GET** `/api/reg-construccion/mis-registros/`

Obtiene todos los registros del usuario autenticado.

### 4. Detalle Completo de un Registro

**GET** `/api/reg-construccion/{id}/detalle-completo/`

Obtiene el detalle completo de un registro incluyendo todos sus datos relacionados.

**Ejemplo de respuesta:**
```json
{
    "id": 1,
    "estado": "construccion",
    "sitio": {...},
    "user": {...},
    "contratista": {...},
    "estructura": {...},
    "title": "Registro de Construcción 1",
    "description": "Descripción del registro",
    "fecha": "2024-01-15",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z",
    "objetivos": [
        {
            "id": 1,
            "objetivo": "Objetivo del proyecto",
            "is_active": true,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    ],
    "avances_componente": [
        {
            "id": 1,
            "fecha": "2024-01-15",
            "componente": {
                "id": 1,
                "name": "Componente A",
                "description": "Descripción del componente",
                "grupo": 1
            },
            "porcentaje_actual": 25,
            "porcentaje_acumulado": 25,
            "comentarios": "Comentarios del avance",
            "is_active": true,
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    ],
    "avance_componente_comentarios": [...],
    "ejecucion_porcentajes": [...]
}
```

### 5. Crear un Nuevo Registro

**POST** `/api/reg-construccion/`

Crea un nuevo registro de construcción.

**Ejemplo de datos:**
```json
{
    "estado": "construccion",
    "sitio_id": 1,
    "contratista_id": 1,
    "estructura_id": 1,
    "title": "Nuevo Registro de Construcción",
    "description": "Descripción del nuevo registro",
    "fecha": "2024-01-15"
}
```

### 6. Actualizar un Registro

**PUT** `/api/reg-construccion/{id}/`

Actualiza un registro existente.

**PATCH** `/api/reg-construccion/{id}/`

Actualiza parcialmente un registro.

### 7. Eliminar un Registro

**DELETE** `/api/reg-construccion/{id}/`

Elimina un registro (marca como inactivo).

## Endpoints de Objetivos

### Listar Objetivos
**GET** `/api/objetivos/`

### Crear Objetivo
**POST** `/api/objetivos/`

### Actualizar Objetivo
**PUT** `/api/objetivos/{id}/`

### Eliminar Objetivo
**DELETE** `/api/objetivos/{id}/`

## Endpoints de Avances por Componente

### Listar Avances
**GET** `/api/avances-componente/`

### Crear Avance
**POST** `/api/avances-componente/`

### Actualizar Avance
**PUT** `/api/avances-componente/{id}/`

### Eliminar Avance
**DELETE** `/api/avances-componente/{id}/`

## Endpoints de Comentarios de Avance

### Listar Comentarios
**GET** `/api/avance-componente-comentarios/`

### Crear Comentario
**POST** `/api/avance-componente-comentarios/`

### Actualizar Comentario
**PUT** `/api/avance-componente-comentarios/{id}/`

### Eliminar Comentario
**DELETE** `/api/avance-componente-comentarios/{id}/`

## Endpoints de Ejecución de Porcentajes

### Listar Porcentajes (Solo Lectura)
**GET** `/api/ejecucion-porcentajes/`

## Códigos de Estado HTTP

- `200 OK`: Petición exitosa
- `201 Created`: Recurso creado exitosamente
- `400 Bad Request`: Datos de entrada inválidos
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: No autorizado
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

## Ejemplos de Uso

### Obtener registros activos de un usuario específico
```bash
curl -H "Authorization: Token <tu_token>" \
     "http://localhost:8000/api/reg-construccion/activos-por-usuario/?user_id=1"
```

### Crear un nuevo registro
```bash
curl -X POST \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "estado": "construccion",
       "sitio_id": 1,
       "title": "Nuevo Proyecto",
       "description": "Descripción del proyecto"
     }' \
     "http://localhost:8000/api/reg-construccion/"
```

### Actualizar un registro
```bash
curl -X PUT \
     -H "Authorization: Token <tu_token>" \
     -H "Content-Type: application/json" \
     -d '{
       "estado": "concluido",
       "title": "Proyecto Actualizado"
     }' \
     "http://localhost:8000/api/reg-construccion/1/"
```
