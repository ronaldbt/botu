#!/usr/bin/env python3
"""
Script para agregar las columnas faltantes en la tabla trading_api_keys
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import text

def fix_missing_columns():
    """Agrega las columnas faltantes para los escáneres 4h"""
    
    with engine.connect() as conn:
        try:
            print("🔧 Agregando columnas faltantes para escáneres 4h...")
            
            # Lista de columnas que faltan según el error
            missing_columns = [
                ("bnb_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("bnb_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("eth_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("eth_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("btc_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("btc_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
                ("paxg_4h_mainnet_enabled", "BOOLEAN DEFAULT FALSE"),
                ("paxg_4h_mainnet_allocated_usdt", "FLOAT DEFAULT 0.0"),
            ]
            
            for column_name, column_type in missing_columns:
                try:
                    conn.execute(text(f"""
                        ALTER TABLE trading_api_keys 
                        ADD COLUMN IF NOT EXISTS {column_name} {column_type};
                    """))
                    conn.commit()
                    print(f"✅ Columna {column_name} agregada")
                except Exception as e:
                    print(f"⚠️  Columna {column_name} ya existe o error: {e}")
            
            # Verificar las columnas agregadas
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'trading_api_keys' 
                AND column_name LIKE '%4h_mainnet%'
                ORDER BY column_name;
            """))
            columns = [row[0] for row in result]
            
            print("\n📊 Columnas 4h Mainnet en la tabla:")
            for col in columns:
                print(f"   ✅ {col}")
                
            print(f"\n🎉 Migración completada. {len(columns)} columnas 4h mainnet disponibles.")
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            raise

if __name__ == "__main__":
    fix_missing_columns()
