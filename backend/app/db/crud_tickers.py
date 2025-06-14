# app/db/crud_tickers.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas.tickers_schema import TickerCreate, TickerUpdate
from typing import List, Optional

# Obtener todos los tickers ordenados
def get_all_tickers(db: Session) -> List[models.Ticker]:
    return db.query(models.Ticker).order_by(
        models.Ticker.tipo,
        models.Ticker.sub_tipo,
        models.Ticker.ticker
    ).all()

# Obtener un ticker por symbol
def get_ticker(db: Session, ticker_symbol: str) -> Optional[models.Ticker]:
    return db.query(models.Ticker).filter(models.Ticker.ticker == ticker_symbol).first()

# Crear o actualizar un ticker (upsert)
def create_or_update_ticker(db: Session, ticker_data: TickerCreate) -> models.Ticker:
    ticker = db.query(models.Ticker).filter(models.Ticker.ticker == ticker_data.ticker).first()

    if ticker:
        # Update
        ticker.tipo = ticker_data.tipo
        ticker.sub_tipo = ticker_data.sub_tipo
        ticker.pais = ticker_data.pais
        ticker.nombre = ticker_data.nombre
        ticker.activo = ticker_data.activo
    else:
        # Create new
        ticker = models.Ticker(**ticker_data.dict())
        db.add(ticker)

    db.commit()
    db.refresh(ticker)
    return ticker

# Actualizar un ticker parcialmente (con PATCH si usas)
def update_ticker(db: Session, ticker_symbol: str, ticker_update: TickerUpdate) -> Optional[models.Ticker]:
    ticker = db.query(models.Ticker).filter(models.Ticker.ticker == ticker_symbol).first()

    if not ticker:
        return None

    # Actualizar solo campos provistos
    update_data = ticker_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticker, field, value)

    db.commit()
    db.refresh(ticker)
    return ticker

# Eliminar un ticker
def delete_ticker(db: Session, ticker_symbol: str) -> bool:
    ticker = db.query(models.Ticker).filter(models.Ticker.ticker == ticker_symbol).first()
    if ticker:
        db.delete(ticker)
        db.commit()
        return True
    return False
