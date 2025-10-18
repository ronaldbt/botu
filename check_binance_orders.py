#!/usr/bin/env python3
"""
Script simple para verificar órdenes de Binance sin usar base de datos
"""

import requests
import hmac
import hashlib
import time
import json
from urllib.parse import urlencode

def get_binance_orders(api_key, secret_key, days_back=7):
    """
    Obtiene órdenes de Binance para BTCUSDT
    """
    try:
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/allOrders"
        
        # Calcular timestamps
        end_time = int(time.time() * 1000)
        start_time = end_time - (days_back * 24 * 60 * 60 * 1000)
        
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
        
        url = f"{base_url}{endpoint}?{query}&signature={signature}"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        orders = response.json()
        
        # Filtrar solo órdenes ejecutadas (FILLED)
        filled_orders = [order for order in orders if order.get('status') == 'FILLED']
        
        return filled_orders
        
    except Exception as e:
        print(f"❌ Error obteniendo órdenes: {e}")
        return []

def analyze_orders(orders):
    """
    Analiza las órdenes y muestra un resumen
    """
    if not orders:
        print("📊 No se encontraron órdenes ejecutadas")
        return
    
    # Separar compras y ventas
    buy_orders = [o for o in orders if o['side'] == 'BUY']
    sell_orders = [o for o in orders if o['side'] == 'SELL']
    
    print(f"📊 Resumen de órdenes:")
    print(f"   • Compras: {len(buy_orders)}")
    print(f"   • Ventas: {len(sell_orders)}")
    print()
    
    # Mostrar compras
    if buy_orders:
        print("🟢 COMPRAS:")
        for order in buy_orders:
            executed_qty = float(order['executedQty'])
            fills = order.get('fills', [])
            avg_price = float(fills[0]['price']) if fills else float(order['price'])
            commission = sum(float(fill.get('commission', 0)) for fill in fills)
            commission_asset = fills[0].get('commissionAsset', '') if fills else ''
            
            print(f"   • ID: {order['orderId']}")
            print(f"     Cantidad: {executed_qty:.8f} BTC")
            print(f"     Precio: ${avg_price:.2f}")
            print(f"     Total: ${executed_qty * avg_price:.2f}")
            print(f"     Comisión: {commission:.8f} {commission_asset}")
            print(f"     Fecha: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order['time']/1000))}")
            print()
    
    # Mostrar ventas
    if sell_orders:
        print("🔴 VENTAS:")
        for order in sell_orders:
            executed_qty = float(order['executedQty'])
            fills = order.get('fills', [])
            avg_price = float(fills[0]['price']) if fills else float(order['price'])
            commission = sum(float(fill.get('commission', 0)) for fill in fills)
            commission_asset = fills[0].get('commissionAsset', '') if fills else ''
            
            print(f"   • ID: {order['orderId']}")
            print(f"     Cantidad: {executed_qty:.8f} BTC")
            print(f"     Precio: ${avg_price:.2f}")
            print(f"     Total: ${executed_qty * avg_price:.2f}")
            print(f"     Comisión: {commission:.8f} {commission_asset}")
            print(f"     Fecha: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order['time']/1000))}")
            print()

def main():
    """
    Función principal
    """
    print("🔍 Verificador de órdenes Binance BTC 30m")
    print("=" * 50)
    
    # Solicitar credenciales
    api_key = input("Ingresa tu API Key de Binance: ").strip()
    secret_key = input("Ingresa tu Secret Key de Binance: ").strip()
    
    if not api_key or not secret_key:
        print("❌ Debes ingresar ambas credenciales")
        return
    
    print("\n📊 Consultando órdenes de Binance...")
    
    # Obtener órdenes
    orders = get_binance_orders(api_key, secret_key)
    
    if orders:
        print(f"✅ Se encontraron {len(orders)} órdenes ejecutadas")
        analyze_orders(orders)
        
        # Buscar pares de compra-venta
        print("🔍 Buscando pares de compra-venta:")
        buy_orders = [o for o in orders if o['side'] == 'BUY']
        sell_orders = [o for o in orders if o['side'] == 'SELL']
        
        for buy in buy_orders:
            buy_time = buy['time']
            buy_qty = float(buy['executedQty'])
            
            # Buscar venta correspondiente
            matching_sells = [
                sell for sell in sell_orders 
                if sell['time'] > buy_time and abs(float(sell['executedQty']) - buy_qty) < 0.001
            ]
            
            if matching_sells:
                sell = matching_sells[0]
                buy_price = float(buy['fills'][0]['price']) if buy.get('fills') else float(buy['price'])
                sell_price = float(sell['fills'][0]['price']) if sell.get('fills') else float(sell['price'])
                
                # Calcular PnL
                pnl_usdt = (sell_price - buy_price) * buy_qty
                pnl_pct = ((sell_price - buy_price) / buy_price) * 100
                
                print(f"   💰 Par encontrado:")
                print(f"      Compra: {buy_qty:.8f} BTC @ ${buy_price:.2f}")
                print(f"      Venta:  {sell['executedQty']:.8f} BTC @ ${sell_price:.2f}")
                print(f"      PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
                print()
    else:
        print("❌ No se encontraron órdenes o hubo un error")

if __name__ == "__main__":
    main()
