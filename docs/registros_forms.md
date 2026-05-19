# Sistema de Clases CSS Automáticas para Formularios

Este sistema permite aplicar automáticamente clases CSS a los campos de formulario basándose en si el campo es requerido o no, de manera completamente genérica.

## Características

- **Completamente genérico**: Funciona con cualquier tipo de campo sin depender de nombres específicos
- **Detección automática de widgets**: Reconoce textareas, selects, checkboxes, inputs, etc.
- **Campos requeridos**: Se aplica la clase `input-success` (verde)
- **Campos opcionales**: Se aplica la clase `input-warning` (amarillo)
- **Soporte para múltiples tipos**: Inputs, textareas, selects, checkboxes, radio buttons
- **Opcional**: Clases específicas por nombre de campo

## Funciones Disponibles

### 1. `get_form_field_css_class(form, field_name, base_class='input sombra')`
Versión completa que incluye clases específicas por nombre de campo.

### 2. `get_form_field_css_class_simple(form, field_name, base_class='input sombra')`
Versión completamente genérica sin clases específicas por nombre.

### 3. `get_field_css_class(field, field_name=None, base_class='input sombra')`
Versión de bajo nivel para casos avanzados.

## Uso Básico

### ⚠️ **Método Obsoleto - Usar Comando Automático**

**En lugar de crear manualmente, usar el comando:**
```bash
python manage.py create_registro_app reg_nombre --pasos mi_formulario
```

### Método Manual (Solo para casos especiales)

### Opción 1: Completamente Genérico (Recomendado)

```python
from registros.forms.utils import get_form_field_css_class_simple

class MiFormulario(forms.Form):
    nombre = forms.CharField(required=True, label='Nombre')
    email = forms.EmailField(required=True, label='Email')
    telefono = forms.CharField(required=False, label='Teléfono')
    comentarios = forms.CharField(widget=forms.Textarea, required=False, label='Comentarios')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Completamente genérico - funciona con cualquier campo
            Field('nombre', css_class=get_form_field_css_class_simple(self, 'nombre')),
            Field('email', css_class=get_form_field_css_class_simple(self, 'email')),
            Field('telefono', css_class=get_form_field_css_class_simple(self, 'telefono')),
            Field('comentarios', css_class=get_form_field_css_class_simple(self, 'comentarios')),
            Submit('submit', 'Guardar')
        )
```

### Opción 2: Con Clases Específicas (Opcional)

```python
from registros.forms.utils import get_form_field_css_class

class MiFormulario(forms.Form):
    nombre = forms.CharField(required=True, label='Nombre')
    email = forms.EmailField(required=True, label='Email')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Incluye clases específicas por nombre de campo
            Field('nombre', css_class=get_form_field_css_class(self, 'nombre')),
            Field('email', css_class=get_form_field_css_class(self, 'email')),
            Submit('submit', 'Guardar')
        )
```

## Tipos de Widgets Soportados

### Inputs de Texto (CharField, EmailField, IntegerField, etc.)
- **Requeridos**: `input input-success sombra`
- **Opcionales**: `input input-warning sombra`

### Textareas
- **Requeridos**: `textarea textarea-success sombra rows-2`
- **Opcionales**: `textarea textarea-warning sombra rows-2`

### Selects (ChoiceField)
- **Requeridos**: `select select-success sombra`
- **Opcionales**: `select select-warning sombra`

### Checkboxes y Radio Buttons
- **Requeridos**: `checkbox checkbox-success sombra`
- **Opcionales**: `checkbox checkbox-warning sombra`

## Uso con ModelForm

```python
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from registros.forms.utils import get_form_field_css_class_simple
from .models import MiModelo

class MiModeloForm(forms.ModelForm):
    class Meta:
        model = MiModelo
        fields = ['campo1', 'campo2', 'campo3']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Completamente genérico
            Field('campo1', css_class=get_form_field_css_class_simple(self, 'campo1')),
            Field('campo2', css_class=get_form_field_css_class_simple(self, 'campo2')),
            Field('campo3', css_class=get_form_field_css_class_simple(self, 'campo3')),
            Submit('submit', 'Guardar')
        )
```

## Ejemplos Completos

### Formulario Genérico Simple

```python
class ContactForm(forms.Form):
    nombre = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True)
    telefono = forms.CharField(required=False, max_length=20)
    mensaje = forms.CharField(widget=forms.Textarea, required=True)
    pais = forms.ChoiceField(
        choices=[('CL', 'Chile'), ('AR', 'Argentina')],
        required=False
    )
    acepta_terminos = forms.BooleanField(required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('nombre', css_class=get_form_field_css_class_simple(self, 'nombre')), css_class='w-full'),
                css_class='mb-3'
            ),
            Div(
                Div(Field('email', css_class=get_form_field_css_class_simple(self, 'email')), css_class='w-full'),
                css_class='mb-3'
            ),
            Div(
                Div(Field('telefono', css_class=get_form_field_css_class_simple(self, 'telefono')), css_class='w-1/2'),
                Div(Field('pais', css_class=get_form_field_css_class_simple(self, 'pais')), css_class='w-1/2'),
                css_class='flex gap-3 mb-3'
            ),
            Div(
                Div(Field('mensaje', css_class=get_form_field_css_class_simple(self, 'mensaje')), css_class='w-full'),
                css_class='mb-3'
            ),
            Div(
                Div(Field('acepta_terminos', css_class=get_form_field_css_class_simple(self, 'acepta_terminos')), css_class='w-full'),
                css_class='mb-3'
            ),
            Submit('submit', 'Enviar', css_class='btn btn-success')
        )
```

### Formulario con Layout Complejo

```python
class ComplexForm(forms.Form):
    # Campos requeridos
    titulo = forms.CharField(required=True, max_length=200)
    descripcion = forms.CharField(widget=forms.Textarea, required=True)
    categoria = forms.ChoiceField(
        choices=[('A', 'Categoría A'), ('B', 'Categoría B')],
        required=True
    )
    
    # Campos opcionales
    subtitulo = forms.CharField(required=False, max_length=100)
    notas = forms.CharField(widget=forms.Textarea, required=False)
    fecha = forms.DateField(required=False)
    activo = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Sección de campos requeridos
            Div(
                HTML('<h3 class="text-lg font-bold mb-3">Información Requerida</h3>'),
                Div(Field('titulo', css_class=get_form_field_css_class_simple(self, 'titulo')), css_class='w-full'),
                Div(Field('descripcion', css_class=get_form_field_css_class_simple(self, 'descripcion')), css_class='w-full'),
                Div(Field('categoria', css_class=get_form_field_css_class_simple(self, 'categoria')), css_class='w-full'),
                css_class='mb-6'
            ),
            
            # Sección de campos opcionales
            Div(
                HTML('<h3 class="text-lg font-bold mb-3">Información Opcional</h3>'),
                Div(
                    Div(Field('subtitulo', css_class=get_form_field_css_class_simple(self, 'subtitulo')), css_class='w-1/2'),
                    Div(Field('fecha', css_class=get_form_field_css_class_simple(self, 'fecha')), css_class='w-1/2'),
                    css_class='flex gap-3 mb-3'
                ),
                Div(Field('notas', css_class=get_form_field_css_class_simple(self, 'notas')), css_class='w-full'),
                Div(Field('activo', css_class=get_form_field_css_class_simple(self, 'activo')), css_class='w-full'),
                css_class='mb-6'
            ),
            
            Submit('submit', 'Guardar', css_class='btn btn-success w-full')
        )
```

## Personalización

### Cambiar la clase base

```python
# Usar una clase base diferente
css_class = get_form_field_css_class_simple(self, 'campo', base_class='input custom-base')
```

### Agregar clases específicas

```python
# Agregar clases adicionales después de obtener la clase base
base_css = get_form_field_css_class_simple(self, 'campo')
css_class = f"{base_css} custom-class"
```

### Personalizar clases específicas por campo

Si necesitas clases específicas por nombre de campo, puedes modificar la función `add_field_specific_classes` en `utils.py`:

```python
def add_field_specific_classes(css_class, field_name):
    specific_classes = {
        'mi_campo_especial': 'w-full rows-3',
        'otro_campo': 'w-1/2',
    }
    
    if field_name in specific_classes:
        css_class += f' {specific_classes[field_name]}'
    
    return css_class
```

## Ventajas del Sistema Genérico

1. **Completamente reutilizable**: Funciona con cualquier formulario sin configuración
2. **Detección automática**: Reconoce automáticamente el tipo de widget
3. **Mantenimiento fácil**: Cambios centralizados en una sola función
4. **Escalable**: Fácil agregar nuevos tipos de widgets
5. **Flexible**: Permite personalización cuando sea necesario
6. **Consistente**: Mismo comportamiento visual en todos los formularios

## Consideraciones

- La función verifica la propiedad `required` del campo
- Para ModelForms, los campos heredan la configuración `blank=True` y `null=True` del modelo
- Las clases CSS asumen que estás usando DaisyUI con las clases `input-success` e `input-warning`
- La función maneja automáticamente diferentes tipos de widgets
- La versión `_simple` es completamente genérica y no depende de nombres de campos específicos

## Recomendación

Para la mayoría de casos, usa `get_form_field_css_class_simple()` ya que es completamente genérico y no depende de nombres específicos de campos. Solo usa `get_form_field_css_class()` si necesitas clases específicas por nombre de campo. 