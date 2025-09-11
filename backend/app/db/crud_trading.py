# backend/app/db/crud_trading.py

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
import hashlib
import os
from cryptography.fernet import Fernet

from app.db.models import TradingApiKey, TradingOrder, User
from app.schemas.trading_schema import (
    TradingApiKeyCreate, 
    TradingApiKeyUpdate,
    TradingOrderCreate
)

# Clave de encriptación (en producción, debe estar en variables de entorno)
ENCRYPTION_KEY = os.getenv('API_KEY_ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_api_key(api_key: str) -> str:
    """Encripta una API key"""
    return cipher_suite.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_api_key: str) -> str:
    """Desencripta una API key"""
    return cipher_suite.decrypt(encrypted_api_key.encode()).decode()

def mask_api_key(api_key: str) -> str:
    """Enmascara una API key para mostrar solo los primeros 8 caracteres"""
    if len(api_key) <= 8:
        return api_key
    return api_key[:8] + '*' * (len(api_key) - 8)

# --------------------------
# CRUD Trading API Keys
# --------------------------

def create_trading_api_key(db: Session, api_key_data: TradingApiKeyCreate, user_id: int) -> TradingApiKey:
    """Crea una nueva API key de trading para un usuario"""
    
    # Verificar si el usuario ya tiene una API key activa para este exchange/testnet
    existing_key = db.query(TradingApiKey).filter(
        and_(
            TradingApiKey.user_id == user_id,
            TradingApiKey.exchange == api_key_data.exchange,
            TradingApiKey.is_testnet == api_key_data.is_testnet,
            TradingApiKey.is_active == True
        )
    ).first()
    
    if existing_key:
        # Desactivar la key existente
        existing_key.is_active = False
        db.commit()
    
    # Encriptar las keys
    encrypted_api_key = encrypt_api_key(api_key_data.api_key)
    encrypted_secret_key = encrypt_api_key(api_key_data.secret_key)
    
    # Crear nueva API key
    db_api_key = TradingApiKey(
        user_id=user_id,
        exchange=api_key_data.exchange,
        api_key=encrypted_api_key,
        secret_key=encrypted_secret_key,
        is_testnet=api_key_data.is_testnet,
        is_active=api_key_data.is_active,
        auto_trading_enabled=api_key_data.auto_trading_enabled,
        max_position_size_usdt=api_key_data.max_position_size_usdt,
        max_concurrent_positions=api_key_data.max_concurrent_positions,
        risk_percentage=api_key_data.risk_percentage,
        btc_enabled=api_key_data.btc_enabled,
        eth_enabled=api_key_data.eth_enabled,
        bnb_enabled=api_key_data.bnb_enabled,
        profit_target=api_key_data.profit_target,
        stop_loss=api_key_data.stop_loss,
        max_hold_hours=api_key_data.max_hold_hours
    )
    
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def get_user_trading_api_keys(db: Session, user_id: int) -> List[TradingApiKey]:
    """Obtiene todas las API keys de trading de un usuario"""
    return db.query(TradingApiKey).filter(TradingApiKey.user_id == user_id).all()

def get_active_trading_api_key(db: Session, user_id: int, testnet: bool = True) -> Optional[TradingApiKey]:
    """Obtiene la API key activa de un usuario para trading"""
    return db.query(TradingApiKey).filter(
        and_(
            TradingApiKey.user_id == user_id,
            TradingApiKey.is_active == True,
            TradingApiKey.is_testnet == testnet,
            TradingApiKey.auto_trading_enabled == True
        )
    ).first()

def get_trading_api_key(db: Session, api_key_id: int, user_id: int) -> Optional[TradingApiKey]:
    """Obtiene una API key específica de un usuario"""
    return db.query(TradingApiKey).filter(
        and_(
            TradingApiKey.id == api_key_id,
            TradingApiKey.user_id == user_id
        )
    ).first()

def update_trading_api_key(db: Session, api_key_id: int, user_id: int, updates: TradingApiKeyUpdate) -> Optional[TradingApiKey]:
    """Actualiza una API key de trading"""
    db_api_key = get_trading_api_key(db, api_key_id, user_id)
    if not db_api_key:
        return None
    
    update_data = updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_api_key, field, value)
    
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

def delete_trading_api_key(db: Session, api_key_id: int, user_id: int) -> bool:
    """Elimina una API key de trading"""
    db_api_key = get_trading_api_key(db, api_key_id, user_id)
    if not db_api_key:
        return False
    
    db.delete(db_api_key)
    db.commit()
    return True

def update_connection_status(db: Session, api_key_id: int, status: str, error: Optional[str] = None):
    """Actualiza el estado de conexión de una API key"""
    db_api_key = db.query(TradingApiKey).filter(TradingApiKey.id == api_key_id).first()
    if db_api_key:
        db_api_key.connection_status = status
        db_api_key.connection_error = error
        db_api_key.last_balance_check = datetime.now()
        db.commit()

def get_decrypted_api_credentials(db: Session, api_key_id: int) -> Optional[tuple]:
    """Obtiene las credenciales desencriptadas de una API key"""
    db_api_key = db.query(TradingApiKey).filter(TradingApiKey.id == api_key_id).first()
    if not db_api_key:
        return None
    
    try:
        api_key = decrypt_api_key(db_api_key.api_key)
        secret_key = decrypt_api_key(db_api_key.secret_key)
        return (api_key, secret_key)
    except Exception:
        return None

def get_users_with_auto_trading_enabled(db: Session, crypto: str) -> List[TradingApiKey]:
    """Obtiene usuarios con trading automático habilitado para una crypto específica"""
    crypto_field = f"{crypto.lower()}_enabled"
    
    return db.query(TradingApiKey).filter(
        and_(
            TradingApiKey.is_active == True,
            TradingApiKey.auto_trading_enabled == True,
            getattr(TradingApiKey, crypto_field) == True
        )
    ).all()

# --------------------------
# CRUD Trading Orders
# --------------------------

def create_trading_order(db: Session, order_data: TradingOrderCreate, user_id: int) -> TradingOrder:
    """Crea una nueva orden de trading"""
    db_order = TradingOrder(
        user_id=user_id,
        api_key_id=order_data.api_key_id,
        alerta_id=order_data.alerta_id,
        symbol=order_data.symbol,
        side=order_data.side,
        order_type=order_data.order_type,
        quantity=order_data.quantity,
        price=order_data.price,
        take_profit_price=order_data.take_profit_price,
        stop_loss_price=order_data.stop_loss_price,
        reason=order_data.reason
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_user_trading_orders(
    db: Session, 
    user_id: int, 
    limit: int = 100,
    symbol: Optional[str] = None,
    status: Optional[str] = None
) -> List[TradingOrder]:
    """Obtiene las órdenes de trading de un usuario"""
    query = db.query(TradingOrder).filter(TradingOrder.user_id == user_id)
    
    if symbol:
        query = query.filter(TradingOrder.symbol == symbol)
    if status:
        query = query.filter(TradingOrder.status == status)
    
    return query.order_by(desc(TradingOrder.created_at)).limit(limit).all()

def get_active_positions(db: Session, user_id: int) -> List[TradingOrder]:
    """Obtiene las posiciones activas (órdenes BUY sin SELL correspondiente)"""
    return db.query(TradingOrder).filter(
        and_(
            TradingOrder.user_id == user_id,
            TradingOrder.side == 'BUY',
            TradingOrder.status == 'FILLED',
            # No hay una orden SELL correspondiente
            ~db.query(TradingOrder).filter(
                and_(
                    TradingOrder.user_id == user_id,
                    TradingOrder.side == 'SELL',
                    TradingOrder.status == 'FILLED',
                    TradingOrder.symbol == TradingOrder.symbol,
                    TradingOrder.created_at > TradingOrder.created_at
                )
            ).exists()
        )
    ).all()

def update_trading_order_status(
    db: Session, 
    order_id: int, 
    status: str,
    binance_order_id: Optional[str] = None,
    executed_price: Optional[float] = None,
    executed_quantity: Optional[float] = None,
    commission: Optional[float] = None,
    commission_asset: Optional[str] = None
) -> Optional[TradingOrder]:
    """Actualiza el estado de una orden de trading"""
    db_order = db.query(TradingOrder).filter(TradingOrder.id == order_id).first()
    if not db_order:
        return None
    
    db_order.status = status
    if binance_order_id:
        db_order.binance_order_id = binance_order_id
    if executed_price:
        db_order.executed_price = executed_price
    if executed_quantity:
        db_order.executed_quantity = executed_quantity
    if commission:
        db_order.commission = commission
    if commission_asset:
        db_order.commission_asset = commission_asset
    
    if status in ['FILLED', 'PARTIALLY_FILLED']:
        db_order.executed_at = datetime.now()
    
    db.commit()
    db.refresh(db_order)
    return db_order

def calculate_pnl(db: Session, sell_order_id: int) -> Optional[TradingOrder]:
    """Calcula el PnL de una orden de venta"""
    sell_order = db.query(TradingOrder).filter(TradingOrder.id == sell_order_id).first()
    if not sell_order or sell_order.side != 'SELL':
        return None
    
    # Buscar la orden de compra correspondiente
    buy_order = db.query(TradingOrder).filter(
        and_(
            TradingOrder.user_id == sell_order.user_id,
            TradingOrder.symbol == sell_order.symbol,
            TradingOrder.side == 'BUY',
            TradingOrder.status == 'FILLED',
            TradingOrder.executed_at < sell_order.executed_at
        )
    ).order_by(desc(TradingOrder.executed_at)).first()
    
    if buy_order and buy_order.executed_price and sell_order.executed_price:
        pnl_usdt = (sell_order.executed_price - buy_order.executed_price) * sell_order.executed_quantity
        pnl_percentage = (sell_order.executed_price / buy_order.executed_price - 1) * 100
        
        sell_order.pnl_usdt = pnl_usdt
        sell_order.pnl_percentage = pnl_percentage
        
        db.commit()
        db.refresh(sell_order)
    
    return sell_order

def get_trading_statistics(db: Session, user_id: int, days: int = 30) -> dict:
    """Obtiene estadísticas de trading de un usuario"""
    start_date = datetime.now() - timedelta(days=days)
    
    orders = db.query(TradingOrder).filter(
        and_(
            TradingOrder.user_id == user_id,
            TradingOrder.created_at >= start_date,
            TradingOrder.status == 'FILLED'
        )
    ).all()
    
    total_trades = len([o for o in orders if o.side == 'SELL'])
    total_pnl = sum([o.pnl_usdt for o in orders if o.pnl_usdt is not None])
    winning_trades = len([o for o in orders if o.pnl_usdt and o.pnl_usdt > 0])
    
    return {
        'total_orders': len(orders),
        'total_trades': total_trades,
        'total_pnl_usdt': total_pnl,
        'winning_trades': winning_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'active_positions': len(get_active_positions(db, user_id))
    }