#!/usr/bin/env python3
"""
Script para verificar TODAS las posiciones en la base de datos
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

async def check_all_positions():
    """Verifica TODAS las posiciones en la base de datos"""
    try:
        from app.db.database import get_db
        from app.db.models import TradingOrder
        
        db = next(get_db())
        
        # Buscar TODAS las órdenes de BTCUSDT
        all_orders = db.query(TradingOrder).filter(
            TradingOrder.symbol == 'BTCUSDT'
        ).order_by(TradingOrder.created_at.desc()).all()
        
        logger.info(f"📊 TODAS LAS ÓRDENES BTCUSDT EN BASE DE DATOS: {len(all_orders)}")
        
        if all_orders:
            print("\n" + "="*100)
            print("📋 HISTORIAL COMPLETO DE ÓRDENES BTCUSDT")
            print("="*100)
            
            for i, order in enumerate(all_orders, 1):
                status_emoji = "✅" if order.status == 'FILLED' else "❌" if order.status == 'REJECTED' else "⏳" if order.status == 'PENDING' else "🏁" if order.status == 'completed' else "❓"
                
                print(f"\n{i}. {status_emoji} Orden ID {order.id} - {order.side.upper()} - {order.status}")
                print(f"   📅 Creada: {order.created_at}")
                print(f"   💰 Cantidad: {order.quantity:.8f} BTC")
                if order.executed_price:
                    print(f"   💵 Precio ejecutado: ${order.executed_price:.2f}")
                if order.executed_quantity:
                    print(f"   📊 Cantidad ejecutada: {order.executed_quantity:.8f} BTC")
                if order.binance_order_id:
                    print(f"   🔗 Binance ID: {order.binance_order_id}")
                if order.pnl_usdt is not None:
                    pnl_emoji = "📈" if order.pnl_usdt > 0 else "📉" if order.pnl_usdt < 0 else "➖"
                    print(f"   {pnl_emoji} PnL: ${order.pnl_usdt:+.2f} ({order.pnl_percentage:+.2f}%)")
                print(f"   👤 API Key ID: {order.api_key_id}")
                print("-" * 80)
        else:
            print("❌ No se encontraron órdenes en la base de datos")
        
        # Verificar específicamente posiciones abiertas
        open_buys = db.query(TradingOrder).filter(
            TradingOrder.symbol == 'BTCUSDT',
            TradingOrder.side == 'buy',
            TradingOrder.status == 'FILLED'
        ).all()
        
        logger.info(f"\n🔍 VERIFICACIÓN ESPECÍFICA:")
        logger.info(f"   📈 Compras FILLED: {len(open_buys)}")
        
        if open_buys:
            print("\n⚠️  POSICIONES QUE IMPEDIRÍAN NUEVAS COMPRAS:")
            for buy in open_buys:
                print(f"   - Compra ID {buy.id}: {buy.executed_quantity:.8f} BTC @ ${buy.executed_price:.2f}")
        else:
            print("\n✅ NO HAY POSICIONES BLOQUEANDO NUEVAS COMPRAS")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error verificando posiciones: {e}")

if __name__ == "__main__":
    asyncio.run(check_all_positions())
