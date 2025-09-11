# backend/app/services/auto_trading_executor.py

import logging
import sys
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session

# Add src path for trading modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from app.db.database import SessionLocal
from app.db import crud_trading
from app.db.models import TradingApiKey, TradingOrder
from app.schemas.trading_schema import TradingOrderCreate
from binance_client import BinanceClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoTradingExecutor:
    """
    Ejecutor de trading automático que usa las mismas estrategias probadas
    Se integra con los scanners existentes para ejecutar trades automáticamente
    """
    
    def __init__(self):
        self.active_connections = {}  # Cache de conexiones por usuario
        
    async def execute_buy_signal(self, crypto: str, signal_data: Dict, alerta_id: Optional[int] = None):
        """
        Ejecuta una señal de compra automáticamente para todos los usuarios que tengan:
        1. API keys configuradas
        2. Auto trading habilitado
        3. La crypto específica habilitada
        
        Args:
            crypto: 'btc', 'eth', 'bnb'
            signal_data: Datos de la señal del scanner (precio, nivel ruptura, etc.)
            alerta_id: ID de la alerta que disparó esta señal
        """
        try:
            db = SessionLocal()
            
            # Obtener usuarios con auto-trading habilitado para esta crypto
            enabled_api_keys = crud_trading.get_users_with_auto_trading_enabled(db, crypto)
            
            if not enabled_api_keys:
                logger.info(f"📊 No hay usuarios con auto-trading habilitado para {crypto.upper()}")
                return
                
            logger.info(f"🚀 Ejecutando señal de compra {crypto.upper()} para {len(enabled_api_keys)} usuarios")
            
            symbol = f"{crypto.upper()}USDT"
            
            for api_key_config in enabled_api_keys:
                try:
                    await self._execute_user_buy_order(
                        db, api_key_config, symbol, signal_data, alerta_id
                    )
                except Exception as e:
                    logger.error(f"❌ Error ejecutando compra para usuario {api_key_config.user_id}: {e}")
                    
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error crítico en execute_buy_signal: {e}")
    
    async def _execute_user_buy_order(
        self, 
        db: Session, 
        api_key_config: TradingApiKey, 
        symbol: str, 
        signal_data: Dict,
        alerta_id: Optional[int]
    ):
        """Ejecuta orden de compra para un usuario específico"""
        try:
            user_id = api_key_config.user_id
            
            # Verificar límites del usuario
            active_positions = len(crud_trading.get_active_positions(db, user_id))
            if active_positions >= api_key_config.max_concurrent_positions:
                logger.info(f"👤 Usuario {user_id}: máximo de posiciones alcanzado ({active_positions})")
                return
            
            # Obtener cliente de Binance
            client = await self._get_binance_client(api_key_config)
            if not client:
                logger.error(f"❌ No se pudo obtener cliente Binance para usuario {user_id}")
                return
            
            # Calcular cantidad a comprar
            position_size_usdt = api_key_config.max_position_size_usdt
            current_price = signal_data.get('entry_price', 0)
            
            if current_price <= 0:
                logger.error(f"❌ Precio inválido para {symbol}: {current_price}")
                return
                
            quantity = position_size_usdt / current_price
            
            # Calcular niveles de TP y SL usando la estrategia probada
            take_profit_price = current_price * (1 + api_key_config.profit_target)  # 8% TP
            stop_loss_price = current_price * (1 - api_key_config.stop_loss)       # 3% SL
            
            # Crear orden en la base de datos PRIMERO
            order_data = TradingOrderCreate(
                api_key_id=api_key_config.id,
                alerta_id=alerta_id,
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quantity=quantity,
                take_profit_price=take_profit_price,
                stop_loss_price=stop_loss_price,
                reason='U_PATTERN'
            )
            
            db_order = crud_trading.create_trading_order(db, order_data, user_id)
            
            # Ejecutar orden en Binance
            try:
                # Si es testnet o modo simulación, solo simular
                if api_key_config.is_testnet:
                    logger.info(f"📊 TESTNET - Simulando compra usuario {user_id}: {quantity:.6f} {symbol} @ ${current_price:.2f}")
                    
                    # Simular orden ejecutada
                    crud_trading.update_trading_order_status(
                        db, db_order.id, 'FILLED',
                        binance_order_id=f"TESTNET_{db_order.id}",
                        executed_price=current_price,
                        executed_quantity=quantity
                    )
                    
                    logger.info(f"✅ Usuario {user_id}: Posición abierta ${position_size_usdt} - TP: ${take_profit_price:.2f} SL: ${stop_loss_price:.2f}")
                    
                else:
                    # TODO: Implementar ejecución real en mainnet
                    logger.info(f"🚀 MAINNET - Ejecutaría compra usuario {user_id}: {quantity:.6f} {symbol} @ ${current_price:.2f}")
                    
                    # Por ahora simular hasta completar implementación de órdenes reales
                    crud_trading.update_trading_order_status(
                        db, db_order.id, 'FILLED',
                        binance_order_id=f"MAINNET_SIM_{db_order.id}",
                        executed_price=current_price,
                        executed_quantity=quantity
                    )
                    
            except Exception as e:
                logger.error(f"❌ Error ejecutando orden Binance usuario {user_id}: {e}")
                crud_trading.update_trading_order_status(db, db_order.id, 'REJECTED')
                
        except Exception as e:
            logger.error(f"❌ Error en _execute_user_buy_order: {e}")
    
    async def check_exit_conditions(self, crypto: str, current_price: float):
        """
        Verifica condiciones de salida para todas las posiciones abiertas de una crypto
        Usa las mismas condiciones que los scanners: 8% TP, 3% SL, max hold time
        """
        try:
            db = SessionLocal()
            
            # Obtener todas las posiciones activas para esta crypto
            symbol = f"{crypto.upper()}USDT"
            
            # Buscar órdenes BUY ejecutadas sin SELL correspondiente
            active_orders = db.query(TradingOrder).filter(
                TradingOrder.symbol == symbol,
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'
            ).all()
            
            for buy_order in active_orders:
                # Verificar si ya tiene una orden SELL
                existing_sell = db.query(TradingOrder).filter(
                    TradingOrder.user_id == buy_order.user_id,
                    TradingOrder.symbol == symbol,
                    TradingOrder.side == 'SELL',
                    TradingOrder.created_at > buy_order.created_at
                ).first()
                
                if existing_sell:
                    continue  # Ya tiene orden de salida
                
                # Verificar condiciones de salida
                exit_reason = await self._check_single_position_exit(buy_order, current_price)
                if exit_reason:
                    await self._execute_exit_order(db, buy_order, current_price, exit_reason)
            
            db.close()
            
        except Exception as e:
            logger.error(f"❌ Error en check_exit_conditions: {e}")
    
    async def _check_single_position_exit(self, buy_order: TradingOrder, current_price: float) -> Optional[str]:
        """Verifica si una posición individual debe cerrarse"""
        try:
            entry_price = buy_order.executed_price
            if not entry_price:
                return None
            
            # Obtener configuración del usuario
            db = SessionLocal()
            api_key_config = crud_trading.get_trading_api_key(db, buy_order.api_key_id, buy_order.user_id)
            db.close()
            
            if not api_key_config:
                return None
            
            # Verificar Take Profit (8% por defecto)
            take_profit_price = entry_price * (1 + api_key_config.profit_target)
            if current_price >= take_profit_price:
                return "TAKE_PROFIT"
            
            # Verificar Stop Loss (3% por defecto)
            stop_loss_price = entry_price * (1 - api_key_config.stop_loss)
            if current_price <= stop_loss_price:
                return "STOP_LOSS"
            
            # Verificar tiempo máximo de holding (320h = 13.3 días por defecto)
            if buy_order.executed_at:
                hours_held = (datetime.now() - buy_order.executed_at).total_seconds() / 3600
                if hours_held >= api_key_config.max_hold_hours:
                    return "MAX_HOLD"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error verificando condiciones de salida: {e}")
            return None
    
    async def _execute_exit_order(self, db: Session, buy_order: TradingOrder, current_price: float, reason: str):
        """Ejecuta orden de salida"""
        try:
            user_id = buy_order.user_id
            symbol = buy_order.symbol
            
            # Obtener API key config
            api_key_config = crud_trading.get_trading_api_key(db, buy_order.api_key_id, user_id)
            if not api_key_config:
                return
            
            # Crear orden SELL
            sell_order_data = TradingOrderCreate(
                api_key_id=buy_order.api_key_id,
                alerta_id=None,
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=buy_order.executed_quantity,
                reason=reason
            )
            
            db_sell_order = crud_trading.create_trading_order(db, sell_order_data, user_id)
            
            # Ejecutar venta
            if api_key_config.is_testnet:
                logger.info(f"📊 TESTNET - Simulando venta usuario {user_id}: {reason} @ ${current_price:.2f}")
                
                crud_trading.update_trading_order_status(
                    db, db_sell_order.id, 'FILLED',
                    binance_order_id=f"TESTNET_SELL_{db_sell_order.id}",
                    executed_price=current_price,
                    executed_quantity=buy_order.executed_quantity
                )
                
                # Calcular PnL
                crud_trading.calculate_pnl(db, db_sell_order.id)
                
                pnl_pct = ((current_price - buy_order.executed_price) / buy_order.executed_price) * 100
                pnl_usd = (current_price - buy_order.executed_price) * buy_order.executed_quantity
                
                logger.info(f"✅ Usuario {user_id}: {reason} - PnL: {pnl_pct:.2f}% (${pnl_usd:.2f})")
                
            else:
                # TODO: Implementar venta real en mainnet
                logger.info(f"🚀 MAINNET - Ejecutaría venta usuario {user_id}: {reason} @ ${current_price:.2f}")
                
                crud_trading.update_trading_order_status(
                    db, db_sell_order.id, 'FILLED',
                    binance_order_id=f"MAINNET_SELL_SIM_{db_sell_order.id}",
                    executed_price=current_price,
                    executed_quantity=buy_order.executed_quantity
                )
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden de salida: {e}")
    
    async def _get_binance_client(self, api_key_config: TradingApiKey) -> Optional[BinanceClient]:
        """Obtiene cliente de Binance para un usuario"""
        try:
            # Obtener credenciales desencriptadas
            db = SessionLocal()
            credentials = crud_trading.get_decrypted_api_credentials(db, api_key_config.id)
            db.close()
            
            if not credentials:
                logger.error(f"❌ No se pudieron obtener credenciales para API key {api_key_config.id}")
                return None
            
            api_key, secret_key = credentials
            
            # Crear cliente
            client = BinanceClient(api_key, secret_key, testnet=api_key_config.is_testnet)
            
            # Verificar conexión si no se ha hecho recientemente
            success, _ = client.test_connection()
            if not success:
                logger.error(f"❌ Conexión fallida para usuario {api_key_config.user_id}")
                
                # Actualizar estado en DB
                db = SessionLocal()
                crud_trading.update_connection_status(db, api_key_config.id, 'error', 'Connection failed')
                db.close()
                return None
            
            return client
            
        except Exception as e:
            logger.error(f"❌ Error creando cliente Binance: {e}")
            return None

# Instancia singleton
auto_trading_executor = AutoTradingExecutor()