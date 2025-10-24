#!/usr/bin/env python3
"""
Script para verificar las posiciones finales
"""

import sys
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingOrder

def check_final_positions():
    db = next(get_db())

    # Verificar posiciones abiertas (compras sin ventas correspondientes)
    open_positions = db.query(TradingOrder).filter(
        TradingOrder.side == 'BUY',
        TradingOrder.status == 'FILLED'
    ).all()

    print(f'Posiciones de compra: {len(open_positions)}')

    # Verificar ventas
    sell_orders = db.query(TradingOrder).filter(
        TradingOrder.side == 'SELL',
        TradingOrder.status == 'FILLED'
    ).all()

    print(f'Órdenes de venta: {len(sell_orders)}')

    # Calcular balance neto
    total_bought = sum(order.quantity for order in open_positions)
    total_sold = sum(order.quantity for order in sell_orders)
    net_balance = total_bought - total_sold

    print(f'\nBalance neto: {net_balance:.8f} BTC')
    print(f'Total comprado: {total_bought:.8f} BTC')
    print(f'Total vendido: {total_sold:.8f} BTC')

    print(f'\nPosiciones abiertas:')
    for order in open_positions:
        print(f'  ID: {order.id} | {order.quantity:.8f} BTC @ ${order.price:.2f} | {order.created_at}')

    print(f'\nVentas recientes:')
    for order in sell_orders[-5:]:  # Últimas 5 ventas
        print(f'  ID: {order.id} | {order.quantity:.8f} BTC @ ${order.price:.2f} | {order.created_at}')

    db.close()

if __name__ == "__main__":
    check_final_positions()
