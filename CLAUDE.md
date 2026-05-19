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
- `.table tbody { background-color: var(--color-secondary); padding-top: 0.25rem; }` — fondo igual al `main`, separación del header
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

Apps afectadas: `reg_construccion/urls.py`, `reg_txtss/urls.py`, `pdf_reports/urls.py`

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
