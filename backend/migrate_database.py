#!/usr/bin/env python3
"""
Script de migración para actualizar la base de datos con las nuevas columnas necesarias.
Ejecutar desde el directorio backend con: python migrate_database.py
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def get_database_url():
    """Obtener URL de conexión a la base de datos"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL no encontrada en variables de entorno")
    return database_url

def execute_migration(conn, migration_sql, description):
    """Ejecutar una migración específica"""
    try:
        with conn.cursor() as cur:
            print(f"Ejecutando: {description}")
            cur.execute(migration_sql)
            conn.commit()
            print(f"✅ Completado: {description}")
    except psycopg2.Error as e:
        conn.rollback()
        if "already exists" in str(e) or "duplicate column" in str(e):
            print(f"⚠️  Ya existe: {description}")
        else:
            print(f"❌ Error en {description}: {e}")
            raise

def main():
    """Función principal de migración"""
    try:
        database_url = get_database_url()
        print(f"Conectando a la base de datos...")
        
        conn = psycopg2.connect(database_url)
        print("✅ Conexión establecida")
        
        # ========================================
        # Migraciones para tabla users
        # ========================================
        
        print("\n📝 Migrando tabla 'users'...")
        
        user_migrations = [
            # Campos de perfil personal
            ("ALTER TABLE users ADD COLUMN full_name VARCHAR", "Agregar campo full_name"),
            ("ALTER TABLE users ADD COLUMN email VARCHAR UNIQUE", "Agregar campo email"),
            ("ALTER TABLE users ADD COLUMN phone VARCHAR", "Agregar campo phone"),
            ("ALTER TABLE users ADD COLUMN country VARCHAR", "Agregar campo country"),
            
            # Campos para Telegram por criptomoneda
            ("ALTER TABLE users ADD COLUMN telegram_chat_id_btc VARCHAR", "Agregar campo telegram_chat_id_btc"),
            ("ALTER TABLE users ADD COLUMN telegram_chat_id_eth VARCHAR", "Agregar campo telegram_chat_id_eth"),
            ("ALTER TABLE users ADD COLUMN telegram_chat_id_bnb VARCHAR", "Agregar campo telegram_chat_id_bnb"),
            ("ALTER TABLE users ADD COLUMN telegram_token_btc VARCHAR UNIQUE", "Agregar campo telegram_token_btc"),
            ("ALTER TABLE users ADD COLUMN telegram_token_eth VARCHAR UNIQUE", "Agregar campo telegram_token_eth"),
            ("ALTER TABLE users ADD COLUMN telegram_token_bnb VARCHAR UNIQUE", "Agregar campo telegram_token_bnb"),
            ("ALTER TABLE users ADD COLUMN telegram_subscribed_btc BOOLEAN DEFAULT FALSE", "Agregar campo telegram_subscribed_btc"),
            ("ALTER TABLE users ADD COLUMN telegram_subscribed_eth BOOLEAN DEFAULT FALSE", "Agregar campo telegram_subscribed_eth"),
            ("ALTER TABLE users ADD COLUMN telegram_subscribed_bnb BOOLEAN DEFAULT FALSE", "Agregar campo telegram_subscribed_bnb"),
            
            # Campos de suscripción y pagos
            ("ALTER TABLE users ADD COLUMN subscription_plan VARCHAR DEFAULT 'free'", "Agregar campo subscription_plan"),
            ("ALTER TABLE users ADD COLUMN subscription_status VARCHAR DEFAULT 'inactive'", "Agregar campo subscription_status"),
            ("ALTER TABLE users ADD COLUMN subscription_start_date TIMESTAMP", "Agregar campo subscription_start_date"),
            ("ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP", "Agregar campo subscription_end_date"),
            ("ALTER TABLE users ADD COLUMN payment_method VARCHAR", "Agregar campo payment_method"),
            ("ALTER TABLE users ADD COLUMN paypal_subscription_id VARCHAR", "Agregar campo paypal_subscription_id"),
            ("ALTER TABLE users ADD COLUMN last_payment_date TIMESTAMP", "Agregar campo last_payment_date"),
            ("ALTER TABLE users ADD COLUMN last_activity TIMESTAMP DEFAULT NOW()", "Agregar campo last_activity"),
        ]
        
        for migration_sql, description in user_migrations:
            execute_migration(conn, migration_sql, description)
        
        # ========================================
        # Migraciones para tabla estados_u
        # ========================================
        
        print("\n📝 Migrando tabla 'estados_u'...")
        
        # Agregar columnas faltantes (ticker ya es primary key)
        estados_u_migrations = [
            ("ALTER TABLE estados_u ADD COLUMN crypto_symbol VARCHAR DEFAULT 'BTC'", "Agregar campo crypto_symbol"),
            ("ALTER TABLE estados_u ADD COLUMN scanner_active BOOLEAN DEFAULT FALSE", "Agregar campo scanner_active"),
            ("ALTER TABLE estados_u ADD COLUMN last_alert_sent TIMESTAMP", "Agregar campo last_alert_sent"),
        ]
        
        for migration_sql, description in estados_u_migrations:
            execute_migration(conn, migration_sql, description)
            
        # Crear índices si no existen
        print("\n📝 Creando índices...")
        
        index_migrations = [
            ("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)", "Índice para users.email"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id_btc ON users(telegram_chat_id_btc)", "Índice para telegram_chat_id_btc"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id_eth ON users(telegram_chat_id_eth)", "Índice para telegram_chat_id_eth"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id_bnb ON users(telegram_chat_id_bnb)", "Índice para telegram_chat_id_bnb"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_token_btc ON users(telegram_token_btc)", "Índice para telegram_token_btc"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_token_eth ON users(telegram_token_eth)", "Índice para telegram_token_eth"),
            ("CREATE INDEX IF NOT EXISTS idx_users_telegram_token_bnb ON users(telegram_token_bnb)", "Índice para telegram_token_bnb"),
            ("CREATE INDEX IF NOT EXISTS idx_estados_u_crypto_symbol ON estados_u(crypto_symbol)", "Índice para estados_u.crypto_symbol"),
        ]
        
        for migration_sql, description in index_migrations:
            execute_migration(conn, migration_sql, description)
        
        print("\n🎉 ¡Migración completada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        return 1
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔐 Conexión cerrada")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())