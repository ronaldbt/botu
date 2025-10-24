#!/usr/bin/env python3
"""
Script para recuperar órdenes de compra de Binance y registrarlas en la base de datos
"""

import asyncio
import logging
import requests
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import urlencode
import sys
import os

# Agregar el path del backend
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingApiKey, TradingOrder, User
from app.db.crud_trading import get_decrypted_api_credentials

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceOrderRecovery:
    """
    Clase para recuperar órdenes de compra de Binance y registrarlas en la base de datos
    """
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
    
    async def get_binance_orders(self, api_key: str, secret_key: str, symbol: str = "BTCUSDT", days_back: int = 7) -> List[Dict]:
        """
        Obtiene órdenes de Binance para un símbolo específico
        """
        try:
            # Calcular timestamps
            current_time = int(time.time() * 1000)
            start_time = current_time - (days_back * 24 * 60 * 60 * 1000)
            
            # Parámetros de la consulta
            params = {
                'symbol': symbol,
                'startTime': start_time,
                'endTime': current_time,
                'timestamp': current_time,
                'recvWindow': 5000
            }
            
            # Crear firma
            query = urlencode(params)
            signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            
            # Headers
            headers = {'X-MBX-APIKEY': api_key}
            
            # URL completa
            url = f"{self.base_url}/api/v3/allOrders?{query}&signature={signature}"
            
            # Realizar consulta
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            orders = response.json()
            logger.info(f"✅ Obtenidas {len(orders)} órdenes de Binance para {symbol}")
            
            return orders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo órdenes de Binance: {e}")
            return []
    
    async def get_binance_trades(self, api_key: str, secret_key: str, symbol: str = "BTCUSDT", days_back: int = 7) -> List[Dict]:
        """
        Obtiene trades de Binance para un símbolo específico
        """
        try:
            # Calcular timestamps
            current_time = int(time.time() * 1000)
            start_time = current_time - (days_back * 24 * 60 * 60 * 1000)
            
            # Parámetros de la consulta
            params = {
                'symbol': symbol,
                'startTime': start_time,
                'endTime': current_time,
                'timestamp': current_time,
                'recvWindow': 5000
            }
            
            # Crear firma
            query = urlencode(params)
            signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            
            # Headers
            headers = {'X-MBX-APIKEY': api_key}
            
            # URL completa
            url = f"{self.base_url}/api/v3/myTrades?{query}&signature={signature}"
            
            # Realizar consulta
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            trades = response.json()
            logger.info(f"✅ Obtenidos {len(trades)} trades de Binance para {symbol}")
            
            return trades
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo trades de Binance: {e}")
            return []
    
    async def recover_orders_for_api_key(self, api_key: TradingApiKey) -> List[Dict]:
        """
        Recupera órdenes para una API key específica
        """
        try:
            db = next(get_db())
            
            # Obtener credenciales
            creds = get_decrypted_api_credentials(db, api_key.id)
            if not creds:
                logger.error(f"No se pudieron obtener credenciales para API key {api_key.id}")
                return []
            
            key, secret = creds
            
            # Determinar símbolos a verificar basado en la configuración
            symbols_to_check = []
            if api_key.btc_30m_mainnet_enabled:
                symbols_to_check.append("BTCUSDT")
            if api_key.bnb_mainnet_enabled:
                symbols_to_check.append("BNBUSDT")
            if api_key.eth_mainnet_enabled:
                symbols_to_check.append("ETHUSDT")
            
            recovered_orders = []
            
            for symbol in symbols_to_check:
                logger.info(f"🔍 Verificando órdenes para {symbol}...")
                
                # Obtener órdenes de Binance
                binance_orders = await self.get_binance_orders(key, secret, symbol, days_back=7)
                
                # Filtrar solo órdenes de compra ejecutadas
                buy_orders = [order for order in binance_orders if 
                             order.get('side') == 'BUY' and 
                             order.get('status') == 'FILLED']
                
                logger.info(f"📊 Encontradas {len(buy_orders)} órdenes de compra ejecutadas para {symbol}")
                
                # Obtener trades para calcular cantidades exactas
                binance_trades = await self.get_binance_trades(key, secret, symbol, days_back=7)
                
                # Procesar cada orden de compra
                for order in buy_orders:
                    order_id = order.get('orderId')
                    symbol_name = order.get('symbol')
                    side = order.get('side')
                    price = float(order.get('price', 0))
                    quantity = float(order.get('executedQty', 0))
                    time_ms = order.get('time')
                    order_time = datetime.fromtimestamp(time_ms / 1000)
                    
                    # Buscar trades correspondientes a esta orden
                    order_trades = [trade for trade in binance_trades if trade.get('orderId') == order_id]
                    
                    if order_trades:
                        # Calcular cantidad total ejecutada y precio promedio
                        total_quantity = sum(float(trade.get('qty', 0)) for trade in order_trades)
                        total_quote = sum(float(trade.get('quoteQty', 0)) for trade in order_trades)
                        avg_price = total_quote / total_quantity if total_quantity > 0 else price
                        
                        # Verificar si ya existe en la base de datos
                        existing_order = db.query(TradingOrder).filter(
                            TradingOrder.binance_order_id == str(order_id),
                            TradingOrder.symbol == symbol_name,
                            TradingOrder.side == side
                        ).first()
                        
                        if not existing_order:
                            # Crear nueva orden en la base de datos
                            new_order = TradingOrder(
                                user_id=api_key.user_id,
                                api_key_id=api_key.id,
                                symbol=symbol_name,
                                side=side,
                                quantity=total_quantity,
                                price=avg_price,
                                total_usdt=total_quote,
                                status='FILLED',
                                binance_order_id=str(order_id),
                                created_at=order_time,
                                updated_at=order_time,
                                source='binance_recovery'
                            )
                            
                            db.add(new_order)
                            db.commit()
                            
                            logger.info(f"✅ Orden recuperada: {symbol_name} {side} - {total_quantity} @ ${avg_price:.2f}")
                            
                            recovered_orders.append({
                                'symbol': symbol_name,
                                'side': side,
                                'quantity': total_quantity,
                                'price': avg_price,
                                'total_usdt': total_quote,
                                'order_id': order_id,
                                'time': order_time
                            })
                        else:
                            logger.info(f"ℹ️ Orden ya existe en DB: {symbol_name} {side} - Order ID: {order_id}")
                    else:
                        logger.warning(f"⚠️ No se encontraron trades para la orden {order_id}")
            
            return recovered_orders
            
        except Exception as e:
            logger.error(f"❌ Error recuperando órdenes para API key {api_key.id}: {e}")
            return []
        finally:
            db.close()
    
    async def recover_all_orders(self):
        """
        Recupera todas las órdenes de todas las API keys activas
        """
        try:
            db = next(get_db())
            
            # Obtener todas las API keys mainnet activas
            api_keys = db.query(TradingApiKey).filter(
                TradingApiKey.is_testnet == False,
                TradingApiKey.is_active == True
            ).all()
            
            logger.info(f"🔍 Recuperando órdenes para {len(api_keys)} API keys")
            
            all_recovered_orders = []
            
            for api_key in api_keys:
                logger.info(f"\n📊 Procesando API key {api_key.id} (Usuario: {api_key.user_id})")
                recovered = await self.recover_orders_for_api_key(api_key)
                all_recovered_orders.extend(recovered)
            
            logger.info(f"\n✅ Recuperación completada: {len(all_recovered_orders)} órdenes recuperadas")
            
            # Mostrar resumen
            if all_recovered_orders:
                print("\n📋 RESUMEN DE ÓRDENES RECUPERADAS:")
                print("=" * 60)
                for order in all_recovered_orders:
                    print(f"🟢 {order['symbol']} {order['side']} - {order['quantity']:.6f} @ ${order['price']:.2f} = ${order['total_usdt']:.2f}")
                    print(f"   Order ID: {order['order_id']} - {order['time']}")
                    print()
            
            return all_recovered_orders
            
        except Exception as e:
            logger.error(f"❌ Error en recuperación general: {e}")
            return []

async def main():
    """
    Función principal
    """
    print("🚀 Iniciando recuperación de órdenes de Binance...")
    print("=" * 60)
    
    recovery = BinanceOrderRecovery()
    recovered_orders = await recovery.recover_all_orders()
    
    if recovered_orders:
        print(f"\n✅ ¡Recuperación exitosa! {len(recovered_orders)} órdenes recuperadas.")
        print("💡 Ahora puedes usar el sistema de trading para vender estas posiciones.")
    else:
        print("\nℹ️ No se encontraron órdenes nuevas para recuperar.")
        print("💡 Verifica que tengas órdenes de compra ejecutadas en Binance en los últimos 7 días.")

if __name__ == "__main__":
    asyncio.run(main())
