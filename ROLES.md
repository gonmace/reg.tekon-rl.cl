# Roles y permisos del proyecto

## Jerarquía

| Rol | Empresa | Alcance de datos |
|-----|---------|-----------------|
| Supermanager (`user_type=''`, sin empresa) | No tiene | Todo |
| GERENCIA | Sí | Todas las empresas |
| COORD | Sí | Su empresa |
| ITO | Sí | Su empresa |
| SEARCHER | Sí | Su empresa |
| VISITA | Sí | Solo lectura |

## Matriz de permisos

| Acción | Super | GERENCIA | COORD | ITO | SEARCHER | VISITA |
|--------|:-----:|:--------:|:-----:|:---:|:--------:|:------:|
| Ver datos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Activar/copiar registros, toggle concluido, cambiar fecha, subir fotos, cambiar descripción, descargar | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Crear usuarios | ✅ | ✅ todas | ✅ propia | ❌ | ❌ | ❌ |
| Editar/eliminar registros, sitios, fotos; borrar/comprimir imágenes; acceso Empresas/Pasos/Widgets | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Template tags — `{% load access_tags %}`

| Tag | Criterio | Usar para |
|-----|----------|-----------|
| `{% editable %}...{% endeditable %}` | `not is_visita` | Botones de escritura que ITO/SEARCHER/COORD/GERENCIA pueden usar |
| `{% supermanager_only %}...{% endsupermanager_only %}` | `is_supermanager` | Acciones destructivas o de administración (solo superusuario) |

## Backend decorators / mixins — `from core.permissions import ...`

| Decorator / Mixin | Criterio | Usar en |
|---|---|---|
| `@not_visita` / `NotVisitaMixin` | `not is_visita` | FBV / CBV que VISITA no puede ejecutar (POST) |
| `@superuser_required` / `SuperuserRequiredMixin` | `is_supermanager` | FBV / CBV que solo supermanager puede ejecutar |

Ambos decoradores devuelven `JsonResponse 403` para endpoints AJAX y `redirect` para páginas normales.

## Regla rápida al agregar un botón o endpoint nuevo

1. **¿Puede un ITO hacerlo?** → `{% editable %}` en template + `@not_visita` en vista
2. **¿Solo el superusuario?** → `{% supermanager_only %}` en template + `@superuser_required` en vista
3. **¿Solo COORD/GERENCIA (no ITO)?** → usar `{% if not request.user.is_ito_like and not request.user.is_visita %}`
   *(sin tag propio por ahora — evaluar si se necesita un tercer tag `coordinator_only`)*

## Propiedades del modelo User relevantes

```python
user.is_visita        # True solo para VISITA
user.is_supermanager  # True si user_type=='' (sin rol = supermanager)
user.is_ito_like      # True para ITO y SEARCHER
user.is_limited       # True para ITO, SEARCHER y VISITA
user.is_coord         # True solo para COORD
user.is_gerencia      # True solo para GERENCIA
```
