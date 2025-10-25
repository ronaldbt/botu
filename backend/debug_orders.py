#!/usr/bin/env python3
"""
Script para debuggear el problema de órdenes que no se ven
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.db.models import TradingOrder, TradingApiKey, User
from sqlalchemy import func, desc
from datetime import datetime, timedelta

def debug_orders():
    """Debug de órdenes en la base de datos"""
    db = SessionLocal()
    try:
        print("🔍 DEBUGGING ÓRDENES EN LA BASE DE DATOS")
        print("=" * 50)
        
        # 1. Verificar usuarios
        users = db.query(User).all()
        print(f"👥 Usuarios en la base de datos: {len(users)}")
        for user in users:
            print(f"  - ID: {user.id}, Email: {user.email}")
        
        # 2. Verificar API keys
        api_keys = db.query(TradingApiKey).all()
        print(f"\n🔑 API Keys en la base de datos: {len(api_keys)}")
        for api_key in api_keys:
            print(f"  - ID: {api_key.id}, User: {api_key.user_id}, Testnet: {api_key.is_testnet}, Active: {api_key.is_active}")
        
        # 3. Verificar órdenes totales
        total_orders = db.query(TradingOrder).count()
        print(f"\n📊 Total órdenes en la base de datos: {total_orders}")
        
        if total_orders == 0:
            print("❌ NO HAY ÓRDENES EN LA BASE DE DATOS")
            return
        
        # 4. Verificar órdenes por símbolo
        orders_by_symbol = db.query(TradingOrder.symbol, func.count(TradingOrder.id)).group_by(TradingOrder.symbol).all()
        print("\n📈 Órdenes por símbolo:")
        for symbol, count in orders_by_symbol:
            print(f"  - {symbol}: {count}")
        
        # 5. Verificar órdenes por estado
        orders_by_status = db.query(TradingOrder.status, func.count(TradingOrder.id)).group_by(TradingOrder.status).all()
        print("\n📊 Órdenes por estado:")
        for status, count in orders_by_status:
            print(f"  - {status}: {count}")
        
        # 6. Verificar órdenes por usuario
        orders_by_user = db.query(TradingOrder.user_id, func.count(TradingOrder.id)).group_by(TradingOrder.user_id).all()
        print("\n👤 Órdenes por usuario:")
        for user_id, count in orders_by_user:
            print(f"  - Usuario {user_id}: {count}")
        
        # 7. Verificar órdenes recientes
        recent_orders = db.query(TradingOrder).order_by(desc(TradingOrder.created_at)).limit(10).all()
        print("\n🕒 Últimas 10 órdenes:")
        for order in recent_orders:
            print(f"  - ID: {order.id}, User: {order.user_id}, Symbol: {order.symbol}, Side: {order.side}, Status: {order.status}, Created: {order.created_at}")
        
        # 8. Verificar órdenes de Bitcoin 30m específicamente
        btc_orders = db.query(TradingOrder).filter(
            TradingOrder.symbol == 'BTCUSDT'
        ).order_by(desc(TradingOrder.created_at)).all()
        print(f"\n₿ Órdenes de Bitcoin (BTCUSDT): {len(btc_orders)}")
        for order in btc_orders[:5]:  # Mostrar solo las primeras 5
            print(f"  - ID: {order.id}, User: {order.user_id}, Side: {order.side}, Status: {order.status}, Reason: {order.reason}, Created: {order.created_at}")
        
        # 9. Verificar si hay órdenes con reason U_PATTERN
        u_pattern_orders = db.query(TradingOrder).filter(
            TradingOrder.reason == 'U_PATTERN'
        ).order_by(desc(TradingOrder.created_at)).all()
        print(f"\n🎯 Órdenes con reason U_PATTERN: {len(u_pattern_orders)}")
        for order in u_pattern_orders[:5]:
            print(f"  - ID: {order.id}, User: {order.user_id}, Symbol: {order.symbol}, Side: {order.side}, Status: {order.status}, Created: {order.created_at}")
        
        # 10. Verificar órdenes de las últimas 24 horas
        yesterday = datetime.now() - timedelta(days=1)
        recent_orders_24h = db.query(TradingOrder).filter(
            TradingOrder.created_at >= yesterday
        ).order_by(desc(TradingOrder.created_at)).all()
        print(f"\n⏰ Órdenes de las últimas 24 horas: {len(recent_orders_24h)}")
        for order in recent_orders_24h:
            print(f"  - ID: {order.id}, User: {order.user_id}, Symbol: {order.symbol}, Side: {order.side}, Status: {order.status}, Created: {order.created_at}")
        
    except Exception as e:
        print(f"❌ Error en debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_orders()
