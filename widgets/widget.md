# Guía para crear nuevos widgets

Un widget tiene dos partes obligatorias:
1. **Clase Python** — define el contrato (datos, validaciones, completitud, display para PDF)
2. **Templates HTML** — el componente visual (ya existía, convenciones sin cambio)

---

## CHECKLIST UNIVERSAL

```
1. CLASE PYTHON  [widgets/widget_types/{nombre}.py]
   [ ] Subclasear WidgetBase
   [ ] Definir: slug, nombre, icon (FontAwesome)
   [ ] Implementar: validate_data(data) → list[str]
   [ ] Implementar: completeness(data) → int 0-3
   [ ] Implementar: to_display(data, config) → dict
   [ ] Decorar con @register_widget

2. REGISTRAR
   [ ] Importar la clase en widgets/widget_types/__init__.py

3. TEMPLATE PRINCIPAL  [widgets/templates/widgets/{nombre}_widget.html]
   [ ] Bloque {% comment %} con Uso / Parámetros / Estados
   [ ] {% with wid=... %} para aislar IDs entre instancias
   [ ] Clase raíz CSS única: .{nombre}-widget
   [ ] data-initialized="true" como primera línea de init()
   [ ] Selector de inicialización: .{nombre}-widget:not([data-initialized])
   [ ] emitState() en init() Y en cada cambio de estado
   [ ] POST a /actividades/api/pasos/{paso}/widgets/{slug}/ al guardar
   [ ] Recibir level del response y emitir postMessage

4. TEMPLATE ÍCONO  [widgets/templates/widgets/{nombre}_widget_icon.html]
   [ ] Un badge por cada nivel que el widget puede emitir
   [ ] data-level coincide con los values del postMessage
   [ ] Colores: badge-ghost(0) / badge-error(1) / badge-warning(2) / badge-success(3)
   [ ] Todos los badges inician con opacity-30

5. PREVIEW (opcional)
   [ ] Agregar a _TEST_VALUES en widgets/views.py
```

---

## Estructura mínima de la clase Python

```python
# widgets/widget_types/mi_widget.py
from widgets.base import WidgetBase
from widgets.registry import register_widget

@register_widget
class MiWidget(WidgetBase):
    slug = "mi_widget"        # coincide con widget_slug en PasoWidget
    nombre = "Mi Widget"      # visible al usuario
    icon = "fa-solid fa-..."  # FontAwesome slug

    def validate_config(self, config: dict) -> list[str]:
        # Valida config de PasoWidget.config al crear en admin
        return []

    def validate_data(self, data: dict) -> list[str]:
        # Valida datos del POST. Retorna lista de errores.
        return []

    def completeness(self, data: dict) -> int:
        # 0=sin config, 1=vacío, 2=parcial, 3=completo
        return 3 if data else 1

    def to_display(self, data: dict, config: dict) -> dict:
        # Formato legible para template PDF
        return {"label": config.get("label", self.nombre), "value": data}
```

---

## Endpoint de guardado (JS → backend)

Todos los widgets usan el mismo endpoint genérico:

```
POST /actividades/api/pasos/{paso_nombre}/widgets/{widget_slug}/
Content-Type: application/json

{
  "registro_ct": "reg_txtss.regtxtss",
  "registro_id": 42,
  "data": { ...datos del widget... }
}
```

Respuesta exitosa:
```json
{"level": 3}
```

Respuesta con error de validación:
```json
{"errors": ["El comentario es requerido"], "status": 400}
```

El widget JS recibe `level` del response y emite el `postMessage`:
```javascript
fetch(saveUrl, { method: 'POST', body: JSON.stringify(payload) })
  .then(r => r.json())
  .then(function(res) {
    if (res.level !== undefined) {
      window.parent.postMessage({ type: 'widget-state', level: res.level }, '*');
    }
  });
```

---

## Cómo funcionan los iconos y estados

**Niveles:**

| Nivel | Significado | Color badge |
|---|---|---|
| 0 | Sin configuración | `badge-ghost` |
| 1 | Sin datos / vacío | `badge-error` |
| 2 | Datos parciales | `badge-warning` |
| 3 | Completo | `badge-success` |

**Al cargar la página (Python):**

La vista calcula el nivel desde `DatoPaso` y lo pasa al template del ícono:
```python
widget = get_widget(pw.widget_slug)
data = dato_paso.get_widget_data(pw.widget_slug) if dato_paso else {}
nivel_inicial = widget.completeness(data)  # se pasa a contexto del template
```

El template del ícono activa el badge correcto sin JS:
```html
<span class="badge badge-sm badge-success {% if nivel_inicial != 3 %}opacity-30{% endif %}"
      data-level="3">Completo</span>
```

**Al interactuar el usuario (JS → postMessage):**

El paso escucha el `postMessage` y actualiza los badges en tiempo real:
```javascript
window.addEventListener('message', function(e) {
  if (e.data.type === 'widget-state') {
    document.querySelectorAll('.icon-estado-badge').forEach(function(b) {
      b.classList.toggle('opacity-30', parseInt(b.dataset.level) !== e.data.level);
    });
  }
});
```

---

## Dónde se almacenan los datos

Todos los widgets guardan en `DatoPaso` (tabla `actividades_datopaso`).

Un solo `DatoPaso` por `(registro, paso_nombre)` contiene todos los widgets del paso:
```json
{
  "comentario_widget": {"text": "Acceso en buen estado"},
  "mapa_1p": {"lat": -33.45, "lon": -70.66},
  "camera_widget": {"photo_ids": [1, 2, 3]}
}
```

Helpers disponibles:
```python
dato_paso.get_widget_data("comentario_widget")  # → {"text": "..."}
dato_paso.set_widget_data("comentario_widget", {"text": "..."})  # guarda y hace save()
```

---

## Dónde se configura un widget (admin)

En Django Admin → Actividades → Pasos → Widgets de paso.

El campo `config` de `PasoWidget` acepta un JSON libre validado por `widget.validate_config()`.
Al crear un `PasoWidget` con config inválida, el admin lanzará un `ValidationError`.

---

## Extracción para informe PDF

Cada widget implementa `to_display(data, config)`. Para obtener todos los datos de un registro:

```python
from widgets.report import get_registro_report_data

pasos = get_registro_report_data(registro)
# retorna lista de pasos con widgets y sus datos formateados
```

---

## Criterio por tipo de widget

---

### Tipo: `input` — Texto, número, fecha

**Cuándo usarlo:** un solo valor: texto libre, número con unidad, fecha, hora.

**Schema de datos:**
```json
{"value": "...", "type": "text|number|date"}
```

**Config aceptada:**
```json
{
  "label": "string",
  "required": true,
  "max_length": 500,
  "unit": "m",
  "placeholder": "Describir..."
}
```

**Completeness:** 1 (vacío) / 3 (con valor)

**to_display:**
```python
def to_display(self, data, config):
    return {
        "label": config.get("label", "Valor"),
        "value": data.get("value", "—"),
        "unit": config.get("unit", ""),
        "is_empty": not data.get("value"),
    }
```

---

### Tipo: `map` — Coordenadas GPS con Leaflet

**Cuándo usarlo:** capturar punto(s) geográfico(s) en un mapa interactivo.

**Schema de datos:**
```json
{"lat": -33.45, "lon": -70.66, "label": "Punto de acceso"}
```

**Config aceptada:**
```json
{
  "label": "Ubicación del empalme",
  "required": false,
  "point_label": "Empalme"
}
```

**Completeness:** 1 (sin punto) / 3 (punto capturado)

**to_display:** retorna `coords_str` y `maps_url` para usar en PDF.

**Validación:** rango lat −90/90, lon −180/180.

---

### Tipo: `camera` — Captura de fotos

**Cuándo usarlo:** adjuntar fotos al paso. Las fotos se guardan en el modelo `Photos` (GenericFK). `DatoPaso` solo guarda `photo_ids` para calcular completitud.

**Schema de datos:**
```json
{"photo_ids": [1, 2, 3], "min_photos": 1}
```

**Config aceptada:**
```json
{
  "label": "Fotos del acceso",
  "min_photos": 2,
  "max_photos": 10,
  "foto_min": 2
}
```

**Completeness:** 1 (0 fotos) / 2 (< mínimo) / 3 (≥ mínimo)

**to_display:** retorna lista de URLs de fotos para el template PDF.

---

### Tipo: `checklist` — Lista de verificación

**Cuándo usarlo:** lista de ítems que el usuario marca. Los ítems se definen en `config.items`.

**Schema de datos:**
```json
{"checked": {"tiene_acceso_vehicular": true, "tiene_energia": false}}
```

**Config aceptada:**
```json
{
  "label": "Verificaciones",
  "items": [
    {"slug": "tiene_acceso_vehicular", "label": "Acceso vehicular", "required": true},
    {"slug": "tiene_energia", "label": "Energía disponible", "required": false}
  ]
}
```

**Completeness:** 1 (ninguno) / 2 (algunos requeridos sin marcar) / 3 (todos los requeridos marcados)

---

### Tipo: `select` — Selección de opciones

**Cuándo usarlo:** el usuario elige una o varias opciones de una lista fija configurada en admin.

**Schema de datos:**
```json
{"selected": ["opcion_a"]}
```

**Config aceptada:**
```json
{
  "label": "Tipo de suelo",
  "options": [
    {"value": "asfalto", "label": "Asfalto"},
    {"value": "tierra", "label": "Tierra"}
  ],
  "multiple": false,
  "required": true
}
```

**Completeness:** 1 (sin selección) / 3 (con selección válida)

---

## Estilo visual — DaisyUI v5 + Tailwind v4

Usar siempre componentes DaisyUI para todos los elementos de UI:

| Elemento | Clase DaisyUI |
|---|---|
| Botones | `btn`, `btn-primary`, `btn-sm`, `btn-ghost` |
| Inputs | `input`, `input-bordered`, `input-sm`, `input-success`, `input-error` |
| Textarea | `textarea`, `textarea-bordered` |
| Badges | `badge`, `badge-sm`, `badge-success`, `badge-error`, `badge-warning`, `badge-ghost` |
| Loading | `loading loading-spinner loading-xs` |
| Modales | `<dialog class="modal">` + `modal-box` |

**Colores semánticos** (nunca hardcodear): `text-primary`, `text-error`, `text-success`,
`bg-base-100`, `bg-base-200`, `border-base-300`, `text-base-content/60`.

**Sombras**: clase utilitaria `sombra` del proyecto (no `shadow-*`).

**No escribir CSS inline** salvo `style="height:Npx"` u otras propiedades sin equivalente en Tailwind.

---

## Estructura del template principal

```html
{% comment %}
widgets/{nombre}_widget.html
<Una línea describiendo qué hace el widget.>

Uso:
  include 'widgets/{nombre}_widget.html' with param1=valor param2=valor

Parámetros:
  param1 — descripción (requerido)
  param2 — descripción (opcional)

Estados:
  1 — Sin datos
  2 — Parcial (si aplica)
  3 — Completo
{% endcomment %}

{% with wid=<campo>|default:"fallback"|slugify %}
<div class="{nombre}-widget ..."
     data-param1="{{ param1 }}"
     data-param2="{{ param2|default:'' }}">

  <!-- HTML con clases DaisyUI -->

</div>

<script>
(function () {
  'use strict';

  function init(widget) {
    widget.dataset.initialized = 'true';

    var saveUrl = '/actividades/api/pasos/' + widget.dataset.pasoNombre + '/widgets/{nombre}_widget/';

    function emitState(level) {
      window.parent.postMessage({ type: 'widget-state', level: level }, '*');
    }

    function save(data) {
      fetch(saveUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({
          registro_ct: widget.dataset.registroCt,
          registro_id: parseInt(widget.dataset.registroId),
          data: data
        })
      })
      .then(function(r) { return r.json(); })
      .then(function(res) {
        if (res.level !== undefined) emitState(res.level);
      });
    }

    // lógica del widget...

    emitState(/* nivel inicial */);
  }

  document.querySelectorAll('.{nombre}-widget:not([data-initialized])').forEach(init);
})();
</script>
{% endwith %}
```

**Reglas inamovibles:**

- `{% with wid=... %}` wrappea todo el template para aislar IDs entre instancias.
- `data-initialized="true"` se asigna como primera línea de `init()`.
- El selector termina en `:not([data-initialized])`.
- `emitState()` se llama en init Y en cada evento que cambia el estado.
- No usar variables fuera del IIFE.
- Si el widget necesita recursos externos (Leaflet, etc.), incluir `<link>`/`<script>` dentro del template.

---

## Estructura del template ícono

```html
<div class="widget-icon-status flex items-center gap-4">
  <div class="shrink-0 flex items-center gap-2">
    <i class="fa-solid fa-<icono> text-primary text-base"></i>
    <span class="text-xs font-semibold text-base-content/60"><Nombre visible></span>
  </div>
  <div class="flex items-center gap-1.5 flex-wrap">
    <!-- Solo los estados que el widget realmente emite -->
    <span class="icon-estado-badge badge badge-sm badge-error opacity-30" data-level="1">Sin datos</span>
    <span class="icon-estado-badge badge badge-sm badge-success opacity-30" data-level="3">Completo</span>
  </div>
</div>
```

Reglas:
- Solo incluir estados que el widget realmente emite.
- `data-level` debe coincidir con los values del `postMessage`.
- Todos los badges inician con `opacity-30`.
