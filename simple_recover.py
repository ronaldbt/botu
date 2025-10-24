#!/usr/bin/env python3
"""
Script simple para recuperar órdenes de Binance sin timestamps
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

def recover_orders():
    """
    Recupera órdenes de Binance sin usar timestamps
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
        
        print(f"🔑 Usando API key ID: {api_key.id}")
        
        # Obtener credenciales
        creds = get_decrypted_api_credentials(db, api_key.id)
        if not creds:
            print("❌ No se pudieron obtener credenciales")
            return
        
        key, secret = creds
        
        # Obtener órdenes de BTCUSDT (sin timestamps)
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/allOrders"
        
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
        
        print(f"🌐 Obteniendo órdenes de BTCUSDT...")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            orders = response.json()
            print(f"✅ Obtenidas {len(orders)} órdenes de Binance")
            
            # Filtrar órdenes de compra ejecutadas
            buy_orders = [order for order in orders if 
                         order.get('side') == 'BUY' and 
                         order.get('status') == 'FILLED']
            
            print(f"📊 Encontradas {len(buy_orders)} órdenes de compra ejecutadas")
            
            # Procesar cada orden
            for order in buy_orders:
                order_id = order.get('orderId')
                symbol = order.get('symbol')
                side = order.get('side')
                price = float(order.get('price', 0))
                quantity = float(order.get('executedQty', 0))
                time_ms = order.get('time')
                order_time = datetime.fromtimestamp(time_ms / 1000)
                
                print(f"\n📋 Orden encontrada:")
                print(f"   ID: {order_id}")
                print(f"   Símbolo: {symbol}")
                print(f"   Lado: {side}")
                print(f"   Cantidad: {quantity}")
                print(f"   Precio: ${price}")
                print(f"   Fecha: {order_time}")
                
                # Verificar si ya existe en la base de datos
                existing_order = db.query(TradingOrder).filter(
                    TradingOrder.binance_order_id == str(order_id),
                    TradingOrder.symbol == symbol,
                    TradingOrder.side == side
                ).first()
                
                if not existing_order:
                    # Crear nueva orden en la base de datos
                    new_order = TradingOrder(
                        user_id=api_key.user_id,
                        api_key_id=api_key.id,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=price,
                        executed_price=price,
                        executed_quantity=quantity,
                        status='FILLED',
                        binance_order_id=str(order_id),
                        created_at=order_time,
                        executed_at=order_time,
                        reason='binance_recovery'
                    )
                    
                    db.add(new_order)
                    db.commit()
                    
                    print(f"✅ Orden registrada en la base de datos")
                    print(f"   Total USDT: ${quantity * price:.2f}")
                else:
                    print(f"ℹ️ Orden ya existe en la base de datos")
            
            print(f"\n🎯 Resumen:")
            print(f"   Órdenes encontradas: {len(buy_orders)}")
            print(f"   Órdenes registradas: {len([o for o in buy_orders if not db.query(TradingOrder).filter(TradingOrder.binance_order_id == str(o.get('orderId'))).first()])}")
            
        else:
            print(f"❌ Error obteniendo órdenes: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Recuperando órdenes de Binance...")
    print("=" * 50)
    recover_orders()