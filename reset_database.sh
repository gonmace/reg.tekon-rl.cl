#!/bin/bash

# Script para resetear la base de datos con backup y restauración de datos
# Uso: ./reset_database.sh

set -e  # Salir si hay algún error

echo "=== SCRIPT DE RESET DE BASE DE DATOS ==="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "Error: No se encontró manage.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    echo "Activando entorno virtual..."
    source .venv/bin/activate
fi

# Crear backup antes de borrar
echo "1. Creando backup de datos actuales..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="backup_data_${TIMESTAMP}.json"

python manage.py backup_restore_data --action=backup --output="$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "Error: Falló la creación del backup"
    exit 1
fi

echo "Backup creado: $BACKUP_FILE"
echo ""

# Confirmar que el usuario quiere continuar
echo "¿Estás seguro de que quieres borrar la base de datos y recrearla?"
echo "Los datos han sido respaldados en: $BACKUP_FILE"
read -p "Escribe 'SI' para continuar: " confirm

if [ "$confirm" != "SI" ]; then
    echo "Operación cancelada. El backup se mantiene en: $BACKUP_FILE"
    exit 0
fi

echo ""

# Hacer backup de la base de datos actual (por si acaso)
echo "2. Haciendo backup de la base de datos SQLite..."
DB_BACKUP="db_backup_${TIMESTAMP}.sqlite3"
cp db.sqlite3 "$DB_BACKUP"
echo "Backup de DB creado: $DB_BACKUP"
echo ""

# Borrar la base de datos
echo "3. Borrando base de datos actual..."
rm -f db.sqlite3
echo "Base de datos borrada."
echo ""

# Borrar migraciones (opcional, pero recomendado para un reset completo)
echo "4. Borrando archivos de migración..."
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
echo "Archivos de migración borrados."
echo ""

# Crear nuevas migraciones
echo "5. Creando nuevas migraciones..."
python manage.py makemigrations

if [ $? -ne 0 ]; then
    echo "Error: Falló la creación de migraciones"
    echo "Restaurando base de datos desde backup..."
    cp "$DB_BACKUP" db.sqlite3
    exit 1
fi

echo "Migraciones creadas."
echo ""

# Aplicar migraciones
echo "6. Aplicando migraciones..."
python manage.py migrate

if [ $? -ne 0 ]; then
    echo "Error: Falló la aplicación de migraciones"
    echo "Restaurando base de datos desde backup..."
    cp "$DB_BACKUP" db.sqlite3
    exit 1
fi

echo "Migraciones aplicadas."
echo ""

# Crear superusuario
echo "7. Creando superusuario por defecto..."
python manage.py create_default_superuser

if [ $? -ne 0 ]; then
    echo "Advertencia: No se pudo crear superusuario automáticamente."
    echo "Puedes crearlo manualmente con: python manage.py createsuperuser"
fi

echo ""

# Establecer contraseñas por defecto
echo "8. Estableciendo contraseñas por defecto..."
python manage.py set_user_passwords

if [ $? -ne 0 ]; then
    echo "Advertencia: No se pudieron establecer contraseñas automáticamente."
    echo "Puedes establecerlas manualmente con: python manage.py set_user_passwords"
fi

echo ""

# Restaurar datos desde el backup
echo "9. Restaurando datos desde backup..."
python manage.py backup_restore_data --action=restore --input="$BACKUP_FILE"

if [ $? -ne 0 ]; then
    echo "Error: Falló la restauración de datos"
    echo "La base de datos está limpia pero sin datos restaurados."
    echo "Puedes restaurar manualmente con: python manage.py backup_restore_data --action=restore --input=$BACKUP_FILE"
    exit 1
fi

echo ""

# Verificar que todo funciona
echo "10. Verificando que la aplicación funciona..."
python manage.py check

if [ $? -eq 0 ]; then
    echo "✅ Verificación exitosa!"
else
    echo "⚠️  Advertencia: La verificación encontró algunos problemas."
fi

echo ""
echo "=== RESET COMPLETADO ==="
echo ""
echo "Archivos de backup creados:"
echo "  - Datos: $BACKUP_FILE"
echo "  - Base de datos: $DB_BACKUP"
echo ""
echo "La base de datos ha sido reseteada y los datos han sido restaurados."
echo "Puedes iniciar el servidor con: python manage.py runserver"
echo "" 