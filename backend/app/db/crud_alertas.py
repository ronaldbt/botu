# backend/app/db/crud_alertas.py

from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.db import models
from app.schemas.alerta_schema import AlertaCreate, AlertaUpdate
from typing import List, Optional
from datetime import datetime

def create_alerta(db: Session, alerta: AlertaCreate, usuario_id: Optional[int] = None):
    """Crear una nueva alerta"""
    db_alerta = models.Alerta(
        ticker=alerta.ticker,
        crypto_symbol=alerta.crypto_symbol,
        tipo_alerta=alerta.tipo_alerta,
        mensaje=alerta.mensaje,
        nivel_ruptura=alerta.nivel_ruptura,
        precio_entrada=alerta.precio_entrada,
        precio_salida=alerta.precio_salida,
        cantidad=alerta.cantidad,
        profit_usd=alerta.profit_usd,
        profit_percentage=alerta.profit_percentage,
        alerta_buy_id=alerta.alerta_buy_id,
        bot_mode=alerta.bot_mode,
        usuario_id=usuario_id
    )
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)
    return db_alerta

def get_alerta(db: Session, alerta_id: int):
    """Obtener una alerta por ID"""
    return db.query(models.Alerta).filter(models.Alerta.id == alerta_id).first()

def get_alertas(db: Session, skip: int = 0, limit: int = 100, ticker: Optional[str] = None, tipo_alerta: Optional[str] = None, crypto_symbol: Optional[str] = None, leida: Optional[bool] = None):
    """Obtener lista de alertas con filtros opcionales"""
    query = db.query(models.Alerta)
    
    if ticker:
        query = query.filter(models.Alerta.ticker == ticker)
    if tipo_alerta:
        query = query.filter(models.Alerta.tipo_alerta == tipo_alerta)
    if crypto_symbol:
        query = query.filter(models.Alerta.crypto_symbol == crypto_symbol)
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

def create_buy_alert(db: Session, ticker: str, crypto_symbol: str, precio_entrada: float, cantidad: float, nivel_ruptura: float = None, usuario_id: int = None, bot_mode: str = "manual"):
    """Crear alerta de compra"""
    mensaje = f"🟢 COMPRA {crypto_symbol} - Precio: ${precio_entrada:.4f} - Cantidad: {cantidad:.6f}"
    
    alerta_data = AlertaCreate(
        ticker=ticker,
        crypto_symbol=crypto_symbol,
        tipo_alerta="BUY",
        mensaje=mensaje,
        nivel_ruptura=nivel_ruptura,
        precio_entrada=precio_entrada,
        cantidad=cantidad,
        bot_mode=bot_mode
    )
    
    return create_alerta(db, alerta_data, usuario_id)

def create_sell_alert(db: Session, buy_alert_id: int, precio_salida: float, usuario_id: int = None, bot_mode: str = "manual"):
    """Crear alerta de venta asociada a una compra"""
    # Obtener la alerta de compra
    buy_alert = get_alerta(db, buy_alert_id)
    if not buy_alert or buy_alert.tipo_alerta != "BUY":
        return None
    
    # Calcular profit
    if buy_alert.precio_entrada and buy_alert.cantidad:
        profit_usd = (precio_salida - buy_alert.precio_entrada) * buy_alert.cantidad
        profit_percentage = ((precio_salida - buy_alert.precio_entrada) / buy_alert.precio_entrada) * 100
    else:
        profit_usd = 0
        profit_percentage = 0
    
    # Crear mensaje
    status_emoji = "🟢" if profit_usd > 0 else "🔴" if profit_usd < 0 else "⚪"
    mensaje = f"{status_emoji} VENTA {buy_alert.crypto_symbol} - Precio: ${precio_salida:.4f} - Ganancia: ${profit_usd:.2f} ({profit_percentage:.2f}%)"
    
    alerta_data = AlertaCreate(
        ticker=buy_alert.ticker,
        crypto_symbol=buy_alert.crypto_symbol,
        tipo_alerta="SELL",
        mensaje=mensaje,
        precio_entrada=buy_alert.precio_entrada,
        precio_salida=precio_salida,
        cantidad=buy_alert.cantidad,
        profit_usd=profit_usd,
        profit_percentage=profit_percentage,
        alerta_buy_id=buy_alert_id,
        bot_mode=bot_mode
    )
    
    # Marcar la alerta de venta con fecha de cierre
    sell_alert = create_alerta(db, alerta_data, usuario_id)
    sell_alert.fecha_cierre = datetime.now()
    db.commit()
    db.refresh(sell_alert)
    
    return sell_alert

def get_trading_summary(db: Session, usuario_id: int = None, crypto_symbol: str = None):
    """Obtener resumen de trading con ganancias/pérdidas"""
    query = db.query(models.Alerta).filter(models.Alerta.tipo_alerta == "SELL")
    
    if usuario_id:
        query = query.filter(models.Alerta.usuario_id == usuario_id)
    if crypto_symbol:
        query = query.filter(models.Alerta.crypto_symbol == crypto_symbol)
    
    sell_alerts = query.all()
    
    total_profit = sum(alert.profit_usd for alert in sell_alerts if alert.profit_usd)
    total_operations = len(sell_alerts)
    winning_operations = len([alert for alert in sell_alerts if alert.profit_usd and alert.profit_usd > 0])
    losing_operations = len([alert for alert in sell_alerts if alert.profit_usd and alert.profit_usd < 0])
    
    win_rate = (winning_operations / total_operations * 100) if total_operations > 0 else 0
    
    return {
        "total_profit": total_profit,
        "total_operations": total_operations,
        "winning_operations": winning_operations,
        "losing_operations": losing_operations,
        "win_rate": win_rate,
        "operations": sell_alerts
    }

def get_open_positions(db: Session, usuario_id: int = None, crypto_symbol: str = None):
    """Obtener posiciones abiertas (compras sin venta correspondiente)"""
    query = db.query(models.Alerta).filter(
        models.Alerta.tipo_alerta == "BUY"
    )
    
    if usuario_id:
        query = query.filter(models.Alerta.usuario_id == usuario_id)
    if crypto_symbol:
        query = query.filter(models.Alerta.crypto_symbol == crypto_symbol)
    
    buy_alerts = query.all()
    
    # Filtrar solo las compras que no tienen venta asociada
    open_positions = []
    for buy_alert in buy_alerts:
        sell_alert = db.query(models.Alerta).filter(
            and_(
                models.Alerta.alerta_buy_id == buy_alert.id,
                models.Alerta.tipo_alerta == "SELL"
            )
        ).first()
        
        if not sell_alert:
            open_positions.append(buy_alert)
    
    return open_positions

def get_alertas_count(db: Session):
    """Obtiene el número total de alertas en el sistema"""
    return db.query(models.Alerta).count()

def get_alertas_by_crypto_since(db: Session, crypto_symbol: str, since_date: datetime, limit: int = 50):
    """Obtener alertas de una crypto específica desde una fecha"""
    return (db.query(models.Alerta)
            .filter(models.Alerta.crypto_symbol == crypto_symbol)
            .filter(models.Alerta.fecha_creacion >= since_date)
            .order_by(models.Alerta.fecha_creacion.desc())
            .limit(limit)
            .all())

