# backend/app/services/auto_trading_mainnet30m_executor.py
# Ejecutor de trading automático específico para Bitcoin 30m Mainnet

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import TradingApiKey, TradingOrder
from app.db.crud_trading import create_trading_order, update_trading_order_status, get_decrypted_api_credentials
from app.schemas.trading_schema import TradingOrderCreate
# from app.services.telegram_service import send_telegram_message

logger = logging.getLogger(__name__)

class AutoTradingMainnet30mExecutor:
    """
    Ejecutor de trading automático específico para Bitcoin 30m en Mainnet
    Maneja órdenes de compra/venta con dinero real
    """
    
    def __init__(self):
        self.environment = "mainnet"
        self.crypto_symbol = "BTC_30m"
    
    def _get_open_position(self, db: Session, api_key_id: int) -> Optional[TradingOrder]:
        """
        Verifica si hay una posición abierta (orden de compra sin venta correspondiente)
        """
        try:
            # Buscar posición abierta para BTCUSDT (BUY ya FILLED y sin SELL posterior)
            buy_order = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key_id,
                TradingOrder.symbol == 'BTCUSDT',
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED'
            ).order_by(TradingOrder.created_at.desc()).first()
            
            if buy_order:
                # Verificar si ya tiene orden de venta correspondiente
                sell_order = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key_id,
                    TradingOrder.symbol == 'BTCUSDT',
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
        
    async def execute_buy_order(self, signal: Dict, user_id: Optional[int] = None):
        """
        Ejecuta orden de compra basada en señal del scanner
        """
        try:
            # Obtener API keys de mainnet habilitadas para BTC 30m
            db = next(get_db())
            query = db.query(TradingApiKey).filter(
                TradingApiKey.is_testnet == False,
                TradingApiKey.btc_30m_mainnet_enabled == True,
                TradingApiKey.is_active == True
            )
            if user_id is not None:
                query = query.filter(TradingApiKey.user_id == user_id)
            api_keys = query.all()
            
            if not api_keys:
                logger.warning("No hay API keys de Mainnet habilitadas para BTC 30m")
                return
            
            for api_key in api_keys:
                try:
                    logger.info(f"[Mainnet30mExecutor] Intentando comprar con API key {api_key.id} | alloc_usdt={api_key.btc_30m_mainnet_allocated_usdt}")
                    await self._execute_buy_for_api_key(db, api_key, signal)
                except Exception as e:
                    logger.error(f"Error ejecutando compra para API key {api_key.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error en execute_buy_order Mainnet: {e}")
        finally:
            db.close()
    
    async def _execute_buy_for_api_key(self, db: Session, api_key: TradingApiKey, signal: Dict):
        """
        Ejecuta compra para una API key específica - SOLO si no tiene posición abierta
        """
        try:
            # Verificar que tenga asignación de USDT
            allocated_usdt = api_key.btc_30m_mainnet_allocated_usdt or 0
            if allocated_usdt <= 0:
                logger.warning(f"API key {api_key.id} no tiene USDT asignado para BTC 30m Mainnet")
                return
            
            # VERIFICAR SI YA TIENE UNA POSICIÓN ABIERTA
            open_position = self._get_open_position(db, api_key.id)
            if open_position:
                logger.info(f"API key {api_key.id} ya tiene una posición abierta (ID: {open_position.id}) - Saltando nueva compra")
                return
            
            # Obtener balance actual
            balance = await self._get_balance(api_key)
            if not balance or balance.get('USDT', 0) < allocated_usdt:
                logger.warning(f"Balance insuficiente para API key {api_key.id}: {balance}")
                return
            
            # Monto a invertir en USDT (usaremos quoteOrderQty en MARKET)
            entry_price = signal['entry_price']
            quote_usdt = float(allocated_usdt)
            
            # Crear orden en DB (PENDING)
            new_order = create_trading_order(
                db,
                TradingOrderCreate(
                    api_key_id=api_key.id,
                    alerta_id=None,
                    symbol='BTCUSDT',
                    side='BUY',
                    order_type='MARKET',
                    quantity=0.0,  # se definirá por ejecución (quoteOrderQty)
                    price=None,
                    take_profit_price=None,
                    stop_loss_price=None,
                    reason='U_PATTERN'
                ),
                user_id=api_key.user_id
            )
            
            # Ejecutar orden en Binance
            logger.info(f"[Mainnet30mExecutor] Preparando orden BUY (quote): total={quote_usdt:.2f} USDT")
            binance_result = await self._execute_binance_order(api_key, {
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'type': 'MARKET',
                'quoteOrderQty': quote_usdt
            })
            
            if binance_result and binance_result.get('success'):
                # Normalizar respuesta
                order_id = str(binance_result.get('orderId')) if binance_result.get('orderId') else None
                executed_qty = float(binance_result.get('executedQty', 0.0))
                fills = binance_result.get('fills', [])
                exec_price = float(fills[0].get('price', entry_price)) if fills else entry_price
                commission = float(fills[0].get('commission', 0.0)) if fills else None
                commission_asset = fills[0].get('commissionAsset', None) if fills else None

                update_trading_order_status(
                    db,
                    order_id=new_order.id,
                    status=binance_result.get('status', 'FILLED'),
                    binance_order_id=order_id,
                    executed_price=exec_price,
                    executed_quantity=executed_qty,
                    commission=commission,
                    commission_asset=commission_asset,
                    reason='U_PATTERN'
                )
                await self._send_buy_notification(api_key, {
                    'quantity': executed_qty,
                    'price': exec_price,
                    'total_usdt': quote_usdt,
                    'signal_data': {
                        'signal_strength': signal.get('signal_strength', 0),
                        'pattern_depth': signal.get('depth', 0),
                        'atr': signal.get('atr', 0),
                        'dynamic_factor': signal.get('dynamic_factor', 1.0)
                    }
                }, binance_result)
                logger.info(f"✅ BUY FILLED db_id={new_order.id} binance_id={order_id} qty={executed_qty:.8f} @ {exec_price:.2f}")
                
            else:
                update_trading_order_status(db, order_id=new_order.id, status=binance_result.get('status','REJECTED'), reason=binance_result.get('msg','BINANCE_ORDER_FAILED'))
                logger.error(f"❌ Error ejecutando orden en Binance para API key {api_key.id}: {binance_result}")
                
        except Exception as e:
            logger.error(f"Error en _execute_buy_for_api_key: {e}")
    
    async def _get_balance(self, api_key: TradingApiKey) -> Optional[Dict]:
        """
        Obtiene balance de la API key desde Binance
        """
        try:
            # Obtener credenciales desencriptadas
            db = next(get_db())
            creds = get_decrypted_api_credentials(db, api_key.id)
            if not creds:
                return None
            key, secret = creds

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
            return { 'USDT': balances.get('USDT', 0.0), 'BTC': balances.get('BTC', 0.0) }
            
        except Exception as e:
            logger.error(f"Error obteniendo balance: {e}")
            return None
    
    async def _execute_binance_order(self, api_key: TradingApiKey, order_data: Dict) -> Optional[Dict]:
        """
        Ejecuta orden en Binance
        """
        try:
            import hmac, hashlib, time
            from urllib.parse import urlencode

            base = "https://api.binance.com"
            endpoint = "/api/v3/order"

            # Credenciales desencriptadas
            db = next(get_db())
            creds = get_decrypted_api_credentials(db, api_key.id)
            if not creds:
                return { 'success': False, 'msg': 'NO_CREDENTIALS' }
            key, secret = creds

            ts = int(time.time() * 1000)
            params = {
                'symbol': order_data['symbol'],
                'side': order_data['side'],
                'type': order_data['type'],
                'timestamp': ts,
                'recvWindow': 5000
            }
            if order_data['type'] == 'MARKET':
                if 'quoteOrderQty' in order_data:
                    params['quoteOrderQty'] = f"{float(order_data['quoteOrderQty']):.2f}"
                elif 'quantity' in order_data:
                    params['quantity'] = f"{float(order_data['quantity']):.8f}"

            query = urlencode(params)
            signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers = { 'X-MBX-APIKEY': key }
            resp = requests.post(f"{base}{endpoint}", headers=headers, data=f"{query}&signature={signature}", timeout=15)
            try:
                data = resp.json()
            except Exception:
                data = { 'status_code': resp.status_code, 'text': resp.text }

            logger.info(f"[Binance] POST /order {params['symbol']} {params['side']} {params['type']} qty={params.get('quantity')} quote={params.get('quoteOrderQty')} resp={resp.status_code} body={data}")
            # Normalizar bandera success
            data['success'] = True if resp.status_code == 200 else False
            return data
            
        except Exception as e:
            logger.error(f"Error ejecutando orden en Binance: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _send_buy_notification(self, api_key: TradingApiKey, order_data: Dict, binance_result: Dict):
        """
        Envía notificación de compra por Telegram
        """
        try:
            message = f"""
💰 **COMPRA BTC 30m MAINNET EJECUTADA**

📊 **Detalles de la operación:**
• Cantidad: {order_data['quantity']:.6f} BTC
• Precio: ${order_data['price']:.2f}
• Total: ${order_data['total_usdt']:.2f} USDT
• Orden ID: {binance_result.get('order_id', 'N/A')}

🎯 **Señal del scanner:**
• Fuerza: {order_data['signal_data']['signal_strength']:.3f}
• Profundidad: {order_data['signal_data']['pattern_depth']*100:.2f}%
• ATR: {order_data['signal_data']['atr']:.2f}

⚠️ **AMBIENTE MAINNET - DINERO REAL**
            """
            
            # await send_telegram_message(api_key.user_id, message)
            logger.info(f"📱 Notificación Telegram Mainnet: {message}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación Mainnet: {e}")
    
    async def check_and_execute_sell_orders(self):
        """
        Verifica y ejecuta órdenes de venta pendientes
        """
        try:
            db = next(get_db())
            
            # Obtener órdenes de compra activas para BTC 30m Mainnet
            active_orders = db.query(TradingOrder).filter(
                TradingOrder.crypto == self.crypto_symbol,
                TradingOrder.environment == self.environment,
                TradingOrder.status == 'filled',
                TradingOrder.side == 'buy'
            ).all()
            
            for order in active_orders:
                try:
                    await self._check_sell_conditions(db, order)
                except Exception as e:
                    logger.error(f"Error verificando orden de venta {order.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Error en check_and_execute_sell_orders: {e}")
        finally:
            db.close()
    
    async def _check_sell_conditions(self, db: Session, buy_order: TradingOrder):
        """
        Verifica condiciones de venta para una orden de compra
        """
        try:
            # Obtener API key
            api_key = db.query(TradingApiKey).filter(
                TradingApiKey.id == buy_order.api_key_id
            ).first()
            
            if not api_key or not api_key.btc_30m_mainnet_enabled:
                return
            
            # Obtener precio actual
            current_price = await self._get_current_price()
            if not current_price:
                return
            
            # Calcular ganancia/pérdida
            entry_price = buy_order.price
            profit_pct = (current_price - entry_price) / entry_price
            
            # Verificar condiciones de venta
            profit_target = 0.04  # 4%
            stop_loss = 0.015     # 1.5%
            
            should_sell = False
            sell_reason = ""
            
            if profit_pct >= profit_target:
                should_sell = True
                sell_reason = "TAKE_PROFIT"
            elif profit_pct <= -stop_loss:
                should_sell = True
                sell_reason = "STOP_LOSS"
            
            if should_sell:
                await self._execute_sell_order(db, buy_order, current_price, sell_reason, profit_pct)
                
        except Exception as e:
            logger.error(f"Error en _check_sell_conditions: {e}")
    
    async def _execute_sell_order(self, db: Session, buy_order: TradingOrder, sell_price: float, reason: str, profit_pct: float):
        """
        Ejecuta orden de venta
        """
        try:
            # Obtener API key
            api_key = db.query(TradingApiKey).filter(
                TradingApiKey.id == buy_order.api_key_id
            ).first()
            
            if not api_key:
                return
            
            # Crear orden de venta
            sell_order_data = {
                'user_id': api_key.user_id,
                'api_key_id': api_key.id,
                'crypto': self.crypto_symbol,
                'side': 'sell',
                'order_type': 'market',
                'quantity': buy_order.quantity,
                'price': sell_price,
                'total_usdt': buy_order.quantity * sell_price,
                'environment': self.environment,
                'parent_order_id': buy_order.id
            }
            
            # Ejecutar venta en Binance
            binance_result = await self._execute_binance_order(api_key, sell_order_data)
            
            if binance_result and binance_result.get('success'):
                # Guardar orden de venta
                sell_order = create_trading_order(db, sell_order_data)
                
                # Actualizar orden de compra
                buy_order.status = 'completed'
                buy_order.sell_order_id = sell_order.id
                db.commit()
                
                # Enviar notificación
                await self._send_sell_notification(api_key, buy_order, sell_order_data, profit_pct, reason)
                
                logger.info(f"✅ Venta BTC 30m Mainnet ejecutada: {profit_pct*100:+.2f}% - {reason}")
                
        except Exception as e:
            logger.error(f"Error ejecutando venta: {e}")
    
    async def _get_current_price(self) -> Optional[float]:
        """
        Obtiene precio actual de BTC
        """
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {'symbol': 'BTCUSDT'}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return float(data['price'])
            
        except Exception as e:
            logger.error(f"Error obteniendo precio actual: {e}")
            return None
    
    async def _send_sell_notification(self, api_key: TradingApiKey, buy_order: TradingOrder, sell_order_data: Dict, profit_pct: float, reason: str):
        """
        Envía notificación de venta por Telegram
        """
        try:
            emoji = "💰" if profit_pct > 0 else "📉"
            
            message = f"""
{emoji} **VENTA BTC 30m MAINNET EJECUTADA**

📊 **Resultado de la operación:**
• Ganancia/Pérdida: {profit_pct*100:+.2f}%
• Precio de venta: ${sell_order_data['price']:.2f}
• Cantidad: {sell_order_data['quantity']:.6f} BTC
• Total: ${sell_order_data['total_usdt']:.2f} USDT
• Razón: {reason}

🎯 **Resumen:**
• Precio entrada: ${buy_order.price:.2f}
• Precio salida: ${sell_order_data['price']:.2f}
• Orden ID: {sell_order_data.get('order_id', 'N/A')}

⚠️ **AMBIENTE MAINNET - DINERO REAL**
            """
            
            # await send_telegram_message(api_key.user_id, message)
            logger.info(f"📱 Notificación Telegram Mainnet: {message}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación de venta Mainnet: {e}")
