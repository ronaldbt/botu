# app/api/v1/tickers_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_tickers
from app.schemas.tickers_schema import TickerOut, TickerCreate, TickerUpdate

router = APIRouter(prefix="/tickers", tags=["tickers"])

# GET /tickers → lista todos los tickers
@router.get("/", response_model=list[TickerOut])
def read_tickers(db: Session = Depends(get_db)):
    """
    Lista todos los tickers en la base de datos.
    """
    return crud_tickers.get_all_tickers(db)

# GET /tickers/{ticker_symbol} → obtener 1 ticker
@router.get("/{ticker_symbol}", response_model=TickerOut)
def read_ticker(ticker_symbol: str, db: Session = Depends(get_db)):
    """
    Obtiene un ticker por symbol.
    """
    ticker = crud_tickers.get_ticker(db, ticker_symbol)
    if not ticker:
        raise HTTPException(status_code=404, detail="Ticker no encontrado")
    return ticker

# POST /tickers → crear o actualizar un ticker (upsert)
@router.post("/", response_model=TickerOut)
def create_or_update_ticker(ticker_data: TickerCreate, db: Session = Depends(get_db)):
    """
    Crea o actualiza un ticker.
    """
    return crud_tickers.create_or_update_ticker(db, ticker_data)

# PUT /tickers/{ticker_symbol} → actualizar parcial un ticker
@router.put("/{ticker_symbol}", response_model=TickerOut)
def update_ticker(ticker_symbol: str, ticker_update: TickerUpdate, db: Session = Depends(get_db)):
    """
    Actualiza parcialmente un ticker.
    """
    updated_ticker = crud_tickers.update_ticker(db, ticker_symbol, ticker_update)
    if not updated_ticker:
        raise HTTPException(status_code=404, detail="Ticker no encontrado para actualizar")
    return updated_ticker

# DELETE /tickers/{ticker_symbol} → eliminar un ticker
@router.delete("/{ticker_symbol}")
def delete_ticker(ticker_symbol: str, db: Session = Depends(get_db)):
    """
    Elimina un ticker.
    """
    deleted = crud_tickers.delete_ticker(db, ticker_symbol)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticker no encontrado para eliminar")
    return {"ok": True}
