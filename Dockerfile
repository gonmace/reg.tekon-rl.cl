FROM python:3.12-slim

# Crear usuario no-root con UID 1000 para que coincida con el usuario del host en bind mounts
RUN groupadd -g 1000 appuser && useradd -u 1000 -g appuser appuser

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        netcat-openbsd \
        libpq-dev \
        curl \
        libgobject-2.0-0 \
        libglib2.0-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf-2.0-0 \
        libffi-dev \
        shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar código y cambiar ownership
COPY . /app/

# Crear directorios necesarios antes del chown para que el volumen herede el owner correcto
RUN mkdir -p /app/logs /app/staticfiles /app/media

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN chown -R appuser:appuser /app
RUN chmod +x /app/entrypoint.sh

# Cambiar a usuario no-root
USER appuser
WORKDIR /app

# Healthcheck para verificar que la aplicación esté funcionando
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000
