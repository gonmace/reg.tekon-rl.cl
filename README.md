# Documentación del Proyecto ReportesTekon

## 📚 Índice de Documentación

### 🚀 Comando para Crear Aplicaciones
- **[COMANDO_CREAR_APPS.md](COMANDO_CREAR_APPS.md)** - Guía completa del comando `create_registro_app`
- **[RESUMEN_COMANDO_CREAR_APPS.md](RESUMEN_COMANDO_CREAR_APPS.md)** - Resumen ejecutivo del comando

### 🔧 Sistema de Registros
- **[GENERIC_STEPS_SYSTEM.md](GENERIC_STEPS_SYSTEM.md)** - Sistema genérico de pasos
- **[registros_config.md](registros_config.md)** - Configuración del sistema de registros
- **[registros_views.md](registros_views.md)** - Vistas del sistema de registros
- **[registros_views_steps.md](registros_views_steps.md)** - Vistas de pasos
- **[registros_forms.md](registros_forms.md)** - Formularios del sistema
- **[registros_components.md](registros_components.md)** - Componentes del sistema

### 🗺️ Sistema de Mapas
- **[MAP_SYSTEM.md](MAP_SYSTEM.md)** - Sistema de mapas
- **[registros_mapa_template.md](registros_mapa_template.md)** - Templates de mapas

### 🔍 Validación y Completitud
- **[registros_completeness_checker.md](registros_completeness_checker.md)** - Verificador de completitud
- **[registros_templatetags_usage.md](registros_templatetags_usage.md)** - Uso de template tags

### 📝 Ejemplos y Guías
- **Comando `create_registro_app`** - Reemplaza la creación manual de pasos
- **Aplicaciones de ejemplo** - `reg_instalacion` y `reg_mantenimiento` como referencias

## 🎯 Comandos Principales

### Crear Nueva Aplicación de Registros
```bash
# Aplicación básica
python manage.py create_registro_app reg_nombre

# Aplicación con título personalizado
python manage.py create_registro_app reg_nombre --title "Título Personalizado"

# Aplicación con pasos específicos
python manage.py create_registro_app reg_nombre --pasos paso1 paso2 paso3

# Aplicación completa
python manage.py create_registro_app reg_nombre \
    --title "Título" \
    --description "Descripción" \
    --pasos paso1 paso2 paso3
```

### Configurar Aplicación
```bash
# Configurar API de Google Maps
python manage.py setup_app_settings --api-key TU_API_KEY

# Verificar configuración
python manage.py check
```

## 📁 Estructura del Proyecto

```
reportesTekon/
├── core/                          # Aplicación principal
│   ├── management/commands/       # Comandos personalizados
│   │   ├── create_registro_app.py # Comando para crear apps
│   │   └── setup_app_settings.py  # Configuración inicial
│   └── ...
├── registros/                     # Sistema genérico de registros
├── reg_txtss/                     # Aplicación de ejemplo
├── reg_instalacion/               # Aplicación creada con comando
├── reg_mantenimiento/             # Aplicación creada con comando
├── docs/                          # Documentación
└── ...
```

## 🔄 Flujo de Desarrollo

### 1. Crear Nueva Aplicación
```bash
python manage.py create_registro_app reg_mi_app --title "Mi Aplicación" --pasos paso1 paso2
```

### 2. Configurar en settings.py
```python
INSTALLED_APPS = [
    # ... otras apps
    'reg_mi_app',
]
```

### 3. Agregar URLs
```python
# urls.py principal
urlpatterns = [
    # ... otras URLs
    path('reg-mi-app/', include('reg_mi_app.urls')),
]
```

### 4. Seguir Instrucciones Automáticas
El comando muestra automáticamente todos los pasos necesarios:

```
📋 PASOS DE CONFIGURACIÓN MANUAL:
1. Agregar "reg_mi_app" a INSTALLED_APPS en config/base.py
2. Agregar URL en config/urls.py: path("reg_mi_app/", include("reg_mi_app.urls"))
3. Agregar al menú en core/menu/menu_builder.py
4. Ejecutar: python manage.py makemigrations reg_mi_app
5. Ejecutar: python manage.py migrate
6. Crear superusuario si no existe: python manage.py createsuperuser
```

### 5. Verificar Funcionamiento
- Ir a http://localhost:8000/reg_mi_app/
- Verificar que aparezca en el menú lateral
- Probar crear un nuevo registro

### 6. Personalizar (Opcional)
- Editar modelos en `reg_mi_app/models.py`
- Configurar formularios en `reg_mi_app/forms.py`
- Personalizar templates en `reg_mi_app/templates/`

## 🎉 Aplicaciones Creadas

### ✅ Aplicaciones de Prueba
- **reg_instalacion**: Instalación (sitio, acceso, empalme)
- **reg_mantenimiento**: Mantenimiento Preventivo (inspeccion, diagnostico, reparacion, pruebas, verificacion)

### 📋 Aplicaciones Originales
- **reg_txtss**: TX/TSS (sitio, acceso, empalme)

## 🚨 Troubleshooting

### Errores Comunes
1. **"La aplicación ya existe"** → Usar `--force`
2. **"Nombre inválido"** → Seguir reglas de validación
3. **"Conflicto de módulo"** → Usar nombre más específico
4. **"No module named"** → Verificar INSTALLED_APPS

### Validación de Nombres
- Solo letras minúsculas, números y guiones bajos
- Debe empezar con una letra
- No puede coincidir con módulos Python existentes

## 📞 Soporte

Para problemas o mejoras:
1. Revisar la documentación específica
2. Verificar ejemplos en aplicaciones existentes
3. Consultar el código fuente del comando
4. Revisar logs de Django para errores específicos 