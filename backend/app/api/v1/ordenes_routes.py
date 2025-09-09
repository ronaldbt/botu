# backend/app/api/v1/ordenes_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import crud_ordenes
from app.schemas.orden_schema import OrdenCreate, OrdenResponse, OrdenUpdate
from app.core.auth import get_current_user
from app.db.models import User

router = APIRouter(prefix="/ordenes", tags=["ordenes"])

# Cryptocurrencies allowed in the system
ALLOWED_TICKERS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

@router.post("/", response_model=OrdenResponse)
def create_orden(
    orden: OrdenCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva orden - solo BTC, ETH, BNB permitidos"""
    if orden.ticker not in ALLOWED_TICKERS:
        raise HTTPException(
            status_code=400, 
            detail=f"Ticker no permitido. Solo se permiten: {', '.join(ALLOWED_TICKERS)}"
        )
    return crud_ordenes.create_orden(db=db, orden=orden, usuario_id=current_user.id)

@router.get("/", response_model=List[OrdenResponse])
def get_ordenes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ticker: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de órdenes con filtros opcionales"""
    return crud_ordenes.get_ordenes(db=db, skip=skip, limit=limit, ticker=ticker, estado=estado)

@router.get("/{orden_id}", response_model=OrdenResponse)
def get_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener una orden específica por ID"""
    orden = crud_ordenes.get_orden(db=db, orden_id=orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return orden

@router.put("/{orden_id}", response_model=OrdenResponse)
def update_orden(
    orden_id: int,
    orden_update: OrdenUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una orden"""
    orden = crud_ordenes.update_orden(db=db, orden_id=orden_id, orden_update=orden_update)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return orden

@router.delete("/{orden_id}")
def delete_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar una orden"""
    orden = crud_ordenes.delete_orden(db=db, orden_id=orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return {"message": "Orden eliminada exitosamente"}

@router.get("/ticker/{ticker}", response_model=List[OrdenResponse])
def get_ordenes_por_ticker(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las órdenes de un ticker específico"""
    return crud_ordenes.get_ordenes_por_ticker(db=db, ticker=ticker)

@router.get("/pendientes/", response_model=List[OrdenResponse])
def get_ordenes_pendientes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las órdenes pendientes"""
    return crud_ordenes.get_ordenes_pendientes(db=db)

@router.get("/usuario/mis-ordenes", response_model=List[OrdenResponse])
def get_mis_ordenes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las órdenes del usuario actual"""
    return crud_ordenes.get_ordenes_por_usuario(db=db, usuario_id=current_user.id)

@router.get("/tickers-permitidos")
def get_tickers_permitidos(
    current_user: User = Depends(get_current_user)
):
    """Obtener la lista de tickers permitidos en el sistema"""
    return {
        "tickers": ALLOWED_TICKERS,
        "descripcion": "Solo se permiten órdenes para estos tickers"
    }

