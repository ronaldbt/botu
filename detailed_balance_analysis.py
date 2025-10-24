#!/usr/bin/env python3
"""
Script para analizar en detalle el balance de BTC
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

def analyze_balance():
    """
    Analiza el balance de BTC en detalle
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
        
        # Obtener balance actual de la cuenta
        base_url = "https://api.binance.com"
        account_endpoint = "/api/v3/account"
        
        current_time = int(time.time() * 1000)
        params = {
            'timestamp': current_time,
            'recvWindow': 5000
        }
        
        query = urlencode(params)
        signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        
        headers = {'X-MBX-APIKEY': key}
        url = f"{base_url}{account_endpoint}?{query}&signature={signature}"
        
        print(f"🌐 Obteniendo balance actual de la cuenta...")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            account_info = response.json()
            
            # Buscar balance de BTC
            btc_balance = None
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'BTC':
                    btc_balance = balance
                    break
            
            if btc_balance:
                print(f"💰 Balance actual de BTC:")
                print(f"  Libre: {btc_balance['free']} BTC")
                print(f"  Bloqueado: {btc_balance['locked']} BTC")
                print(f"  Total: {float(btc_balance['free']) + float(btc_balance['locked'])} BTC")
            
            # Obtener todos los trades de BTCUSDT
            trades_endpoint = "/api/v3/myTrades"
            params = {
                'symbol': 'BTCUSDT',
                'timestamp': current_time,
                'recvWindow': 5000
            }
            
            query = urlencode(params)
            signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            
            url = f"{base_url}{trades_endpoint}?{query}&signature={signature}"
            
            print(f"\n🌐 Obteniendo todos los trades de BTCUSDT...")
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                trades = response.json()
                print(f"✅ Obtenidos {len(trades)} trades de Binance")
                
                # Calcular balance manualmente
                total_bought = 0
                total_sold = 0
                
                print(f"\n📊 ANÁLISIS CRONOLÓGICO DE TRADES:")
                print("=" * 100)
                
                # Ordenar trades por fecha
                sorted_trades = sorted(trades, key=lambda x: x.get('time', 0))
                
                for i, trade in enumerate(sorted_trades, 1):
                    trade_time = datetime.fromtimestamp(trade.get('time', 0) / 1000)
                    is_buyer = trade.get('isBuyer', False)
                    quantity = float(trade.get('qty', 0))
                    price = float(trade.get('price', 0))
                    commission = float(trade.get('commission', 0))
                    commission_asset = trade.get('commissionAsset', '')
                    order_id = trade.get('orderId', '')
                    
                    side = "COMPRA" if is_buyer else "VENTA"
                    
                    if is_buyer:
                        # Para compras, la comisión se descuenta de la cantidad recibida si es en BTC
                        net_quantity = quantity - (commission if commission_asset == 'BTC' else 0)
                        total_bought += net_quantity
                    else:
                        # Para ventas, la comisión se descuenta de la cantidad vendida si es en BTC
                        net_quantity = quantity - (commission if commission_asset == 'BTC' else 0)
                        total_sold += net_quantity
                    
                    print(f"Trade {i:2d}: {trade_time.strftime('%Y-%m-%d %H:%M:%S')} | {side:6s} | {quantity:.8f} BTC @ ${price:8.2f} | Comisión: {commission:.8f} {commission_asset:3s} | Neto: {net_quantity:.8f} BTC | Order: {order_id}")
                
                print("=" * 100)
                print(f"📋 RESUMEN FINAL:")
                print(f"  Total comprado (neto): {total_bought:.8f} BTC")
                print(f"  Total vendido (neto): {total_sold:.8f} BTC")
                print(f"  Balance calculado: {total_bought - total_sold:.8f} BTC")
                print(f"  Balance real en Binance: {float(btc_balance['free']) + float(btc_balance['locked']):.8f} BTC")
                print(f"  Diferencia: {abs((total_bought - total_sold) - (float(btc_balance['free']) + float(btc_balance['locked']))):.8f} BTC")
                
                # Verificar si hay trades que no se están contando
                if abs((total_bought - total_sold) - (float(btc_balance['free']) + float(btc_balance['locked']))) > 0.000001:
                    print(f"\n⚠️  HAY UNA DIFERENCIA! Esto puede deberse a:")
                    print(f"  1. Trades en otros pares (como BTC/BNB)")
                    print(f"  2. Transferencias internas")
                    print(f"  3. Staking o recompensas")
                    print(f"  4. Trades muy antiguos no incluidos en la consulta")
                
            else:
                print(f"❌ Error obteniendo trades: {response.status_code}")
                print(f"   Respuesta: {response.text}")
            
        else:
            print(f"❌ Error obteniendo balance: {response.status_code}")
            print(f"   Respuesta: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Analizando balance de BTC en detalle...")
    print("=" * 60)
    analyze_balance()
