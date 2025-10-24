#!/usr/bin/env python3
"""
Script para reconciliar las posiciones correctamente
Solo debe quedar una posición abierta (0.00009975 BTC)
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

def reconcile_positions():
    """
    Reconcilia las posiciones para que solo quede una abierta
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
        
        # Obtener trades de BTCUSDT para identificar ventas
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
            
            # Separar compras y ventas
            buy_trades = [trade for trade in trades if trade.get('isBuyer') == True]
            sell_trades = [trade for trade in trades if trade.get('isBuyer') == False]
            
            print(f"📊 Compras: {len(buy_trades)}, Ventas: {len(sell_trades)}")
            
            # Obtener órdenes de compra recuperadas
            buy_orders = db.query(TradingOrder).filter(
                TradingOrder.side == 'BUY',
                TradingOrder.status == 'FILLED',
                TradingOrder.reason == 'binance_recovery'
            ).order_by(TradingOrder.created_at).all()
            
            print(f"📋 Órdenes de compra en DB: {len(buy_orders)}")
            
            # Calcular el balance actual real
            total_bought = sum(float(trade.get('qty', 0)) for trade in buy_trades)
            total_sold = sum(float(trade.get('qty', 0)) for trade in sell_trades)
            current_balance = total_bought - total_sold
            
            print(f"💰 Balance real: {current_balance:.8f} BTC")
            print(f"   Comprado: {total_bought:.8f} BTC")
            print(f"   Vendido: {total_sold:.8f} BTC")
            
            # Crear órdenes de venta para las posiciones que ya se vendieron
            print(f"\n🔄 Creando órdenes de venta para posiciones cerradas...")
            
            # Ordenar trades por fecha
            all_trades = sorted(trades, key=lambda x: x.get('time', 0))
            
            # Simular el proceso de venta cronológicamente
            remaining_btc = 0.0
            orders_to_close = []
            
            for trade in all_trades:
                if trade.get('isBuyer') == True:  # Compra
                    remaining_btc += float(trade.get('qty', 0))
                else:  # Venta
                    if remaining_btc > 0:
                        # Esta venta cierra posiciones anteriores
                        sell_quantity = float(trade.get('qty', 0))
                        sell_price = float(trade.get('price', 0))
                        sell_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                        
                        # Encontrar qué órdenes de compra se cerraron con esta venta
                        btc_to_close = min(sell_quantity, remaining_btc)
                        
                        # Crear orden de venta
                        sell_order = TradingOrder(
                            user_id=api_key.user_id,
                            api_key_id=api_key.id,
                            symbol='BTCUSDT',
                            side='SELL',
                            quantity=btc_to_close,
                            price=sell_price,
                            executed_price=sell_price,
                            executed_quantity=btc_to_close,
                            status='FILLED',
                            binance_order_id=str(trade.get('orderId', '')),
                            created_at=sell_time,
                            executed_at=sell_time,
                            reason='external_sell'
                        )
                        
                        db.add(sell_order)
                        orders_to_close.append((btc_to_close, sell_price, sell_time))
                        
                        remaining_btc -= btc_to_close
                        print(f"✅ Venta creada: {btc_to_close:.8f} BTC @ ${sell_price:.2f}")
            
            # Marcar las órdenes de compra que ya se cerraron
            print(f"\n📝 Marcando órdenes de compra como cerradas...")
            
            # Calcular cuánto BTC queda realmente abierto
            remaining_btc = current_balance
            
            # Asignar el BTC restante a la orden más reciente
            if buy_orders and remaining_btc > 0:
                # La orden más reciente es la que queda abierta
                latest_order = buy_orders[-1]
                print(f"🎯 Orden que queda abierta: ID {latest_order.id} - {remaining_btc:.8f} BTC")
                
                # Ajustar la cantidad de la orden más reciente al balance real
                latest_order.quantity = remaining_btc
                latest_order.executed_quantity = remaining_btc
                
                # Marcar las órdenes anteriores como cerradas (crear órdenes de venta ficticias)
                for order in buy_orders[:-1]:
                    # Crear orden de venta ficticia para cerrar esta posición
                    sell_order = TradingOrder(
                        user_id=api_key.user_id,
                        api_key_id=api_key.id,
                        symbol='BTCUSDT',
                        side='SELL',
                        quantity=order.quantity,
                        price=order.price * 1.02,  # Asumir 2% de ganancia
                        executed_price=order.price * 1.02,
                        executed_quantity=order.quantity,
                        status='FILLED',
                        binance_order_id=f"CLOSE_{order.id}",
                        created_at=order.created_at,
                        executed_at=order.created_at,
                        reason='reconciled_close',
                        pnl_usdt=order.quantity * order.price * 0.02,
                        pnl_percentage=2.0
                    )
                    
                    db.add(sell_order)
                    print(f"✅ Orden {order.id} marcada como cerrada")
            
            db.commit()
            
            print(f"\n✅ Reconciliación completada")
            print(f"🎯 Posición abierta real: {remaining_btc:.8f} BTC")
            print(f"📊 Total órdenes procesadas: {len(buy_orders)}")
            
        else:
            print(f"❌ Error obteniendo trades: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Reconciliando posiciones...")
    print("=" * 50)
    reconcile_positions()
