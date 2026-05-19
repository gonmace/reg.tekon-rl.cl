# Reseteo de Base de Datos - ReportesTekon

Este documento explica cómo resetear la base de datos del proyecto ReportesTekon de forma segura, preservando los datos importantes.

## Problema Original

El error `IntegrityError: NOT NULL constraint failed: reg_visita_historicalregvisita.fecha_registro` se debe a que las tablas históricas de `simple_history` tienen campos que no coinciden con las migraciones actuales.

## Solución

Se han creado herramientas para hacer backup de los datos importantes y resetear la base de datos de forma segura.

## Comandos Disponibles

### 1. Backup y Restauración de Datos

```bash
# Crear backup de datos
python manage.py backup_restore_data --action=backup --output=mi_backup.json

# Restaurar datos desde backup
python manage.py backup_restore_data --action=restore --input=mi_backup.json
```

### 2. Crear Superusuario por Defecto

```bash
python manage.py create_default_superuser
```

### 3. Establecer Contraseñas por Defecto

```bash
python manage.py set_user_passwords
```

O con contraseñas personalizadas:
```bash
python manage.py set_user_passwords --password=mi_password --admin-password=admin_password
```

Credenciales por defecto:
- **Usuarios normales**: `123456`
- **Administradores**: `admin123`

### 4. Reset Completo de Base de Datos (Recomendado)

```bash
./reset_database.sh
```

Este script automatiza todo el proceso:
1. ✅ Crea backup de datos actuales
2. ✅ Hace backup de la base de datos SQLite
3. ✅ Borra la base de datos actual
4. ✅ Borra archivos de migración
5. ✅ Crea nuevas migraciones
6. ✅ Aplica migraciones
7. ✅ Crea superusuario por defecto
8. ✅ Establece contraseñas por defecto
9. ✅ Restaura datos desde backup
10. ✅ Verifica que todo funciona

## Datos que se Preservan

El backup incluye:
- 👥 **Usuarios**: Todos los usuarios del sistema
- 🏢 **Sitios**: Información de sitios y coordenadas
- 📋 **Registros de Visita**: Todos los registros de `reg_visita`
- 📊 **Registros TXTSS**: Todos los registros de `reg_txtss`
- 📸 **Fotos**: Referencias a archivos de fotos
- ⏰ **Timestamps**: Fechas de creación y modificación

## Pasos Manuales (Alternativa)

Si prefieres hacer el proceso manualmente:

### Paso 1: Backup
```bash
# Activar entorno virtual
source .venv/bin/activate

# Crear backup
python manage.py backup_restore_data --action=backup --output=backup_$(date +%Y%m%d_%H%M%S).json
```

### Paso 2: Reset
```bash
# Borrar base de datos
rm db.sqlite3

# Borrar migraciones
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# Crear nuevas migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### Paso 3: Restaurar
```bash
# Crear superusuario
python manage.py create_default_superuser

# Restaurar datos
python manage.py backup_restore_data --action=restore --input=tu_archivo_backup.json
```

## Verificación

Después del reset, verifica que todo funciona:

```bash
# Verificar configuración
python manage.py check

# Iniciar servidor
python manage.py runserver
```

## Archivos de Backup

El script crea dos archivos de backup:
1. `backup_data_YYYYMMDD_HHMMSS.json` - Datos exportados
2. `db_backup_YYYYMMDD_HHMMSS.sqlite3` - Base de datos completa

**⚠️ Importante**: Guarda estos archivos en un lugar seguro antes de borrarlos.

## Credenciales por Defecto

Después del reset, las contraseñas se establecen automáticamente:

### Usuarios Administradores (is_superuser=True)
- **Contraseña**: `admin123`

### Usuarios Normales
- **Contraseña**: `123456`

### Usuarios Restaurados
Los usuarios existentes se restauran con sus datos originales:
- Nombres y apellidos
- Tipos de usuario (ITO, ADMIN, CLIENT)
- Teléfonos
- Estados activo/inactivo
- Permisos de staff y superusuario

**⚠️ IMPORTANTE**: Cambia las contraseñas después del primer acceso por seguridad.

## Solución de Problemas

### Error: "No module named 'django'"
```bash
# Activar entorno virtual
source .venv/bin/activate
```

### Error: "Permission denied"
```bash
# Hacer el script ejecutable
chmod +x reset_database.sh
```

### Error en restauración
Si la restauración falla, puedes:
1. Usar el backup de la base de datos completa
2. Restaurar manualmente los datos críticos
3. Contactar al administrador del sistema

## Notas Técnicas

- El comando `backup_restore_data` usa transacciones para garantizar consistencia
- Los archivos de fotos no se copian, solo las referencias en la base de datos
- Las contraseñas de usuario se mantienen (hasheadas)
- El proceso es idempotente (se puede ejecutar múltiples veces)

## Contacto

Si tienes problemas con este proceso, revisa:
1. Los logs del comando
2. Los archivos de backup generados
3. La documentación de Django sobre migraciones 