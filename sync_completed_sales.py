#!/usr/bin/env python3
"""
Script para sincronizar las ventas completadas en Binance con la base de datos
Esto permitirá que el sistema ejecute nuevas compras
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

async def sync_completed_sales():
    """Sincroniza las ventas completadas en Binance con la base de datos"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingApiKey, TradingOrder
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
        
        logger.info(f"🔍 Verificando posiciones para {len(api_keys)} API keys")
        
        for api_key in api_keys:
            try:
                logger.info(f"\n📊 Procesando API key {api_key.id}...")
                
                # Obtener credenciales
                creds = get_decrypted_api_credentials(db, api_key.id)
                if not creds:
                    logger.warning(f"No se pudieron obtener credenciales para API key {api_key.id}")
                    continue
                
                key, secret = creds
                
                # Obtener trades de Binance
                trades = await get_binance_trades(key, secret)
                if not trades:
                    continue
                
                # Obtener posiciones abiertas en la base de datos
                open_positions = db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key.id,
                    TradingOrder.symbol == 'BTCUSDT',
                    TradingOrder.side == 'buy',
                    TradingOrder.status == 'FILLED'
                ).all()
                
                logger.info(f"📋 Encontradas {len(open_positions)} posiciones abiertas en BD")
                
                # Para cada posición abierta, verificar si ya se vendió en Binance
                for position in open_positions:
                    await check_and_close_position(db, position, trades)
                
            except Exception as e:
                logger.error(f"Error procesando API key {api_key.id}: {e}")
        
        db.commit()
        logger.info("✅ Sincronización completada")
        
    except Exception as e:
        logger.error(f"Error en sincronización: {e}")
    finally:
        if 'db' in locals():
            db.close()

async def get_binance_trades(api_key: str, secret_key: str):
    """Obtiene trades de Binance"""
    try:
        base_url = "https://api.binance.com"
        endpoint = "/api/v3/myTrades"
        ts = int(time.time() * 1000)
        
        params = {
            'symbol': 'BTCUSDT',
            'timestamp': ts,
            'recvWindow': 5000
        }
        
        query = urlencode(params)
        signature = hmac.new(secret_key.encode(), query.encode(), hashlib.sha256).hexdigest()
        headers = {'X-MBX-APIKEY': api_key}
        
        url = f"{base_url}{endpoint}?{query}&signature={signature}"
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Error obteniendo trades de Binance: {e}")
        return []

async def check_and_close_position(db, position, trades):
    """Verifica si una posición ya se vendió en Binance y la cierra"""
    try:
        # Buscar ventas después de esta compra
        buy_time = position.created_at.timestamp() * 1000
        matching_sells = [
            trade for trade in trades 
            if not trade['isBuyer'] and trade['time'] > buy_time
        ]
        
        if matching_sells:
            # La posición ya se vendió en Binance
            sell_trade = matching_sells[0]  # Usar la primera venta
            
            logger.info(f"🔄 Posición ID {position.id} ya vendida en Binance - Sincronizando...")
            
            # Crear registro de venta en la base de datos
            from app.db.models import TradingOrder
            sell_order = TradingOrder(
                api_key_id=position.api_key_id,
                symbol='BTCUSDT',
                side='sell',
                order_type='market',
                quantity=float(sell_trade['qty']),
                status='FILLED',
                executed_price=float(sell_trade['price']),
                executed_quantity=float(sell_trade['qty']),
                created_at=datetime.fromtimestamp(sell_trade['time'] / 1000),
                commission=float(sell_trade['commission']),
                commission_asset=sell_trade['commissionAsset']
            )
            
            # Calcular PnL
            valor_compra = position.executed_quantity * position.executed_price
            valor_venta = sell_order.executed_quantity * sell_order.executed_price
            pnl_usdt = valor_venta - valor_compra
            pnl_pct = (pnl_usdt / valor_compra) * 100
            
            sell_order.pnl_usdt = pnl_usdt
            sell_order.pnl_percentage = pnl_pct
            
            # Marcar compra como completada
            position.status = 'completed'
            position.sell_order_id = sell_order.id
            
            db.add(sell_order)
            
            emoji = "📈" if pnl_usdt > 0 else "📉" if pnl_usdt < 0 else "➖"
            logger.info(f"{emoji} Posición {position.id} sincronizada: Venta @ ${sell_order.executed_price:.2f}, PnL: ${pnl_usdt:+.2f} ({pnl_pct:+.2f}%)")
            
        else:
            logger.info(f"⏳ Posición ID {position.id} sigue abierta - Sin venta en Binance")
            
    except Exception as e:
        logger.error(f"Error verificando posición {position.id}: {e}")

async def check_open_positions():
    """Verifica el estado actual de las posiciones abiertas"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingOrder
        
        db = next(get_db())
        
        # Buscar todas las posiciones abiertas
        open_positions = db.query(TradingOrder).filter(
            TradingOrder.symbol == 'BTCUSDT',
            TradingOrder.side == 'buy',
            TradingOrder.status == 'FILLED'
        ).all()
        
        logger.info(f"📊 POSICIONES ABIERTAS EN BASE DE DATOS: {len(open_positions)}")
        
        for position in open_positions:
            logger.info(f"  - Posición ID {position.id}: {position.executed_quantity:.8f} BTC @ ${position.executed_price:.2f} (Creada: {position.created_at})")
        
        # Buscar posiciones completadas
        completed_positions = db.query(TradingOrder).filter(
            TradingOrder.symbol == 'BTCUSDT',
            TradingOrder.side == 'buy',
            TradingOrder.status == 'completed'
        ).all()
        
        logger.info(f"✅ POSICIONES COMPLETADAS: {len(completed_positions)}")
        
        for position in completed_positions:
            logger.info(f"  - Posición ID {position.id}: Completada")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error verificando posiciones: {e}")

async def main():
    """Función principal"""
    logger.info("🔄 Iniciando sincronización de ventas completadas")
    
    try:
        # 1. Verificar estado actual
        logger.info("📊 Paso 1: Verificando estado actual de posiciones...")
        await check_open_positions()
        
        # 2. Sincronizar ventas completadas
        logger.info("🔄 Paso 2: Sincronizando ventas completadas...")
        await sync_completed_sales()
        
        # 3. Verificar estado final
        logger.info("📊 Paso 3: Verificando estado final...")
        await check_open_positions()
        
        logger.info("✅ Sincronización completada exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la sincronización: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Sincronización completada!")
        print("Las posiciones vendidas en Binance ahora aparecen como completadas en el sistema.")
        print("El sistema puede ejecutar nuevas compras.")
    else:
        print("\n💥 Sincronización falló. Revisa los logs para más detalles.")
        sys.exit(1)
