#!/usr/bin/env python3
"""
Script para corregir la base de datos y preparar mejoras de UI
"""

import sys
sys.path.append('backend')

from app.db.database import get_db
from app.db.models import TradingOrder

def fix_database():
    """
    Corrige la base de datos con los valores reales
    """
    db = next(get_db())

    # Obtener la orden abierta (ID 8)
    open_order = db.query(TradingOrder).filter(
        TradingOrder.id == 8
    ).first()

    if open_order:
        print(f"🔧 Corrigiendo orden ID {open_order.id}:")
        print(f"  Antes: {open_order.quantity:.8f} BTC @ ${open_order.price:.2f} = ${open_order.quantity * open_order.price:.2f}")
        
        # Corregir a la cantidad real de la última compra
        open_order.quantity = 0.00009
        open_order.executed_quantity = 0.00009
        
        db.commit()
        
        print(f"  Después: {open_order.quantity:.8f} BTC @ ${open_order.price:.2f} = ${open_order.quantity * open_order.price:.2f}")
        print(f"✅ Orden corregida correctamente")
    else:
        print(f"❌ No se encontró la orden abierta")

    db.close()

if __name__ == "__main__":
    print("🔧 Corrigiendo base de datos...")
    print("=" * 50)
    fix_database()
