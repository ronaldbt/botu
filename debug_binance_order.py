#!/usr/bin/env python3
"""
Script para debuggear una orden específica de Binance
"""

import asyncio
import sys
import os
import json

# Agregar el path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def debug_order():
    """Debug de una orden específica"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingApiKey
        from app.db.crud_trading import get_decrypted_api_credentials
        import requests
        import hmac
        import hashlib
        import time
        from urllib.parse import urlencode
        
        # Obtener API key
        db = next(get_db())
        api_key = db.query(TradingApiKey).filter(
            TradingApiKey.is_testnet == False,
            TradingApiKey.btc_30m_mainnet_enabled == True,
            TradingApiKey.is_active == True
        ).first()
        
        if not api_key:
            print("No hay API keys habilitadas")
            return
        
        # Obtener credenciales
        creds = get_decrypted_api_credentials(db, api_key.id)
        if not creds:
            print("No se pudieron obtener credenciales")
            return
        
        key, secret = creds
        
        # Consultar la última orden específica (la venta más reciente)
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/allOrders"
        ts = int(time.time() * 1000)
        
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
        
        # Buscar la venta más reciente
        sell_orders = [o for o in orders if o['side'] == 'SELL' and o['status'] == 'FILLED']
        if sell_orders:
            latest_sell = sell_orders[-1]  # La más reciente
            print("ÚLTIMA VENTA ENCONTRADA:")
            print(json.dumps(latest_sell, indent=2))
            
            print("\nANÁLISIS:")
            print(f"Order ID: {latest_sell['orderId']}")
            print(f"Symbol: {latest_sell['symbol']}")
            print(f"Side: {latest_sell['side']}")
            print(f"Type: {latest_sell['type']}")
            print(f"Status: {latest_sell['status']}")
            print(f"Orig Qty: {latest_sell['origQty']}")
            print(f"Executed Qty: {latest_sell['executedQty']}")
            print(f"Price: {latest_sell['price']}")
            print(f"Fills: {latest_sell.get('fills', [])}")
            
            if latest_sell.get('fills'):
                print("\nDETALLE DE FILLS:")
                for i, fill in enumerate(latest_sell['fills']):
                    print(f"  Fill {i+1}:")
                    print(f"    Price: {fill.get('price')}")
                    print(f"    Qty: {fill.get('qty')}")
                    print(f"    Commission: {fill.get('commission')}")
                    print(f"    Commission Asset: {fill.get('commissionAsset')}")
        
        else:
            print("No se encontraron órdenes de venta")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(debug_order())
