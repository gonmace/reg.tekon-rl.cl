# Comando para Crear Aplicaciones de Registros

## Descripción

El comando `create_registro_app` permite crear aplicaciones de registros completas con estructura similar a `reg_txtss` de forma automática y personalizable.

## Uso Básico

```bash
python manage.py create_registro_app <nombre_app>
```

## Validación de Nombres

El comando valida que el nombre de la aplicación cumpla con las siguientes reglas:
- Solo letras minúsculas, números y guiones bajos
- Debe empezar con una letra
- Ejemplos válidos: `reg_instalacion`, `reg_mantenimiento_2024`
- Ejemplos inválidos: `RegInstalacion`, `reg-instalacion`, `1reg_app`

## Parámetros

### Obligatorios
- `app_name`: Nombre de la aplicación (ej: `reg_instalacion`, `reg_mantenimiento`)

### Opcionales
- `--title`: Título de la aplicación (ej: "Instalación", "Mantenimiento")
- `--description`: Descripción de la aplicación
- `--pasos`: Lista de pasos para el registro (ej: sitio acceso empalme)
- `--force`: Forzar la creación aunque la aplicación ya exista

## Ejemplos de Uso

### 1. Aplicación básica con pasos por defecto
```bash
python manage.py create_registro_app reg_instalacion
```

### 2. Aplicación con título personalizado
```bash
python manage.py create_registro_app reg_mantenimiento --title "Mantenimiento Preventivo"
```

### 3. Aplicación con pasos específicos
```bash
python manage.py create_registro_app reg_auditoria --pasos inspeccion verificacion documentacion
```

### 4. Aplicación completa con todos los parámetros
```bash
python manage.py create_registro_app reg_servicio \
    --title "Servicio Técnico" \
    --description "Aplicación para registros de servicios técnicos" \
    --pasos diagnostico reparacion pruebas
```

## Estructura Generada

El comando crea una aplicación completa con la siguiente estructura:

```
reg_nombre/
├── __init__.py
├── admin.py          # Configuración de admin
├── apps.py           # Configuración de la app
├── config.py         # Configuración de registros
├── forms.py          # Formularios para cada paso
├── models.py         # Modelos de datos
├── urls.py           # URLs de la aplicación
├── views.py          # Vistas genéricas
├── migrations/       # Migraciones Django
└── templates/
    └── reg_nombre/
        ├── list.html     # Template de listado
        ├── steps.html    # Template de pasos
        └── partials/     # Templates parciales
```

## Características Incluidas

### ✅ Modelos
- Modelo principal de registro heredando de `RegistroBase`
- Modelos de pasos heredando de `PasoBase`
- Campos básicos: sitio, usuario, título, descripción
- Historial de cambios con `simple_history`

### ✅ Vistas
- `ListRegistrosView`: Listado de registros con tabla
- `StepsRegistroView`: Vista de pasos del registro
- `ElementoRegistroView`: Vista para elementos individuales
- `ActivarRegistroView`: Activación de registros

### ✅ Formularios
- Formularios Crispy Forms para cada paso
- Configuración automática de campos
- Validación y manejo de errores

### ✅ Configuración
- Configuración declarativa usando el sistema de registros
- Integración con el sistema de pasos
- Templates personalizables

### ✅ Admin
- Configuración de Django Admin
- Filtros y búsqueda
- Campos de solo lectura para auditoría

### ✅ Templates
- Templates HTML responsivos
- Integración con el sistema de diseño
- Breadcrumbs y navegación

### ✅ PDF Automático
- Templates de PDF generados automáticamente
- Vistas de PDF con WeasyTemplateView
- URLs para generar y previsualizar PDF
- Integración con mapas y fotos

### ✅ Manejo de Errores
- Validación de nombres de aplicación
- Detección de aplicaciones existentes
- Opción `--force` para sobrescribir
- Mensajes de error descriptivos
- Corrección automática de templates
- URLs correctas sin vistas inexistentes

## Pasos Después de la Creación

El comando ahora incluye **instrucciones automáticas** que se muestran al final de la creación, y genera un archivo `SETUP.md` con todos los pasos necesarios.

### Pasos Automáticos Mostrados

Al crear la aplicación, el comando muestra automáticamente:

```
📋 PASOS DE CONFIGURACIÓN MANUAL:
1. Agregar "reg_nombre" a INSTALLED_APPS en config/base.py
2. Agregar URL en config/urls.py: path("reg_nombre/", include("reg_nombre.urls"))
3. Agregar al menú en core/menu/menu_builder.py
4. Ejecutar: python manage.py makemigrations reg_nombre
5. Ejecutar: python manage.py migrate
6. Crear superusuario si no existe: python manage.py createsuperuser
7. ✅ PDF automático: Templates y vistas generados automáticamente
```

### Archivo SETUP.md Generado

Cada aplicación creada incluye un archivo `SETUP.md` con:

1. **Configuración de INSTALLED_APPS** - Código exacto para agregar
2. **Configuración de URLs** - Código exacto para incluir
3. **Configuración del Menú** - Código exacto para el menú lateral
4. **Comandos de Migración** - Comandos exactos a ejecutar
5. **Verificación de Funcionamiento** - Pasos para probar
6. **Generación de PDF** - URLs para generar y previsualizar PDF
7. **Notas Técnicas** - Información sobre la estructura

### Ejemplo de SETUP.md

```markdown
# Configuración Manual para Mi Aplicación

## 1. Agregar a INSTALLED_APPS (config/base.py)
```python
INSTALLED_APPS = [
    # ... otras apps
    'reg_mi_app',
]
```

## 2. Agregar URL (config/urls.py)
```python
urlpatterns = [
    # ... otras URLs
    path('reg_mi_app/', include('reg_mi_app.urls')),
]
```

## 3. Agregar al Menú (core/menu/menu_builder.py)
```python
menu = [
    # ... otros items
    MenuItem('Mi Aplicación', 'reg_mi_app:list', 'fas fa-file-alt', module='registros'),
]
```
```

## Personalización Avanzada

### Agregar Campos Específicos

Editar `models.py` para agregar campos adicionales:

```python
class PasoEspecifico(PasoBase):
    registro = models.ForeignKey(RegNombre, on_delete=models.CASCADE)
    campo_especifico = models.CharField(max_length=100)
    coordenadas = models.FloatField(validators=[validar_latitud])
    # ... más campos
```

### Configurar Mapas

Editar `config.py` para agregar componentes de mapa:

```python
from registros.config import create_2_point_map_config

mapa_component = create_2_point_map_config(
    model_class1='current',
    lat1='lat',
    lon1='lon',
    name1='Ubicación',
    icon1_color='#FF4040',
    # ... más configuración
)

PASOS_CONFIG['paso'] = create_custom_config(
    # ... configuración existente
    sub_elementos=[mapa_component]
)
```

### Agregar Fotos

```python
from registros.config import create_photos_config

fotos_component = create_photos_config(
    photo_min=3,
    photos_template='photos/photos_main.html'
)

PASOS_CONFIG['paso'] = create_custom_config(
    # ... configuración existente
    sub_elementos=[fotos_component]
)
```

## Ventajas del Comando

1. **Rapidez**: Crea una aplicación completa en segundos
2. **Consistencia**: Todas las apps siguen la misma estructura
3. **Flexibilidad**: Fácil personalización después de la creación
4. **Integración**: Usa el sistema genérico de registros existente
5. **Mantenibilidad**: Código limpio y bien estructurado

## Troubleshooting

### Error: "La aplicación ya existe"
```bash
python manage.py create_registro_app reg_nombre --force
```

### Error: "Nombre de aplicación inválido"
- Usar solo letras minúsculas, números y guiones bajos
- Empezar con una letra
- Ejemplo válido: `reg_instalacion_2024`

### Error: "conflicts with the name of an existing Python module"
- El nombre de la aplicación no puede coincidir con módulos Python existentes
- Usar un nombre más específico o diferente
- Ejemplo: cambiar `reg_demo` por `reg_demo_app`

### Error: "migrations/__init__.py already exists"
- El comando maneja automáticamente este error
- Usar `--force` para sobrescribir la aplicación existente
- El comando elimina y recrea la estructura completa

### Error: "No module named 'reg_nombre'"
- Verificar que la app esté en `INSTALLED_APPS`
- Ejecutar `python manage.py check` para validar

## Detalles Técnicos

### Funcionamiento Interno
- **Creación Manual**: No usa `startapp` de Django, crea la estructura manualmente
- **Manejo de Conflictos**: Detecta aplicaciones existentes y permite sobrescribir
- **Validación**: Valida nombres antes de crear la estructura
- **Templates Dinámicos**: Genera contenido basado en parámetros

### Archivos Generados
- **Modelos**: Heredan de `RegistroBase` y `PasoBase`
- **Vistas**: Usan el sistema genérico de registros
- **Formularios**: Crispy Forms con configuración automática
- **Configuración**: Sistema declarativo de registros
- **Templates**: HTML responsivo con integración de diseño

## Contribuir

Para mejorar el comando:

1. Editar `core/management/commands/create_registro_app.py`
2. Agregar nuevas funcionalidades
3. Probar con diferentes configuraciones
4. Actualizar esta documentación 