"""
Simulador de Órdenes para Pruebas del Sistema
Simula órdenes de compra y venta para probar todo el ciclo del sistema
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.db.database import get_db
from app.db.models import TradingOrder, TradingApiKey
from app.schemas.trading_schema import TradingOrderCreate
from app.services.trading_service import create_trading_order
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class OrderSimulator:
    """Simulador de órdenes para pruebas del sistema"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_simulated_buy_order(self, api_key_id: int, user_id: int, 
                                 quantity: float, price: float, 
                                 binance_order_id: str = None) -> TradingOrder:
        """
        Crea una orden de compra simulada
        
        Args:
            api_key_id: ID de la API key
            user_id: ID del usuario
            quantity: Cantidad de BTC
            price: Precio de compra
            binance_order_id: ID de orden de Binance (opcional)
            
        Returns:
            TradingOrder creada
        """
        try:
            # Crear orden de compra
            buy_order_data = TradingOrderCreate(
                api_key_id=api_key_id,
                symbol='BTCUSDT',
                side='buy',
                order_type='market',
                quantity=quantity,
                price=price
            )
            
            # Crear la orden en la base de datos
            buy_order = create_trading_order(self.db, buy_order_data, user_id)
            
            # Simular que la orden se ejecutó
            buy_order.status = 'FILLED'
            buy_order.executed_quantity = quantity
            buy_order.executed_price = price
            buy_order.binance_order_id = binance_order_id or f"SIM_BUY_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            buy_order.created_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"✅ Orden de compra simulada creada: ID {buy_order.id}, {quantity} BTC @ ${price:,.2f}")
            return buy_order
            
        except Exception as e:
            logger.error(f"Error creando orden de compra simulada: {e}")
            self.db.rollback()
            raise
    
    def create_simulated_sell_order(self, api_key_id: int, user_id: int,
                                  quantity: float, price: float,
                                  binance_order_id: str = None) -> TradingOrder:
        """
        Crea una orden de venta simulada
        
        Args:
            api_key_id: ID de la API key
            user_id: ID del usuario
            quantity: Cantidad de BTC
            price: Precio de venta
            binance_order_id: ID de orden de Binance (opcional)
            
        Returns:
            TradingOrder creada
        """
        try:
            # Crear orden de venta
            sell_order_data = TradingOrderCreate(
                api_key_id=api_key_id,
                symbol='BTCUSDT',
                side='sell',
                order_type='market',
                quantity=quantity,
                price=price
            )
            
            # Crear la orden en la base de datos
            sell_order = create_trading_order(self.db, sell_order_data, user_id)
            
            # Simular que la orden se ejecutó
            sell_order.status = 'FILLED'
            sell_order.executed_quantity = quantity
            sell_order.executed_price = price
            sell_order.binance_order_id = binance_order_id or f"SIM_SELL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            sell_order.created_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"✅ Orden de venta simulada creada: ID {sell_order.id}, {quantity} BTC @ ${price:,.2f}")
            return sell_order
            
        except Exception as e:
            logger.error(f"Error creando orden de venta simulada: {e}")
            self.db.rollback()
            raise
    
    def complete_position(self, buy_order: TradingOrder, sell_price: float) -> TradingOrder:
        """
        Completa una posición creando la orden de venta y marcando la compra como completada
        
        Args:
            buy_order: Orden de compra a completar
            sell_price: Precio de venta
            
        Returns:
            Orden de venta creada
        """
        try:
            # Crear orden de venta
            sell_order = self.create_simulated_sell_order(
                api_key_id=buy_order.api_key_id,
                user_id=buy_order.user_id,
                quantity=buy_order.executed_quantity,
                price=sell_price
            )
            
            # Marcar la orden de compra como completada
            buy_order.status = 'COMPLETED'
            self.db.commit()
            
            logger.info(f"✅ Posición completada: Buy ID {buy_order.id} -> Sell ID {sell_order.id}")
            return sell_order
            
        except Exception as e:
            logger.error(f"Error completando posición: {e}")
            self.db.rollback()
            raise
    
    def simulate_complete_trade_cycle(self, api_key_id: int, user_id: int,
                                    buy_price: float, sell_price: float,
                                    quantity: float = 0.0001) -> Dict:
        """
        Simula un ciclo completo de trading (compra + venta)
        
        Args:
            api_key_id: ID de la API key
            user_id: ID del usuario
            buy_price: Precio de compra
            sell_price: Precio de venta
            quantity: Cantidad de BTC
            
        Returns:
            Dict con información del ciclo completo
        """
        try:
            # 1. Crear orden de compra
            buy_order = self.create_simulated_buy_order(
                api_key_id=api_key_id,
                user_id=user_id,
                quantity=quantity,
                price=buy_price
            )
            
            # 2. Esperar un poco (simular tiempo de mercado)
            await asyncio.sleep(1)
            
            # 3. Crear orden de venta
            sell_order = self.create_simulated_sell_order(
                api_key_id=api_key_id,
                user_id=user_id,
                quantity=quantity,
                price=sell_price
            )
            
            # 4. Marcar compra como completada
            buy_order.status = 'COMPLETED'
            self.db.commit()
            
            # 5. Calcular PnL
            buy_value = quantity * buy_price
            sell_value = quantity * sell_price
            gross_pnl = sell_value - buy_value
            commission_rate = 0.001
            total_commission = (buy_value + sell_value) * commission_rate
            net_pnl = gross_pnl - total_commission
            
            result = {
                'buy_order_id': buy_order.id,
                'sell_order_id': sell_order.id,
                'quantity': quantity,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'buy_value': buy_value,
                'sell_value': sell_value,
                'gross_pnl': gross_pnl,
                'net_pnl': net_pnl,
                'total_commission': total_commission,
                'is_profitable': net_pnl > 0
            }
            
            logger.info(f"✅ Ciclo completo simulado: PnL neto ${net_pnl:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error simulando ciclo completo: {e}")
            raise
    
    def cleanup_simulated_orders(self, api_key_id: int):
        """
        Limpia órdenes simuladas (para pruebas)
        
        Args:
            api_key_id: ID de la API key
        """
        try:
            # Eliminar órdenes simuladas
            simulated_orders = self.db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key_id,
                TradingOrder.binance_order_id.like('SIM_%')
            ).all()
            
            for order in simulated_orders:
                self.db.delete(order)
            
            self.db.commit()
            logger.info(f"✅ {len(simulated_orders)} órdenes simuladas eliminadas")
            
        except Exception as e:
            logger.error(f"Error limpiando órdenes simuladas: {e}")
            self.db.rollback()
            raise
