#!/usr/bin/env python3
"""
Script para migrar las columnas 4h mainnet en PostgreSQL
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import text

def migrate_4h_columns():
    """Migra las columnas 4h mainnet en PostgreSQL"""
    
    with engine.connect() as conn:
        try:
            print("🔧 Migrando columnas 4h mainnet en PostgreSQL...")
            
            # Lista de columnas que necesitamos agregar
            columns_to_add = [
                ("bnb_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("bnb_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("eth_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("eth_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("btc_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("btc_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("paxg_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("paxg_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    # Verificar si la columna ya existe
                    check_result = conn.execute(text(f"""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'trading_api_keys' 
                        AND column_name = '{column_name}';
                    """))
                    
                    if check_result.fetchone():
                        print(f"✅ Columna {column_name} ya existe")
                    else:
                        # Agregar la columna
                        conn.execute(text(f"""
                            ALTER TABLE trading_api_keys 
                            ADD COLUMN {column_name} {column_type};
                        """))
                        conn.commit()
                        print(f"✅ Columna {column_name} agregada")
                        
                except Exception as e:
                    print(f"⚠️  Error con columna {column_name}: {e}")
            
            # Verificar todas las columnas 4h
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'trading_api_keys' 
                AND column_name LIKE '%4h_mainnet%'
                ORDER BY column_name;
            """))
            columns = [row[0] for row in result]
            
            print("\n📊 Columnas 4h Mainnet disponibles:")
            for col in columns:
                print(f"   ✅ {col}")
                
            print(f"\n🎉 Migración completada. {len(columns)} columnas 4h mainnet disponibles.")
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            raise

if __name__ == "__main__":
    migrate_4h_columns()
