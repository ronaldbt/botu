#!/usr/bin/env python3

"""
Script para agregar las columnas de Telegram al modelo User
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL

def add_telegram_columns():
    """Agrega las columnas de Telegram a la tabla users"""
    
    engine = create_engine(DATABASE_URL)
    
    # Lista de columnas a agregar
    columns_to_add = [
        "telegram_chat_id VARCHAR",
        "telegram_token VARCHAR UNIQUE",
        "telegram_subscribed BOOLEAN DEFAULT FALSE",
        "subscription_status VARCHAR DEFAULT 'inactive'",
        "last_activity TIMESTAMP DEFAULT NOW()"
    ]
    
    with engine.connect() as connection:
        # Verificar si las columnas ya existen
        result = connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
        """))
        existing_columns = [row[0] for row in result]
        
        print(f"Columnas existentes en 'users': {existing_columns}")
        
        # Agregar columnas que no existen
        for column_def in columns_to_add:
            column_name = column_def.split()[0]
            
            if column_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE users ADD COLUMN {column_def}"
                    print(f"Ejecutando: {sql}")
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"✅ Columna '{column_name}' agregada exitosamente")
                except Exception as e:
                    print(f"❌ Error agregando columna '{column_name}': {e}")
            else:
                print(f"⏭️ Columna '{column_name}' ya existe")
    
    print("\n🎉 Migración completada!")

if __name__ == "__main__":
    print("🔄 Agregando columnas de Telegram a la tabla users...")
    add_telegram_columns()