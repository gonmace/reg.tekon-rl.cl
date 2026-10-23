# CLAUDE.md — Convenciones del proyecto reportesTekon

## Regla de estilos

> **Preferir siempre clases de Tailwind o DaisyUI** en templates y `tables.py`. Editar `styles.css` solo cuando no existe clase equivalente (layout mobile complejo, `nth-child`, etc.).

---

## Stack
- Django 5.x + django-tables2 + HTMX 2.x
- Tailwind CSS v4 + DaisyUI v5
- Template base: `cupertino.html` (custom)
- CSS compilado: `theme/static_src/src/styles.css` → `static/css/dist/styles.css`
- Reconstruir CSS: `cd theme/static_src && npm run build` (o `npm run start` para watch)

---

## Tablas (django-tables2)

### Configuración estándar para TODAS las tablas

Toda tabla nueva debe seguir este patrón:

```python
class MiTabla(tables.Table):
    mi_columna = tables.Column(
        verbose_name='Label',
        attrs={'th': {'class': 'text-center'}, 'td': {'class': 'text-center py-1 md:px-4'}},
    )
    nombre = tables.Column(verbose_name='Nombre', attrs={'td': {'class': 'py-1 md:px-4'}})

    class Meta:
        template_name = "django_tables2/cupertino.html"
        attrs = {'class': 'table w-full'}
        row_attrs = {'class': 'pt-2'}   # ← obligatorio: padding-top en cada fila
```

**Por qué:**
- `py-1` en `td`: padding vertical en todos los breakpoints. No usar `py-*` sin pensar: en desktop sobreescribe el CSS de `styles.css` porque `@layer utilities` > `@layer components`.
- `md:px-4` en `td`: padding horizontal solo en desktop (≥ 768px). En mobile los td usan layout `inline-flex` con `padding: 0` definido en styles.css.
- `row_attrs = {'class': 'pt-2'}` en `tr`: separa visualmente cada fila del header sticky en mobile.

### Template de tabla
- Archivo: `templates/django_tables2/cupertino.html`
- El `tr` recibe `{{ row.attrs.as_html }}` → los `row_attrs` se renderizan directamente en el HTML

---

## Mobile: layout de tabla como cards

### CSS (`theme/static_src/src/styles.css`, dentro de `@layer components`)

El breakpoint mobile es `max-width: 768px`. En mobile, cada `tr` se convierte en una card con layout de 3 líneas via flexbox con `order`.

```
Línea 1: PTI ID (izq.)    · Operador ID (der.)
Línea 2: Nombre sitio     · Tipo badge (der.)
Línea 3: Región · Comuna  · Acciones (der.)
```

**Reglas clave:**
- `.table-card { overflow: clip; }` — permite sticky en hijos (no usar `overflow: hidden`)
- `.table-card-header { position: sticky; top: 0; z-index: 10; background-color: var(--color-base-200); }` — header fijo al scrollear
- `.table tbody { background-color: transparent; padding-top: 0.25rem; }` — deja ver el fondo del contenedor mayor (no usar un color fijo: en el tema claro se vería distinto), separación del header
- `.table tbody tr { display: flex; flex-wrap: wrap; background-color: var(--color-base-100); border-radius: var(--radius-box); }` — cada fila como card
- Badge de tipo sitio: `--size: 1rem; font-size: 0.6rem` en mobile para no estirar la línea 2

### Scroll
- El scroll ocurre en `<main class="flex-1 overflow-y-auto">` (base.html)
- El header sticky se queda fijo mientras el contenido de la tabla scrollea
- `overflow: hidden` en `.table-card` rompe el sticky → usar `overflow: clip`

---

## Imports pesados — lazy loading

`weasyprint` tarda ~11 segundos en importarse. **Nunca importar a nivel de módulo en `urls.py`.**

Patrón correcto para vistas PDF:

```python
# urls.py
def _pdf_view(request, *args, **kwargs):
    from .pdf_views import MiPDFView
    return MiPDFView.as_view()(request, *args, **kwargs)

urlpatterns = [
    path('pdf/<int:id>/', _pdf_view, name='pdf'),
]
```

Apps afectadas: `reg_construccion/urls.py`, `reg_txtss/urls.py`, `pdf_reports/urls.py` (`reg_construccion` es la app de Construcción Sitios, ver abajo)

---

## Startup
- `python3 manage.py check` debe tardar < 2 segundos
- Si tarda más: buscar imports de `weasyprint` o `django_weasyprint` a nivel de módulo

---

## HTMX en tablas
- El wrapper `#<app>-table-wrapper` es el target HTMX para search, sort y paginación
- Usa `hx-boost="true"` + `hx-target` + `hx-swap="innerHTML"` en el wrapper
- `SitiosView.get_template_names()` retorna `partials/table_swap.html` en requests HTMX

---

## Scripts en modales cargados con fetch

**Los `<script>` dentro de HTML inyectado via `innerHTML` NO se ejecutan** (restricción HTML5 en todos los navegadores modernos).

Patrón incorrecto — el script nunca corre:
```javascript
// ❌ El <script> dentro del HTML del modal no se ejecuta
modalContent.innerHTML = html;
```

Patrón correcto — adjuntar handlers en el JS del llamador, DESPUÉS de inyectar el HTML:
```javascript
// ✅ Inyectar HTML y luego adjuntar el handler programáticamente
modalContent.innerHTML = html;
var form = document.getElementById('mi-form');
if (form) {
    form.dataset.itemId = id;
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitForm(form);
    });
}
```

**Regla:** Nunca poner lógica de submit en `<script>` inline de un template parcial cargado via fetch. Toda la lógica JS debe vivir en el archivo `.js` estático de la página que hace el fetch.

---

## Venv
```bash
source .venv/bin/activate
python3 manage.py runserver 8001
```

---

## Registros por pasos (TX/TSS, Construcción Sitios)

- El timeline de pasos dinámicos es **genérico**: `registros/views/dynamic_steps.py` (`DynamicPasoViewBase`, `MapaSaveViewBase`, `get_dynamic_steps`, `make_toggle_concluido`/`make_formatear_registro`/`make_resumen_formatear`). Cada app lo subclasea fijando `registro_model` y `url_namespace`.
- **Convención:** el namespace de URLs de la app == su prefijo en `config/urls.py` (`reg_txtss` → `/reg_txtss/`, `reg_construccion` → `/reg_construccion/`) y publica `steps`, `paso_dinamico`, `mapa_save`. El motor arma URLs de fotos como `/<namespace>/<id>/<paso>/photos/`.
- Cada app registra su modelo en `AppConfig.ready()` con `registros.registry.register_registro_model(namespace, Model)`. `photos` lo usa para resolver el registro por URL (nunca asumir `RegTxtss`).
- Widgets (`widgets/widget_types/`): además de `validate_*`/`to_display`, pueden definir `extra_context(context)` (variables para su template) y `before_save(cleaned, stored, request, registro, paso, config)` (p. ej. permisos por rol antes de persistir).
- **Construcción Sitios** (`reg_construccion`): un registro por **visita** (en la interfaz y el PDF se llama **«reporte»**; único `(sitio, fecha)`); un sitio activado acumula varias visitas. Tipo de actividad `reg_construccion_torres` (sembrado en la migración 0002): pasos `obra_objetivos` (se muestra como «Actividades», con lista + cámara de fotos (mín. 4) + segunda cámara «Libro de obras» (`camera_libro_widget`, etapa `obra_libro`, opcional); la clave interna se conserva por los datos guardados), `obra_avance`, `obra_electrico` (un comentario + cámara) y `obra_comentarios` («Comentarios y acciones»: `lista_widget` con `multilinea`/`numerada: false`, un párrafo por entrada en el PDF). No hay paso de fotos general: cada sección con cámara tiene sus fotos (`etapa` = nombre del paso, o `config['etapa']` en cámaras extra como `camera_libro_widget`, que permiten dos cámaras en un mismo paso) y su selector 1/2 por fila en el PDF. El PDF oculta Eléctrico y Comentarios si están vacíos. La tabla de ítems (partidas de obra) es `tabla_avance_widget`: el % anterior/acumulado **se calcula** recorriendo las visitas del sitio (no se guarda); `RegConstruccion.avance_pct` es un denormalizado que mantiene `reg_construccion/signals.py`.
- **Listado maestro-detalle** (`/reg_construccion/`): arriba `SitiosObraTable` (una fila por sitio con el resumen de su última visita, una sola consulta con subqueries) y abajo el panel `#obra-visitas-panel` con las visitas del sitio elegido (`visitas_sitio`, HTMX; la selección va en `?sitio=ID`). El alcance por rol es `core.permissions.alcance_registros`. Los enlaces/filtros del panel usan `hx-get` explícitos, no los links relativos de django-tables2. Las tablas móviles se ordenan por `nth-child` en `styles.css` (`.reg-obra-sitios-table`, `.reg-obra-visitas-table`): si cambian las columnas, hay que actualizar ese bloque.
- Datos de Construcción solo para sitios `TORRE`. Definir los ítems (plantilla, agregar, borrar) es el permiso `definir_items_obra` (por defecto superusuario y ADMINISTRADOR); ITO y Buscador solo editan el `% actual`.

## Roles y permisos

Roles: superusuario (`user_type=''`, sin empresa), ADMINISTRADOR (global si no tiene empresa; de empresa si la tiene, y entonces solo ve/administra lo de su empresa), ITO, Buscador (`SEARCHER`) y Visita. **No existe COORD.** Toda decisión de permisos va por `core/permissions.py` (`tiene_permiso`, `alcance_registros`, `can_access_registro`, ...): no consultar `user_type` ni `is_*` sueltos en vistas o plantillas. Las acciones configurables viven en `core/permisos_catalogo.py` y el superusuario las edita en `/usuarios/` (por rol y por usuario). Detalle, tags y matriz en `ROLES.md`; al agregar un botón o endpoint, seguir su «Regla rápida». Los tests que dependen del mapa de permisos por rol (caché) deben hacer `cache.clear()` en `setUp`.

## Registro concluido

Un registro concluido es de **solo lectura para todos** (reglas en `ROLES.md`). Todo endpoint que escriba datos de un registro debe hacer `registro_bloqueado_response(registro)` (`core/permissions.py`) y devolver su 403 si no es `None`; las plantillas con widgets reciben `bloqueado` en el contexto (`btn_access` lo traduce a `disabled`). El PDF recibe `borrador = not registro.concluido` (marca de agua `.marca-agua` en `weasyprint.css`).

## Dashboard (inicio `/`)

Solo Construcción Sitios. Vista: `core/views/dashboard.py`; plantilla `core/templates/pages/dashboard.html`; toda la lógica en `reg_construccion/dashboard.py` (`panel`, `actividad_reciente`, `pendientes`, `mapa_geojson`, y `sitios_con_ultima_visita`, que también usa el listado maestro). Todo pasa por `alcance_registros` y se cachea por alcance (`cached`). Mapa Leaflet: `static/js/dashboard_construccion.js` + `reg_construccion:api_mapa_dashboard`; las teselas de OSM exigen `referrerPolicy: 'origin'` (sin Referer responde «Access blocked»). Usuarios sin acceso a `construccion` ven una bienvenida. El app `dashboard` (TX/TSS ejecutivo) fue eliminado; sus tablas huérfanas pueden borrarse: `DROP TABLE dashboard_dashboardmetric, dashboard_sitiodashboard; DELETE FROM django_migrations WHERE app='dashboard';`

## Impersonate

`django-hijack`. Solo `is_superuser` de Django puede impersonar, y nunca a otro superuser (`users/permissions.py::can_hijack`). Botón en la lista de Usuarios; banner en `templates/base.html`. Los cambios hechos mientras se impersona quedan en `simple_history` a nombre del usuario impersonado; los inicios/fines se registran en el logger `users.hijack`.

## Correo

- `EMAIL_BACKEND` es `core.email_backend.ConfigurableEmailBackend`: al enviar resuelve la config con `core/email_config.py::get_email_config()`. Por defecto lee `EMAIL_*` del `.env` (sin `EMAIL_HOST` va a la consola); si en **Configuración → Correo** (solo superusuario) hay una configuración personalizada activa (`core.models.correo.ConfiguracionCorreo`), esa manda. Los correos con el remitente por defecto salen con el de la config activa.
- La contraseña personalizada se guarda **sin cifrar** en base (decisión del proyecto); nunca se muestra en pantalla ni en errores. Una config personalizada solo se activa si conecta.
- Las pruebas de la pantalla (conectar / enviar) usan lo que esté en el formulario, aunque no se haya guardado. Las pruebas automáticas deben mockear `core.views.correo.conectar` / `crear_backend` (no tocar la red).
- El certificado del SMTP del hosting es `*.web-hosting.com`: se usa el nombre real del servidor en `EMAIL_HOST` para que la verificación SSL pase.

## Notas
- `User.get_full_name` es una **propiedad** (sin paréntesis) en este proyecto.
- Varios archivos usan finales de línea CRLF (`templates/base.html`, `registros/views/*.py`, `photos/views.py`, ...): al editar por script, conservar el formato para no ensuciar el diff.
- Si hay `tailwind start` corriendo, `static/css/dist/styles.css` se regenera sin minificar: antes de commitear, correr `cd theme/static_src && npm run build`.
