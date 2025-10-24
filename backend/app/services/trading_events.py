from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
import json
import logging

logger = logging.getLogger(__name__)


def _create_event(
    db: Session,
    *,
    event_type: str,
    order: Optional[models.TradingOrder] = None,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    symbol: str,
    side: Optional[str] = None,
    quantity: Optional[float] = None,
    price: Optional[float] = None,
    total_usdt: Optional[float] = None,
    pnl_usdt: Optional[float] = None,
    pnl_percentage: Optional[float] = None,
    source: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> models.TradingEvent:
    """Crea un TradingEvent en estado PENDING"""
    event = models.TradingEvent(
        event_type=event_type,
        order_id=order.id if order else None,
        api_key_id=api_key_id or (order.api_key_id if order else None),
        user_id=user_id or (order.user_id if order else None),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        total_usdt=total_usdt,
        pnl_usdt=pnl_usdt,
        pnl_percentage=pnl_percentage,
        source=source,
        payload=json.dumps(payload or {})
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(f"🧾 TradingEvent creado: {event.event_type} #{event.id} {symbol} {side}")
    return event


def publish_order_filled_buy(
    *,
    order: Optional[models.TradingOrder] = None,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    symbol: str,
    quantity: float,
    price: float,
    total_usdt: Optional[float] = None,
    source: str = "executor",
    extra: Optional[Dict[str, Any]] = None,
) -> models.TradingEvent:
    db = SessionLocal()
    try:
        return _create_event(
            db,
            event_type="ORDER_FILLED_BUY",
            order=order,
            user_id=user_id,
            api_key_id=api_key_id,
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            price=price,
            total_usdt=total_usdt,
            source=source,
            payload=extra,
        )
    finally:
        db.close()


def publish_order_filled_sell(
    *,
    order: Optional[models.TradingOrder] = None,
    user_id: Optional[int] = None,
    api_key_id: Optional[int] = None,
    symbol: str,
    quantity: float,
    price: float,
    pnl_usdt: Optional[float] = None,
    pnl_percentage: Optional[float] = None,
    source: str = "executor",
    extra: Optional[Dict[str, Any]] = None,
) -> models.TradingEvent:
    db = SessionLocal()
    try:
        return _create_event(
            db,
            event_type="ORDER_FILLED_SELL",
            order=order,
            user_id=user_id,
            api_key_id=api_key_id,
            symbol=symbol,
            side="SELL",
            quantity=quantity,
            price=price,
            pnl_usdt=pnl_usdt,
            pnl_percentage=pnl_percentage,
            source=source,
            payload=extra,
        )
    finally:
        db.close()


