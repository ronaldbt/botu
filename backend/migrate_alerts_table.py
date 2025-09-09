#!/usr/bin/env python3
"""
Migration script to update the alerts table with new profit tracking columns
"""

from sqlalchemy import create_engine, text, inspect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:your_password@localhost/botu')

def migrate_alerts_table():
    """Add new columns to the alerts table for profit tracking"""
    engine = create_engine(DATABASE_URL)
    
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('alertas')]
    
    with engine.connect() as connection:
        # Rename precio_actual to precio_entrada if it exists
        if 'precio_actual' in columns and 'precio_entrada' not in columns:
            print("Renaming precio_actual to precio_entrada...")
            connection.execute(text("ALTER TABLE alertas RENAME COLUMN precio_actual TO precio_entrada"))
            connection.commit()
            
        # Add new columns if they don't exist
        new_columns = [
            ("precio_salida", "ALTER TABLE alertas ADD COLUMN precio_salida FLOAT"),
            ("cantidad", "ALTER TABLE alertas ADD COLUMN cantidad FLOAT"),
            ("profit_usd", "ALTER TABLE alertas ADD COLUMN profit_usd FLOAT"),
            ("profit_percentage", "ALTER TABLE alertas ADD COLUMN profit_percentage FLOAT"),
            ("fecha_cierre", "ALTER TABLE alertas ADD COLUMN fecha_cierre TIMESTAMP"),
            ("alerta_buy_id", "ALTER TABLE alertas ADD COLUMN alerta_buy_id INTEGER"),
            ("bot_mode", "ALTER TABLE alertas ADD COLUMN bot_mode VARCHAR(50)"),
        ]
        
        for column_name, sql_command in new_columns:
            if column_name not in columns:
                print(f"Adding column {column_name}...")
                try:
                    connection.execute(text(sql_command))
                    connection.commit()
                    print(f"✅ Added column {column_name}")
                except Exception as e:
                    print(f"❌ Error adding column {column_name}: {e}")
            else:
                print(f"⚠️  Column {column_name} already exists, skipping...")
        
        print("\n🎉 Alert table migration completed!")

if __name__ == "__main__":
    migrate_alerts_table()