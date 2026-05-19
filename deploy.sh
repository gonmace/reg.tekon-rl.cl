#!/bin/bash

# Script de despliegue para Reportes Tekon en servidor Linux
# Uso: ./deploy.sh [produccion|desarrollo]

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_message() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que se ejecute como root o con sudo
if [[ $EUID -ne 0 ]]; then
   print_error "Este script debe ejecutarse como root o con sudo"
   exit 1
fi

# Configuración
PROJECT_NAME="reportesTekon"
PROJECT_DIR="/home/pti/$PROJECT_NAME"
NGINX_SITES_AVAILABLE="/etc/nginx/sites-available"
NGINX_SITES_ENABLED="/etc/nginx/sites-enabled"
DOMAIN="con.btspti.com"  # Subdominio para Reportes Tekon

print_message "Iniciando despliegue de $PROJECT_NAME..."

# 1. Crear directorio del proyecto
print_message "Creando directorio del proyecto..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 2. Detener contenedores existentes si existen
print_message "Deteniendo contenedores existentes..."
docker-compose down 2>/dev/null || true

# 3. Copiar archivos del proyecto
print_message "Copiando archivos del proyecto..."
# Nota: Ajustar la ruta según donde estén los archivos
# cp -r /ruta/local/del/proyecto/* $PROJECT_DIR/

# 4. Configurar archivo .env para producción
print_message "Configurando variables de entorno..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    print_warning "Archivo .env no encontrado. Creando desde env.example..."
    cp $PROJECT_DIR/env.example $PROJECT_DIR/.env
    print_warning "IMPORTANTE: Edita el archivo .env con tus configuraciones de producción"
fi

# 5. Construir y ejecutar contenedores
print_message "Construyendo y ejecutando contenedores..."
docker-compose build --no-cache
docker-compose up -d

# 6. Esperar a que los contenedores estén listos
print_message "Esperando a que los contenedores estén listos..."
sleep 30

# 7. Verificar que los contenedores estén funcionando
print_message "Verificando estado de los contenedores..."
if docker-compose ps | grep -q "Up"; then
    print_success "Contenedores ejecutándose correctamente"
else
    print_error "Error: Los contenedores no están funcionando"
    docker-compose logs
    exit 1
fi

# 8. Configurar Nginx
print_message "Configurando Nginx..."

# Copiar configuración de Nginx
cp $PROJECT_DIR/nginx-reportestekon.conf $NGINX_SITES_AVAILABLE/$PROJECT_NAME

# Actualizar rutas en la configuración
sed -i "s|/home/pti/reportesTekon|$PROJECT_DIR|g" $NGINX_SITES_AVAILABLE/$PROJECT_NAME
sed -i "s|con.btspti.com|$DOMAIN|g" $NGINX_SITES_AVAILABLE/$PROJECT_NAME

# Verificar que los certificados SSL existan
if [ ! -f "/etc/letsencrypt/live/btspti.com/fullchain.pem" ]; then
    print_warning "Certificados SSL no encontrados. Configurando SSL para el subdominio..."
    # Agregar el subdominio a los certificados existentes
    certbot certonly --nginx -d btspti.com -d www.btspti.com -d $DOMAIN --expand
fi

# Crear enlace simbólico
ln -sf $NGINX_SITES_AVAILABLE/$PROJECT_NAME $NGINX_SITES_ENABLED/$PROJECT_NAME

# Verificar configuración de Nginx
print_message "Verificando configuración de Nginx..."
if nginx -t; then
    print_success "Configuración de Nginx válida"
    systemctl reload nginx
    print_success "Nginx recargado"
else
    print_error "Error en la configuración de Nginx"
    exit 1
fi

# 9. Configurar firewall (opcional)
print_message "Configurando firewall..."
ufw allow 80/tcp 2>/dev/null || true
ufw allow 443/tcp 2>/dev/null || true

# 10. Configurar servicio systemd para auto-inicio
print_message "Configurando auto-inicio..."
cat > /etc/systemd/system/$PROJECT_NAME.service << EOF
[Unit]
Description=Reportes Tekon Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable $PROJECT_NAME.service

# 11. Verificación final
print_message "Realizando verificación final..."
sleep 10

# Verificar que la aplicación responda
if curl -f http://localhost:8001/ > /dev/null 2>&1; then
    print_success "Aplicación respondiendo correctamente en puerto 8001"
else
    print_warning "La aplicación no responde en localhost:8001"
fi

# Mostrar información del despliegue
print_success "Despliegue completado exitosamente!"
echo ""
echo "Información del despliegue:"
echo "=========================="
echo "Proyecto: $PROJECT_NAME"
echo "Directorio: $PROJECT_DIR"
echo "Puerto aplicación: 8001"
echo "Puerto base de datos: 5433"
echo "Dominio configurado: $DOMAIN"
echo ""
echo "Comandos útiles:"
echo "================"
echo "Ver logs: cd $PROJECT_DIR && docker-compose logs -f"
echo "Reiniciar: systemctl restart $PROJECT_NAME"
echo "Estado: systemctl status $PROJECT_NAME"
echo "Nginx: systemctl status nginx"
echo ""
echo "IMPORTANTE:"
echo "==========="
echo "1. Edita $PROJECT_DIR/.env con tus configuraciones de producción"
echo "2. Configura tu dominio DNS para apuntar a este servidor"
echo "3. Si usas SSL, configura los certificados y descomenta la sección HTTPS en Nginx"
echo "4. Ajusta las rutas en nginx-reportestekon.conf según tu estructura de archivos"
