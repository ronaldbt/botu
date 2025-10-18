#!/usr/bin/env python3
"""
Script simple para verificar órdenes reales en Binance sin tocar la base de datos
Solo para verificar qué órdenes se ejecutaron realmente
"""

import asyncio
import requests
import hmac
import hashlib
import time
from datetime import datetime
from urllib.parse import urlencode

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleBinanceChecker:
    """Verificador simple de órdenes de Binance"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.binance.com"
    
    async def get_recent_orders(self, days_back: int = 7):
        """Obtiene órdenes de los últimos días"""
        try:
            end_time = int(time.time() * 1000)
            start_time = end_time - (days_back * 24 * 60 * 60 * 1000)
            
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
            signature = hmac.new(self.secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
            headers = {'X-MBX-APIKEY': self.api_key}
            
            url = f"{self.base_url}{endpoint}?{query}&signature={signature}"
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            orders = response.json()
            
            # Filtrar solo órdenes ejecutadas
            filled_orders = [order for order in orders if order.get('status') == 'FILLED']
            
            logger.info(f"✅ Encontradas {len(filled_orders)} órdenes ejecutadas en los últimos {days_back} días")
            
            return filled_orders
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo órdenes: {e}")
            return []
    
    def analyze_orders(self, orders):
        """Analiza las órdenes y muestra información detallada"""
        if not orders:
            logger.info("📊 No hay órdenes ejecutadas")
            return
        
        # Separar compras y ventas
        buy_orders = [o for o in orders if o['side'] == 'BUY']
        sell_orders = [o for o in orders if o['side'] == 'SELL']
        
        logger.info(f"📈 Compras: {len(buy_orders)}")
        logger.info(f"📉 Ventas: {len(sell_orders)}")
        
        print("\n" + "="*80)
        print("📊 ANÁLISIS DE ÓRDENES EN BINANCE")
        print("="*80)
        
        # Mostrar compras
        if buy_orders:
            print(f"\n🟢 COMPRAS ({len(buy_orders)}):")
            for i, order in enumerate(buy_orders, 1):
                timestamp = datetime.fromtimestamp(order['time'] / 1000)
                price = float(order['fills'][0]['price']) if order.get('fills') else float(order['price'])
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
        
        # Mostrar ventas
        if sell_orders:
            print(f"\n🔴 VENTAS ({len(sell_orders)}):")
            for i, order in enumerate(sell_orders, 1):
                timestamp = datetime.fromtimestamp(order['time'] / 1000)
                price = float(order['fills'][0]['price']) if order.get('fills') else float(order['price'])
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
            print("\n💰 ANÁLISIS DE GANANCIAS/PÉRDIDAS:")
            print("-" * 50)
            
            # Buscar pares de compra-venta
            for buy_order in buy_orders:
                buy_time = buy_order['time']
                buy_price = float(buy_order['fills'][0]['price']) if buy_order.get('fills') else float(buy_order['price'])
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
                    sell_price = float(sell_order['fills'][0]['price']) if sell_order.get('fills') else float(sell_order['price'])
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
        
        print("="*80)

async def main():
    """Función principal"""
    print("🔍 Verificador de órdenes Binance")
    print("Este script solo lee las órdenes, no modifica nada")
    print()
    
    # Pedir credenciales al usuario
    print("📝 Necesito tus credenciales de Binance para consultar las órdenes:")
    api_key = input("API Key: ").strip()
    secret_key = input("Secret Key: ").strip()
    
    if not api_key or not secret_key:
        print("❌ Credenciales requeridas")
        return
    
    try:
        checker = SimpleBinanceChecker(api_key, secret_key)
        
        # Obtener órdenes de los últimos 7 días
        orders = await checker.get_recent_orders(days_back=7)
        
        # Analizar y mostrar
        checker.analyze_orders(orders)
        
        print("\n✅ Verificación completada")
        print("💡 Esta información te ayudará a verificar qué órdenes se ejecutaron realmente")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
