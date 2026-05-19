# Dashboard Ejecutivo

## Descripción

El Dashboard Ejecutivo es una aplicación profesional y ejecutiva que proporciona una vista completa y detallada de todos los sitios existentes en la base de datos, su estado de construcción y los registros TXTSS asociados.

## Características Principales

### 📊 Dashboard Principal
- **Estadísticas en tiempo real**: Muestra métricas clave como total de sitios, registros TXTSS, registros de construcción y usuarios activos
- **Gráficos interactivos**: Visualización de estados de construcción con gráficos de dona
- **Filtros avanzados**: Por estado, región y otros criterios
- **Tabla de sitios**: Vista detallada con información de cada sitio y sus registros

### 🏗️ Dashboard de Construcción
- **Filtros específicos**: Por estado, sitio, usuario y fechas
- **Estadísticas por estado**: Conteo de registros por cada estado de construcción
- **Tabla detallada**: Con información completa de cada registro de construcción

### 📄 Dashboard TXTSS
- **Filtros de búsqueda**: Por sitio, usuario y rangos de fechas
- **Estadísticas de usuarios**: Conteo de usuarios únicos y sitios únicos
- **Vista de registros**: Tabla completa de todos los registros TXTSS

### 🗺️ Dashboard de Sitios
- **Búsqueda avanzada**: Por nombre, PTI ID, operador ID y comuna
- **Filtros por estado y región**: Para encontrar sitios específicos
- **Información detallada**: Estado actual, registros asociados y fechas de último registro

## URLs Disponibles

- **Dashboard Principal**: `/dashboard/`
- **Dashboard Sitios**: `/dashboard/sitios/`
- **Dashboard Construcción**: `/dashboard/construccion/`
- **Dashboard TXTSS**: `/dashboard/txtss/`
- **API Estadísticas**: `/dashboard/api/stats/`
- **API Detalle Sitio**: `/dashboard/api/sitio/<id>/`

## Modelos

### DashboardMetric
Almacena métricas generales del sistema que se actualizan periódicamente:
- `metric_type`: Tipo de métrica (sitios_totales, registros_txtss, etc.)
- `value`: Valor numérico de la métrica
- `last_updated`: Fecha de última actualización

### SitioDashboard
Almacena información resumida de cada sitio para el dashboard:
- `sitio`: Relación con el modelo Site
- `total_registros_txtss`: Número total de registros TXTSS
- `total_registros_construccion`: Número total de registros de construcción
- `estado_actual`: Estado actual del sitio
- `ultimo_registro_txtss`: Fecha del último registro TXTSS
- `ultimo_registro_construccion`: Fecha del último registro de construcción

## Comandos de Gestión

### Poblar Métricas
```bash
python manage.py populate_dashboard_metrics
```

Este comando actualiza todas las métricas del dashboard con datos actuales de la base de datos.

## Características Técnicas

### Actualización en Tiempo Real
- Las estadísticas se actualizan automáticamente cada 30 segundos
- APIs RESTful para obtener datos actualizados
- Gráficos interactivos con Chart.js

### Diseño Responsivo
- Interfaz adaptativa para dispositivos móviles y de escritorio
- Componentes reutilizables con DaisyUI
- Navegación intuitiva y accesible

### Filtros y Búsqueda
- Filtros múltiples combinables
- Búsqueda por texto en campos específicos
- Paginación eficiente para grandes volúmenes de datos

### Seguridad
- Autenticación requerida para todas las vistas
- Verificación de permisos de usuario
- Protección CSRF en todos los formularios

## Integración con el Sistema

El Dashboard Ejecutivo se integra perfectamente con el sistema existente:

- **Menú principal**: Enlace agregado en el menú de navegación
- **Breadcrumbs**: Navegación consistente con el resto de la aplicación
- **Estilos**: Utiliza el mismo sistema de diseño que el resto de la aplicación
- **APIs**: Proporciona endpoints para integración con otras aplicaciones

## Personalización

### Agregar Nuevas Métricas
1. Agregar el tipo de métrica en `DashboardMetric.METRIC_TYPES`
2. Implementar la lógica en `DashboardStats`
3. Actualizar las plantillas para mostrar la nueva métrica

### Agregar Nuevos Filtros
1. Modificar las vistas correspondientes
2. Actualizar las plantillas con los nuevos campos de filtro
3. Agregar la lógica de filtrado en el backend

### Personalizar Gráficos
1. Modificar la configuración de Chart.js en las plantillas
2. Agregar nuevos tipos de gráficos según sea necesario
3. Personalizar colores y estilos

## Mantenimiento

### Actualización Regular de Métricas
Se recomienda ejecutar el comando de población de métricas regularmente:
```bash
# Actualizar métricas diariamente
python manage.py populate_dashboard_metrics
```

### Monitoreo de Rendimiento
- Las consultas están optimizadas con `select_related` y `prefetch_related`
- Paginación implementada para evitar sobrecarga de memoria
- Índices de base de datos recomendados para campos de búsqueda frecuente

## Soporte

Para reportar problemas o solicitar nuevas características, contactar al equipo de desarrollo.
