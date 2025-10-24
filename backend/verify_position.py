#!/usr/bin/env python3
"""
Script para verificar la posición corregida
"""

import sys
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingOrder

def verify_position():
    db = next(get_db())

    # Verificar la posición abierta
    open_order = db.query(TradingOrder).filter(
        TradingOrder.side == 'BUY',
        TradingOrder.status == 'FILLED'
    ).first()

    if open_order:
        print(f'✅ Posición abierta corregida:')
        print(f'   Cantidad: {open_order.quantity:.8f} BTC')
        print(f'   Precio: ${open_order.price:.2f}')
        print(f'   Total invertido: ${open_order.quantity * open_order.price:.2f}')
        print(f'   Fecha: {open_order.created_at}')
    else:
        print('❌ No se encontró posición abierta')

    db.close()

if __name__ == "__main__":
    verify_position()
