# backend/app/api/v1/alertas_routes.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db import crud_alertas
from app.schemas.alerta_schema import AlertaCreate, AlertaResponse, AlertaUpdate
from app.core.auth import get_current_user
from app.db.models import User

router = APIRouter(prefix="/alertas", tags=["alertas"])

@router.post("/", response_model=AlertaResponse)
def create_alerta(
    alerta: AlertaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva alerta"""
    return crud_alertas.create_alerta(db=db, alerta=alerta, usuario_id=current_user.id)

@router.get("/", response_model=List[AlertaResponse])
def get_alertas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    ticker: Optional[str] = Query(None),
    tipo_alerta: Optional[str] = Query(None),
    leida: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de alertas con filtros opcionales"""
    return crud_alertas.get_alertas(db=db, skip=skip, limit=limit, ticker=ticker, tipo_alerta=tipo_alerta, leida=leida)

@router.get("/{alerta_id}", response_model=AlertaResponse)
def get_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener una alerta específica por ID"""
    alerta = crud_alertas.get_alerta(db=db, alerta_id=alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta

@router.put("/{alerta_id}", response_model=AlertaResponse)
def update_alerta(
    alerta_id: int,
    alerta_update: AlertaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una alerta"""
    alerta = crud_alertas.update_alerta(db=db, alerta_id=alerta_id, alerta_update=alerta_update)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alerta

@router.delete("/{alerta_id}")
def delete_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Eliminar una alerta"""
    alerta = crud_alertas.delete_alerta(db=db, alerta_id=alerta_id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta eliminada exitosamente"}

@router.get("/no-leidas/", response_model=List[AlertaResponse])
def get_alertas_no_leidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas no leídas"""
    return crud_alertas.get_alertas_no_leidas(db=db)

@router.post("/marcar-leidas/")
def marcar_alertas_como_leidas(
    alerta_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Marcar múltiples alertas como leídas"""
    crud_alertas.marcar_alertas_como_leidas(db=db, alerta_ids=alerta_ids)
    return {"message": f"{len(alerta_ids)} alertas marcadas como leídas"}

@router.get("/ticker/{ticker}", response_model=List[AlertaResponse])
def get_alertas_por_ticker(
    ticker: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas de un ticker específico"""
    return crud_alertas.get_alertas_por_ticker(db=db, ticker=ticker)

@router.get("/usuario/mis-alertas", response_model=List[AlertaResponse])
def get_mis_alertas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener todas las alertas del usuario actual"""
    return crud_alertas.get_alertas_por_usuario(db=db, usuario_id=current_user.id)

