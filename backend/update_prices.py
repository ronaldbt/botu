#!/usr/bin/env python3
"""
Script para actualizar los precios reales de las órdenes usando trades de Binance
"""

import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
import sys
import os
from datetime import datetime

# Agregar el path del backend
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingApiKey, TradingOrder
from app.db.crud_trading import get_decrypted_api_credentials

def update_order_prices():
    """
    Actualiza los precios reales de las órdenes usando trades de Binance
    """
    try:
        db = next(get_db())
        
        # Obtener la API key
        api_key = db.query(TradingApiKey).filter(
            TradingApiKey.is_testnet == False,
            TradingApiKey.is_active == True
        ).first()
        
        if not api_key:
            print("❌ No se encontró API key")
            return
        
        # Obtener credenciales
        creds = get_decrypted_api_credentials(db, api_key.id)
        if not creds:
            print("❌ No se pudieron obtener credenciales")
            return
        
        key, secret = creds
        
        # Obtener trades de BTCUSDT
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/myTrades"
        
        current_time = int(time.time() * 1000)
        params = {
            'symbol': 'BTCUSDT',
            'timestamp': current_time,
            'recvWindow': 5000
        }
        
        query = urlencode(params)
        signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        
        headers = {'X-MBX-APIKEY': key}
        url = f"{base_url}{endpoint}?{query}&signature={signature}"
        
        print(f"🌐 Obteniendo trades de BTCUSDT...")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ Obtenidos {len(trades)} trades de Binance")
            
            # Obtener órdenes de compra recuperadas
            orders = db.query(TradingOrder).filter(
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED',
                TradingOrder.reason == 'binance_recovery'
            ).all()
            
            print(f"📊 Actualizando precios de {len(orders)} órdenes...")
            
            for order in orders:
                # Buscar trades correspondientes a esta orden
                order_trades = [trade for trade in trades if trade.get('orderId') == int(order.binance_order_id)]
                
                if order_trades:
                    # Calcular precio promedio y cantidad total
                    total_quantity = sum(float(trade.get('qty', 0)) for trade in order_trades)
                    total_quote = sum(float(trade.get('quoteQty', 0)) for trade in order_trades)
                    avg_price = total_quote / total_quantity if total_quantity > 0 else 0
                    
                    # Actualizar la orden
                    order.price = avg_price
                    order.executed_price = avg_price
                    order.executed_quantity = total_quantity
                    
                    print(f"✅ Orden {order.id}: Precio actualizado a ${avg_price:.2f} (Cantidad: {total_quantity:.8f})")
                else:
                    print(f"⚠️ No se encontraron trades para la orden {order.id} (Order ID: {order.binance_order_id})")
            
            db.commit()
            print(f"\n✅ Precios actualizados correctamente")
            
            # Mostrar resumen final
            print("\n📋 RESUMEN FINAL:")
            print("=" * 60)
            total_btc = 0
            total_usdt = 0
            for order in orders:
                order_total = order.quantity * order.price
                total_btc += order.quantity
                total_usdt += order_total
                print(f"ID: {order.id} | {order.quantity:.8f} BTC @ ${order.price:.2f} = ${order_total:.2f}")
            
            print("=" * 60)
            print(f"Total BTC: {total_btc:.8f} BTC")
            print(f"Total USDT: ${total_usdt:.2f}")
            print(f"Balance actual en Binance: 0.00009975 BTC")
            print(f"BTC vendido: {total_btc - 0.00009975:.8f} BTC")
            
        else:
            print(f"❌ Error obteniendo trades: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Actualizando precios de órdenes...")
    print("=" * 50)
    update_order_prices()
