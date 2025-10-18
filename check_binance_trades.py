#!/usr/bin/env python3
"""
Script para verificar trades reales en Binance usando myTrades API
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Agregar el path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_binance_trades():
    """Verifica trades en Binance usando myTrades API"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingApiKey
        from app.db.crud_trading import get_decrypted_api_credentials
        import requests
        import hmac
        import hashlib
        import time
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
        
        logger.info(f"🔍 Verificando trades para {len(api_keys)} API keys")
        
        for api_key in api_keys:
            try:
                logger.info(f"\n📊 Verificando API key {api_key.id}...")
                
                # Obtener credenciales
                creds = get_decrypted_api_credentials(db, api_key.id)
                if not creds:
                    logger.warning(f"No se pudieron obtener credenciales para API key {api_key.id}")
                    continue
                
                key, secret = creds
                
                # Consultar trades de los últimos 7 días
                current_time_ms = int(time.time() * 1000)
                start_time = current_time_ms - (7 * 24 * 60 * 60 * 1000)
                
                base_url = "https://api.binance.com"
                endpoint = "/api/v3/myTrades"
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
                
                trades = response.json()
                
                logger.info(f"✅ API key {api_key.id}: {len(trades)} trades encontrados")
                
                if trades:
                    print(f"\n{'='*80}")
                    print(f"📊 TRADES PARA API KEY {api_key.id}")
                    print(f"{'='*80}")
                    
                    # Separar compras y ventas
                    buy_trades = [t for t in trades if t['isBuyer']]
                    sell_trades = [t for t in trades if not t['isBuyer']]
                    
                    print(f"\n🟢 COMPRAS ({len(buy_trades)}):")
                    for i, trade in enumerate(buy_trades, 1):
                        timestamp = datetime.fromtimestamp(trade['time'] / 1000)
                        price = float(trade['price'])
                        quantity = float(trade['qty'])
                        total = float(trade['quoteQty'])
                        commission = float(trade['commission'])
                        commission_asset = trade['commissionAsset']
                        
                        print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"     Precio: ${price:,.2f}")
                        print(f"     Cantidad: {quantity:.8f} BTC")
                        print(f"     Total: ${total:,.2f} USDT")
                        print(f"     Comisión: {commission:.8f} {commission_asset}")
                        print(f"     Trade ID: {trade['id']}")
                        print()
                    
                    print(f"\n🔴 VENTAS ({len(sell_trades)}):")
                    for i, trade in enumerate(sell_trades, 1):
                        timestamp = datetime.fromtimestamp(trade['time'] / 1000)
                        price = float(trade['price'])
                        quantity = float(trade['qty'])
                        total = float(trade['quoteQty'])
                        commission = float(trade['commission'])
                        commission_asset = trade['commissionAsset']
                        
                        print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"     Precio: ${price:,.2f}")
                        print(f"     Cantidad: {quantity:.8f} BTC")
                        print(f"     Total: ${total:,.2f} USDT")
                        print(f"     Comisión: {commission:.8f} {commission_asset}")
                        print(f"     Trade ID: {trade['id']}")
                        print()
                    
                    # Análisis de PnL
                    if buy_trades and sell_trades:
                        print(f"\n💰 ANÁLISIS DE GANANCIAS/PÉRDIDAS:")
                        print("-" * 50)
                        
                        # Buscar pares de compra-venta
                        for buy_trade in buy_trades:
                            buy_time = buy_trade['time']
                            buy_price = float(buy_trade['price'])
                            buy_qty = float(buy_trade['qty'])
                            buy_total = float(buy_trade['quoteQty'])
                            
                            # Buscar venta correspondiente (después de la compra)
                            matching_sells = [
                                sell for sell in sell_trades 
                                if sell['time'] > buy_time
                            ]
                            
                            if matching_sells:
                                # Usar la primera venta encontrada
                                sell_trade = matching_sells[0]
                                sell_price = float(sell_trade['price'])
                                sell_qty = float(sell_trade['qty'])
                                sell_total = float(sell_trade['quoteQty'])
                                
                                pnl_usdt = sell_total - buy_total
                                pnl_pct = (pnl_usdt / buy_total) * 100
                                
                                emoji = "📈" if pnl_usdt > 0 else "📉" if pnl_usdt < 0 else "➖"
                                
                                print(f"{emoji} Compra: ${buy_price:,.2f} → Venta: ${sell_price:,.2f}")
                                print(f"   PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
                                print(f"   Compra ID: {buy_trade['id']}")
                                print(f"   Venta ID: {sell_trade['id']}")
                                print(f"   Cantidad: {buy_qty:.8f} BTC")
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
    asyncio.run(check_binance_trades())
