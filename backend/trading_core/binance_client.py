# src/binance_client.py

import requests
import logging
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL de la API pública de Binance
BINANCE_API_BASE = "https://api.binance.com/api/v3"
BINANCE_TESTNET_BASE = "https://testnet.binance.vision/api/v3"

def get_spot_client():
    """
    Cliente público de Binance (sin API keys) - Solo para datos históricos
    """
    logger.info("Cliente Binance público creado - Solo datos históricos")
    return None  # No necesitamos cliente, usaremos requests directo

def fetch_klines(symbol: str, interval: str = "1h", limit: int = 1000):
    """
    Obtiene velas (klines) de Binance usando la API pública
    
    Args:
        symbol: Símbolo del par (ej: "BTCUSDT")
        interval: Intervalo de tiempo (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Número de velas a obtener (máx 1000)
    
    Returns:
        Lista de velas con formato [timestamp, open, high, low, close, volume, ...]
    """
    try:
        url = f"{BINANCE_API_BASE}/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        klines = response.json()
        logger.info(f"📊 Binance API devolvió {len(klines)} velas para {symbol} (intervalo: {interval})")
        
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
        
        logger.info(f"✅ Procesadas {len(formatted_klines)} velas para {symbol} - Rango: {datetime.fromtimestamp(formatted_klines[0]['timestamp']/1000).strftime('%Y-%m-%d')} a {datetime.fromtimestamp(formatted_klines[-1]['timestamp']/1000).strftime('%Y-%m-%d')}")
        return formatted_klines
        
    except requests.RequestException as e:
        logger.error(f"Error obteniendo klines para {symbol}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado obteniendo klines: {e}")
        raise

def get_symbol_info(symbol: str):
    """
    Obtiene información del símbolo (filtros, precisiones, etc.) usando la API pública
    """
    try:
        url = f"{BINANCE_API_BASE}/exchangeInfo"
        params = {'symbol': symbol.upper()}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        exchange_info = response.json()
        return exchange_info["symbols"][0]
    except requests.RequestException as e:
        logger.error(f"Error obteniendo info del símbolo {symbol}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado obteniendo info del símbolo {symbol}: {e}")
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
    Obtiene información de la cuenta - NO DISPONIBLE en API pública
    """
    logger.warning("get_account_info no está disponible en la API pública de Binance")
    raise NotImplementedError("Información de cuenta requiere API keys privadas")

def get_ticker_price(symbol: str):
    """
    Obtiene precio actual del símbolo usando la API pública
    """
    try:
        url = f"{BINANCE_API_BASE}/ticker/price"
        params = {'symbol': symbol.upper()}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        ticker = response.json()
        return float(ticker["price"])
    except requests.RequestException as e:
        logger.error(f"Error obteniendo precio de {symbol}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado obteniendo precio de {symbol}: {e}")
        raise

def fetch_current_price(symbol: str):
    """
    Alias para get_ticker_price para compatibilidad
    """
    return get_ticker_price(symbol)

def test_connection():
    """
    Prueba la conexión con Binance usando la API pública
    """
    try:
        url = f"{BINANCE_API_BASE}/time"
        response = requests.get(url)
        response.raise_for_status()
        
        server_time = response.json()
        logger.info(f"Conexión exitosa - Tiempo del servidor: {server_time}")
        return True
    except Exception as e:
        logger.error(f"Error de conexión: {e}")
        return False

class BinanceClient:
    """
    Cliente autenticado de Binance para operaciones que requieren API keys
    """
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.base_url = BINANCE_TESTNET_BASE if testnet else BINANCE_API_BASE
        
    def _generate_signature(self, params: str) -> str:
        """Genera firma HMAC SHA256 para autenticación"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: dict = None, signed: bool = False):
        """Realiza petición HTTP a la API de Binance"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        if params is None:
            params = {}
            
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            params['signature'] = self._generate_signature(query_string)
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, data=params)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Error en petición a Binance: {e}")
            if hasattr(e.response, 'json'):
                try:
                    error_detail = e.response.json()
                    logger.error(f"Detalles del error: {error_detail}")
                except:
                    pass
            raise
    
    def get_account_info(self):
        """Obtiene información de la cuenta"""
        try:
            return self._make_request('GET', 'account', signed=True)
        except Exception as e:
            logger.error(f"Error obteniendo información de cuenta: {e}")
            raise
    
    def test_connection(self):
        """Prueba la conexión autenticada"""
        try:
            # Probar primero conexión básica
            ping_url = f"{self.base_url}/ping"
            response = requests.get(ping_url)
            response.raise_for_status()
            
            # Probar autenticación
            account_info = self.get_account_info()
            return True, account_info
            
        except Exception as e:
            logger.error(f"Error en prueba de conexión autenticada: {e}")
            return False, str(e)
    
    def get_balances(self):
        """Obtiene balances de la cuenta"""
        try:
            account_info = self.get_account_info()
            return account_info.get('balances', [])
        except Exception as e:
            logger.error(f"Error obteniendo balances: {e}")
            raise

    def place_market_order(self, symbol: str, side: str, quantity: float):
        """
        Coloca una orden de mercado en Binance
        
        Args:
            symbol: Par de trading (ej: "BTCUSDT")
            side: "BUY" o "SELL"
            quantity: Cantidad a comprar/vender
            
        Returns:
            dict: {"success": bool, "order": dict, "error": str}
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'side': side.upper(),
                'type': 'MARKET',
                'quantity': f"{quantity:.8f}".rstrip('0').rstrip('.')
            }
            
            logger.info(f"🚀 Ejecutando orden {side} {quantity:.8f} {symbol} en {'TESTNET' if self.testnet else 'MAINNET'}")
            
            # Usar endpoint correcto según testnet/mainnet
            endpoint = 'order' if not self.testnet else 'order'
            
            order_response = self._make_request('POST', endpoint, params, signed=True)
            
            logger.info(f"✅ Orden ejecutada: {order_response.get('orderId')} - Status: {order_response.get('status')}")
            
            return {
                "success": True,
                "order": order_response,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error ejecutando orden {side} {symbol}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "order": None,
                "error": error_msg
            }

    def place_order(self, **kwargs):
        """
        Coloca una orden general en Binance (market o limit)
        
        Args:
            symbol: Par de trading (ej: "BTCUSDT")
            side: "BUY" o "SELL"
            type: "MARKET" o "LIMIT"
            quantity: Cantidad a comprar/vender
            price: Precio (solo para órdenes LIMIT)
            timeInForce: "GTC", "IOC", "FOK" (solo para órdenes LIMIT)
            
        Returns:
            dict: Respuesta de Binance con detalles de la orden
        """
        try:
            # Validar parámetros requeridos
            required_params = ['symbol', 'side', 'type', 'quantity']
            for param in required_params:
                if param not in kwargs:
                    raise ValueError(f"Parámetro requerido faltante: {param}")
            
            params = {
                'symbol': kwargs['symbol'].upper(),
                'side': kwargs['side'].upper(),
                'type': kwargs['type'].upper(),
                'quantity': f"{float(kwargs['quantity']):.8f}".rstrip('0').rstrip('.')
            }
            
            # Agregar parámetros específicos para órdenes LIMIT
            if kwargs['type'].upper() == 'LIMIT':
                if 'price' not in kwargs:
                    raise ValueError("Precio requerido para órdenes LIMIT")
                params['price'] = f"{float(kwargs['price']):.2f}"
                params['timeInForce'] = kwargs.get('timeInForce', 'GTC')
            
            logger.info(f"🚀 Ejecutando orden {kwargs['side']} {kwargs['type']} {kwargs['quantity']} {kwargs['symbol']} en {'TESTNET' if self.testnet else 'MAINNET'}")
            
            order_response = self._make_request('POST', 'order', params, signed=True)
            
            logger.info(f"✅ Orden ejecutada: {order_response.get('orderId')} - Status: {order_response.get('status')}")
            
            return order_response
            
        except Exception as e:
            error_msg = f"Error ejecutando orden {kwargs.get('side', 'N/A')} {kwargs.get('symbol', 'N/A')}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

    def cancel_order(self, symbol: str, order_id: str):
        """
        Cancela una orden por ID
        
        Args:
            symbol: Par de trading
            order_id: ID de la orden a cancelar
            
        Returns:
            dict: {"success": bool, "order": dict, "error": str}
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'orderId': order_id
            }
            
            response = self._make_request('DELETE', 'order', params, signed=True)
            
            return {
                "success": True,
                "order": response,
                "error": None
            }
            
        except Exception as e:
            error_msg = f"Error cancelando orden {order_id}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "order": None,
                "error": error_msg
            }

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


