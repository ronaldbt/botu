#!/usr/bin/env python3
"""
Script para verificar las órdenes recuperadas
"""

import sys
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingOrder

def check_orders():
    db = next(get_db())
    orders = db.query(TradingOrder).filter(
        TradingOrder.side == 'BUY',
        TradingOrder.status == 'FILLED',
        TradingOrder.reason == 'binance_recovery'
    ).all()

    print(f'Órdenes de compra recuperadas: {len(orders)}')
    print('=' * 60)

    total_btc = 0
    for order in orders:
        print(f'ID: {order.id} | {order.symbol} | Cantidad: {order.quantity:.8f} BTC | Precio: ${order.price:.2f} | Fecha: {order.created_at}')
        total_btc += order.quantity

    print('=' * 60)
    print(f'Total BTC: {total_btc:.8f} BTC')
    print(f'Balance actual en Binance: 0.00009975 BTC')
    print(f'Diferencia: {abs(total_btc - 0.00009975):.8f} BTC')
    
    db.close()

if __name__ == "__main__":
    check_orders()
