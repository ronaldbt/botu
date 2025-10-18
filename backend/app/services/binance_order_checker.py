# backend/app/services/binance_order_checker.py
# Script para verificar órdenes reales en Binance y arreglar registros

import asyncio
import logging
import requests
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode

from app.db.database import get_db
from app.db.models import TradingApiKey, TradingOrder
from app.db.crud_trading import get_decrypted_api_credentials

logger = logging.getLogger(__name__)

class BinanceOrderChecker:
    """
    Clase para verificar órdenes reales en Binance y sincronizar con la base de datos
    """
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
    
    async def check_all_orders_for_api_key(self, api_key: TradingApiKey) -> List[Dict]:
        """
        Verifica todas las órdenes de BTCUSDT para una API key específica
        """
        try:
            # Obtener credenciales
            db = next(get_db())
            creds = get_decrypted_api_credentials(db, api_key.id)
            if not creds:
                logger.error(f"No se pudieron obtener credenciales para API key {api_key.id}")
                return []
            
            key, secret = creds
            
            # Consultar órdenes de los últimos 7 días
            end_time = int(time.time() * 1000)
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 días atrás
            
            orders = await self._get_binance_orders(key, secret, start_time, end_time)
            
            logger.info(f"✅ Encontradas {len(orders)} órdenes en Binance para API key {api_key.id}")
            
            return orders
            
        except Exception as e:
            logger.error(f"Error verificando órdenes para API key {api_key.id}: {e}")
            return []
        finally:
            db.close()
    
    async def _get_binance_orders(self, api_key: str, secret_key: str, start_time: int, end_time: int) -> List[Dict]:
        """
        Obtiene órdenes de Binance usando la API
        """
        try:
            endpoint = "/api/v3/allOrders"
            ts = int(time.time() * 1000)
            
            params = {
                'symbol': 'BTCUSDT',
                'startTime': start_time,
                'endTime': end_time,
                'timestamp': ts,
                'recvWindow': 5000
            }
            
            query = urlencode(params)
            signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers = {'X-MBX-APIKEY': api_key}
            
            url = f"{self.base_url}{endpoint}?{query}&signature={signature}"
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            orders = response.json()
            
            # Filtrar solo órdenes ejecutadas (FILLED)
            filled_orders = [order for order in orders if order.get('status') == 'FILLED']
            
            return filled_orders
            
        except Exception as e:
            logger.error(f"Error obteniendo órdenes de Binance: {e}")
            return []
    
    async def sync_database_with_binance(self):
        """
        Sincroniza la base de datos con las órdenes reales de Binance
        """
        try:
            db = next(get_db())
            
            # Obtener todas las API keys habilitadas para BTC 30m
            api_keys = db.query(TradingApiKey).filter(
                TradingApiKey.is_testnet == False,
                TradingApiKey.btc_30m_mainnet_enabled == True,
                TradingApiKey.is_active == True
            ).all()
            
            logger.info(f"🔍 Verificando órdenes para {len(api_keys)} API keys")
            
            for api_key in api_keys:
                await self._sync_api_key_orders(db, api_key)
            
            db.commit()
            logger.info("✅ Sincronización completada")
            
        except Exception as e:
            logger.error(f"Error en sincronización: {e}")
        finally:
            db.close()
    
    async def _sync_api_key_orders(self, db, api_key: TradingApiKey):
        """
        Sincroniza órdenes para una API key específica
        """
        try:
            # Obtener órdenes de Binance
            binance_orders = await self.check_all_orders_for_api_key(api_key)
            
            if not binance_orders:
                return
            
            # Agrupar órdenes por tipo (BUY/SELL)
            buy_orders = [o for o in binance_orders if o['side'] == 'BUY']
            sell_orders = [o for o in binance_orders if o['side'] == 'SELL']
            
            logger.info(f"📊 API Key {api_key.id}: {len(buy_orders)} compras, {len(sell_orders)} ventas")
            
            # Procesar cada compra
            for buy_order in buy_orders:
                await self._process_binance_buy_order(db, api_key, buy_order)
            
            # Procesar cada venta
            for sell_order in sell_orders:
                await self._process_binance_sell_order(db, api_key, sell_order)
                
        except Exception as e:
            logger.error(f"Error sincronizando API key {api_key.id}: {e}")
    
    async def _process_binance_buy_order(self, db, api_key: TradingApiKey, binance_order: Dict):
        """
        Procesa una orden de compra de Binance
        """
        try:
            binance_order_id = str(binance_order['orderId'])
            
            # Verificar si ya existe en la base de datos
            existing_order = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key.id,
                TradingOrder.binance_order_id == binance_order_id
            ).first()
            
            if existing_order:
                # Actualizar si es necesario
                if existing_order.status != 'FILLED':
                    existing_order.status = 'FILLED'
                    existing_order.executed_price = float(binance_order['fills'][0]['price']) if binance_order.get('fills') else float(binance_order['price'])
                    existing_order.executed_quantity = float(binance_order['executedQty'])
                    
                    # Extraer comisión
                    commission = 0
                    commission_asset = ''
                    if binance_order.get('fills'):
                        for fill in binance_order['fills']:
                            commission += float(fill.get('commission', 0))
                            commission_asset = fill.get('commissionAsset', '')
                    
                    existing_order.commission = commission if commission > 0 else None
                    existing_order.commission_asset = commission_asset if commission_asset else None
                    
                    logger.info(f"✅ Actualizada compra: ID {existing_order.id}, Precio: ${existing_order.executed_price:.2f}, Cantidad: {existing_order.executed_quantity:.8f}")
            else:
                # Crear nueva orden en la base de datos
                new_order = TradingOrder(
                    api_key_id=api_key.id,
                    symbol='BTCUSDT',
                    side='buy',
                    order_type='market',
                    quantity=float(binance_order['origQty']),
                    price=float(binance_order['price']) if binance_order['price'] != '0.00000000' else None,
                    status='FILLED',
                    binance_order_id=binance_order_id,
                    executed_price=float(binance_order['fills'][0]['price']) if binance_order.get('fills') else float(binance_order['price']),
                    executed_quantity=float(binance_order['executedQty']),
                    created_at=datetime.fromtimestamp(binance_order['time'] / 1000)
                )
                
                # Extraer comisión
                commission = 0
                commission_asset = ''
                if binance_order.get('fills'):
                    for fill in binance_order['fills']:
                        commission += float(fill.get('commission', 0))
                        commission_asset = fill.get('commissionAsset', '')
                
                new_order.commission = commission if commission > 0 else None
                new_order.commission_asset = commission_asset if commission_asset else None
                
                db.add(new_order)
                logger.info(f"✅ Creada nueva compra: Precio: ${new_order.executed_price:.2f}, Cantidad: {new_order.executed_quantity:.8f}")
                
        except Exception as e:
            logger.error(f"Error procesando compra de Binance: {e}")
    
    async def _process_binance_sell_order(self, db, api_key: TradingApiKey, binance_order: Dict):
        """
        Procesa una orden de venta de Binance
        """
        try:
            binance_order_id = str(binance_order['orderId'])
            
            # Verificar si ya existe en la base de datos
            existing_order = db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key.id,
                TradingOrder.binance_order_id == binance_order_id
            ).first()
            
            if existing_order:
                # Actualizar si es necesario
                if existing_order.status != 'FILLED':
                    existing_order.status = 'FILLED'
                    existing_order.executed_price = float(binance_order['fills'][0]['price']) if binance_order.get('fills') else float(binance_order['price'])
                    existing_order.executed_quantity = float(binance_order['executedQty'])
                    
                    # Extraer comisión
                    commission = 0
                    commission_asset = ''
                    if binance_order.get('fills'):
                        for fill in binance_order['fills']:
                            commission += float(fill.get('commission', 0))
                            commission_asset = fill.get('commissionAsset', '')
                    
                    existing_order.commission = commission if commission > 0 else None
                    existing_order.commission_asset = commission_asset if commission_asset else None
                    
                    logger.info(f"✅ Actualizada venta: ID {existing_order.id}, Precio: ${existing_order.executed_price:.2f}, Cantidad: {existing_order.executed_quantity:.8f}")
            else:
                # Crear nueva orden en la base de datos
                new_order = TradingOrder(
                    api_key_id=api_key.id,
                    symbol='BTCUSDT',
                    side='sell',
                    order_type='market',
                    quantity=float(binance_order['origQty']),
                    price=float(binance_order['price']) if binance_order['price'] != '0.00000000' else None,
                    status='FILLED',
                    binance_order_id=binance_order_id,
                    executed_price=float(binance_order['fills'][0]['price']) if binance_order.get('fills') else float(binance_order['price']),
                    executed_quantity=float(binance_order['executedQty']),
                    created_at=datetime.fromtimestamp(binance_order['time'] / 1000)
                )
                
                # Extraer comisión
                commission = 0
                commission_asset = ''
                if binance_order.get('fills'):
                    for fill in binance_order['fills']:
                        commission += float(fill.get('commission', 0))
                        commission_asset = fill.get('commissionAsset', '')
                
                new_order.commission = commission if commission > 0 else None
                new_order.commission_asset = commission_asset if commission_asset else None
                
                db.add(new_order)
                logger.info(f"✅ Creada nueva venta: Precio: ${new_order.executed_price:.2f}, Cantidad: {new_order.executed_quantity:.8f}")
                
        except Exception as e:
            logger.error(f"Error procesando venta de Binance: {e}")
    
    async def fix_position_3_and_6(self):
        """
        Arregla específicamente las posiciones 3 y 6 que aparecen en los logs
        """
        try:
            db = next(get_db())
            
            # Buscar las posiciones problemáticas
            position_3 = db.query(TradingOrder).filter(TradingOrder.id == 3).first()
            position_6 = db.query(TradingOrder).filter(TradingOrder.id == 6).first()
            
            if position_3:
                logger.info(f"🔍 Procesando posición 3: {position_3.side} - {position_3.status}")
                await self._fix_position(db, position_3)
            
            if position_6:
                logger.info(f"🔍 Procesando posición 6: {position_6.side} - {position_6.status}")
                await self._fix_position(db, position_6)
            
            db.commit()
            logger.info("✅ Posiciones 3 y 6 procesadas")
            
        except Exception as e:
            logger.error(f"Error arreglando posiciones: {e}")
        finally:
            db.close()
    
    async def _fix_position(self, db, position: TradingOrder):
        """
        Arregla una posición específica
        """
        try:
            if position.side == 'buy' and position.status == 'FILLED':
                # Buscar si hay una venta correspondiente en Binance
                api_key = db.query(TradingApiKey).filter(TradingApiKey.id == position.api_key_id).first()
                if api_key:
                    binance_orders = await self.check_all_orders_for_api_key(api_key)
                    
                    # Buscar venta después de esta compra
                    sell_orders = [
                        o for o in binance_orders 
                        if o['side'] == 'SELL' and o['time'] > position.created_at.timestamp() * 1000
                    ]
                    
                    if sell_orders:
                        # Usar la primera venta encontrada
                        sell_order = sell_orders[0]
                        
                        # Crear registro de venta en la base de datos
                        sell_record = TradingOrder(
                            api_key_id=position.api_key_id,
                            symbol='BTCUSDT',
                            side='sell',
                            order_type='market',
                            quantity=float(sell_order['executedQty']),
                            status='FILLED',
                            binance_order_id=str(sell_order['orderId']),
                            executed_price=float(sell_order['fills'][0]['price']) if sell_order.get('fills') else float(sell_order['price']),
                            executed_quantity=float(sell_order['executedQty']),
                            created_at=datetime.fromtimestamp(sell_order['time'] / 1000)
                        )
                        
                        # Calcular PnL
                        valor_compra = position.executed_quantity * position.executed_price
                        valor_venta = sell_record.executed_quantity * sell_record.executed_price
                        pnl_usdt = valor_venta - valor_compra
                        pnl_pct = (pnl_usdt / valor_compra) * 100
                        
                        sell_record.pnl_usdt = pnl_usdt
                        sell_record.pnl_percentage = pnl_pct
                        
                        # Marcar compra como completada
                        position.status = 'completed'
                        position.sell_order_id = sell_record.id
                        
                        db.add(sell_record)
                        
                        logger.info(f"✅ Posición {position.id} arreglada: Venta @ ${sell_record.executed_price:.2f}, PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
                        
        except Exception as e:
            logger.error(f"Error arreglando posición {position.id}: {e}")

# Instancia global
binance_order_checker = BinanceOrderChecker()
