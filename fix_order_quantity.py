#!/usr/bin/env python3
"""
Script para corregir la cantidad de la orden abierta
"""

import sys
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingOrder

def fix_order_quantity():
    db = next(get_db())

    # Obtener la orden abierta
    open_order = db.query(TradingOrder).filter(
        TradingOrder.side == 'BUY',
        TradingOrder.status == 'FILLED',
        TradingOrder.id == 8
    ).first()

    if open_order:
        print(f'Orden actual: {open_order.quantity:.8f} BTC @ ${open_order.price:.2f}')
        print(f'Valor actual: ${open_order.quantity * open_order.price:.2f}')
        
        # Corregir a la cantidad real de Binance
        open_order.quantity = 0.00009
        open_order.executed_quantity = 0.00009
        
        db.commit()
        
        print(f'Orden corregida: {open_order.quantity:.8f} BTC @ ${open_order.price:.2f}')
        print(f'Valor corregido: ${open_order.quantity * open_order.price:.2f}')
    else:
        print('No se encontró la orden abierta')

    db.close()

if __name__ == "__main__":
    fix_order_quantity()
