#!/usr/bin/env python3
"""
Script para arreglar la posición inconsistente (Orden ID 6)
"""

import asyncio
import sys
import os
import logging

# Agregar el path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_inconsistent_position():
    """Arregla la posición inconsistente (Orden ID 6)"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingOrder, TradingApiKey
        from app.db.crud_trading import get_decrypted_api_credentials
        import requests
        import hmac
        import hashlib
        import time
        from urllib.parse import urlencode
        from datetime import datetime
        
        db = next(get_db())
        
        # Buscar la orden ID 6 problemática
        problematic_order = db.query(TradingOrder).filter(TradingOrder.id == 6).first()
        
        if not problematic_order:
            logger.info("No se encontró la orden ID 6")
            return
        
        logger.info(f"🔍 Encontrada orden problemática ID {problematic_order.id}:")
        logger.info(f"   Side: {problematic_order.side}")
        logger.info(f"   Status: {problematic_order.status}")
        logger.info(f"   Quantity: {problematic_order.executed_quantity:.8f} BTC")
        logger.info(f"   Price: ${problematic_order.executed_price:.2f}")
        logger.info(f"   Created: {problematic_order.created_at}")
        
        # Obtener API key para verificar trades en Binance
        api_key_config = db.query(TradingApiKey).filter(TradingApiKey.id == problematic_order.api_key_id).first()
        if not api_key_config:
            logger.error("No se encontró la API key")
            return
        
        # Obtener credenciales
        creds = get_decrypted_api_credentials(db, api_key_config.id)
        if not creds:
            logger.error("No se pudieron obtener credenciales")
            return
        
        key, secret = creds
        
        # Obtener trades de Binance
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
        
        # Buscar venta correspondiente a esta compra
        buy_time = problematic_order.created_at.timestamp() * 1000
        
        # Buscar ventas después de esta compra
        matching_sells = [
            trade for trade in trades 
            if not trade['isBuyer'] and trade['time'] > buy_time
        ]
        
        if matching_sells:
            # Encontró una venta correspondiente
            sell_trade = matching_sells[0]
            
            logger.info(f"✅ Encontrada venta correspondiente en Binance:")
            logger.info(f"   Trade ID: {sell_trade['id']}")
            logger.info(f"   Time: {datetime.fromtimestamp(sell_trade['time'] / 1000)}")
            logger.info(f"   Price: ${float(sell_trade['price']):.2f}")
            logger.info(f"   Quantity: {float(sell_trade['qty']):.8f} BTC")
            
            # Crear registro de venta en la base de datos
            sell_order = TradingOrder(
                user_id=api_key_config.user_id,  # Agregar user_id
                api_key_id=problematic_order.api_key_id,
                symbol='BTCUSDT',
                side='sell',
                order_type='market',
                quantity=float(sell_trade['qty']),
                status='FILLED',
                executed_price=float(sell_trade['price']),
                executed_quantity=float(sell_trade['qty']),
                created_at=datetime.fromtimestamp(sell_trade['time'] / 1000),
                commission=float(sell_trade['commission']),
                commission_asset=sell_trade['commissionAsset'],
                binance_order_id=str(sell_trade['orderId'])
            )
            
            # Calcular PnL
            valor_compra = problematic_order.executed_quantity * problematic_order.executed_price
            valor_venta = sell_order.executed_quantity * sell_order.executed_price
            pnl_usdt = valor_venta - valor_compra
            pnl_pct = (pnl_usdt / valor_compra) * 100
            
            sell_order.pnl_usdt = pnl_usdt
            sell_order.pnl_percentage = pnl_pct
            
            # Marcar compra como completada
            problematic_order.status = 'completed'
            problematic_order.sell_order_id = sell_order.id
            
            db.add(sell_order)
            db.commit()
            
            emoji = "📈" if pnl_usdt > 0 else "📉" if pnl_usdt < 0 else "➖"
            logger.info(f"{emoji} Posición sincronizada: Venta @ ${sell_order.executed_price:.2f}, PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
            
        else:
            # No hay venta correspondiente, verificar si realmente se vendió
            logger.warning("⚠️ No se encontró venta correspondiente en Binance")
            logger.warning("Esto podría significar que:")
            logger.warning("1. La posición aún está abierta")
            logger.warning("2. La venta se hizo manualmente fuera del sistema")
            logger.warning("3. Hay un problema con los timestamps")
            
            # Verificar si hay BTC en el balance
            balance = await get_current_balance(key, secret)
            btc_balance = balance.get('BTC', 0.0)
            
            if btc_balance > 0.00001:  # Si hay BTC significativo
                logger.info(f"💰 Balance actual de BTC: {btc_balance:.8f} BTC")
                logger.info("La posición parece estar abierta - no se requiere acción")
            else:
                logger.info("💰 Balance de BTC muy bajo - probablemente ya se vendió")
                logger.info("Considerando marcar como completada...")
                
                # Marcar como completada sin crear orden de venta
                problematic_order.status = 'completed'
                db.commit()
                logger.info("✅ Posición marcada como completada")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error arreglando posición: {e}")

async def get_current_balance(api_key: str, secret_key: str):
    """Obtiene el balance actual"""
    try:
        import hmac, hashlib, time
        from urllib.parse import urlencode
        
        url = "https://api.binance.com/api/v3/account"
        ts = int(time.time() * 1000)
        params = { 'timestamp': ts }
        query = urlencode(params)
        signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
        headers = { 'X-MBX-APIKEY': api_key }
        
        response = requests.get(f"{url}?{query}&signature={signature}", headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        balances = { b['asset']: float(b['free']) + float(b['locked']) for b in data.get('balances', []) }
        
        return balances
        
    except Exception as e:
        logger.error(f"Error obteniendo balance: {e}")
        return {}

if __name__ == "__main__":
    asyncio.run(fix_inconsistent_position())
