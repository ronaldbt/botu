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
from app.services import trading_events

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
        
        # Sistema de reinversión de ganancias
        self.profit_tracking = {}  # Tracking de ganancias por usuario
        self.reinvestment_enabled = True  # Habilitar reinversión automática
    
    async def _calculate_reinvestment_amount(self, api_key_id: int, user_id: int) -> float:
        """
        Calcula cuánto USDT adicional usar de ganancias acumuladas
        """
        try:
            db = SessionLocal()
            
            # Obtener ganancias acumuladas del usuario
            total_profits = 0.0
            
            # Buscar todas las operaciones cerradas con ganancia
            closed_orders = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key_id,
                TradingOrder.side == 'SELL',
                TradingOrder.status == 'FILLED',
                TradingOrder.pnl_usdt > 0  # Solo ganancias
            ).all()
            
            for order in closed_orders:
                if order.pnl_usdt:
                    total_profits += order.pnl_usdt
            
            # Usar máximo 50% de las ganancias acumuladas para reinversión
            reinvestment_amount = total_profits * 0.5
            
            if reinvestment_amount > 0:
                logger.info(f"💰 [REINVERSIÓN] Usuario {user_id}: ${reinvestment_amount:.2f} de ganancias acumuladas disponibles")
                return reinvestment_amount
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculando reinversión: {e}")
            return 0.0
        finally:
            db.close()
    
    async def _log_reinvestment(self, amount: float, user_id: int, crypto: str):
        """
        Log de reinversión de ganancias
        """
        if amount > 0:
            logger.info(f"💰 [REINVERSIÓN] Usuario {user_id} - Usando ${amount:.2f} de ganancias acumuladas para {crypto.upper()}")
            return f"💰 Reinversión: Usando ${amount:.2f} de ganancias acumuladas para nueva compra {crypto.upper()}"
        return None
    
    async def _check_has_open_positions(self, crypto: str, user_id: Optional[int] = None) -> bool:
        """
        Verifica si hay posiciones abiertas para una crypto específica
        Si se especifica user_id, solo verifica para ese usuario
        Si no se especifica, verifica para todos los usuarios
        """
        try:
            from app.db.database import get_db
            from app.db.models import TradingOrder, TradingApiKey
            
            db = next(get_db())
            
            # Mapear crypto a símbolo y campo de habilitación
            crypto_config = {
                'btc': {'symbol': 'BTCUSDT', 'enabled_field': 'btc_4h_mainnet_enabled'},
                'eth': {'symbol': 'ETHUSDT', 'enabled_field': 'eth_mainnet_enabled'},
                'paxg': {'symbol': 'PAXGUSDT', 'enabled_field': 'paxg_4h_mainnet_enabled'},
                'bnb': {'symbol': 'BNBUSDT', 'enabled_field': 'bnb_mainnet_enabled'}
            }
            
            if crypto not in crypto_config:
                return False
            
            config = crypto_config[crypto]
            
            # Verificar si hay posiciones abiertas
            query = db.query(TradingApiKey).filter(
                getattr(TradingApiKey, config['enabled_field']) == True,
                TradingApiKey.is_active == True
            )
            
            # Si se especifica user_id, filtrar por usuario
            if user_id is not None:
                query = query.filter(TradingApiKey.user_id == user_id)
            
            api_keys = query.all()
            
            for api_key in api_keys:
                open_orders = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == config['symbol'],
                    TradingOrder.side == 'BUY',
                    TradingOrder.status == 'FILLED'
                ).all()
                
                if open_orders:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verificando posiciones {crypto}: {e}")
            return False
        finally:
            db.close()
    
    def _get_open_position(self, db: Session, api_key_id: int, symbol: str) -> Optional[TradingOrder]:
        """
        Verifica si hay una posición abierta para un símbolo específico
        """
        try:
            # Buscar posición abierta (BUY ya FILLED y sin SELL posterior)
            buy_order = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key_id,
                TradingOrder.symbol == symbol,
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'
            ).order_by(TradingOrder.created_at.desc()).first()
            
            if buy_order:
                # Verificar si ya tiene orden de venta correspondiente
                sell_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key_id,
                    TradingOrder.symbol == symbol,
                    TradingOrder.side == 'SELL',
                    TradingOrder.status == 'FILLED',
                    TradingOrder.created_at > buy_order.created_at
                ).first()
                
                # Si no hay orden de venta, la posición está abierta
                if not sell_order:
                    return buy_order
            
            return None
            
        except Exception as e:
            logger.error(f"Error verificando posición abierta: {e}")
            return None
        
    async def execute_buy_signal(self, crypto: str, signal_data: Dict, alerta_id: Optional[int] = None):
        """
        Ejecuta una señal de compra automáticamente para todos los usuarios que tengan:
        1. API keys MAINNET configuradas
        2. Auto trading habilitado
        3. La crypto específica habilitada
        4. Sin posiciones abiertas
        
        Args:
            crypto: 'btc', 'eth', 'bnb', 'paxg'
            signal_data: Datos de la señal del scanner (precio, nivel ruptura, etc.)
            alerta_id: ID de la alerta que disparó esta señal
        """
        try:
            # NO verificar posiciones globalmente aquí
            # Cada usuario se verificará individualmente en _execute_user_buy_order
            logger.info(f"🔍 [AUTO TRADING] {crypto.upper()} - Iniciando verificación de compra por usuario")
            
            db = SessionLocal()
            
            # Para BTC 4h, usar lógica específica
            if crypto == 'btc':
                # Buscar usuarios con BTC 4h mainnet habilitado
                mainnet_api_keys = db.query(TradingApiKey).filter(
                    TradingApiKey.is_testnet == False,
                    TradingApiKey.is_active == True,
                    TradingApiKey.btc_4h_mainnet_enabled == True
                ).all()
                
                if not mainnet_api_keys:
                    logger.info(f"📊 No hay usuarios con auto-trading MAINNET habilitado para BTC 4h")
                    db.close()
                    return
                    
                logger.info(f"🚀 [AUTO TRADING MAINNET] Ejecutando señal de compra BTC 4h para {len(mainnet_api_keys)} usuarios")
                logger.info(f"📊 [AUTO TRADING MAINNET] Datos de la señal: {signal_data}")
                
                symbol = "BTCUSDT"
                
                for api_key_config in mainnet_api_keys:
                    try:
                        await self._execute_user_buy_order(
                            db, api_key_config, symbol, signal_data, alerta_id
                        )
                    except Exception as e:
                        logger.error(f"❌ Error ejecutando compra MAINNET para usuario {api_key_config.user_id}: {e}")
                        
            else:
                # Para otras cryptos, usar la lógica original
                enabled_api_keys = crud_trading.get_users_with_auto_trading_enabled(db, crypto)
                
                # Filtrar solo API keys de MAINNET
                mainnet_api_keys = [key for key in enabled_api_keys if not key.is_testnet]
                
                if not mainnet_api_keys:
                    logger.info(f"📊 No hay usuarios con auto-trading MAINNET habilitado para {crypto.upper()}")
                    db.close()
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
            
            # VERIFICAR SI YA TIENE UNA POSICIÓN ABIERTA PARA ESTE SÍMBOLO
            open_position = self._get_open_position(db, api_key_config.id, symbol)
            if open_position:
                logger.info(f"👤 Usuario {user_id}: ya tiene una posición abierta para {symbol} (ID: {open_position.id}) - Saltando nueva compra")
                return
            
            # Verificar límites del usuario
            active_positions = len(crud_trading.get_active_positions(db, user_id))
            if active_positions >= api_key_config.max_concurrent_positions:
                logger.info(f"👤 Usuario {user_id}: máximo de posiciones alcanzado ({active_positions})")
                return
            
            # Obtener cliente de Binance (ya no se usa, eliminado)
            # client = await self._get_binance_client(api_key_config)
            # if not client:
            #     logger.error(f"❌ No se pudo obtener cliente Binance para usuario {user_id}")
            #     return
            
            # Calcular cantidad a comprar
            # Usar campo específico de asignación si existe (ej: btc_4h_mainnet_allocated_usdt)
            crypto_lower = symbol.replace('USDT', '').lower()
            
            # Para BTC, verificar si es BTC 4h (por el contexto del scanner)
            if crypto_lower == 'btc':
                # Verificar si tiene asignación específica para BTC 4h
                if hasattr(api_key_config, 'btc_4h_mainnet_allocated_usdt') and api_key_config.btc_4h_mainnet_allocated_usdt > 0:
                    position_size_usdt = api_key_config.btc_4h_mainnet_allocated_usdt
                else:
                    position_size_usdt = api_key_config.max_position_size_usdt
            else:
                # Para otras cryptos, usar la lógica original
                allocated_field = f"{crypto_lower}_mainnet_allocated_usdt"
                
                if hasattr(api_key_config, allocated_field):
                    position_size_usdt = getattr(api_key_config, allocated_field, 0) or api_key_config.max_position_size_usdt
                else:
                    position_size_usdt = api_key_config.max_position_size_usdt
            
            # Verificar balance de BNB para optimizar comisiones
            balance = await self._get_balance_from_binance(api_key_config)
            bnb_balance = balance.get('BNB', 0.0) if balance else 0.0
            
            if bnb_balance > 0.1:  # Al menos 0.1 BNB para comisiones
                logger.info(f"✅ [AUTO TRADING] Usuario {user_id} tiene {bnb_balance:.3f} BNB - Comisiones optimizadas")
            else:
                logger.warning(f"⚠️ [AUTO TRADING] Usuario {user_id} tiene poco BNB ({bnb_balance:.3f}) - Considera agregar más para comisiones más baratas")
            
            # Calcular reinversión de ganancias si está habilitada
            reinvestment_amount = 0.0
            if self.reinvestment_enabled:
                reinvestment_amount = await self._calculate_reinvestment_amount(api_key_config.id, user_id)
                
                if reinvestment_amount > 0:
                    # Añadir ganancias a la asignación base
                    total_investment = position_size_usdt + reinvestment_amount
                    reinvestment_log = await self._log_reinvestment(reinvestment_amount, user_id, crypto_lower)
                    if reinvestment_log:
                        logger.info(f"💰 [REINVERSIÓN] {reinvestment_log}")
                else:
                    total_investment = position_size_usdt
            else:
                total_investment = position_size_usdt
            
            logger.info(f"💰 [AUTO TRADING] Usuario {user_id} - Asignación {symbol}: ${position_size_usdt:.2f} USDT + Reinversión: ${reinvestment_amount:.2f} USDT = Total: ${total_investment:.2f} USDT")
            
            if total_investment <= 0:
                logger.warning(f"⚠️ Usuario {user_id}: Sin asignación USDT para {symbol}")
                return
            
            current_price = signal_data.get('entry_price', 0)
            
            if current_price <= 0:
                logger.error(f"❌ Precio inválido para {symbol}: {current_price}")
                return
            
            # Usar quoteOrderQty (valor en USDT) en vez de calcular quantity
            # Esto permite a Binance calcular la cantidad exacta y evita problemas de LOT_SIZE
            quote_usdt = float(total_investment)
            
            logger.info(f"💰 [AUTO TRADING] Preparando compra {symbol}: ${quote_usdt:.2f} USDT a precio ~${current_price:.2f}")
            
            # Crear orden en la base de datos PRIMERO (PENDING)
            order_data = TradingOrderCreate(
                api_key_id=api_key_config.id,
                alerta_id=alerta_id,
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quantity=0.0,  # Se definirá por ejecución (quoteOrderQty)
                price=None,
                take_profit_price=None,
                stop_loss_price=None,
                reason='U_PATTERN'
            )
            
            db_order = crud_trading.create_trading_order(db, order_data, user_id)
            
            # Ejecutar orden REAL en Binance
            try:
                # Obtener credenciales
                credentials = crud_trading.get_decrypted_api_credentials(db, api_key_config.id)
                if not credentials:
                    logger.error(f"❌ No se pudieron obtener credenciales para usuario {user_id}")
                    crud_trading.update_trading_order_status(db, db_order.id, 'REJECTED')
                    return
                
                api_key, secret_key = credentials
                
                logger.info(f"🚀 [AUTO TRADING MAINNET] Ejecutando compra REAL usuario {user_id}: {symbol}")
                logger.info(f"💵 [AUTO TRADING MAINNET] Valor: ${quote_usdt:.2f} USDT")
                logger.info(f"🎯 [AUTO TRADING MAINNET] IMPORTANTE: Esta es una orden REAL con DINERO REAL!")
                
                # Ejecutar orden usando quoteOrderQty
                order_result = await self._execute_binance_order_quote(
                    api_key, secret_key, symbol, 'BUY', quote_usdt
                )
                
                if order_result['success']:
                    binance_order = order_result['order']
                    fills = binance_order.get('fills', [])
                    executed_price = float(fills[0].get('price', current_price)) if fills else current_price
                    executed_quantity = float(binance_order.get('executedQty', 0.0))
                    commission = float(fills[0].get('commission', 0.0)) if fills else 0.0
                    commission_asset = fills[0].get('commissionAsset', '') if fills else ''
                    
                    logger.info(f"✅ [AUTO TRADING MAINNET] ORDEN REAL EJECUTADA EN BINANCE MAINNET!")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Binance Order ID: {binance_order.get('orderId')}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Price: ${executed_price:.2f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Quantity: {executed_quantity:.8f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Commission: {commission:.8f} {commission_asset}")
                    
                    # Actualizar orden con datos reales de Binance
                    crud_trading.update_trading_order_status(
                        db, db_order.id, 'FILLED',
                        binance_order_id=binance_order.get('orderId'),
                        executed_price=executed_price,
                        executed_quantity=executed_quantity,
                        commission=commission if commission > 0 else None,
                        commission_asset=commission_asset if commission_asset else None
                    )
                    
                    logger.info(f"✅ MAINNET - Usuario {user_id}: Compra ejecutada {symbol} ${executed_price * executed_quantity:.2f}")
                    # Publicar evento BUY_FILLED desacoplado
                    try:
                        trading_events.publish_order_filled_buy(
                            order=db.query(TradingOrder).filter(TradingOrder.id == db_order.id).first(),
                            symbol=symbol,
                            quantity=executed_quantity,
                            price=executed_price,
                            total_usdt=executed_price * executed_quantity,
                            source="executor",
                            extra={"binance_order_id": binance_order.get('orderId')}
                        )
                    except Exception as pub_err:
                        logger.error(f"⚠️ Error publicando evento BUY_FILLED: {pub_err}")
                    
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
        Simplificado: solo verifica si hay posiciones abiertas
        """
        try:
            # Verificar si hay posiciones abiertas para esta crypto específica
            has_positions = await self._check_has_open_positions(crypto)
            
            if not has_positions:
                logger.info(f"📊 [AUTO TRADING] {crypto.upper()} sin posiciones abiertas - No verificando ventas")
                return
            
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
        """Verifica si una posición individual debe cerrarse con cálculo de PnL preciso"""
        try:
            entry_price = buy_order.executed_price or buy_order.price
            executed_quantity = buy_order.executed_quantity or buy_order.quantity
            
            if not entry_price or not executed_quantity:
                return None
            
            # Obtener configuración del usuario
            db = SessionLocal()
            api_key_config = crud_trading.get_trading_api_key(db, buy_order.api_key_id, buy_order.user_id)
            db.close()
            
            if not api_key_config:
                return None
            
            # Calcular PnL REAL considerando comisiones
            valor_compra_usdt = executed_quantity * entry_price
            
            # Calcular cantidad vendible (restar comisión si fue pagada en crypto)
            cantidad_vendible = executed_quantity
            if buy_order.commission and buy_order.commission > 0:
                # Determinar si la comisión fue en el asset que estamos vendiendo
                symbol_base = buy_order.symbol.replace('USDT', '')  # Ej: BTC, BNB, ETH
                if buy_order.commission_asset == symbol_base:
                    cantidad_vendible -= buy_order.commission
            
            # Valor actual de la posición
            valor_actual_usdt = cantidad_vendible * current_price
            
            # PnL en USDT y porcentaje (PRECISO)
            pnl_usdt = valor_actual_usdt - valor_compra_usdt
            profit_pct = pnl_usdt / valor_compra_usdt
            
            # Log del estado de la posición
            crypto_symbol = buy_order.symbol.replace('USDT', '')
            logger.info(f"💰 Posición {crypto_symbol} ID {buy_order.id}: Invertido ${valor_compra_usdt:.2f} | Valor actual ${valor_actual_usdt:.2f} | PnL ${pnl_usdt:+.2f} ({profit_pct*100:+.2f}%)")
            
            # Verificar Take Profit
            if profit_pct >= api_key_config.profit_target:
                logger.info(f"🎯 TAKE PROFIT {crypto_symbol} ID {buy_order.id}: {profit_pct*100:+.2f}%")
                return "TAKE_PROFIT"
            
            # Verificar Stop Loss
            if profit_pct <= -api_key_config.stop_loss:
                logger.warning(f"🛑 STOP LOSS {crypto_symbol} ID {buy_order.id}: {profit_pct*100:+.2f}%")
                return "STOP_LOSS"
            
            # Verificar tiempo máximo de holding
            if buy_order.executed_at or buy_order.created_at:
                created_time = buy_order.executed_at or buy_order.created_at
                hours_held = (datetime.now() - created_time).total_seconds() / 3600
                if hours_held >= api_key_config.max_hold_hours:
                    logger.warning(f"⏰ MAX HOLD TIME {crypto_symbol} ID {buy_order.id}: {hours_held:.1f}h")
                    return "MAX_HOLD"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error verificando condiciones de salida: {e}")
            return None
    
    async def _execute_exit_order(self, db: Session, buy_order: TradingOrder, current_price: float, reason: str):
        """Ejecuta orden de salida usando balance real de Binance"""
        try:
            user_id = buy_order.user_id
            symbol = buy_order.symbol
            
            # Obtener API key config
            api_key_config = crud_trading.get_trading_api_key(db, buy_order.api_key_id, user_id)
            if not api_key_config:
                return
            
            # Obtener balance real de la crypto disponible (Binance ya maneja las comisiones automáticamente)
            balance = await self._get_balance_from_binance(api_key_config)
            if not balance:
                logger.error(f"❌ No se pudo obtener balance para API key {api_key_config.id}")
                return
            
            # Usar el balance real de la crypto disponible
            symbol_base = symbol.replace('USDT', '').lower()  # Ej: btc, bnb, eth
            sell_quantity = balance.get(symbol_base.upper(), 0.0)
            original_quantity = buy_order.executed_quantity or buy_order.quantity
            
            # Verificar balance de BNB para comisiones optimizadas
            bnb_balance = balance.get('BNB', 0.0)
            bnb_info = f" (BNB: {bnb_balance:.3f})" if bnb_balance > 0 else " (sin BNB - comisiones estándar)"
            
            # Log de comisión de compra para referencia
            if buy_order.commission and buy_order.commission > 0:
                logger.info(f"📊 Comisión de compra pagada en {buy_order.commission_asset}: {buy_order.commission:.8f}")
            
            # Ajustar cantidad según LOT_SIZE de Binance
            import math
            step_size = self._get_step_size_for_symbol(symbol)
            sell_quantity = math.floor(sell_quantity / step_size) * step_size
            
            # Verificar cantidad mínima y valor notional mínimo
            min_notional = 5.0  # $5 USD mínimo en Binance
            order_value = sell_quantity * current_price
            
            if sell_quantity < step_size:
                error_log = f"❌ Balance {symbol_base} insuficiente para vender: {sell_quantity:.8f} {symbol_base} (mínimo: {step_size:.8f})"
                logger.error(error_log)
                return
            
            if order_value < min_notional:
                error_log = f"❌ Valor de orden muy bajo: ${order_value:.2f} (mínimo: ${min_notional:.2f})"
                logger.error(error_log)
                return
            
            logger.info(f"💰 Preparando venta: {sell_quantity:.8f} {symbol_base} @ ${current_price:,.2f} (${order_value:.2f}) - {reason}{bnb_info}")
            
            # Crear orden SELL
            sell_order_data = TradingOrderCreate(
                api_key_id=buy_order.api_key_id,
                alerta_id=None,
                symbol=symbol,
                side='SELL',
                order_type='MARKET',
                quantity=sell_quantity,
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
                    api_key, secret_key, symbol, 'SELL', sell_quantity, False  # Siempre mainnet
                )
                
                if order_result['success']:
                    binance_order = order_result['order']
                    executed_price = float(binance_order.get('fills', [{}])[0].get('price', current_price))
                    executed_quantity = float(binance_order.get('executedQty', sell_quantity))
                    
                    # Extraer comisión de venta
                    sell_commission = 0
                    sell_commission_asset = ""
                    for fill in binance_order.get('fills', []):
                        if 'commission' in fill:
                            sell_commission += float(fill.get('commission', 0))
                            sell_commission_asset = fill.get('commissionAsset', '')
                    
                    logger.info(f"✅ [AUTO TRADING MAINNET] VENTA REAL EJECUTADA EN BINANCE MAINNET!")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Binance Order ID: {binance_order.get('orderId')}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Price: ${executed_price:.2f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Executed Quantity: {executed_quantity:.6f}")
                    logger.info(f"✅ [AUTO TRADING MAINNET] Commission: {sell_commission:.6f} {sell_commission_asset}")
                    
                    # Actualizar orden con datos reales de Binance
                    crud_trading.update_trading_order_status(
                        db, db_sell_order.id, 'FILLED',
                        binance_order_id=binance_order.get('orderId'),
                        executed_price=executed_price,
                        executed_quantity=executed_quantity,
                        commission=sell_commission if sell_commission > 0 else None,
                        commission_asset=sell_commission_asset if sell_commission_asset else None
                    )
                    
                    # Calcular PnL FINAL PRECISO después de todas las comisiones
                    valor_compra_real = buy_order.executed_quantity * buy_order.executed_price
                    valor_venta_real = executed_quantity * executed_price
                    
                    # Si la comisión de venta fue en USDT, restarla
                    if sell_commission > 0 and sell_commission_asset == 'USDT':
                        valor_venta_real -= sell_commission
                    
                    # Guardar PnL preciso
                    pnl_final_usdt = valor_venta_real - valor_compra_real
                    pnl_final_pct = (pnl_final_usdt / valor_compra_real) * 100 if valor_compra_real > 0 else 0
                    
                    # Actualizar campos de PnL en la orden de venta
                    db_sell_order_obj = db.query(TradingOrder).filter(TradingOrder.id == db_sell_order.id).first()
                    if db_sell_order_obj:
                        db_sell_order_obj.pnl_usdt = pnl_final_usdt
                        db_sell_order_obj.pnl_percentage = pnl_final_pct
                        db.commit()
                    
                    # Actualizar orden de compra como completada
                    buy_order.status = 'completed'
                    db.commit()
                    
                    logger.info(f"✅ MAINNET - Usuario {user_id}: {reason} ejecutado - PnL: ${pnl_final_usdt:+.2f} ({pnl_final_pct:+.2f}%)")
                    # Publicar evento SELL_FILLED desacoplado
                    try:
                        trading_events.publish_order_filled_sell(
                            order=db.query(TradingOrder).filter(TradingOrder.id == db_sell_order.id).first(),
                            symbol=symbol,
                            quantity=executed_quantity,
                            price=executed_price,
                            pnl_usdt=pnl_final_usdt,
                            pnl_percentage=pnl_final_pct,
                            source="executor",
                            extra={"reason": reason, "buy_order_id": buy_order.id}
                        )
                    except Exception as pub_err:
                        logger.error(f"⚠️ Error publicando evento SELL_FILLED: {pub_err}")
                    
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
        """Ejecuta una orden real en Binance MAINNET usando HMAC SHA256 con quantity"""
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
            from urllib.parse import urlencode
            query = urlencode(params)
            signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            
            headers = {'X-MBX-APIKEY': api_key}
            
            logger.info(f"📤 [Binance] POST /order {symbol} {side} MARKET qty={quantity:.8f}")
            
            # Enviar orden
            response = requests.post(f"{url}?{query}&signature={signature}", headers=headers, timeout=15)
            
            try:
                data = response.json()
            except:
                data = {'status_code': response.status_code, 'text': response.text}
            
            logger.info(f"[Binance] POST /order {symbol} {side} qty={quantity:.8f} resp={response.status_code} body={data}")
            data['success'] = True if response.status_code == 200 else False
            return data
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden Binance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_binance_order_quote(self, api_key: str, secret_key: str, symbol: str, side: str, quote_usdt: float):
        """Ejecuta una orden en Binance MAINNET usando quoteOrderQty (valor en USDT)"""
        try:
            base_url = "https://api.binance.com"
            endpoint = "/api/v3/order"
            
            # Parámetros de la orden
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quoteOrderQty': f"{float(quote_usdt):.2f}",
                'recvWindow': 5000,
                'timestamp': int(time.time() * 1000)
            }
            
            # Crear signature HMAC SHA256
            from urllib.parse import urlencode
            query = urlencode(params)
            signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            
            headers = {'X-MBX-APIKEY': api_key}
            
            logger.info(f"📤 [Binance] POST /order {symbol} {side} MARKET quoteOrderQty=${quote_usdt:.2f}")
            
            # Enviar orden
            response = requests.post(f"{base_url}{endpoint}?{query}&signature={signature}", headers=headers, timeout=15)
            
            try:
                data = response.json()
            except:
                data = {'status_code': response.status_code, 'text': response.text}
            
            logger.info(f"[Binance] POST /order {symbol} {side} quote=${quote_usdt:.2f} resp={response.status_code} body={data}")
            data['success'] = True if response.status_code == 200 else False
            return data
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando orden Binance: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_step_size_for_symbol(self, symbol: str) -> float:
        """Retorna el step size (LOT_SIZE) según el símbolo"""
        # Step sizes comunes en Binance
        step_sizes = {
            'BTCUSDT': 0.00001,   # 0.00001 BTC
            'ETHUSDT': 0.0001,    # 0.0001 ETH
            'BNBUSDT': 0.01,      # 0.01 BNB
            'SOLUSDT': 0.01,      # 0.01 SOL
        }
        return step_sizes.get(symbol, 0.00001)  # Default: 0.00001
    
    async def _get_balance_from_binance(self, api_key_config: TradingApiKey) -> Optional[Dict]:
        """
        Obtiene balance de la API key desde Binance (incluyendo BNB)
        """
        try:
            # Obtener credenciales desencriptadas
            credentials = crud_trading.get_decrypted_api_credentials(SessionLocal(), api_key_config.id)
            if not credentials:
                return None
            key, secret = credentials

            import hmac, hashlib, time
            from urllib.parse import urlencode
            url = "https://api.binance.com/api/v3/account"
            ts = int(time.time() * 1000)
            params = { 'timestamp': ts }
            query = urlencode(params)
            signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers = { 'X-MBX-APIKEY': key }
            resp = requests.get(f"{url}?{query}&signature={signature}", headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            balances = { b['asset']: float(b['free']) + float(b['locked']) for b in data.get('balances', []) }
            return { 
                'USDT': balances.get('USDT', 0.0), 
                'BTC': balances.get('BTC', 0.0),
                'ETH': balances.get('ETH', 0.0),
                'BNB': balances.get('BNB', 0.0),
                'SOL': balances.get('SOL', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return None
    

# Instancia singleton
auto_trading_executor = AutoTradingExecutor()