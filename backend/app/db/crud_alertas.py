# backend/app/db/crud_alertas.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas.alerta_schema import AlertaCreate, AlertaUpdate
from typing import List, Optional

def create_alerta(db: Session, alerta: AlertaCreate, usuario_id: Optional[int] = None):
    """Crear una nueva alerta"""
    db_alerta = models.Alerta(
        ticker=alerta.ticker,
        tipo_alerta=alerta.tipo_alerta,
        mensaje=alerta.mensaje,
        nivel_ruptura=alerta.nivel_ruptura,
        precio_actual=alerta.precio_actual,
        usuario_id=usuario_id
    )
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)
    return db_alerta

def get_alerta(db: Session, alerta_id: int):
    """Obtener una alerta por ID"""
    return db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()

def get_alertas(db: Session, skip: int = 0, limit: int = 100, ticker: Optional[str] = None, tipo_alerta: Optional[str] = None, leida: Optional[bool] = None):
    """Obtener lista de alertas con filtros opcionales"""
    query = db.query(models.Alerta)
    
    if ticker:
        query = query.filter(models.Alerta.ticker == ticker)
    if tipo_alerta:
        query = query.filter(models.Alerta.tipo_alerta == tipo_alerta)
    if leida is not None:
        query = query.filter(models.Alerta.leida == leida)
    
    return query.order_by(models.Alerta.fecha_creacion.desc()).offset(skip).limit(limit).all()

def update_alerta(db: Session, alerta_id: int, alerta_update: AlertaUpdate):
    """Actualizar una alerta"""
    db_alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not db_alerta:
        return None
    
    for field, value in alerta_update.dict(exclude_unset=True).items():
        setattr(db_alerta, field, value)
    
    db.commit()
    db.refresh(db_alerta)
    return db_alerta

def delete_alerta(db: Session, alerta_id: int):
    """Eliminar una alerta"""
    db_alerta = db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()
    if not db_alerta:
        return None
    
    db.delete(db_alerta)
    db.commit()
    return db_alerta

def get_alertas_no_leidas(db: Session):
    """Obtener todas las alertas no leídas"""
    return db.query(models.Alerta).filter(models.Alerta.leida == False).all()

def marcar_alertas_como_leidas(db: Session, alerta_ids: List[int]):
    """Marcar múltiples alertas como leídas"""
    db.query(models.Alerta).filter(models.Alerta.id.in_(alerta_ids)).update({"leida": True})
    db.commit()

def get_alertas_por_ticker(db: Session, ticker: str):
    """Obtener todas las alertas de un ticker específico"""
    return db.query(models.Alerta).filter(models.Alerta.ticker == ticker).order_by(models.Alerta.fecha_creacion.desc()).all()

def get_alertas_por_usuario(db: Session, usuario_id: int):
    """Obtener todas las alertas de un usuario"""
    return db.query(models.Alerta).filter(models.Alerta.usuario_id == usuario_id).order_by(models.Alerta.fecha_creacion.desc()).all()

