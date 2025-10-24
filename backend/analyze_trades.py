#!/usr/bin/env python3
"""
Script para analizar los trades de Binance y entender las comisiones y lotes
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
from app.db.models import TradingApiKey
from app.db.crud_trading import get_decrypted_api_credentials

def analyze_trades():
    """
    Analiza los trades de Binance para entender comisiones y lotes
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
        
        print(f"🌐 Obteniendo trades detallados de BTCUSDT...")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            trades = response.json()
            print(f"✅ Obtenidos {len(trades)} trades de Binance")
            
            # Filtrar solo los trades de la última compra (19/10/2025)
            last_buy_trades = []
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                if trade_time.date() == datetime(2025, 10, 19).date() and trade.get('isBuyer') == True:
                    last_buy_trades.append(trade)
            
            print(f"\n📊 Trades de compra del 19/10/2025: {len(last_buy_trades)}")
            print("=" * 80)
            
            total_quantity = 0
            total_quote = 0
            total_commission = 0
            
            for i, trade in enumerate(last_buy_trades, 1):
                trade_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                quantity = float(trade.get('qty', 0))
                price = float(trade.get('price', 0))
                quote_qty = float(trade.get('quoteQty', 0))
                commission = float(trade.get('commission', 0))
                commission_asset = trade.get('commissionAsset', '')
                order_id = trade.get('orderId', '')
                
                total_quantity += quantity
                total_quote += quote_qty
                total_commission += commission
                
                print(f"Trade {i}:")
                print(f"  Hora: {trade_time}")
                print(f"  Order ID: {order_id}")
                print(f"  Cantidad: {quantity:.8f} BTC")
                print(f"  Precio: ${price:.2f}")
                print(f"  Valor: ${quote_qty:.2f}")
                print(f"  Comisión: {commission:.8f} {commission_asset}")
                print(f"  Neto recibido: {quantity - (commission if commission_asset == 'BTC' else 0):.8f} BTC")
                print()
            
            print("=" * 80)
            print(f"📋 RESUMEN DE LA COMPRA DEL 19/10/2025:")
            print(f"  Total cantidad: {total_quantity:.8f} BTC")
            print(f"  Total valor: ${total_quote:.2f}")
            print(f"  Total comisión: {total_commission:.8f} {commission_asset}")
            print(f"  Neto recibido: {total_quantity - (total_commission if commission_asset == 'BTC' else 0):.8f} BTC")
            print(f"  Precio promedio: ${total_quote / total_quantity:.2f}")
            
            # Verificar balance actual
            print(f"\n💰 VERIFICACIÓN DE BALANCE:")
            print(f"  Balance actual en Binance: 0.00009975 BTC")
            print(f"  Diferencia: {abs(0.00009975 - (total_quantity - total_commission)):.8f} BTC")
            
            # Analizar si hay más trades después
            print(f"\n🔍 BUSCANDO TRADES POSTERIORES...")
            later_trades = []
            for trade in trades:
                trade_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                if trade_time > datetime(2025, 10, 19, 10, 37, 34):  # Después de la compra
                    later_trades.append(trade)
            
            if later_trades:
                print(f"  Encontrados {len(later_trades)} trades posteriores:")
                for trade in later_trades:
                    trade_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                    is_buyer = trade.get('isBuyer', False)
                    quantity = float(trade.get('qty', 0))
                    price = float(trade.get('price', 0))
                    side = "COMPRA" if is_buyer else "VENTA"
                    print(f"    {trade_time}: {side} {quantity:.8f} BTC @ ${price:.2f}")
            else:
                print(f"  No hay trades posteriores a la compra")
            
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
    print("🔍 Analizando trades de Binance...")
    print("=" * 60)
    analyze_trades()
