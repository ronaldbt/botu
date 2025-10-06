#!/usr/bin/env python3
"""
Script para migrar la base de datos PostgreSQL en Docker
"""
import os
import sys
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://botu:botu_secure_password_2024@postgres:5432/botu")

async def migrate_database():
    """Migrar la base de datos PostgreSQL"""
    try:
        logger.info("🚀 Iniciando migración de base de datos...")
        
        # Crear engine asíncrono
        engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
        
        # Crear sesión
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Crear todas las tablas
            logger.info("📋 Creando tablas...")
            
            # Importar modelos
            from app.db.models import Base
            from app.db.models import User, TradingApiKey, Order, Signal, Ticker, Alert, EstadoU
            
            # Crear tablas
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ Tablas creadas exitosamente")
            
            # Verificar conexión
            result = await session.execute(text("SELECT version();"))
            version = result.scalar()
            logger.info(f"📊 PostgreSQL version: {version}")
            
            # Verificar tablas creadas
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"📋 Tablas en la base de datos: {', '.join(tables)}")
            
            # Crear usuario admin por defecto si no existe
            logger.info("👤 Verificando usuario admin...")
            result = await session.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'"))
            admin_count = result.scalar()
            
            if admin_count == 0:
                logger.info("👤 Creando usuario admin por defecto...")
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                admin_user = User(
                    username="admin",
                    email="admin@botut.net",
                    password_hash=pwd_context.hash("admin123"),
                    is_active=True,
                    is_admin=True
                )
                session.add(admin_user)
                await session.commit()
                logger.info("✅ Usuario admin creado: username=admin, password=admin123")
            else:
                logger.info("✅ Usuario admin ya existe")
                
        logger.info("🎉 Migración completada exitosamente!")
        
    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        sys.exit(1)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_database())
