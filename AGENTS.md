# AGENTS.md — Guía para agentes IA en reportesTekon

> Leé también `CLAUDE.md` para convenciones generales del proyecto.

## Regla principal — CSS

> **Siempre usar clases de Tailwind o DaisyUI.** Solo tocar `styles.css` cuando no existe clase equivalente (ej. `nth-child`, `display: contents`, layout mobile complejo). Nunca escribir CSS puro para algo que se puede expresar con utilidades.

---

## Antes de tocar CSS

El CSS se compila con Tailwind v4. Hay dos tipos de cambios:

| Tipo | Archivo | ¿Requiere rebuild? |
|------|---------|-------------------|
| Clases utilitarias Tailwind (`py-1`, `pt-2`, etc.) en HTML/Python | `tables.py`, templates | **No** — se detectan en runtime |
| CSS custom en `@layer components` | `theme/static_src/src/styles.css` | **Sí** → `cd theme/static_src && npm run build` |

**Regla:** Si el usuario dice "no se está aplicando", probablemente es un cambio de CSS que necesita rebuild. Prefer siempre agregar clases Tailwind directamente en el HTML/Python cuando sea posible.

---

## Agregar una tabla nueva

1. Crear la clase en `<app>/tables.py` siguiendo el patrón de `SiteTable` (ver `CLAUDE.md`)
2. Agregar `row_attrs = {'class': 'pt-2'}` en `Meta`
3. Usar `template_name = "django_tables2/cupertino.html"`
4. El CSS mobile ya es global — no requiere cambios adicionales

---

## No hacer

- ❌ `from django_weasyprint.views import WeasyTemplateView` a nivel de módulo en `urls.py` → startup lento (~11s)
- ❌ `overflow: hidden` en `.table-card` → rompe el sticky del header
- ❌ Agregar `defer` a jQuery → rompe `$(document).ready()` en `base_head.html`
- ❌ Reconstruir CSS para aplicar `row_attrs` o clases td — eso va directo en el HTML
- ❌ Escribir CSS puro en `styles.css` cuando una clase Tailwind o DaisyUI puede hacer lo mismo

---

## Estructura de templates de tabla

```
base.html
  └── data_table_page.html        (bloques: table_title, table_search, table_actions, table_content)
        └── pages/sitios.html     (ejemplo: sitios)
              └── #sitios-table-wrapper  (target HTMX)
                    └── cupertino.html  (render_table)
```

## CSS mobile — breakpoint y orden de reglas

```css
/* En styles.css, dentro de @layer components: */
@media (max-width: 768px) {
  .table-card { background-color: transparent; }
  .table { display: block; background: transparent; }
  .table thead { display: none; }
  .table tbody { display: block; background-color: var(--color-secondary); padding-top: 0.25rem; }
  .table tbody tr { display: flex; flex-wrap: wrap; ... }
  /* Las reglas específicas de columna (nth-child) van DESPUÉS */
}
```

El orden importa: las reglas más específicas (`nth-child`) deben ir después de las generales.
