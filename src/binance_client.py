# src/binance_client.py

import os
from dotenv import load_dotenv
from binance.spot import Spot as SpotClient
from binance.error import ClientError
import logging

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_spot_client():
    """
    Crea cliente de Binance Spot con soporte para testnet
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    use_testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
    
    if not api_key or not api_secret:
        raise ValueError("BINANCE_API_KEY y BINANCE_API_SECRET deben estar configurados en .env")
    
    # URL base para testnet
    base_url = "https://testnet.binance.vision" if use_testnet else None
    
    client = SpotClient(
        api_key=api_key,
        api_secret=api_secret,
        base_url=base_url
    )
    
    logger.info(f"Cliente Binance creado - Testnet: {use_testnet}")
    return client

def fetch_klines(symbol: str, interval: str = "1h", limit: int = 200):
    """
    Obtiene velas (klines) de Binance
    
    Args:
        symbol: Símbolo del par (ej: "BTCUSDT")
        interval: Intervalo de tiempo (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Número de velas a obtener (máx 1000)
    
    Returns:
        Lista de velas con formato [timestamp, open, high, low, close, volume, ...]
    """
    try:
        client = get_spot_client()
        klines = client.klines(symbol, interval, limit=limit)
        
        # Convertir a formato más limpio
        formatted_klines = []
        for kline in klines:
            formatted_klines.append({
                'timestamp': int(kline[0]),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'close_time': int(kline[6]),
                'quote_volume': float(kline[7]),
                'trades': int(kline[8]),
                'taker_buy_base': float(kline[9]),
                'taker_buy_quote': float(kline[10])
            })
        
        logger.info(f"Obtenidas {len(formatted_klines)} velas para {symbol}")
        return formatted_klines
        
    except ClientError as e:
        logger.error(f"Error obteniendo klines para {symbol}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado obteniendo klines: {e}")
        raise

def get_symbol_info(symbol: str):
    """
    Obtiene información del símbolo (filtros, precisiones, etc.)
    """
    try:
        client = get_spot_client()
        exchange_info = client.exchange_info(symbol=symbol)
        return exchange_info["symbols"][0]
    except ClientError as e:
        logger.error(f"Error obteniendo info del símbolo {symbol}: {e}")
        raise

def get_filters(symbol_info: dict):
    """
    Extrae filtros importantes del símbolo
    """
    lot = next(f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE")
    price = next(f for f in symbol_info["filters"] if f["filterType"] == "PRICE_FILTER")
    notional = next(f for f in symbol_info["filters"] if f["filterType"] == "NOTIONAL")
    return lot, price, notional

def get_account_info():
    """
    Obtiene información de la cuenta
    """
    try:
        client = get_spot_client()
        account = client.account()
        return account
    except ClientError as e:
        logger.error(f"Error obteniendo info de cuenta: {e}")
        raise

def get_ticker_price(symbol: str):
    """
    Obtiene precio actual del símbolo
    """
    try:
        client = get_spot_client()
        ticker = client.ticker_price(symbol)
        return float(ticker["price"])
    except ClientError as e:
        logger.error(f"Error obteniendo precio de {symbol}: {e}")
        raise

def test_connection():
    """
    Prueba la conexión con Binance
    """
    try:
        client = get_spot_client()
        # Probar con un endpoint simple
        server_time = client.time()
        logger.info(f"Conexión exitosa - Tiempo del servidor: {server_time}")
        return True
    except Exception as e:
        logger.error(f"Error de conexión: {e}")
        return False

if __name__ == "__main__":
    # Prueba básica
    print("Probando conexión con Binance...")
    if test_connection():
        print("✅ Conexión exitosa")
        
        # Probar obtención de velas
        try:
            klines = fetch_klines("BTCUSDT", "1h", 10)
            print(f"✅ Velas obtenidas: {len(klines)}")
            print(f"Última vela: {klines[-1]}")
        except Exception as e:
            print(f"❌ Error obteniendo velas: {e}")
    else:
        print("❌ Error de conexión")


