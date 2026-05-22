# Prompt addendum: Control de acceso por rol en widgets

> Adjunta este documento al prompt principal (`PROMPT_widget_ajax.md` o `PROMPT_widget_form.md`)
> al crear cualquier widget nuevo. Las reglas aquí descritas son **obligatorias** en todos los widgets.

---

## Sistema de acceso

El proyecto usa el templatetag `{% btn_access %}` (definido en `core/templatetags/access_tags.py`)
para calcular el nivel de acceso del usuario actual en tiempo de render.

### Tabla de comportamiento por rol

| Rol | `btn_access` devuelve | Resultado visual |
|-----|-----------------------|-----------------|
| Supermanager | `allowed` | Normal, sin restricción |
| ITO | `allowed` | Normal, sin restricción |
| SEARCHER | `allowed` | Normal, sin restricción |
| GERENCIA | `disabled` | Botón visible pero inactivo (opacity 0.4, sin click) |
| COORD | `disabled` | Botón visible pero inactivo (opacity 0.4, sin click) |
| VISITA | `hidden` | Botón oculto (`display:none`) |

El CSS global en `static/css/dist/styles.css` aplica el comportamiento automáticamente:
```css
[data-access="hidden"]   { display: none !important; }
[data-access="disabled"] { pointer-events: none !important; opacity: 0.4; cursor: not-allowed !important; }
```

Los campos de formulario (inputs, textarea, select) quedan bloqueados para VISITA
mediante `<fieldset disabled>` en `actividades/templates/actividades/elemento.html` —
**no se necesita lógica adicional en el template del widget** para los campos.

---

## Reglas según tipo de widget

### Widget AJAX (tiene botones de guardar propios)

**Al inicio del template**, justo después de `{% load ... %}`:

```django
{% load access_tags %}
{% btn_access as access_val %}
```

**En cada botón de acción** (guardar, calcular, subir, capturar):

```django
<button type="button" class="btn btn-success ..."
        data-access="{{ access_val }}">
  Guardar
</button>
```

**Si el botón es un `<label>` para un `<input type="file">`** (widgets de fotos):

```django
<input type="file" class="sr-only ..."
       {% if access_val != 'allowed' %}disabled{% endif %}>
<label class="btn btn-success ..."
       data-access="{{ access_val }}">
  Seleccionar imágenes
</label>
```

> El `disabled` en el input impide la activación por teclado.
> El `data-access` en el label impide la activación por mouse.

### Widget FORM (sin botones propios, form externo)

Los campos de texto (`<input>`, `<textarea>`, `<select>`) quedan bloqueados para VISITA
automáticamente por el `<fieldset disabled>` que los envuelve en `elemento.html`.

**No añadir lógica de rol en el template del widget form.**

El botón "Guardar" del form externo ya tiene `data-access="{% btn_access %}"` en `elemento.html`.

---

## Patrón completo de referencia (widget ajax)

```django
{% load static access_tags %}
{% btn_access as access_val %}
{% with wid=save_url|default:"preview"|slugify %}

<div class="mi-widget bg-base-100 rounded-lg p-4 sombra"
     data-save-url="{{ save_url }}">

  <!-- ... contenido del widget ... -->

  <div class="flex gap-2">
    <button type="button" class="mi-calc-btn btn btn-primary btn-sm flex-1 gap-2"
            data-access="{{ access_val }}">
      <i class="fa-solid fa-calculator"></i> Calcular
    </button>
    <button type="button" class="mi-save-btn btn btn-success btn-sm flex-1 gap-2"
            data-access="{{ access_val }}" disabled>
      <i class="fa-solid fa-floppy-disk"></i> Guardar
    </button>
  </div>

</div>
{% endwith %}
```

---

## Checklist adicional (añadir al checklist del prompt principal)

- [ ] `{% load access_tags %}` incluido en el template
- [ ] `{% btn_access as access_val %}` declarado una sola vez al inicio del template
- [ ] **Todos** los botones de acción tienen `data-access="{{ access_val }}"`
- [ ] Si hay `<label for="file-input">`: también tiene `data-access` y el `<input>` tiene `{% if access_val != 'allowed' %}disabled{% endif %}`
- [ ] Los campos de formulario (`<input>`, `<textarea>`) **no** necesitan lógica de rol — el `<fieldset>` de `elemento.html` los cubre
- [ ] **No** replicar la lógica de `btn_access` inline (`{% if user.is_visita %}`, etc.) — usar solo el templatetag

---

## Lo que NO se debe hacer

```django
{# ❌ Lógica inline — no usar #}
{% if request.user.is_visita %}
  {# ocultar botón #}
{% elif request.user.is_coord %}
  {# deshabilitar botón #}
{% endif %}

{# ❌ Pasar can_edit desde la vista — no usar #}
'can_edit': request.user.is_supermanager or request.user.is_ito_like

{# ❌ JS que recorre inputs y los deshabilita — no usar #}
container.querySelectorAll('input').forEach(el => el.disabled = true);
```

```django
{# ✅ Correcto #}
{% btn_access as access_val %}
<button data-access="{{ access_val }}">Guardar</button>
```
