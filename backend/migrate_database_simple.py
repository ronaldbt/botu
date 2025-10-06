#!/usr/bin/env python3
"""
Script simple para migrar la base de datos PostgreSQL
"""
import os
import sys
from sqlalchemy import create_engine, text
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://botu:botu_secure_password_2024@postgres:5432/botu")

def migrate_database():
    """Migrar la base de datos PostgreSQL"""
    try:
        logger.info("🚀 Iniciando migración de base de datos...")
        
        # Crear engine
        engine = create_engine(DATABASE_URL)
        
        # Crear todas las tablas
        logger.info("📋 Creando tablas...")
        
        # Importar modelos
        from app.db.models import Base
        from app.db.models import User, TradingApiKey, Orden, TradingOrder, Signal, Ticker, Alerta, EstadoU
        
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tablas creadas exitosamente")
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"📊 PostgreSQL version: {version}")
            
            # Verificar tablas creadas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 Tablas en la base de datos: {', '.join(tables)}")
            
            # Crear usuario admin por defecto si no existe
            logger.info("👤 Verificando usuario admin...")
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'"))
            admin_count = result.scalar()
            
            if admin_count == 0:
                logger.info("👤 Creando usuario admin por defecto...")
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                # Crear hash de contraseña (contraseña corta para evitar problemas con bcrypt)
                password_hash = pwd_context.hash("admin123"[:72])
                
                admin_user = User(
                    username="admin",
                    email="admin@botut.net",
                    password_hash=password_hash,
                    is_active=True,
                    is_admin=True
                )
                
                # Insertar usuario admin
                conn.execute(text("""
                    INSERT INTO users (username, email, password_hash, is_active, is_admin, created_at, updated_at)
                    VALUES (:username, :email, :password_hash, :is_active, :is_admin, NOW(), NOW())
                """), {
                    'username': admin_user.username,
                    'email': admin_user.email,
                    'password_hash': admin_user.password_hash,
                    'is_active': admin_user.is_active,
                    'is_admin': admin_user.is_admin
                })
                conn.commit()
                logger.info("✅ Usuario admin creado: username=admin, password=admin123")
            else:
                logger.info("✅ Usuario admin ya existe")
                
        logger.info("🎉 Migración completada exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
