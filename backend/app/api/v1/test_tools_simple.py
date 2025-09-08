# backend/app/api/v1/test_tools_simple.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_tickers
from app.core.auth import get_current_user
from app.schemas.auth_schema import UserOut
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/test-tools", tags=["test-tools"])

# Modelos Pydantic
class TickerInfo(BaseModel):
    symbol: str
    name: Optional[str]
    type: str

@router.get("/tickers", response_model=List[TickerInfo])
def get_available_tickers_for_test(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene lista de tickers disponibles para backtest"""
    try:
        tickers_db = crud_tickers.get_all_tickers(db)
        crypto_tickers = [
            TickerInfo(
                symbol=t.ticker,
                name=t.nombre or t.ticker,
                type=t.tipo
            ) 
            for t in tickers_db if t.tipo == 'crypto' and t.activo
        ]
        print(f"Found {len(crypto_tickers)} crypto tickers")
        return crypto_tickers
    except Exception as e:
        print(f"Error getting tickers: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tickers: {str(e)}")

@router.get("/health")
def health_check():
    """Verifica que el servicio esté funcionando"""
    return {"status": "ok", "message": "Test tools service is running"}
