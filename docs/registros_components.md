# Sistema de Componentes de Registros

Este directorio contiene el sistema de componentes para manejar registros de forma declarativa y reutilizable.

## Archivos Principales

### `base.py`
Contiene la clase base `ElementoRegistro` que proporciona la funcionalidad común para todos los elementos:
- Gestión de formularios
- Manejo de instancias de modelos
- Validación y guardado
- Información de completitud

### `registro_config.py`
Sistema de configuración declarativa que permite definir registros de forma simple:

- **`RegistroConfig`**: Configuración completa de un tipo de registro
- **`PasoConfig`**: Configuración de un paso de registro
- **`ElementoConfig`**: Configuración de un elemento dentro de un paso
- **`SubElementoConfig`**: Configuración de sub-elementos (mapa, fotos, etc.)
- **`ElementoGenerico`**: Elemento genérico que se configura dinámicamente

### `utils.py`
Funciones utilitarias para manejar elementos:
- `handle_elemento_ajax_request`: Maneja peticiones AJAX para elementos
- `handle_elemento_form_request`: Maneja peticiones de formulario normales
- Funciones auxiliares para renderizado y validación

## Uso Actual

El sistema se utiliza principalmente en:

1. **`registros/config.py`**: Configuración de registros usando `RegistroConfig`
2. **`registros/views/elemento_views.py`**: Vistas que usan `ElementoGenerico`
3. **`registros/views/generic_registro_views.py`**: Vistas genéricas que usan la configuración

## Ejemplo de Configuración

```python
from registros.components import RegistroConfig, ElementoConfig, SubElementoConfig

config = RegistroConfig(
    registro_model=MiModelo,
    pasos={
        'sitio': PasoConfig(
            elemento=ElementoConfig(
                nombre='sitio',
                model=RSitio,
                form_class=RSitioForm,
                sub_elementos=[
                    SubElementoConfig(
                        tipo='mapa',
                        config={'lat_field': 'lat', 'lon_field': 'lon'}
                    ),
                    SubElementoConfig(
                        tipo='fotos',
                        config={'min_files': 4}
                    )
                ]
            )
        )
    }
)
```

## Ventajas

- **Configuración declarativa**: Define registros sin duplicar código
- **Reutilización**: Una sola implementación para múltiples tipos
- **Flexibilidad**: Configuración por elemento y sub-elemento
- **Mantenibilidad**: Lógica centralizada y bien organizada 