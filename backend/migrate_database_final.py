#!/usr/bin/env python3
"""
Script final para migrar la base de datos PostgreSQL
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
            
            # Verificar si hay usuarios
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            logger.info(f"👤 Usuarios en la base de datos: {user_count}")
            
            if user_count == 0:
                logger.info("ℹ️  No hay usuarios en la base de datos. Puedes crear un usuario admin manualmente desde la aplicación.")
            else:
                logger.info("✅ Base de datos lista para usar")
                
        logger.info("🎉 Migración completada exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
