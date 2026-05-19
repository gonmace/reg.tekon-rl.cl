# CompletenessChecker - Verificador de Completitud de Modelos

## Descripción

La clase `CompletenessChecker` es una utilidad genérica para verificar si los registros de modelos Django tienen todos los campos obligatorios llenos. Esta clase centraliza la lógica de verificación de completitud que antes se repetía en cada modelo.

## Características

- ✅ Verifica campos obligatorios (sin `blank=True` y `null=True`)
- ✅ Excluye campos automáticos y relaciones
- ✅ Maneja errores cuando el registro no existe
- ✅ Retorna información detallada sobre la completitud
- ✅ Funciona con cualquier modelo Django

## Uso

### 1. Importar la clase

```python
from registros.models.completeness_checker import (
    CompletenessChecker, 
    check_model_completeness, 
    check_instance_completeness
)
```
```

### 2. Verificar por ID del modelo

```python
# Usando la función de conveniencia
result = check_model_completeness(REmpalme, rempalme_id)

# O usando la clase directamente
result = CompletenessChecker.check_completeness(REmpalme, rempalme_id)
```

### 3. Verificar una instancia específica

```python
# Si ya tienes la instancia del modelo
instance = REmpalme.objects.get(id=1)
result = check_instance_completeness(instance)

# O usando la clase directamente
result = CompletenessChecker.check_completeness_by_instance(instance)
```

### 4. En modelos Django

```python
from registros.models.completeness_checker import check_model_completeness

class MiModelo(BaseModel):
    # ... campos del modelo ...
    
    @staticmethod
    def check_completeness(model_id):
        """
        Verifica si un registro tiene todos los campos obligatorios llenos.
        """
        return check_model_completeness(MiModelo, model_id)
```

## Estructura de Respuesta

La función retorna un diccionario con la siguiente estructura:

```python
{
    'color': str,           # 'success', 'warning', o 'error'
    'is_complete': bool,    # True si todos los campos están llenos
    'missing_fields': list, # Lista de campos faltantes
    'total_fields': int,    # Total de campos obligatorios
    'filled_fields': int    # Total de campos llenos
}
```

### Códigos de Color

- **`success`**: Todos los campos obligatorios están llenos
- **`warning`**: Faltan algunos campos obligatorios
- **`error`**: El registro no existe

## Ejemplo de Uso Completo

```python
from registros.models.completeness_checker import check_model_completeness
from reg_nombre.models import MiModelo

# Verificar completitud de un modelo
result = check_model_completeness(MiModelo, 123)

if result['is_complete']:
    print(f"✅ Registro completo ({result['filled_fields']}/{result['total_fields']} campos)")
else:
    print(f"⚠️  Registro incompleto. Campos faltantes: {result['missing_fields']}")
    print(f"   Progreso: {result['filled_fields']}/{result['total_fields']} campos")
```

## Ventajas de Usar CompletenessChecker

1. **DRY (Don't Repeat Yourself)**: Elimina código duplicado
2. **Mantenibilidad**: Cambios centralizados en un solo lugar
3. **Consistencia**: Mismo comportamiento en todos los modelos
4. **Flexibilidad**: Funciona con cualquier modelo Django
5. **Tipado**: Incluye type hints para mejor desarrollo

## Migración de Código Existente

Si tienes modelos con métodos `check_completeness` duplicados, puedes reemplazarlos fácilmente:

### Antes:
```python
@staticmethod
def check_completeness(model_id):
    # 50+ líneas de código duplicado...
    pass
```

### Después:
```python
from registrostxtss.models.completeness_checker import check_model_completeness

@staticmethod
def check_completeness(model_id):
    return check_model_completeness(MiModelo, model_id)
```

## Notas Técnicas

- La clase verifica automáticamente los campos que tienen `blank=True` y `null=True`
- Excluye campos automáticos como `id`, `created_at`, etc.
- Excluye campos de relación (ForeignKey, ManyToManyField, etc.)
- Maneja correctamente los errores cuando el registro no existe 