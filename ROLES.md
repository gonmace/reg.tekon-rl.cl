# Roles y permisos del proyecto

## Jerarquía

| Rol | Empresa | Alcance de datos |
|-----|---------|-----------------|
| Supermanager (`user_type=''`, sin empresa) | No tiene | Todo |
| ADMINISTRADOR | Sí | Todas las empresas |
| COORD | Sí | Su empresa |
| ITO | Sí | Su empresa |
| SEARCHER | Sí | Su empresa |
| VISITA | Sí | Solo lectura |

## Matriz de permisos

| Acción | Super | ADMINISTRADOR | COORD | ITO | SEARCHER | VISITA |
|--------|:-----:|:--------:|:-----:|:---:|:--------:|:------:|
| Ver datos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Activar/copiar registros, toggle concluido, cambiar fecha, subir fotos, cambiar descripción, descargar | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Acceso a Usuarios / crear usuarios | ✅ | ❌ | ✅ propia | ❌ | ❌ | ❌ |
| Invitar por correo (el usuario crea su contraseña) | ✅ | ❌ | ✅ ITO/Buscador de su empresa | ❌ | ❌ | ❌ |
| Cambiar el ITO/Buscador de un registro o visita (botón Editar de Acciones; no concluidos) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Editar/eliminar sitios | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Editar/eliminar registros, fotos; borrar/comprimir imágenes; acceso a Pasos, Widgets y Configuración de correo | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Ver las páginas de Sitios y Empresas | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

## Template tags — `{% load access_tags %}`

| Tag | Criterio | Usar para |
|-----|----------|-----------|
| `{% editable %}...{% endeditable %}` | `not is_visita` | Botones de escritura que ITO/SEARCHER/COORD/ADMINISTRADOR pueden usar |
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
3. **¿Solo COORD/ADMINISTRADOR (no ITO)?** → usar `{% if not request.user.is_ito_like and not request.user.is_visita %}`
   *(sin tag propio por ahora — evaluar si se necesita un tercer tag `coordinator_only`)*

## Propiedades del modelo User relevantes

```python
user.is_visita        # True solo para VISITA
user.is_supermanager  # True si user_type=='' (sin rol = supermanager)
user.is_ito_like      # True para ITO y SEARCHER
user.is_limited       # True para ITO, SEARCHER y VISITA
user.is_coord         # True solo para COORD
user.is_administrador      # True solo para ADMINISTRADOR
```

## Impersonate

Solo `is_superuser` de Django (no basta con ser supermanager, `user_type == ''`) puede ver la app como otro usuario, desde Usuarios → botón de espía. No se puede impersonar a otro superuser ni a usuarios inactivos o eliminados. Un banner permite volver a la cuenta propia. Los cambios hechos durante la impersonación se atribuyen al usuario impersonado en el historial.

## Construcción Sitios

| Rol | Ver | Activar sitio | Nueva visita / editar cabecera | Definir ítems (plantilla, agregar, borrar) | Cargar % actual, actividades inspeccionadas, comentarios, fotos |
|---|---|---|---|---|---|
| Supermanager | todas | sí | sí | sí | sí |
| ADMINISTRADOR | todas | sí | no | sí | no |
| COORD | las de su contratista | sí | las de su contratista | no | sí |
| ITO / BUSCADOR | las suyas | no | las suyas | no | sí (de los ítems, solo la columna «% actual») |
| VISITA | todas (lectura) | no | no | no | no |

## Registro concluido (TX/TSS y Construcción Sitios)

- **El PDF se puede generar siempre.** Si el registro no está concluido sale con la marca de agua **BORRADOR** en todas las páginas (y `-BORRADOR` en el nombre del archivo); concluido sale limpio.
- **Concluir:** ITO, Buscador y superusuario, con un aviso de que ya no se podrá modificar el formulario.
- **Reabrir (desmarcar):** solo **superusuario y ADMINISTRADOR**. COORD, ITO, Buscador y Visita no pueden.
- **Concluido = solo lectura para todos, también para el superusuario**: datos de los pasos, fotos, mapas, tabla de ítems, fecha, alternativa y cabecera. Para corregir hay que reabrir primero. Siguen permitidos: reabrir, formatear (superusuario) y crear registros/visitas nuevas. En Construcción Sitios una visita concluida **no se puede eliminar** (ni el botón ni el endpoint): hay que reabrirla primero.
- Backend: `core/permissions.py` → `puede_cambiar_concluido`, `registro_bloqueado`, `registro_bloqueado_response`.

