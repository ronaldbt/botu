"""
Sistema de Cálculo de PnL (Profit and Loss) Real
Calcula ganancias/pérdidas reales por operación, descontando comisiones
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from app.db.models import TradingOrder
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)

class PnLCalculator:
    """Calculadora de ganancias/pérdidas reales"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_operation_pnl(self, buy_order: TradingOrder, sell_order: TradingOrder) -> Dict:
        """
        Calcula PnL real de una operación (compra + venta)
        
        Args:
            buy_order: Orden de compra
            sell_order: Orden de venta
            
        Returns:
            Dict con información detallada del PnL
        """
        try:
            # Cantidades
            buy_qty = float(buy_order.executed_quantity or 0)
            sell_qty = float(sell_order.executed_quantity or 0)
            
            # Precios
            buy_price = float(buy_order.executed_price or 0)
            sell_price = float(sell_order.executed_price or 0)
            
            # Calcular valores
            buy_value = buy_qty * buy_price
            sell_value = sell_qty * sell_price
            
            # PnL bruto
            gross_pnl = sell_value - buy_value
            gross_pnl_percent = (gross_pnl / buy_value * 100) if buy_value > 0 else 0
            
            # Comisiones (asumiendo 0.1% por operación)
            commission_rate = 0.001
            buy_commission = buy_value * commission_rate
            sell_commission = sell_value * commission_rate
            total_commission = buy_commission + sell_commission
            
            # PnL neto (descontando comisiones)
            net_pnl = gross_pnl - total_commission
            net_pnl_percent = (net_pnl / buy_value * 100) if buy_value > 0 else 0
            
            return {
                'buy_order_id': buy_order.id,
                'sell_order_id': sell_order.id,
                'buy_qty': buy_qty,
                'sell_qty': sell_qty,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'buy_value': buy_value,
                'sell_value': sell_value,
                'gross_pnl': gross_pnl,
                'gross_pnl_percent': gross_pnl_percent,
                'buy_commission': buy_commission,
                'sell_commission': sell_commission,
                'total_commission': total_commission,
                'net_pnl': net_pnl,
                'net_pnl_percent': net_pnl_percent,
                'is_profitable': net_pnl > 0
            }
            
        except Exception as e:
            logger.error(f"Error calculando PnL: {e}")
            return {}
    
    def get_all_operations_pnl(self, api_key_id: int) -> List[Dict]:
        """
        Obtiene PnL de todas las operaciones completadas
        
        Args:
            api_key_id: ID de la API key
            
        Returns:
            Lista de operaciones con PnL calculado
        """
        try:
            # Buscar todas las órdenes de compra cerradas
            closed_buys = self.db.query(TradingOrder).filter(
                TradingOrder.api_key_id == api_key_id,
                TradingOrder.symbol == 'BTCUSDT',
                TradingOrder.side == 'BUY',
                TradingOrder.status.in_(['CLOSED', 'completed'])
            ).order_by(TradingOrder.created_at.desc()).all()
            
            operations = []
            for buy_order in closed_buys:
                # Buscar venta asociada
                sell_order = self.db.query(TradingOrder).filter(
                    TradingOrder.api_key_id == api_key_id,
                    TradingOrder.symbol == 'BTCUSDT',
                    TradingOrder.side == 'SELL',
                    TradingOrder.status == 'FILLED',
                    TradingOrder.created_at > buy_order.created_at
                ).order_by(TradingOrder.created_at.asc()).first()
                
                if sell_order:
                    pnl_data = self.calculate_operation_pnl(buy_order, sell_order)
                    if pnl_data:
                        pnl_data['buy_created_at'] = buy_order.created_at
                        pnl_data['sell_created_at'] = sell_order.created_at
                        operations.append(pnl_data)
            
            return operations
            
        except Exception as e:
            logger.error(f"Error obteniendo operaciones PnL: {e}")
            return []
    
    def get_total_pnl_summary(self, api_key_id: int) -> Dict:
        """
        Obtiene resumen total de PnL
        
        Args:
            api_key_id: ID de la API key
            
        Returns:
            Resumen total de ganancias/pérdidas
        """
        try:
            operations = self.get_all_operations_pnl(api_key_id)
            
            if not operations:
                return {
                    'total_operations': 0,
                    'total_gross_pnl': 0,
                    'total_net_pnl': 0,
                    'total_commission': 0,
                    'profitable_operations': 0,
                    'losing_operations': 0,
                    'win_rate': 0
                }
            
            total_gross_pnl = sum(op['gross_pnl'] for op in operations)
            total_net_pnl = sum(op['net_pnl'] for op in operations)
            total_commission = sum(op['total_commission'] for op in operations)
            
            profitable_ops = sum(1 for op in operations if op['is_profitable'])
            losing_ops = len(operations) - profitable_ops
            win_rate = (profitable_ops / len(operations) * 100) if operations else 0
            
            return {
                'total_operations': len(operations),
                'total_gross_pnl': total_gross_pnl,
                'total_net_pnl': total_net_pnl,
                'total_commission': total_commission,
                'profitable_operations': profitable_ops,
                'losing_operations': losing_ops,
                'win_rate': win_rate,
                'operations': operations
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen PnL: {e}")
            return {}
