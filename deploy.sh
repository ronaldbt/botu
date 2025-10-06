#!/bin/bash

# Script de despliegue para Botu Trading
set -e

echo "🚀 Iniciando despliegue de Botu Trading..."

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde env.example..."
    cp env.example .env
    echo "⚠️  Por favor edita el archivo .env con tus configuraciones antes de continuar"
    echo "   Especialmente cambia SECRET_KEY y POSTGRES_PASSWORD"
    read -p "¿Continuar? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Construir y levantar los servicios
echo "🔨 Construyendo imágenes Docker..."
docker-compose build --no-cache

echo "🚀 Iniciando servicios..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado de los servicios
echo "🔍 Verificando estado de los servicios..."
docker-compose ps

# Mostrar logs
echo "📋 Mostrando logs de los servicios..."
docker-compose logs --tail=50

echo "✅ Despliegue completado!"
echo ""
echo "🌐 URLs disponibles:"
echo "   - Frontend: http://localhost (o tu dominio configurado)"
echo "   - Backend API: http://localhost/api"
echo "   - Traefik Dashboard: http://localhost:8080"
echo ""
echo "📊 Para ver los logs en tiempo real:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Para detener los servicios:"
echo "   docker-compose down"
