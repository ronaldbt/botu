-- Script de inicialización para PostgreSQL
-- Este archivo se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear la base de datos si no existe (aunque ya se crea con POSTGRES_DB)
-- CREATE DATABASE IF NOT EXISTS botu;

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Configurar timezone
SET timezone = 'UTC';

-- Crear usuario si no existe (aunque ya se crea con POSTGRES_USER)
-- CREATE USER IF NOT EXISTS botu WITH PASSWORD 'botu_secure_password_2024';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON DATABASE botu TO botu;

-- Mensaje de confirmación
\echo 'Base de datos botu inicializada correctamente'
