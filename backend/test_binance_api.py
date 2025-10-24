#!/usr/bin/env python3
"""
Script simple para probar la API de Binance
"""

import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
import sys
import os

# Agregar el path del backend
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingApiKey
from app.db.crud_trading import get_decrypted_api_credentials

def test_binance_api():
    """
    Prueba simple de la API de Binance
    """
    try:
        db = next(get_db())
        
        # Obtener la primera API key
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
        print(f"🔑 API Key: {key[:8]}...")
        
        # Probar endpoint de account info primero
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/account"
        
        current_time = int(time.time() * 1000)
        params = {
            'timestamp': current_time,
            'recvWindow': 5000
        }
        
        query = urlencode(params)
        signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        
        headers = {'X-MBX-APIKEY': key}
        url = f"{base_url}{endpoint}?{query}&signature={signature}"
        
        print(f"🌐 Probando: {url}")
        
        response = requests.get(url, headers=headers, timeout=15)
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            account_info = response.json()
            print("✅ API funcionando correctamente")
            print(f"📊 Balances: {len(account_info.get('balances', []))} activos")
            
            # Buscar BTC
            btc_balance = None
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'BTC':
                    btc_balance = balance
                    break
            
            if btc_balance:
                print(f"₿ BTC Balance: {btc_balance['free']} (Free) / {btc_balance['locked']} (Locked)")
            else:
                print("₿ BTC Balance: 0")
                
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_binance_api()
