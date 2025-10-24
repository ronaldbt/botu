"""
API Routes para Historial de Órdenes Mainnet
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import TradingOrder, TradingApiKey
from app.core.auth import get_current_user
from app.db.models import User
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/mainnet/history")
async def get_mainnet_history(
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    system_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el historial de órdenes mainnet para el usuario actual
    """
    try:
        # Obtener API keys del usuario
        api_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True
        ).all()
        
        if not api_keys:
            return {
                "orders": [],
                "total": 0,
                "message": "No hay API keys mainnet activas"
            }
        
        api_key_ids = [api_key.id for api_key in api_keys]
        
        # Obtener órdenes con paginación (todas las criptomonedas mainnet)
        orders_query = db.query(TradingOrder).filter(
            TradingOrder.api_key_id.in_(api_key_ids),
            TradingOrder.symbol.in_(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'PAXGUSDT'])
        )
        
        # Filtrar solo órdenes del sistema si se solicita
        if system_only:
            orders_query = orders_query.filter(
                TradingOrder.reason.in_(['U_PATTERN', 'MANUAL_TRADE', 'EXTERNAL_SELL'])
            )
        
        orders_query = orders_query.order_by(TradingOrder.created_at.desc())
        
        total_orders = orders_query.count()
        orders = orders_query.offset(offset).limit(limit).all()
        
        # Formatear órdenes para el frontend
        formatted_orders = []
        for order in orders:
            # Calcular PnL si es una orden de venta
            pnl = None
            pnl_percent = None
            
            if order.side == 'SELL' and order.status == 'FILLED':
                # Buscar la orden de compra asociada (mismo símbolo)
                buy_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == order.api_key_id,
                    TradingOrder.symbol == order.symbol,  # Mismo símbolo
                    TradingOrder.side == 'BUY',
                    TradingOrder.status.in_(['FILLED', 'COMPLETED']),
                    TradingOrder.created_at < order.created_at
                ).order_by(TradingOrder.created_at.desc()).first()
                
                if buy_order:
                    buy_price = float(buy_order.executed_price or 0)
                    sell_price = float(order.executed_price or 0)
                    quantity = float(order.executed_quantity or 0)
                    
                    if buy_price > 0 and sell_price > 0 and quantity > 0:
                        buy_value = quantity * buy_price
                        sell_value = quantity * sell_price
                        gross_pnl = sell_value - buy_value
                        
                        # Comisiones (0.1% por operación)
                        commission_rate = 0.001
                        total_commission = (buy_value + sell_value) * commission_rate
                        net_pnl = gross_pnl - total_commission
                        pnl_percent = (net_pnl / buy_value * 100) if buy_value > 0 else 0
                        pnl = net_pnl
            
            # Determinar si es una orden del sistema o externa
            is_system_order = order.reason in ['U_PATTERN', 'MANUAL_TRADE', 'EXTERNAL_SELL']
            
            formatted_orders.append({
                "id": order.id,
                "date": order.created_at.isoformat() if order.created_at else None,
                "symbol": order.symbol,
                "type": order.side,
                "quantity": float(order.executed_quantity or 0),
                "price": float(order.executed_price or 0),
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "status": order.status,
                "binance_order_id": order.binance_order_id,
                "reason": order.reason,
                "is_system_order": is_system_order,
                "source": "Sistema" if is_system_order else "Externa"
            })
        
        logger.info(f"📊 Historial mainnet obtenido: {len(formatted_orders)} órdenes")
        
        return {
            "orders": formatted_orders,
            "total": total_orders,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_orders
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo historial mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.get("/mainnet/positions")
async def get_mainnet_positions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las posiciones abiertas mainnet para el usuario actual
    """
    try:
        # Obtener API keys del usuario
        api_keys = db.query(TradingApiKey).filter(
            TradingApiKey.user_id == current_user.id,
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True
        ).all()
        
        if not api_keys:
            return {
                "positions": [],
                "message": "No hay API keys mainnet activas"
            }
        
        positions = []
        for api_key in api_keys:
            # Buscar órdenes de compra ejecutadas que no están completadas (todas las criptomonedas)
            buy_orders = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key.id,
                TradingOrder.symbol.in_(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'PAXGUSDT']),
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'
            ).order_by(TradingOrder.created_at.desc()).all()
            
            for buy_order in buy_orders:
                # Verificar si ya tiene orden de venta posterior (mismo símbolo)
                sell_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == buy_order.symbol,  # Mismo símbolo
                    TradingOrder.side == 'SELL',
                    TradingOrder.status == 'FILLED',
                    TradingOrder.created_at > buy_order.created_at
                ).order_by(TradingOrder.created_at.asc()).first()
                
                # Si no hay venta, es una posición abierta
                if not sell_order:
                    positions.append({
                        "id": buy_order.id,
                        "symbol": buy_order.symbol,
                        "side": buy_order.side,
                        "quantity": float(buy_order.executed_quantity or 0),
                        "entry_price": float(buy_order.executed_price or 0),
                        "entry_value": float(buy_order.executed_quantity or 0) * float(buy_order.executed_price or 0),
                        "created_at": buy_order.created_at.isoformat() if buy_order.created_at else None,
                        "binance_order_id": buy_order.binance_order_id
                    })
        
        logger.info(f"📊 Posiciones mainnet obtenidas para usuario {current_user.id}: {len(positions)} posiciones")
        
        return {
            "positions": positions,
            "total": len(positions)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo posiciones mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo posiciones: {str(e)}")
