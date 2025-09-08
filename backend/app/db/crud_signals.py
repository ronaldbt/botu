# app/db/crud_signals.py

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db import models
from app.schemas import u_schema

# Crear una señal
def create_signal(db: Session, signal: u_schema.SignalCreate):
    db_signal = models.Signal(
        ticker=signal.ticker,
        date=signal.date,
        nivel_ruptura=signal.nivel_ruptura,
        slope_left=signal.slope_left,
        precio_cierre=signal.precio_cierre
    )
    db.add(db_signal)
    db.commit()
    db.refresh(db_signal)
    return db_signal

# Obtener señales
def get_signals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Signal).order_by(desc(models.Signal.date)).offset(skip).limit(limit).all()

# Obtener todas las señales
def get_all_signals(db: Session):
    return db.query(models.Signal).order_by(desc(models.Signal.date)).all()
