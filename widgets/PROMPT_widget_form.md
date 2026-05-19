# Prompt: Crear un widget de tipo FORM

Crea un nuevo widget de tipo **form** en el proyecto reportesTekon siguiendo exactamente las instrucciones de este documento.

---

## ★ ESPECIFICACIÓN DEL WIDGET A CREAR ★

> Completa esta sección antes de enviar el prompt. Todo lo demás es instrucción fija.

```
NOMBRE DEL WIDGET   : _______________________________________________
SLUG                : _______________________________________________widget
  (snake_case, termina en _widget, ej. inspeccion_visual_widget)

ICONO FONT AWESOME  : fa-solid fa-___________________________________
  (buscar en https://fontawesome.com/icons)

DESCRIPCIÓN BREVE   : _______________________________________________
  (una línea, qué captura este widget)

CONFIG KEYS         : _______________________________________________
  (claves opcionales que el admin puede configurar en PasoWidget.config,
   ej. label="Texto encabezado", max_length=200)
```

### Campos del formulario

Completa una fila por cada campo. Agrega o elimina filas según necesites.

| Nombre del campo | Tipo HTML | ¿Requerido? | Valor por defecto | Descripción |
|-----------------|-----------|-------------|-------------------|-------------|
| `___________` | texto / número / textarea / checkbox | sí / no | `___________` | _________ |
| `___________` | texto / número / textarea / checkbox | sí / no | `___________` | _________ |
| `___________` | texto / número / textarea / checkbox | sí / no | `___________` | _________ |

### Lógica de completitud

```
Nivel 1 (vacío)   : cuando _________________________________________
Nivel 2 (parcial) : cuando _________________________________________
                    (dejar en blanco si no aplica nivel 2)
Nivel 3 (completo): cuando _________________________________________
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

### ¿Qué es un widget de tipo FORM?

Un widget **form** cumple estas condiciones:
- Sus campos HTML tienen atributo `name=` y **no tienen submit propio**.
- Vive dentro del `<form method="post">` que renderiza `actividades/templates/actividades/elemento.html`.
- Los datos se envían cuando el usuario presiona el botón "Guardar" del form externo.
- El JS del template **solo emite `postMessage`** para actualizar el estado visual — no hace `fetch()`.
- El guardado lo maneja `DynamicPasoView.post()` en `reg_txtss/views.py`.

**Ejemplos existentes:** `comentario_widget`, `ubicacion_widget`, `poste_form_widget`.

---

## 2. Archivos que debes crear o modificar

Para un widget con slug `mi_widget` debes:

| # | Acción | Archivo |
|---|--------|---------|
| 1 | **Crear** | `widgets/widget_types/mi_widget.py` |
| 2 | **Crear** | `widgets/templates/widgets/mi_widget.html` |
| 3 | **Crear** | `widgets/templates/widgets/mi_widget_boton.html` |
| 4 | **Modificar** | `widgets/widget_types/__init__.py` |
| 5 | **Modificar** | `actividades/forms.py` → función `build_dynamic_form()` |

---

## 3. Archivo 1: Clase Python del widget

**Ruta:** `widgets/widget_types/mi_widget.py`

```python
from widgets.base import WidgetBase
from widgets.registry import register_widget


@register_widget
class MiWidget(WidgetBase):
    slug = "mi_widget"           # Debe coincidir con el nombre del archivo
    nombre = "Nombre Legible"    # Se muestra en el catálogo de admin
    icon = "fa-solid fa-ICONO"   # FontAwesome 6, ej. fa-solid fa-pen

    def validate_data(self, data: dict) -> list:
        """
        Valida los datos antes de guardarlos.
        Retorna lista de strings de error (vacía = válido).
        Solo valida lo que el usuario ingresa — no defaults.
        """
        errors = []
        campo = str(data.get("campo_requerido", "")).strip()
        if not campo:
            errors.append("El campo requerido es obligatorio")
        return errors

    def completeness(self, data: dict) -> int:
        """
        Retorna el nivel de completitud:
          1 — sin datos / vacío
          2 — datos parciales (si aplica)
          3 — completo
        Nota: nivel 0 es para widgets no operativos (sin config), raro en form widgets.
        """
        campos_requeridos = ["campo_requerido", "otro_campo"]
        campos_opcionales = ["campo_opcional"]
        todos = campos_requeridos + campos_opcionales

        llenados = sum(1 for f in todos if str(data.get(f, "")).strip())
        if llenados == 0:
            return 1
        if llenados < len(todos):
            return 2
        return 3

    def to_display(self, data: dict, config: dict) -> dict:
        """
        Convierte los datos crudos a formato legible para PDF/informe.
        El parámetro config viene de PasoWidget.config (JSON).
        """
        return {
            "label": config.get("label", "Mi Widget"),
            "campo_requerido": data.get("campo_requerido", ""),
            "otro_campo": data.get("otro_campo", ""),
            "campo_opcional": data.get("campo_opcional", ""),
            "is_empty": not str(data.get("campo_requerido", "")).strip(),
        }
```

### Reglas de la clase Python

- El `slug` debe terminar en `_widget` y coincidir exactamente con el nombre del archivo (sin `.py`).
- `validate_data` solo lanza errores en campos inválidos; no rechaza datos vacíos opcionales.
- `completeness` nunca retorna 0 en widgets form normales (0 es para widget no configurado).
- `to_display` siempre incluye `"label"` y `"is_empty"` para facilitar el render en PDF.
- No importes modelos externos aquí salvo que sea estrictamente necesario.

---

## 4. Archivo 2: Template HTML del widget

**Ruta:** `widgets/templates/widgets/mi_widget.html`

El template recibe como contexto:
- Las claves de `PasoWidget.config` inyectadas directamente (ej. `{{ label }}`)
- `datos` — dict con los valores actuales del widget (prepopulado desde `DatoPaso`)
- El form externo ya existe en `elemento.html`; NO debes añadir `<form>` ni `<button type="submit">`

```django
{% comment %}
widgets/mi_widget.html
Descripción breve del widget.

Nombre:
  Nombre Legible

Tipo:
  form

Uso:
  include 'widgets/mi_widget.html'

Config:
  label — etiqueta del widget, default "Mi Widget"

Estados:
  1 — Sin datos
  2 — Datos parciales
  3 — Datos completos
{% endcomment %}

<div class="flex flex-col gap-4">

  <p class="text-sm font-semibold text-base-content/60 flex items-center gap-2">
    <i class="fa-solid fa-ICONO text-primary"></i>
    {{ label|default:"Mi Widget" }}
  </p>

  <!-- Campo requerido -->
  <div class="form-control">
    <label class="label pb-1" for="id_campo_requerido">
      <span class="label-text text-sm">
        Campo Requerido <span class="text-error">*</span>
      </span>
    </label>
    <input type="text"
           name="campo_requerido"
           id="id_campo_requerido"
           value="{{ datos.campo_requerido|default:'' }}"
           required
           class="input input-bordered w-full" />
  </div>

  <!-- Otro campo requerido -->
  <div class="form-control">
    <label class="label pb-1" for="id_otro_campo">
      <span class="label-text text-sm">
        Otro Campo <span class="text-error">*</span>
      </span>
    </label>
    <input type="text"
           name="otro_campo"
           id="id_otro_campo"
           value="{{ datos.otro_campo|default:'' }}"
           required
           class="input input-bordered w-full" />
  </div>

  <!-- Campo opcional -->
  <div class="form-control">
    <label class="label pb-1" for="id_campo_opcional">
      <span class="label-text text-sm">
        Campo Opcional
        <span class="text-base-content/40 text-xs ml-1">(opcional)</span>
      </span>
    </label>
    <input type="text"
           name="campo_opcional"
           id="id_campo_opcional"
           value="{{ datos.campo_opcional|default:'' }}"
           placeholder="Descripción..."
           class="input input-bordered w-full" />
  </div>

</div>

<script>
(function () {
  // Lista de nombres de campos que contribuyen al nivel de completitud.
  // Debe coincidir con la lógica de completeness() en la clase Python.
  var FIELDS = ['campo_requerido', 'otro_campo', 'campo_opcional'];

  function computeLevel() {
    var filled = FIELDS.filter(function (name) {
      var el = document.querySelector('[name="' + name + '"]');
      return el && el.value.trim() !== '';
    }).length;
    if (filled === 0) return 1;
    return filled === FIELDS.length ? 3 : 2;
  }

  function emit() {
    window.parent.postMessage({ type: 'widget-state', level: computeLevel() }, '*');
  }

  // Escuchar cambios en todos los campos
  FIELDS.forEach(function (name) {
    var el = document.querySelector('[name="' + name + '"]');
    if (el) el.addEventListener('input', emit);
  });

  // Emitir estado inicial al cargar
  emit();
})();
</script>
```

### Reglas del template form

- **NUNCA** añadir `<form>`, `<button type="submit">` ni `fetch()` — el form es externo.
- Todos los `<input>` y `<textarea>` deben tener `name=` con el nombre exacto del campo.
- Prellenar valores con `{{ datos.CAMPO|default:'' }}`.
- El JS es un IIFE (`(function(){ ... })()`). No asignar variables globales.
- `emit()` se llama en cada `input` event y una vez al cargar para el estado inicial.
- La lógica de `computeLevel()` en JS debe **espejear exactamente** `completeness()` en Python.
- Usar clases Tailwind/DaisyUI. No añadir estilos inline salvo casos excepcionales.

---

## 5. Archivo 3: Template del botón de estado

**Ruta:** `widgets/templates/widgets/mi_widget_boton.html`

Este template renderiza el botón circular que muestra el estado del widget en la pantalla de pasos.
El contexto `widget` es un objeto `_EnrichedWidget` con los atributos: `url`, `color`, `icon`.

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

## 6. Archivo 4: Registrar el widget en `__init__.py`

**Ruta:** `widgets/widget_types/__init__.py`

Añade el import de tu clase. Mantén el orden alfabético de los imports.

```python
# Agregar en la posición alfabética correcta:
from widgets.widget_types.mi_widget import MiWidget

# Y añadir al __all__:
__all__ = [..., "MiWidget", ...]
```

Ejemplo del archivo completo actualizado:
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

## 7. Archivo 5: Actualizar `build_dynamic_form()`

**Ruta:** `actividades/forms.py`

La función `build_dynamic_form()` construye el form Django para un paso dinámicamente.
Debes añadir un bloque `elif slug == 'mi_widget':` con los campos de tu widget.

```python
def build_dynamic_form(paso, data=None, initial=None, widget_slug=None):
    fields = {}
    merged_initial = {}
    pws = paso.paso_widgets.order_by('orden')
    if widget_slug:
        pws = pws.filter(widget_slug=widget_slug)
    for pw in pws:
        slug = pw.widget_slug
        # ... bloques existentes ...
        elif slug == 'mi_widget':
            # Valores iniciales por defecto (si aplica)
            merged_initial.update({
                'campo_requerido': 'Valor por defecto',
            })
            fields['campo_requerido'] = forms.CharField(
                required=True,
                label='Campo Requerido',
            )
            fields['otro_campo'] = forms.CharField(
                required=True,
                label='Otro Campo',
            )
            fields['campo_opcional'] = forms.CharField(
                required=False,
                label='Campo Opcional',
            )
        # ... resto de bloques ...
```

### Tipos de campos Django disponibles

| Tipo de dato | Clase Django |
|---|---|
| Texto corto | `forms.CharField(required=True/False)` |
| Texto largo | `forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))` |
| Booleano (checkbox) | `forms.BooleanField(required=False)` |
| Número entero | `forms.IntegerField(required=True/False)` |
| Número decimal | `forms.FloatField(required=True/False)` |
| Elección fija | `forms.ChoiceField(choices=[('v', 'Label'), ...])` |

---

## 8. Niveles de completitud (referencia rápida)

| Nivel | Estado | Badge DaisyUI | Cuándo usarlo |
|-------|--------|---------------|---------------|
| `1` | Vacío | `badge-error` | El usuario no ha ingresado ningún dato |
| `2` | Parcial | `badge-warning` | Algunos campos llenados, faltan obligatorios |
| `3` | Completo | `badge-success` | Todos los campos requeridos tienen valor |

Nivel `0` (sin config) **no aplica** para widgets form normales.

---

## 9. Checklist de verificación

Antes de considerar el widget terminado, verifica:

- [ ] `slug` en la clase Python termina en `_widget`
- [ ] `slug` coincide con el nombre del archivo `.py`
- [ ] `slug` coincide con el nombre del template `.html`
- [ ] Los campos tienen `name=` con el mismo nombre que en `build_dynamic_form()`
- [ ] Los campos se precargan con `{{ datos.CAMPO|default:'' }}`
- [ ] `computeLevel()` en JS espeja `completeness()` en Python
- [ ] `emit()` se llama al inicio (estado inicial) y en cada `input` event
- [ ] No hay `<form>`, `<button type="submit">` ni `fetch()` en el template
- [ ] El template tiene el bloque `{% comment %}` con metadatos al inicio
- [ ] `MiWidget` importado en `widgets/widget_types/__init__.py` y en `__all__`
- [ ] Bloque `elif slug == 'mi_widget':` añadido en `build_dynamic_form()`
- [ ] `mi_widget_boton.html` creado (copiar patrón estándar, solo cambiar `title`)

---

## 10. Ejemplo de referencia: `comentario_widget`

El widget más simple del sistema. Úsalo como referencia base.

- Clase: `widgets/widget_types/comentario.py`
- Template: `widgets/templates/widgets/comentario_widget.html`
- Botón: `widgets/templates/widgets/comentario_widget_boton.html`
- En `build_dynamic_form()`: bloque `elif slug == 'comentario_widget':`

Para un widget con más campos, ver `poste_form_widget` en los mismos paths.
