#!/bin/sh
set -e

mkdir -p /app/logs

echo "Esperando a que PostgreSQL esté disponible..."
while ! nc -z ${POSTGRES_HOST:-construccion-db} ${POSTGRES_PORT:-5432}; do
  echo "PostgreSQL no está listo, esperando..."
  sleep 2
done
echo "PostgreSQL está listo"

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "Verificando superusuario..."
python manage.py create_default_superuser

echo "Iniciando Gunicorn..."
GUNICORN_WORKERS=${GUNICORN_WORKERS:-3}
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "$GUNICORN_WORKERS" \
    --worker-class gthread \
    --threads 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 2 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
