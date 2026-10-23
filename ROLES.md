# Roles y permisos del proyecto

Toda decisión de permisos pasa por `core/permissions.py`. Hay dos cosas distintas:

- **Alcance** (fijo, según rol y empresa): qué registros ve cada usuario.
- **Permisos** (configurables): qué acciones puede hacer. El superusuario los cambia desde **Usuarios → Roles y permisos** (por rol) y desde **Editar usuario → Excepciones de permisos** (por usuario).

## Roles

| Rol | `user_type` | Empresa | Alcance de datos |
|-----|-------------|---------|------------------|
| Superusuario | `''` (sin rol) | **No puede tener** | Todo |
| ADMINISTRADOR global | `ADMINISTRADOR` | Sin empresa | Todas las empresas |
| ADMINISTRADOR de empresa | `ADMINISTRADOR` | Con empresa | Registros de usuarios de su empresa |
| ITO | `ITO` | Obligatoria | Solo sus propios registros |
| Buscador | `SEARCHER` | Obligatoria | Solo sus propios registros |
| Visita | `VISITA` | Obligatoria | Todo, solo lectura (nunca escribe) |

El rol Coordinador (`COORD`) se eliminó: la migración `users/0008` pasó los COORD a ADMINISTRADOR (con su empresa), dejó a los ADMINISTRADOR anteriores como globales (sin empresa) y quitó la empresa a los superusuarios.

Además, `User.report_access` limita a qué reportes accede cada usuario (vacío = todos). Se valida en el servidor en `alcance_registros` y `can_access_registro`.

## Permisos configurables (valores por defecto)

Catálogo: `core/permisos_catalogo.py` (`ACCIONES`). Para agregar una acción basta una entrada ahí; no requiere migración.

| Acción | Super | ADMINISTRADOR | ITO / Buscador | Visita |
|--------|:-----:|:-------------:|:--------------:|:------:|
| `cargar_datos` — visitas, pasos, fotos, mapas, % actual, fecha, copiar | ✅ | ✅ | ✅ | ❌ |
| `activar_registro` — activar registros y sitios de obra | ✅ | ✅ | ❌ | ❌ |
| `cambiar_responsable` — cambiar el ITO/Buscador de un registro | ✅ | ✅ | ❌ | ❌ |
| `concluir` | ✅ | ✅ | ✅ | ❌ |
| `reabrir` | ✅ | ✅ | ❌ | ❌ |
| `definir_items_obra` — plantilla, agregar, borrar ítems | ✅ | ✅ | ❌ | ❌ |
| `gestionar_usuarios` | ✅ | ✅ | ❌ | ❌ |
| `editar_sitios_empresas` — ver y editar Sitios y Empresas | ✅ | ✅ (solo global) | ❌ | ❌ |

Todo esto dentro del alcance: un ADMINISTRADOR de empresa o un ITO solo actúan sobre los registros que ven.

### Orden de resolución (`tiene_permiso(user, accion)`)

1. Superusuario → sí.
2. Visita → no (no se puede configurar).
3. Excepción del usuario (`PermisoUsuario`) → manda.
4. Permiso del rol (`PermisoRol`) → manda.
5. Valor por defecto del catálogo.

`PermisoRol`/`PermisoUsuario` guardan solo las diferencias con el valor por defecto (con historial). El mapa por rol se cachea y se invalida al guardar (`invalidar_cache_permisos`). Las excepciones por usuario las define solo el superusuario.

### Usuarios (permiso `gestionar_usuarios`)

- Superusuario: crea, edita y elimina a cualquiera.
- ADMINISTRADOR global: a cualquiera salvo superusuarios y otros administradores globales; puede crear ADMINISTRADOR de empresa, pero no globales.
- Con empresa (ADMINISTRADOR): solo ITO/Buscador/Visita de su empresa; no crea administradores.
- Reglas en `core.permissions.puede_editar_usuario` y `users.permissions.validar_rol_empresa`.

## Fijo en código (no configurable)

| Acción | Quién |
|--------|-------|
| Crear, importar y **eliminar** sitios y empresas | Solo superusuario |
| Eliminar registros, fotos, reportes; borrar/comprimir imágenes | Solo superusuario |
| Pasos, Widgets, Catálogo, Formatear, Configuración de correo | Solo superusuario |
| Impersonar | Solo `is_superuser` de Django (ver abajo) |
| Descargar PDF | Todos, dentro de su alcance |
| Cualquier escritura | Nunca Visita |

## Template tags — `{% load access_tags %}`

| Tag | Criterio | Usar para |
|-----|----------|-----------|
| `{% con_permiso 'accion' %}...{% endcon_permiso %}` | `tiene_permiso(user, 'accion')` | Botones de una acción configurable |
| `{% permiso 'accion' as ok %}` | ídem, como valor | Condiciones en plantillas |
| `{% editable %}...{% endeditable %}` | `not is_visita` | Botones de escritura genéricos |
| `{% supermanager_only %}...{% endsupermanager_only %}` | `is_supermanager` | Acciones solo del superusuario |
| `{% editor_sitios %}...{% endeditor_sitios %}` | `puede_editar_sitios_empresas` | Editar Sitios y Empresas |
| `{% btn_access as access %}` | VISITA → `hidden`; concluido → `disabled`; `puede_escribir` del contexto; si no, `cargar_datos` | Controles de widgets |

## Backend — `from core.permissions import ...`

| Helper | Criterio | Usar en |
|---|---|---|
| `tiene_permiso(user, accion)` | Resolución de arriba | Cualquier decisión por acción |
| `permiso_required(accion)` / `PermisoRequiredMixin` (`accion`, `solo_escritura`, `siempre_json`) | `tiene_permiso` | FBV / CBV |
| `CargaDatosMixin` | POST solo con `cargar_datos` (JSON 403) | Endpoints que guardan datos de un registro |
| `ActivarRegistroMixin` | `activar_registro` | Vistas de activación |
| `UsuariosAccessMixin`, `puede_gestionar_usuarios`, `puede_editar_usuario` | `gestionar_usuarios` + alcance | Usuarios |
| `SitiosEmpresasAccessMixin`, `puede_editar_sitios_empresas` | Superusuario o ADMINISTRADOR global con `editar_sitios_empresas` | Sitios y Empresas |
| `@not_visita` / `NotVisitaMixin` | `not is_visita` | Endpoints que Visita no puede ejecutar |
| `@superuser_required` / `SuperuserRequiredMixin` | `is_supermanager` | Solo superusuario |
| `alcance_registros(qs, user)` | Alcance + `report_access` | Listados, dashboard, galería |
| `can_access_registro(user, registro)` | Misma regla a nivel de objeto | Detalle, fotos, PDF |
| `puede_escribir_registro(user, registro)` | `cargar_datos` + alcance | Escritura sobre un registro |
| `puede_cambiar_concluido(user, registro)` | `concluir`/`reabrir` + alcance | Concluir y reabrir |

Los decoradores y mixins devuelven `JsonResponse 403` para endpoints AJAX y `redirect` para páginas; un anónimo va al login.

## Regla rápida al agregar un botón o endpoint nuevo

1. ¿Es una acción que se quiera poder dar o quitar por rol? → agregarla a `ACCIONES` y usar `{% con_permiso %}` + `permiso_required` / `PermisoRequiredMixin`.
2. ¿Solo el superusuario? → `{% supermanager_only %}` + `@superuser_required`.
3. ¿Lo que cualquiera menos Visita puede hacer? → `{% editable %}` + `@not_visita`.
4. Si toca datos de un registro: además `can_access_registro` / `puede_escribir_registro` y `registro_bloqueado_response`.

## Propiedades del modelo User relevantes

```python
user.is_supermanager     # user_type=='' (superusuario; no tiene empresa)
user.is_administrador    # ADMINISTRADOR (global o de empresa)
user.is_admin_global     # ADMINISTRADOR sin empresa
user.is_admin_empresa    # ADMINISTRADOR con empresa
user.is_ito_like         # ITO y SEARCHER
user.is_limited          # ITO, SEARCHER y VISITA
user.is_visita           # VISITA
```

## Impersonate

Solo `is_superuser` de Django (no basta con ser supermanager, `user_type == ''`) puede ver la app como otro usuario, desde Usuarios → botón de espía. No se puede impersonar a otro superuser ni a usuarios inactivos o eliminados. Un banner permite volver a la cuenta propia. Los cambios hechos durante la impersonación se atribuyen al usuario impersonado en el historial.

## Construcción Sitios

Con los valores por defecto:

| Rol | Ver | Activar sitio | Nueva visita / editar cabecera | Definir ítems | Cargar % actual, actividades, comentarios, fotos |
|---|---|---|---|---|---|
| Superusuario | todas | sí | sí | sí | sí |
| ADMINISTRADOR global | todas | sí | sí | sí | sí |
| ADMINISTRADOR de empresa | las de su empresa | sí | las de su empresa | sí | sí (su empresa) |
| ITO / Buscador | las suyas | no | las suyas | no | sí (de los ítems, solo la columna «% actual») |
| Visita | todas (lectura) | no | no | no | no |

Quien tiene `definir_items_obra` pero no `cargar_datos` guarda únicamente la tabla de ítems y conserva el «% actual» ya cargado.

## Registro concluido (TX/TSS y Construcción Sitios)

- **El PDF se puede generar siempre.** Si el registro no está concluido sale con la marca de agua **BORRADOR** en todas las páginas (y `-BORRADOR` en el nombre del archivo); concluido sale limpio.
- **Concluir:** permiso `concluir` (por defecto ADMINISTRADOR, ITO, Buscador y superusuario), con un aviso de que ya no se podrá modificar el formulario.
- **Reabrir (desmarcar):** permiso `reabrir` (por defecto superusuario y ADMINISTRADOR).
- **Concluido = solo lectura para todos, también para el superusuario**: datos de los pasos, fotos, mapas, tabla de ítems, fecha, alternativa y cabecera. Para corregir hay que reabrir primero. Siguen permitidos: reabrir, formatear (superusuario) y crear registros/visitas nuevas. En Construcción Sitios una visita concluida **no se puede eliminar** (ni el botón ni el endpoint): hay que reabrirla primero.
- Backend: `core/permissions.py` → `puede_cambiar_concluido`, `registro_bloqueado`, `registro_bloqueado_response`.
