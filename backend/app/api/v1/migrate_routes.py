# backend/app/api/v1/migrate_routes.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import get_current_user
from app.db.models import User
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/migrate", tags=["migrate"])

@router.post("/add-4h-columns")
async def add_4h_columns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint temporal para agregar columnas 4h mainnet"""
    try:
        # Verificar que el usuario sea admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar migraciones")
        
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
        
        added_columns = []
        existing_columns = []
        
        for column_name, column_type in columns_to_add:
            try:
                # Verificar si la columna ya existe
                check_result = db.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'trading_api_keys' 
                    AND column_name = '{column_name}';
                """))
                
                if check_result.fetchone():
                    existing_columns.append(column_name)
                else:
                    # Agregar la columna
                    db.execute(text(f"""
                        ALTER TABLE trading_api_keys 
                        ADD COLUMN {column_name} {column_type};
                    """))
                    db.commit()
                    added_columns.append(column_name)
                    
            except Exception as e:
                logger.error(f"Error con columna {column_name}: {e}")
        
        # Verificar todas las columnas 4h
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'trading_api_keys' 
            AND column_name LIKE '%4h_mainnet%'
            ORDER BY column_name;
        """))
        all_columns = [row[0] for row in result]
        
        return {
            "message": "Migración completada",
            "added_columns": added_columns,
            "existing_columns": existing_columns,
            "total_4h_columns": len(all_columns),
            "all_4h_columns": all_columns
        }
        
    except Exception as e:
        logger.error(f"Error en migración: {e}")
        raise HTTPException(status_code=500, detail=f"Error en migración: {str(e)}")
