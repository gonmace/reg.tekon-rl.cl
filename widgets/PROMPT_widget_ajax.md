# Prompt: Crear un widget de tipo AJAX

Crea un nuevo widget de tipo **ajax** en el proyecto reportesTekon siguiendo exactamente las instrucciones de este documento.

---

## ★ ESPECIFICACIÓN DEL WIDGET A CREAR ★

> Completa esta sección antes de enviar el prompt. Todo lo demás es instrucción fija.

```
NOMBRE DEL WIDGET   : _______________________________________________
SLUG                : _______________________________________________widget
  (snake_case, termina en _widget, ej. temperatura_widget)

ICONO FONT AWESOME  : fa-solid fa-___________________________________
  (buscar en https://fontawesome.com/icons)

DESCRIPCIÓN BREVE   : _______________________________________________
  (una línea, qué calcula o captura este widget)

CONFIG KEYS         : _______________________________________________
  (claves opcionales que el admin puede configurar en PasoWidget.config,
   ej. label="Texto encabezado", unidad="metros")
```

### Datos de entrada del widget

Campos que el usuario introduce antes de calcular/guardar.

| Nombre del campo | Tipo HTML | ¿Requerido? | Descripción |
|-----------------|-----------|-------------|-------------|
| `___________` | texto / número / select | sí / no | _________ |
| `___________` | texto / número / select | sí / no | _________ |

### Datos que se guardan en backend

Campos que el widget envía en el `fetch()` al endpoint de guardado.

| Nombre del campo | Tipo Python | Descripción |
|-----------------|-------------|-------------|
| `___________` | str / float / int / bool / list | _________ |
| `___________` | str / float / int / bool / list | _________ |

### Lógica de cálculo

```
¿Qué operación/transformación hace el widget con los datos de entrada?

___________________________________________________________________
___________________________________________________________________

¿Necesita alguna librería JS especial? (ej. Leaflet, Haversine, etc.)

___________________________________________________________________
```

### Lógica de completitud y estados

```
Nivel 1 (vacío)     : cuando _____________________________________
Nivel 2 (calculado) : cuando _____________________________________
                      (valor calculado en JS pero aún no guardado)
Nivel 3 (guardado)  : cuando _____________________________________
```

---

---

## 1. Contexto del sistema de widgets

Los widgets son componentes reutilizables que capturan datos en los pasos de actividades.
Cada registro (ej. `RegTxtss`) tiene pasos, y cada paso tiene uno o más widgets configurados en `PasoWidget`.

Los datos de cada paso se guardan en `DatoPaso.datos` (JSONField) con la estructura:
```json
{
  "slug_widget_a": { ...datos del widget A... },
  "slug_widget_b": { ...datos del widget B... }
}
```

### ¿Qué es un widget de tipo AJAX?

Un widget **ajax** cumple estas condiciones:
- Tiene su propio botón "Guardar" en el template.
- Guarda datos enviando un `fetch()` POST directamente al endpoint `save_widget_data`.
- No depende del form externo de `elemento.html` — puede estar dentro o fuera de él.
- Puede tener estados intermedios (ej. "calculado pero no guardado" = nivel 2).
- El JS maneja todo: cálculo, validación client-side, `fetch`, y `postMessage` de estado.
- Recibe `save_url` como parámetro de configuración en el template.

**Ejemplos existentes:** `distancia_widget`, `camera_widget`, `mapa_1p_widget`, `mapa_2p_widget`.

---

## 2. Endpoint de guardado (ya existe, no modificar)

El endpoint genérico está en `actividades/views.py:254`:

```
POST /actividades/api/pasos/<paso_nombre>/widgets/<widget_slug>/
```

**Payload JSON esperado:**
```json
{
  "registro_ct": "reg_txtss.regtxtss",
  "registro_id": 42,
  "data": {
    "campo_a": "valor",
    "campo_b": 123.45
  }
}
```

**Respuesta exitosa:**
```json
{"level": 3}
```

**Respuesta con errores de validación:**
```json
{"errors": ["Mensaje de error"], "status": 400}
```

El endpoint llama automáticamente a `widget.validate_data(data)`, guarda en `DatoPaso`, y reconstruye `ContextoRegistro`. No requiere modificación.

La URL `save_url` se genera en `actividades/views.py` y se pasa como variable de contexto al template. Está disponible como `{{ save_url }}` en el template.

---

## 3. Archivos que debes crear o modificar

Para un widget con slug `mi_widget` debes:

| # | Acción | Archivo |
|---|--------|---------|
| 1 | **Crear** | `widgets/widget_types/mi_widget.py` |
| 2 | **Crear** | `widgets/templates/widgets/mi_widget.html` |
| 3 | **Crear** | `widgets/templates/widgets/mi_widget_boton.html` |
| 4 | **Modificar** | `widgets/widget_types/__init__.py` |

**No** se modifica `actividades/forms.py` para widgets ajax.

---

## 4. Archivo 1: Clase Python del widget

**Ruta:** `widgets/widget_types/mi_widget.py`

```python
from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class MiWidget(WidgetBase):
    slug = "mi_widget"           # Debe coincidir con el nombre del archivo
    nombre = "Nombre Legible"    # Se muestra en el catálogo de admin
    icon = "fa-solid fa-ICONO"   # FontAwesome 6, ej. fa-solid fa-ruler

    def validate_data(self, data: dict) -> list:
        """
        Valida los datos antes de guardarlos.
        Retorna lista de strings de error (vacía = válido).
        """
        errors = []
        valor = data.get("valor_principal")
        if valor is None:
            errors.append("valor_principal es requerido")
            return errors
        try:
            v = float(valor)
        except (ValueError, TypeError):
            errors.append("valor_principal debe ser un número")
            return errors
        if v < 0:
            errors.append("valor_principal no puede ser negativo")
        return errors

    def completeness(self, data: dict) -> int:
        """
        Retorna el nivel de completitud:
          1 — sin datos / widget vacío
          2 — cálculo realizado pero no guardado (raro en Python, pero posible)
          3 — datos guardados y válidos

        Para widgets ajax el nivel 3 suele significar "guardado en backend".
        """
        if data.get("valor_principal") is not None:
            return 3
        return 1

    def to_display(self, data: dict, config: dict) -> dict:
        """
        Convierte los datos crudos a formato legible para PDF/informe.
        """
        valor = data.get("valor_principal")
        return {
            "label": config.get("label", "Mi Widget"),
            "valor_principal": valor,
            "valor_str": f"{valor:.2f} unidades" if valor is not None else "Sin datos",
            "is_empty": valor is None,
        }
```

### Reglas de la clase Python

- El `slug` debe terminar en `_widget` y coincidir con el nombre del archivo (sin `.py`).
- `validate_data` puede recibir `None` en cualquier campo — siempre usar `.get()` con default.
- `completeness` devuelve `3` cuando los datos están **realmente guardados** en backend.
- `to_display` siempre incluye `"label"` y `"is_empty"` para el render en PDF.

---

## 5. Archivo 2: Template HTML del widget

**Ruta:** `widgets/templates/widgets/mi_widget.html`

El template recibe como contexto:
- `save_url` — URL del endpoint POST donde guardar los datos
- `valor_principal` — valor ya guardado (puede estar vacío)
- Las claves de `PasoWidget.config` inyectadas directamente (ej. `{{ label }}`)

```django
{% comment %}
widgets/mi_widget.html
Descripción breve del widget.

Nombre:
  Nombre Legible

Tipo:
  ajax

Uso:
  include 'widgets/mi_widget.html'

Parámetros:
  save_url         — URL del endpoint POST donde se guarda el resultado
  valor_principal  — Valor ya guardado (opcional)

Config:
  label — etiqueta del widget, default "Mi Widget"

Estados:
  1 — Sin datos
  2 — Calculado/procesado pero no guardado
  3 — Guardado en backend
{% endcomment %}
{% with wid=save_url|default:"preview"|slugify %}

<div class="mi-widget bg-base-100 rounded-lg p-4 sombra"
     data-save-url="{{ save_url }}"
     data-valor="{{ valor_principal|default:'' }}">

  <p class="text-sm font-semibold text-base-content/60 flex items-center gap-2 mb-3">
    <i class="fa-solid fa-ICONO text-primary"></i>
    {{ label|default:"Mi Widget" }}
  </p>

  <!-- Inputs de entrada -->
  <div class="flex flex-col gap-3 mb-3">

    <div class="form-control">
      <label class="label pb-1">
        <span class="label-text text-sm">Valor Principal</span>
      </label>
      <input type="number" step="any" placeholder="Ingresa un valor"
             class="mi-input-principal input input-sm input-bordered w-full font-mono"
             value="{{ valor_principal|default:'' }}">
    </div>

  </div>

  <!-- Resultado -->
  <div class="flex items-center justify-between gap-3 rounded-lg bg-base-200 px-4 py-3 mb-3">
    <div class="flex items-center gap-2">
      <i class="fa-solid fa-ICONO text-base-content/30 text-sm"></i>
      <span class="mi-result-display text-2xl font-bold font-mono text-base-content">
        {% if valor_principal %}{{ valor_principal }}{% else %}—{% endif %}
      </span>
    </div>
  </div>

  <!-- Botones -->
  <div class="flex gap-2">
    <button type="button" class="mi-calc-btn btn btn-primary btn-sm flex-1 gap-2">
      <i class="fa-solid fa-calculator"></i> Calcular
    </button>
    <button type="button" class="mi-save-btn btn btn-success btn-sm flex-1 gap-2" disabled>
      <i class="fa-solid fa-floppy-disk"></i>
      <span class="mi-save-label">
        {% if valor_principal %}Actualizar{% else %}Guardar{% endif %}
      </span>
    </button>
  </div>

</div>

<script>
(function () {
  'use strict';

  // ── Inicialización ──────────────────────────────────────────────────
  // Selecciona solo elementos no inicializados para evitar duplicados
  var w = document.querySelector('.mi-widget:not([data-initialized])');
  if (!w) return;
  w.dataset.initialized = 'true';

  var saveUrl      = w.dataset.saveUrl;
  var inputEl      = w.querySelector('.mi-input-principal');
  var resultEl     = w.querySelector('.mi-result-display');
  var calcBtn      = w.querySelector('.mi-calc-btn');
  var saveBtn      = w.querySelector('.mi-save-btn');
  var saveLabel    = w.querySelector('.mi-save-label');

  // Estado en memoria
  var savedValue   = w.dataset.valor ? parseFloat(w.dataset.valor) : null;
  var lastCalc     = null;  // Calculado pero no guardado aún

  // ── CSRF ────────────────────────────────────────────────────────────
  function getCsrf() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  // ── Estado ─────────────────────────────────────────────────────────
  function emitState(level) {
    window.parent.postMessage({ type: 'widget-state', level: level }, '*');
  }

  function currentLevel() {
    if (savedValue !== null) return 3;
    if (lastCalc !== null) return 2;
    return 1;
  }

  // ── Calcular ───────────────────────────────────────────────────────
  calcBtn.addEventListener('click', function () {
    var raw = parseFloat(inputEl.value);

    if (isNaN(raw)) {
      if (window.Alert) window.Alert.error('Ingresa un valor válido.', { autoHide: 3000 });
      return;
    }
    if (raw < 0) {
      if (window.Alert) window.Alert.error('El valor no puede ser negativo.', { autoHide: 3000 });
      return;
    }

    // Calcular resultado
    lastCalc = raw;  // ← reemplazar por la lógica real si hay transformación
    resultEl.textContent = lastCalc.toFixed(2);
    savedValue = null;
    saveBtn.disabled = false;
    saveLabel.textContent = 'Guardar';
    emitState(2);
  });

  // ── Guardar ────────────────────────────────────────────────────────
  saveBtn.addEventListener('click', function () {
    if (!saveUrl || lastCalc === null) return;

    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="loading loading-spinner loading-xs"></span>';

    fetch(saveUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf()
      },
      body: JSON.stringify({
        valor_principal: lastCalc,
        // Añadir más campos si el widget requiere más datos
      }),
    })
    .then(function (r) { return r.json(); })
    .then(function (result) {
      if (result.level !== undefined && result.errors === undefined) {
        savedValue = lastCalc;
        saveLabel.textContent = 'Actualizar';
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i><span class="mi-save-label">Actualizar</span>';
        saveLabel = w.querySelector('.mi-save-label');
        emitState(3);
        if (window.Alert) window.Alert.success('Guardado correctamente', { autoHide: 2000 });
      } else {
        var msg = (result.errors || ['Error al guardar']).join(', ');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i><span class="mi-save-label">Guardar</span>';
        saveLabel = w.querySelector('.mi-save-label');
        if (window.Alert) window.Alert.error(msg, { autoHide: 0, dismissible: true });
      }
    })
    .catch(function () {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i><span class="mi-save-label">Guardar</span>';
      saveLabel = w.querySelector('.mi-save-label');
      if (window.Alert) window.Alert.error('Error de conexión', { autoHide: 0, dismissible: true });
    });
  });

  // ── Estado inicial ─────────────────────────────────────────────────
  emitState(currentLevel());

})();
</script>
{% endwith %}
```

### Reglas del template ajax

- **SIEMPRE** usar `data-save-url="{{ save_url }}"` en el div raíz del widget.
- **SIEMPRE** usar `data-CAMPO="{{ campo|default:'' }}"` para prepoblar valores ya guardados.
- Inicializar con `querySelector('.clase:not([data-initialized])')` para evitar duplicados.
- La clase raíz del div (ej. `mi-widget`) debe ser única en el sistema.
- `getCsrf()` lee el token del form externo de `elemento.html` (siempre presente en la página).
- `emitState(2)` al calcular, `emitState(3)` al guardar exitosamente.
- `emitState(currentLevel())` al final para emitir el estado inicial correcto.
- Usar `window.Alert.success/error()` para feedback visual al usuario.
- El JS es un IIFE. No asignar variables globales.
- `saveBtn` se deshabilita mientras el fetch está en curso; restaurar en `.catch()` y en error.

---

## 6. Archivo 3: Template del botón de estado

**Ruta:** `widgets/templates/widgets/mi_widget_boton.html`

Estándar para todos los widgets. El contexto `widget` tiene: `url`, `color`, `icon`.

```django
{% comment %}
widgets/mi_widget_boton.html
{% endcomment %}
<a href="{{ widget.url }}"
   class="btn btn-{{ widget.color }} btn-circle sombra active:scale-95 transition-transform duration-100"
   title="Nombre Legible">
  <i class="{{ widget.icon }} text-xl"></i>
</a>
```

No modificar este template — es estándar para todos los widgets.

---

## 7. Archivo 4: Registrar el widget en `__init__.py`

**Ruta:** `widgets/widget_types/__init__.py`

Añade el import de tu clase en orden alfabético.

```python
from widgets.widget_types.camera import CameraWidget
from widgets.widget_types.comentario import ComentarioWidget
from widgets.widget_types.distancia import DistanciaWidget
from widgets.widget_types.imgs_desc import ImgsDescWidget
from widgets.widget_types.mi_widget import MiWidget          # ← nuevo
from widgets.widget_types.mapa_1p import Mapa1pWidget
from widgets.widget_types.mapa_2p import Mapa2pWidget
from widgets.widget_types.poste_form import PosteFormWidget
from widgets.widget_types.ubicacion import UbicacionWidget

__all__ = [
    "CameraWidget", "ComentarioWidget", "DistanciaWidget", "ImgsDescWidget",
    "MiWidget",                                                                # ← nuevo
    "Mapa1pWidget", "Mapa2pWidget", "PosteFormWidget", "UbicacionWidget",
]
```

---

## 8. Niveles de completitud (referencia rápida)

| Nivel | Estado | Badge DaisyUI | Cuándo usarlo |
|-------|--------|---------------|---------------|
| `1` | Vacío | `badge-error` | Sin datos, widget recién abierto |
| `2` | Calculado | `badge-warning` | Resultado disponible pero **no guardado** en backend |
| `3` | Guardado | `badge-success` | Datos guardados exitosamente en `DatoPaso` |

Nivel `0` (sin config) se usa cuando `save_url` está vacío o el widget no está operativo.

---

## 9. Diferencias clave respecto a widgets form

| Aspecto | Form | **Ajax** |
|---------|------|----------|
| Submit | Form externo | **`fetch()` propio** |
| Botón Guardar | No tiene | **Sí, en el template** |
| `save_url` | No usa | **Obligatorio** |
| CSRF | Del form externo | **`getCsrf()` en JS** |
| Modifica `forms.py` | Sí | **No** |
| Nivel 2 | Raro | **Frecuente** (calculado ≠ guardado) |

---

## 10. Checklist de verificación

Antes de considerar el widget terminado, verifica:

- [ ] `slug` en la clase Python termina en `_widget`
- [ ] `slug` coincide con el nombre del archivo `.py` y el template `.html`
- [ ] El div raíz del template tiene `data-save-url="{{ save_url }}"`
- [ ] Los valores iniciales se leen de `w.dataset.CAMPO` al inicializar el JS
- [ ] Se usa `querySelector('.clase:not([data-initialized])')` para inicializar
- [ ] `getCsrf()` está definida y se usa en el header del `fetch()`
- [ ] `emitState(2)` al calcular, `emitState(3)` al guardar
- [ ] `emitState(currentLevel())` al final del IIFE (estado inicial)
- [ ] El botón "Guardar" se deshabilita durante el fetch y se restaura en error/catch
- [ ] El template tiene el bloque `{% comment %}` con metadatos al inicio
- [ ] `MiWidget` importado en `widgets/widget_types/__init__.py` y en `__all__`
- [ ] **No** se modifica `actividades/forms.py`
- [ ] `mi_widget_boton.html` creado (copiar patrón estándar, solo cambiar `title`)

---

## 11. Ejemplo de referencia: `distancia_widget`

El widget ajax más completo y representativo del sistema.

- Clase: `widgets/widget_types/distancia.py`
- Template: `widgets/templates/widgets/distancia_widget.html`
- Botón: `widgets/templates/widgets/distancia_widget_boton.html`

Tiene los 3 niveles de estado (1/2/3), validación client-side, y fetch al endpoint estándar.
