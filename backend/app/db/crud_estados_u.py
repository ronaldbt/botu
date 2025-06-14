# app/db/crud_estados_u.py

from sqlalchemy.orm import Session
from app.db import models
from app.schemas import estados_u_schema
from datetime import date

# Crear o actualizar estado
def upsert_estado_u(db: Session, estado: estados_u_schema.EstadoUCreate):
    db_estado = db.query(models.EstadoU).filter(models.EstadoU.ticker == estado.ticker).first()

    if db_estado:
        # actualizar
        db_estado.estado_actual = estado.estado_actual
        db_estado.ultima_fecha_escaneo = estado.ultima_fecha_escaneo
        db_estado.proxima_fecha_escaneo = estado.proxima_fecha_escaneo
        db_estado.nivel_ruptura = estado.nivel_ruptura
        db_estado.slope_left = estado.slope_left
        db_estado.precio_cierre = estado.precio_cierre
    else:
        # crear
        db_estado = models.EstadoU(
            ticker=estado.ticker,
            estado_actual=estado.estado_actual,
            ultima_fecha_escaneo=estado.ultima_fecha_escaneo,
            proxima_fecha_escaneo=estado.proxima_fecha_escaneo,
            nivel_ruptura=estado.nivel_ruptura,
            slope_left=estado.slope_left,
            precio_cierre=estado.precio_cierre
        )
        db.add(db_estado)

    db.commit()
    db.refresh(db_estado)
    return db_estado

# Obtener un ticker
def get_estado_u(db: Session, ticker: str):
    return db.query(models.EstadoU).filter(models.EstadoU.ticker == ticker).first()

# Obtener todos los estados simples
def get_all_estados_u(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.EstadoU).offset(skip).limit(limit).all()

# Obtener todos los estados con datos de Ticker (para vista EstadosTickersView)
def get_all_estados_with_tickers(
    db: Session,
    tipo: str = None,
    sub_tipo: str = None,
    pais: str = None,
    estado_actual: str = None,
    skip: int = 0,
    limit: int = 1000
):
    query = db.query(
        models.EstadoU,
        models.Ticker.tipo,
        models.Ticker.sub_tipo,
        models.Ticker.pais
    ).join(models.Ticker, models.EstadoU.ticker == models.Ticker.ticker)

    # Aplicar filtros
    if tipo:
        query = query.filter(models.Ticker.tipo == tipo)
    if sub_tipo:
        query = query.filter(models.Ticker.sub_tipo == sub_tipo)
    if pais:
        query = query.filter(models.Ticker.pais == pais)
    if estado_actual:
        query = query.filter(models.EstadoU.estado_actual == estado_actual)

    # Ordenar por ticker
    query = query.order_by(models.EstadoU.ticker.asc())

    # Aplicar paginación
    results = query.offset(skip).limit(limit).all()

    # Formatear resultados
    estados = []
    for estado_u, tipo, sub_tipo, pais in results:
        estados.append(estados_u_schema.EstadoUWithTickerSchema(
            ticker=estado_u.ticker,
            estado_actual=estado_u.estado_actual,
            ultima_fecha_escaneo=estado_u.ultima_fecha_escaneo,
            proxima_fecha_escaneo=estado_u.proxima_fecha_escaneo,
            nivel_ruptura=estado_u.nivel_ruptura,
            slope_left=estado_u.slope_left,
            precio_cierre=estado_u.precio_cierre,
            tipo=tipo,
            sub_tipo=sub_tipo,
            pais=pais
        ))

    return estados

# Eliminar un ticker
def delete_estado_u(db: Session, ticker: str):
    db_estado = db.query(models.EstadoU).filter(models.EstadoU.ticker == ticker).first()
    if db_estado:
        db.delete(db_estado)
        db.commit()
