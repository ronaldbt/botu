#!/usr/bin/env python3
"""
Script para agregar columnas de BNB Mainnet a la tabla trading_api_keys
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine
from sqlalchemy import text

def add_bnb_mainnet_columns():
    """Agrega las columnas necesarias para BNB Mainnet"""
    
    with engine.connect() as conn:
        try:
            print("🔧 Agregando columnas BNB Mainnet...")
            
            # Agregar bnb_mainnet_enabled
            try:
                conn.execute(text("""
                    ALTER TABLE trading_api_keys 
                    ADD COLUMN IF NOT EXISTS bnb_mainnet_enabled BOOLEAN DEFAULT FALSE;
                """))
                conn.commit()
                print("✅ Columna bnb_mainnet_enabled agregada")
            except Exception as e:
                print(f"⚠️  Columna bnb_mainnet_enabled ya existe o error: {e}")
            
            # Agregar bnb_mainnet_allocated_usdt
            try:
                conn.execute(text("""
                    ALTER TABLE trading_api_keys 
                    ADD COLUMN IF NOT EXISTS bnb_mainnet_allocated_usdt FLOAT DEFAULT 0.0;
                """))
                conn.commit()
                print("✅ Columna bnb_mainnet_allocated_usdt agregada")
            except Exception as e:
                print(f"⚠️  Columna bnb_mainnet_allocated_usdt ya existe o error: {e}")
            
            # Verificar las columnas
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'trading_api_keys' 
                AND column_name IN ('bnb_mainnet_enabled', 'bnb_mainnet_allocated_usdt');
            """))
            columns = [row[0] for row in result]
            
            print("\n📊 Columnas BNB Mainnet en la tabla:")
            for col in columns:
                print(f"   ✅ {col}")
            
            if len(columns) == 2:
                print("\n🎉 ¡Migración completada exitosamente!")
            else:
                print(f"\n⚠️  Solo se encontraron {len(columns)}/2 columnas. Verifica manualmente.")
                
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: Agregar columnas BNB Mainnet")
    print("=" * 60)
    add_bnb_mainnet_columns()
    print("=" * 60)

