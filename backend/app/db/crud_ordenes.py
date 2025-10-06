# backend/app/db/crud_ordenes.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas.orden_schema import OrdenCreate, OrdenUpdate
from typing import List, Optional

def create_orden(db: Session, orden: OrdenCreate, usuario_id: Optional[int] = None):
    """Crear una nueva orden"""
    db_orden = models.Orden(
        ticker=orden.ticker,
        tipo_orden=orden.tipo_orden,
        cantidad=orden.cantidad,
        precio=orden.precio,
        motivo=orden.motivo,
        nivel_ruptura=orden.nivel_ruptura,
        usuario_id=usuario_id
    )
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden

def get_orden(db: Session, orden_id: int):
    """Obtener una orden por ID"""
    return db.query(models.Orden).filter(models.Orden.id == orden_id).first()

def get_ordenes(db: Session, skip: int = 0, limit: int = 100, ticker: Optional[str] = None, estado: Optional[str] = None):
    """Obtener lista de órdenes con filtros opcionales"""
    query = db.query(models.Orden)
    
    if ticker:
        query = query.filter(models.Orden.ticker == ticker)
    if estado:
        query = query.filter(models.Orden.estado == estado)
    
    return query.offset(skip).limit(limit).all()

def update_orden(db: Session, orden_id: int, orden_update: OrdenUpdate):
    """Actualizar una orden"""
    db_orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if not db_orden:
        return None
    
    for field, value in orden_update.dict(exclude_unset=True).items():
        setattr(db_orden, field, value)
    
    db.commit()
    db.refresh(db_orden)
    return db_orden

def delete_orden(db: Session, orden_id: int):
    """Eliminar una orden"""
    db_orden = db.query(models.Orden).filter(models.Orden.id == orden_id).first()
    if not db_orden:
        return None
    
    db.delete(db_orden)
    db.commit()
    return db_orden

def get_ordenes_por_ticker(db: Session, ticker: str):
    """Obtener todas las órdenes de un ticker específico"""
    return db.query(models.Orden).filter(models.Orden.ticker == ticker).all()

def get_ordenes_pendientes(db: Session):
    """Obtener todas las órdenes pendientes"""
    return db.query(models.Orden).filter(models.Orden.estado == 'PENDING').all()

def get_ordenes_por_usuario(db: Session, usuario_id: int):
    """Obtener todas las órdenes de un usuario"""
    return db.query(models.Orden).filter(models.Orden.usuario_id == usuario_id).all()

