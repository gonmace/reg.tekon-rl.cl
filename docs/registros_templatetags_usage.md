# Uso de Templatetags Genéricos para URLs de Registros

Este archivo muestra cómo usar los templatetags genéricos para generar URLs de registros de manera dinámica.

## Cargar los Templatetags

```html
{% load registro_urls %}
```

## Funciones Disponibles

### 1. get_registro_url(etapa, registro_id, tipo='form')

Genera URLs para cualquier tipo de vista relacionada con registros.

**Parámetros:**
- `etapa`: Nombre de la etapa (sitio, acceso, equipamiento, etc.)
- `registro_id`: ID del registro
- `tipo`: Tipo de URL (form, photos, edit, delete, view, etc.)

**Ejemplos de uso:**

```html
<!-- URL para formulario de sitio -->
<a href="{% get_registro_url 'sitio' registro_id %}">Editar Sitio</a>

<!-- URL para fotos de acceso -->
<a href="{% get_registro_url 'acceso' registro_id 'photos' %}">Ver Fotos</a>

<!-- URL para editar equipamiento -->
<a href="{% get_registro_url 'equipamiento' registro_id 'edit' %}">Editar</a>

<!-- URL para eliminar seguridad -->
<a href="{% get_registro_url 'seguridad' registro_id 'delete' %}">Eliminar</a>
```

### 2. get_registro_photos_url(etapa, registro_id)

Función de conveniencia para generar URLs de fotos.

**Ejemplos de uso:**

```html
<!-- URL para fotos de sitio -->
<a href="{% get_registro_photos_url 'sitio' registro_id %}">Fotos del Sitio</a>

<!-- URL para fotos de acceso -->
<a href="{% get_registro_photos_url 'acceso' registro_id %}">Fotos de Acceso</a>
```

## Patrones de URL Soportados

El sistema intenta generar URLs usando estos patrones:

1. **Formularios**: `reg_txtss:r_{etapa}`
2. **Fotos**: `reg_txtss:photos_{etapa}`
3. **Edición**: `reg_txtss:edit_{etapa}`
4. **Eliminación**: `reg_txtss:delete_{etapa}`
5. **Vista**: `reg_txtss:view_{etapa}`
6. **Personalizado**: `reg_txtss:{tipo}_{etapa}`

## URLs de Fallback

Si no existe una URL específica, el sistema genera URLs genéricas:

- **Formularios**: `/reg_txtss/{registro_id}/{etapa}/`
- **Fotos**: `/reg_txtss/{registro_id}/{etapa}/photos/`

## Ejemplos Completos

### En un Template de Lista

```html
{% load registro_urls %}

<div class="registro-actions">
    <a href="{% get_registro_url 'sitio' registro.id %}" class="btn btn-primary">
        Editar Sitio
    </a>
    <a href="{% get_registro_url 'acceso' registro.id %}" class="btn btn-secondary">
        Editar Acceso
    </a>
    <a href="{% get_registro_photos_url 'sitio' registro.id %}" class="btn btn-info">
        Ver Fotos
    </a>
</div>
```

### En un Componente Reutilizable

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

### En un Menú de Navegación

```html
{% load registro_urls %}

<nav class="etapas-nav">
    <ul>
        <li><a href="{% get_registro_url 'sitio' registro_id %}">Sitio</a></li>
        <li><a href="{% get_registro_url 'acceso' registro_id %}">Acceso</a></li>
        <li><a href="{% get_registro_url 'equipamiento' registro_id %}">Equipamiento</a></li>
        <li><a href="{% get_registro_url 'seguridad' registro_id %}">Seguridad</a></li>
    </ul>
</nav>
```

## Ventajas

1. **Genérico**: Funciona con cualquier etapa sin modificar el template
2. **Flexible**: Soporta diferentes tipos de URLs
3. **Robusto**: Tiene fallbacks para URLs que no existen
4. **Mantenible**: Centraliza la lógica de generación de URLs
5. **Escalable**: Fácil agregar nuevos tipos de URLs

## Configuración de URLs

Para que funcione correctamente, asegúrate de que tus URLs sigan estos patrones:

```python
# reg_nombre/urls.py
urlpatterns = [
    # Formularios
    path('sitio/<int:registro_id>/', RSitioView.as_view(), name='r_sitio'),
    path('acceso/<int:registro_id>/', RAccesoView.as_view(), name='r_acceso'),
    
    # Fotos (opcional)
    path('sitio/<int:registro_id>/photos/', RSitioPhotosView.as_view(), name='photos_sitio'),
    path('acceso/<int:registro_id>/photos/', RAccesoPhotosView.as_view(), name='photos_acceso'),
    
    # Otros tipos (opcional)
    path('sitio/<int:registro_id>/edit/', RSitioEditView.as_view(), name='edit_sitio'),
    path('sitio/<int:registro_id>/delete/', RSitioDeleteView.as_view(), name='delete_sitio'),
]
``` 