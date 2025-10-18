#!/usr/bin/env python3
"""
Script para verificar órdenes reales en Binance usando credenciales de la base de datos
"""

import asyncio
import sys
import os
import logging

# Agregar el path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_binance_orders():
    """Verifica órdenes en Binance usando credenciales de la base de datos"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingApiKey
        from app.db.crud_trading import get_decrypted_api_credentials
        import requests
        import hmac
        import hashlib
        import time
        from datetime import datetime
        from urllib.parse import urlencode
        
        # Obtener API keys habilitadas para BTC 30m Mainnet
        db = next(get_db())
        api_keys = db.query(TradingApiKey).filter(
            TradingApiKey.is_testnet == False,
            TradingApiKey.btc_30m_mainnet_enabled == True,
            TradingApiKey.is_active == True
        ).all()
        
        if not api_keys:
            logger.warning("No hay API keys habilitadas para BTC 30m Mainnet")
            return
        
        logger.info(f"🔍 Verificando órdenes para {len(api_keys)} API keys")
        
        for api_key in api_keys:
            try:
                logger.info(f"\n📊 Verificando API key {api_key.id}...")
                
                # Obtener credenciales
                creds = get_decrypted_api_credentials(db, api_key.id)
                if not creds:
                    logger.warning(f"No se pudieron obtener credenciales para API key {api_key.id}")
                    continue
                
                key, secret = creds
                
                # Consultar órdenes de los últimos 7 días
                current_time_ms = int(time.time() * 1000)
                end_time = current_time_ms
                start_time = current_time_ms - (7 * 24 * 60 * 60 * 1000)
                
                base_url = "https://api.binance.com"
                endpoint = "/api/v3/allOrders"
                ts = current_time_ms
                
                params = {
                    'symbol': 'BTCUSDT',
                    'timestamp': ts,
                    'recvWindow': 5000
                }
                
                query = urlencode(params)
                signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
                headers = {'X-MBX-APIKEY': key}
                
                url = f"{base_url}{endpoint}?{query}&signature={signature}"
                
                response = requests.get(url, headers=headers, timeout=15)
                response.raise_for_status()
                
                orders = response.json()
                
                # Filtrar solo órdenes ejecutadas
                filled_orders = [order for order in orders if order.get('status') == 'FILLED']
                
                logger.info(f"✅ API key {api_key.id}: {len(filled_orders)} órdenes ejecutadas")
                
                if filled_orders:
                    print(f"\n{'='*80}")
                    print(f"📊 ÓRDENES PARA API KEY {api_key.id}")
                    print(f"{'='*80}")
                    
                    # Separar compras y ventas
                    buy_orders = [o for o in filled_orders if o['side'] == 'BUY']
                    sell_orders = [o for o in filled_orders if o['side'] == 'SELL']
                    
                    print(f"\n🟢 COMPRAS ({len(buy_orders)}):")
                    for i, order in enumerate(buy_orders, 1):
                        timestamp = datetime.fromtimestamp(order['time'] / 1000)
                        # Para órdenes MARKET, usar el precio promedio de los fills
                        if order.get('fills') and len(order['fills']) > 0:
                            total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in order['fills'])
                            quantity = float(order['executedQty'])
                            price = total_cost / quantity if quantity > 0 else 0
                        else:
                            price = float(order['price']) if order['price'] != '0.00000000' else 0
                            quantity = float(order['executedQty'])
                        total = price * quantity
                        
                        # Comisión
                        commission = 0
                        commission_asset = ''
                        if order.get('fills'):
                            for fill in order['fills']:
                                commission += float(fill.get('commission', 0))
                                commission_asset = fill.get('commissionAsset', '')
                        
                        print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"     Precio: ${price:,.2f}")
                        print(f"     Cantidad: {quantity:.8f} BTC")
                        print(f"     Total: ${total:,.2f} USDT")
                        print(f"     Comisión: {commission:.8f} {commission_asset}")
                        print(f"     Orden ID: {order['orderId']}")
                        print()
                    
                    print(f"\n🔴 VENTAS ({len(sell_orders)}):")
                    for i, order in enumerate(sell_orders, 1):
                        timestamp = datetime.fromtimestamp(order['time'] / 1000)
                        # Para órdenes MARKET, usar el precio promedio de los fills
                        if order.get('fills') and len(order['fills']) > 0:
                            total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in order['fills'])
                            quantity = float(order['executedQty'])
                            price = total_cost / quantity if quantity > 0 else 0
                        else:
                            price = float(order['price']) if order['price'] != '0.00000000' else 0
                            quantity = float(order['executedQty'])
                        total = price * quantity
                        
                        # Comisión
                        commission = 0
                        commission_asset = ''
                        if order.get('fills'):
                            for fill in order['fills']:
                                commission += float(fill.get('commission', 0))
                                commission_asset = fill.get('commissionAsset', '')
                        
                        print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"     Precio: ${price:,.2f}")
                        print(f"     Cantidad: {quantity:.8f} BTC")
                        print(f"     Total: ${total:,.2f} USDT")
                        print(f"     Comisión: {commission:.8f} {commission_asset}")
                        print(f"     Orden ID: {order['orderId']}")
                        print()
                    
                    # Análisis de PnL
                    if buy_orders and sell_orders:
                        print(f"\n💰 ANÁLISIS DE GANANCIAS/PÉRDIDAS:")
                        print("-" * 50)
                        
                        # Buscar pares de compra-venta
                        for buy_order in buy_orders:
                            buy_time = buy_order['time']
                            # Calcular precio promedio para compra
                            if buy_order.get('fills') and len(buy_order['fills']) > 0:
                                total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in buy_order['fills'])
                                buy_qty = float(buy_order['executedQty'])
                                buy_price = total_cost / buy_qty if buy_qty > 0 else 0
                            else:
                                buy_price = float(buy_order['price']) if buy_order['price'] != '0.00000000' else 0
                                buy_qty = float(buy_order['executedQty'])
                            buy_total = buy_price * buy_qty
                            
                            # Buscar venta correspondiente (después de la compra)
                            matching_sells = [
                                sell for sell in sell_orders 
                                if sell['time'] > buy_time
                            ]
                            
                            if matching_sells:
                                # Usar la primera venta encontrada
                                sell_order = matching_sells[0]
                                # Calcular precio promedio para venta
                                if sell_order.get('fills') and len(sell_order['fills']) > 0:
                                    total_cost = sum(float(fill['qty']) * float(fill['price']) for fill in sell_order['fills'])
                                    sell_qty = float(sell_order['executedQty'])
                                    sell_price = total_cost / sell_qty if sell_qty > 0 else 0
                                else:
                                    sell_price = float(sell_order['price']) if sell_order['price'] != '0.00000000' else 0
                                    sell_qty = float(sell_order['executedQty'])
                                sell_total = sell_price * sell_qty
                                
                                pnl_usdt = sell_total - buy_total
                                pnl_pct = (pnl_usdt / buy_total) * 100
                                
                                emoji = "📈" if pnl_usdt > 0 else "📉" if pnl_usdt < 0 else "➖"
                                
                                print(f"{emoji} Compra: ${buy_price:,.2f} → Venta: ${sell_price:,.2f}")
                                print(f"   PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
                                print(f"   Compra ID: {buy_order['orderId']}")
                                print(f"   Venta ID: {sell_order['orderId']}")
                                print()
                    
                    print(f"{'='*80}")
                
            except Exception as e:
                logger.error(f"Error verificando API key {api_key.id}: {e}")
        
        logger.info("✅ Verificación completada")
        
    except Exception as e:
        logger.error(f"Error general: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(check_binance_orders())
