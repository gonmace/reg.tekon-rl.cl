# Componentes Reutilizables

Este directorio contiene componentes JavaScript y CSS reutilizables que pueden ser utilizados en múltiples aplicaciones del proyecto.

## Componentes Disponibles

### 1. Alert Component (`alert-component.js`)

Componente para mostrar alertas y confirmaciones usando DaisyUI.

#### Uso

```html
<!-- Incluir en el HTML -->
<script src="{% static 'js/components/alert-component.js' %}"></script>
```

#### API

```javascript
// Alertas simples
Alert.success('Operación exitosa');
Alert.error('Ha ocurrido un error');
Alert.warning('Advertencia importante');
Alert.info('Información relevante');

// Alertas con opciones
Alert.success('Mensaje', {
    autoHide: 3000,  // Auto-ocultar en 3 segundos
    dismissible: false,  // No se puede cerrar manualmente
    icon: 'fa-solid fa-check'  // Icono personalizado
});

// Confirmaciones
Alert.confirm(
    '¿Estás seguro de que quieres eliminar este elemento?',
    () => {
        // Código a ejecutar si se confirma
        console.log('Confirmado');
    },
    () => {
        // Código a ejecutar si se cancela
        console.log('Cancelado');
    },
    {
        title: 'Confirmar eliminación',
        confirmText: 'Eliminar',
        cancelText: 'Cancelar'
    }
);

// Ocultar alertas
Alert.hide('alert-id');  // Ocultar alerta específica
Alert.hideAll();  // Ocultar todas las alertas
```

### 2. DataTables CSS (`../css/datatables.css`)

Estilos CSS para DataTables que incluyen soporte para tema claro y oscuro.

#### Uso

```html
<!-- Incluir en el HTML -->
<link rel="stylesheet" href="{% static 'css/datatables.css' %}">
```

#### Características

- Estilos responsivos para DataTables
- Soporte para tema claro y oscuro
- Animaciones suaves
- Compatible con DaisyUI
- Estilos personalizados para paginación, búsqueda y filtros

## Integración con Django

### 1. Configuración en settings.py

Asegúrate de que los archivos estáticos estén configurados correctamente:

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
```

### 2. Uso en templates

```html
{% load static %}

{% block css %}
<link rel="stylesheet" href="{% static 'css/datatables.css' %}">
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/components/alert-component.js' %}"></script>
<script type="module" src="{% static 'js/core.js' %}"></script>
{% endblock %}
```

### 3. Uso en JavaScript

```javascript
// El componente Alert estará disponible globalmente
document.addEventListener('DOMContentLoaded', function() {
    // Tu código aquí
    Alert.success('Página cargada correctamente');
});
```

## Personalización

### Alert Component

Puedes personalizar los estilos de las alertas modificando las clases CSS en el archivo `alert-component.js`:

```javascript
const alertClasses = {
    success: 'bg-green-50 border-l-4 border-green-400 text-green-800',
    error: 'bg-red-50 border-l-4 border-red-400 text-red-800',
    warning: 'bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800',
    info: 'bg-blue-50 border-l-4 border-blue-400 text-blue-800'
};
```

### DataTables CSS

Puedes personalizar los estilos de DataTables modificando las variables CSS en `datatables.css`:

```css
:root {
    --dt-row-selected: 13, 110, 253;
    --dt-row-selected-text: 255, 255, 255;
    --dt-row-hover: 0, 0, 0;
    /* ... más variables */
}
```

## Dependencias

- **Font Awesome**: Para los iconos de las alertas
- **DaisyUI**: Para los estilos de los botones y componentes
- **Tailwind CSS**: Para las clases de utilidad

## Compatibilidad

- Navegadores modernos (Chrome, Firefox, Safari, Edge)
- Soporte para tema oscuro/claro
- Responsive design
- Accesibilidad básica

## Contribución

Para agregar nuevos componentes:

1. Crea el archivo en el directorio apropiado
2. Documenta su uso en este README
3. Incluye ejemplos de uso
4. Mantén la consistencia con el estilo existente 