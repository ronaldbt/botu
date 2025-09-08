# src/binance_trader.py

import os
import logging
from dotenv import load_dotenv
from binance_client import get_spot_client, get_symbol_info, get_filters, get_ticker_price
from binance.error import ClientError

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def round_step(quantity: float, step_size: float) -> float:
    """
    Redondea cantidad según el step size del símbolo
    """
    precision = max(0, str(step_size)[::-1].find('.'))
    return float(f"{(int(quantity / step_size) * step_size):.{precision}f}")

def place_market_buy(symbol: str, quote_amount_usdt: float):
    """
    Realiza compra market con cantidad en USDT
    
    Args:
        symbol: Símbolo del par (ej: "BTCUSDT")
        quote_amount_usdt: Cantidad en USDT a gastar
    
    Returns:
        Respuesta de la orden
    """
    try:
        client = get_spot_client()
        
        # Obtener precio actual
        price = get_ticker_price(symbol)
        logger.info(f"Precio actual de {symbol}: {price}")
        
        # Calcular cantidad de base
        qty = quote_amount_usdt / price
        
        # Obtener información del símbolo y filtros
        symbol_info = get_symbol_info(symbol)
        lot, price_filter, notional = get_filters(symbol_info)
        
        # Extraer valores de filtros
        step_size = float(lot["stepSize"])
        min_qty = float(lot["minQty"])
        min_notional = float(notional["minNotional"])
        
        # Ajustar cantidad según filtros
        qty = max(min_qty, round_step(qty, step_size))
        
        # Verificar notional mínimo
        if qty * price < min_notional:
            raise ValueError(f"Monto insuficiente. Mínimo: {min_notional} USDT")
        
        logger.info(f"Ejecutando compra market: {qty} {symbol} (~{quote_amount_usdt} USDT)")
        
        # Ejecutar orden
        order = client.new_order(
            symbol=symbol,
            side="BUY",
            type="MARKET",
            quantity=qty
        )
        
        logger.info(f"✅ Orden de compra ejecutada: {order}")
        return order
        
    except ClientError as e:
        logger.error(f"Error en compra market: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en compra: {e}")
        raise

def place_market_sell(symbol: str, quantity: float):
    """
    Realiza venta market con cantidad específica
    
    Args:
        symbol: Símbolo del par (ej: "BTCUSDT")
        quantity: Cantidad a vender
    
    Returns:
        Respuesta de la orden
    """
    try:
        client = get_spot_client()
        
        # Obtener información del símbolo y filtros
        symbol_info = get_symbol_info(symbol)
        lot, price_filter, notional = get_filters(symbol_info)
        
        # Extraer valores de filtros
        step_size = float(lot["stepSize"])
        min_qty = float(lot["minQty"])
        
        # Ajustar cantidad según filtros
        quantity = max(min_qty, round_step(quantity, step_size))
        
        logger.info(f"Ejecutando venta market: {quantity} {symbol}")
        
        # Ejecutar orden
        order = client.new_order(
            symbol=symbol,
            side="SELL",
            type="MARKET",
            quantity=quantity
        )
        
        logger.info(f"✅ Orden de venta ejecutada: {order}")
        return order
        
    except ClientError as e:
        logger.error(f"Error en venta market: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en venta: {e}")
        raise

def place_limit_buy(symbol: str, quantity: float, price: float):
    """
    Realiza compra limit con precio específico
    """
    try:
        client = get_spot_client()
        
        # Obtener información del símbolo y filtros
        symbol_info = get_symbol_info(symbol)
        lot, price_filter, notional = get_filters(symbol_info)
        
        # Extraer valores de filtros
        step_size = float(lot["stepSize"])
        min_qty = float(lot["minQty"])
        tick_size = float(price_filter["tickSize"])
        min_price = float(price_filter["minPrice"])
        max_price = float(price_filter["maxPrice"])
        
        # Ajustar cantidad y precio según filtros
        quantity = max(min_qty, round_step(quantity, step_size))
        price = max(min_price, round_step(price, tick_size))
        price = min(max_price, price)
        
        logger.info(f"Ejecutando compra limit: {quantity} {symbol} a {price}")
        
        # Ejecutar orden
        order = client.new_order(
            symbol=symbol,
            side="BUY",
            type="LIMIT",
            quantity=quantity,
            price=price,
            timeInForce="GTC"  # Good Till Cancel
        )
        
        logger.info(f"✅ Orden limit de compra creada: {order}")
        return order
        
    except ClientError as e:
        logger.error(f"Error en compra limit: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado en compra limit: {e}")
        raise

def get_open_orders(symbol: str = None):
    """
    Obtiene órdenes abiertas
    """
    try:
        client = get_spot_client()
        orders = client.get_open_orders(symbol=symbol)
        logger.info(f"Órdenes abiertas: {len(orders)}")
        return orders
    except ClientError as e:
        logger.error(f"Error obteniendo órdenes abiertas: {e}")
        raise

def cancel_order(symbol: str, order_id: int):
    """
    Cancela una orden específica
    """
    try:
        client = get_spot_client()
        result = client.cancel_order(symbol=symbol, orderId=order_id)
        logger.info(f"✅ Orden {order_id} cancelada: {result}")
        return result
    except ClientError as e:
        logger.error(f"Error cancelando orden: {e}")
        raise

def get_account_balance(asset: str = None):
    """
    Obtiene balance de la cuenta
    """
    try:
        client = get_spot_client()
        account = client.account()
        
        if asset:
            # Buscar balance específico
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return {
                        'asset': balance['asset'],
                        'free': float(balance['free']),
                        'locked': float(balance['locked'])
                    }
            return None
        else:
            # Retornar todos los balances con saldo > 0
            balances = []
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                if free > 0 or locked > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': free,
                        'locked': locked,
                        'total': free + locked
                    })
            return balances
            
    except ClientError as e:
        logger.error(f"Error obteniendo balance: {e}")
        raise

def test_trading_functions():
    """
    Prueba las funciones de trading (solo en testnet)
    """
    use_testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    
    if not use_testnet:
        logger.warning("⚠️  Esta función solo debe usarse en testnet!")
        return
    
    try:
        # Probar obtención de balance
        print("Probando obtención de balance...")
        balances = get_account_balance()
        print(f"Balances: {balances}")
        
        # Probar obtención de precio
        print("Probando obtención de precio...")
        price = get_ticker_price("BTCUSDT")
        print(f"Precio BTCUSDT: {price}")
        
        # Probar información del símbolo
        print("Probando información del símbolo...")
        symbol_info = get_symbol_info("BTCUSDT")
        print(f"Info BTCUSDT: {symbol_info['symbol']} - Status: {symbol_info['status']}")
        
        print("✅ Todas las pruebas pasaron")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")

if __name__ == "__main__":
    # Ejecutar pruebas
    test_trading_functions()


