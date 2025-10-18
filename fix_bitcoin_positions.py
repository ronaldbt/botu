#!/usr/bin/env python3
"""
Script para verificar y arreglar las posiciones de Bitcoin 30m Mainnet
Ejecutar desde la raíz del proyecto: python fix_bitcoin_positions.py
"""

import asyncio
import sys
import os
import logging

# Agregar el path del backend
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.binance_order_checker import binance_order_checker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    Función principal para verificar y arreglar posiciones
    """
    logger.info("🚀 Iniciando verificación y arreglo de posiciones Bitcoin 30m")
    
    try:
        # 1. Sincronizar todas las órdenes con Binance
        logger.info("📊 Paso 1: Sincronizando base de datos con Binance...")
        await binance_order_checker.sync_database_with_binance()
        
        # 2. Arreglar específicamente las posiciones 3 y 6
        logger.info("🔧 Paso 2: Arreglando posiciones 3 y 6...")
        await binance_order_checker.fix_position_3_and_6()
        
        logger.info("✅ Verificación y arreglo completados exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error durante la verificación: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Proceso completado exitosamente!")
        print("Las posiciones han sido verificadas y arregladas.")
    else:
        print("\n💥 Proceso falló. Revisa los logs para más detalles.")
        sys.exit(1)
