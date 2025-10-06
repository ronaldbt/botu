# backend/app/services/auto_trading_executor.py

import logging
import os
import hmac
import hashlib
import time
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db import crud_trading
from app.db.models import TradingApiKey, TradingOrder
from app.schemas.trading_schema import TradingOrderCreate

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
        1. API keys MAINNET configuradas
        2. Auto trading habilitado
        3. La crypto específica habilitada
        
        Args:
            crypto: 'btc', 'eth', 'bnb'
            signal_data: Datos de la señal del scanner (precio, nivel ruptura, etc.)
            alerta_id: ID de la alerta que disparó esta señal
        """
        try:
            db = SessionLocal()
            
            # Obtener usuarios con auto-trading habilitado para esta crypto (solo MAINNET)
            enabled_api_keys = crud_trading.get_users_with_auto_trading_enabled(db, crypto)
            
            # Filtrar solo API keys de MAINNET
            mainnet_api_keys = [key for key in enabled_api_keys if not key.is_testnet]
            
            if not mainnet_api_keys:
                logger.info(f"📊 No hay usuarios con auto-trading MAINNET habilitado para {crypto.upper()}")
                return
                
            logger.info(f"🚀 [AUTO TRADING MAINNET] Ejecutando señal de compra {crypto.upper()} para {len(mainnet_api_keys)} usuarios")
            logger.info(f"📊 [AUTO TRADING MAINNET] Datos de la señal: {signal_data}")
            
            symbol = f"{crypto.upper()}USDT"
            
            for api_key_config in mainnet_api_keys:
                try:
                    await self._execute_user_buy_order(
                        db, api_key_config, symbol, signal_data, alerta_id
                    )
                except Exception as e:
                    logger.error(f"❌ Error ejecutando compra MAINNET para usuario {api_key_config.user_id}: {e}")
                    
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
            
            # Ejecutar orden REAL en Binance usando la misma lógica que mainnet30m_executor
            try:
                # Obtener credenciales
                credentials = crud_trading.get_decrypted_api_credentials(db, api_key_config.id)
                if not credentials:
                    logger.error(f"❌ No se pudieron obtener credenciales para usuario {user_id}")
                    crud_trading.update_trading_order_status(db, db_order.id, 'REJECTED')
                    return
                
                api_key, secret_key = credentials
                
                # Ejecutar orden REAL de compra en MAINNET
                logger.info(f"🚀 [AUTO TRADING MAINNET] Ejecutando compra REAL usuario {user_id}")
                logger.info(f"💰 [AUTO TRADING MAINNET] Cantidad: {quantity:.6f} {symbol}")
                logger.info(f"💵 [AUTO TRADING MAINNET] Precio: ${current_price:.2f}")
                logger.info(f"🎯 [AUTO TRADING MAINNET] IMPORTANTE: Esta es una orden REAL con DINERO REAL!")
                
                # Usar la misma función de ejecución que mainnet30m_executor (solo MAINNET)
                order_result = await self._execute_binance_order(
                    api_key, secret_key, symbol, 'BUY', quantity, False  # Siempre mainnet
                )
                
                if order_result['success']:
                    binance_order = order_result['order']
                    executed_price = float(binance_order.get('fills', [{}])[0].get('price', current_price))
                    executed_quantity = float(binance_order.get('executedQty', quantity))
                    commission = sum([float(fill.get('commission', 0)) for fill in binance_order.get('fills', [])])
                    
                    logger.info(f"✅ [AUTO TRADING MAINNET] ORDEN REAL EJECUTADA EN BINANCE MAINNET!")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Binance Order ID: {binance_order.get('orderId')}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Price: ${executed_price:.2f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Quantity: {executed_quantity:.6f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Commission: {commission:.6f}")
                    
                    # Actualizar orden con datos reales de Binance
                    crud_trading.update_trading_order_status(
                        db, db_order.id, 'FILLED',
                        binance_order_id=binance_order.get('orderId'),
                        executed_price=executed_price,
                        executed_quantity=executed_quantity,
                        commission=commission,
                        commission_asset=binance_order.get('fills', [{}])[0].get('commissionAsset', 'BNB')
                    )
                    
                    logger.info(f"✅ MAINNET - Usuario {user_id}: Compra ejecutada ${executed_price * executed_quantity:.2f} - TP: ${take_profit_price:.2f} SL: ${stop_loss_price:.2f}")
                    
                else:
                    # Error en la orden
                    logger.error(f"❌ [AUTO TRADING MAINNET] ERROR EN BINANCE MAINNET usuario {user_id}: {order_result.get('error', 'Unknown error')}")
                    logger.error(f"❌ [AUTO TRADING MAINNET] La orden NO se ejecutó realmente en Binance!")
                    crud_trading.update_trading_order_status(db, db_order.id, 'REJECTED', reason=str(order_result.get('error')))
                    
            except Exception as e:
                logger.error(f"❌ Error ejecutando orden Binance usuario {user_id}: {e}")
                crud_trading.update_trading_order_status(db, db_order.id, 'REJECTED', reason=str(e))
                
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
            
            # Ejecutar venta REAL en Binance MAINNET
            try:
                # Obtener credenciales
                credentials = crud_trading.get_decrypted_api_credentials(db, api_key_config.id)
                if not credentials:
                    logger.error(f"❌ No se pudieron obtener credenciales para venta usuario {user_id}")
                    crud_trading.update_trading_order_status(db, db_sell_order.id, 'REJECTED')
                    return
                
                api_key, secret_key = credentials
                
                # Ejecutar orden REAL de venta en MAINNET
                logger.info(f"🚀 [AUTO TRADING MAINNET] Ejecutando venta REAL usuario {user_id}: {reason}")
                logger.info(f"💰 [AUTO TRADING MAINNET] Cantidad: {buy_order.executed_quantity:.6f} {symbol}")
                logger.info(f"💵 [AUTO TRADING MAINNET] Precio: ${current_price:.2f}")
                logger.info(f"🎯 [AUTO TRADING MAINNET] IMPORTANTE: Esta es una venta REAL con DINERO REAL!")
                
                # Usar la misma función de ejecución que mainnet30m_executor (solo MAINNET)
                order_result = await self._execute_binance_order(
                    api_key, secret_key, symbol, 'SELL', buy_order.executed_quantity, False  # Siempre mainnet
                )
                
                if order_result['success']:
                    binance_order = order_result['order']
                    executed_price = float(binance_order.get('fills', [{}])[0].get('price', current_price))
                    executed_quantity = float(binance_order.get('executedQty', buy_order.executed_quantity))
                    commission = sum([float(fill.get('commission', 0)) for fill in binance_order.get('fills', [])])
                    
                    logger.info(f"✅ [AUTO TRADING MAINNET] VENTA REAL EJECUTADA EN BINANCE MAINNET!")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Binance Order ID: {binance_order.get('orderId')}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Price: ${executed_price:.2f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Quantity: {executed_quantity:.6f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Commission: {commission:.6f}")
                    
                    # Actualizar orden con datos reales de Binance
                    crud_trading.update_trading_order_status(
                        db, db_sell_order.id, 'FILLED',
                        binance_order_id=binance_order.get('orderId'),
                        executed_price=executed_price,
                        executed_quantity=executed_quantity,
                        commission=commission,
                        commission_asset=binance_order.get('fills', [{}])[0].get('commissionAsset', 'BNB')
                    )
                    
                    # Calcular PnL real
                    crud_trading.calculate_pnl(db, db_sell_order.id)
                    
                    pnl_pct = ((executed_price - buy_order.executed_price) / buy_order.executed_price) * 100
                    pnl_usd = (executed_price - buy_order.executed_price) * executed_quantity
                    
                    logger.info(f"✅ MAINNET - Usuario {user_id}: {reason} ejecutado - PnL: {pnl_pct:.2f}% (${pnl_usd:.2f})")
                    
                else:
                    # Error en la orden
                    logger.error(f"❌ [AUTO TRADING MAINNET] ERROR EN BINANCE MAINNET venta usuario {user_id}: {order_result.get('error', 'Unknown error')}")
                    logger.error(f"❌ [AUTO TRADING MAINNET] La venta NO se ejecutó realmente en Binance!")
                    crud_trading.update_trading_order_status(db, db_sell_order.id, 'REJECTED', reason=str(order_result.get('error')))
                    
            except Exception as sell_error:
                logger.error(f"❌ Error ejecutando venta Binance usuario {user_id}: {sell_error}")
                crud_trading.update_trading_order_status(db, db_sell_order.id, 'REJECTED', reason=str(sell_error))
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden de salida: {e}")
    
    async def _execute_binance_order(self, api_key: str, secret_key: str, symbol: str, side: str, quantity: float, is_testnet: bool = False):
        """Ejecuta una orden real en Binance MAINNET usando HMAC SHA256"""
        try:
            # Solo usar mainnet - ignorar parámetro is_testnet
            base_url = "https://api.binance.com"
            endpoint = "/api/v3/order"
            url = f"{base_url}{endpoint}"
            
            # Parámetros de la orden
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': f"{quantity:.8f}",
                'recvWindow': 5000,
                'timestamp': int(time.time() * 1000)
            }
            
            # Crear signature HMAC SHA256
            query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = hmac.new(
                secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params['signature'] = signature
            
            # Headers
            headers = {
                'X-MBX-APIKEY': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            logger.info(f"📤 [Binance MAINNET] Enviando orden {side} {symbol} cantidad {quantity:.8f}")
            logger.info(f"📤 [Binance MAINNET] URL: {url}")
            logger.info(f"📤 [Binance MAINNET] Params: {params}")
            
            # Enviar orden
            response = requests.post(url, data=params, headers=headers, timeout=10)
            
            logger.info(f"📥 [Binance MAINNET] Response status: {response.status_code}")
            logger.info(f"📥 [Binance MAINNET] Response body: {response.text}")
            
            if response.status_code == 200:
                order_data = response.json()
                return {
                    'success': True,
                    'order': order_data
                }
            else:
                error_data = response.json() if response.text else {}
                return {
                    'success': False,
                    'error': error_data.get('msg', f'HTTP {response.status_code}')
                }
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden Binance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    

# Instancia singleton
auto_trading_executor = AutoTradingExecutor()