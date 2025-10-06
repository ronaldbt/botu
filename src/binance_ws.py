# src/binance_ws.py

import os
import json
import logging
from dotenv import load_dotenv
from binance.websocket.spot.websocket_client import SpotWebsocketClient as WSClient

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceWebSocket:
    def __init__(self):
        self.ws_client = None
        self.use_testnet = os.getenv("BINANCE_TESTNET", "true").lower() == "true"
        self.stream_url = "wss://testnet.binance.vision/ws" if self.use_testnet else None
        
    def start(self):
        """Inicia el cliente WebSocket"""
        self.ws_client = WSClient(stream_url=self.stream_url)
        self.ws_client.start()
        logger.info(f"WebSocket iniciado - Testnet: {self.use_testnet}")
    
    def stop(self):
        """Detiene el cliente WebSocket"""
        if self.ws_client:
            self.ws_client.stop()
            logger.info("WebSocket detenido")
    
    def subscribe_klines(self, symbol: str, interval: str = "1h", callback=None):
        """
        Suscribe a velas en tiempo real
        
        Args:
            symbol: Símbolo del par (ej: "BTCUSDT")
            interval: Intervalo de tiempo (1m, 5m, 15m, 1h, 4h, 1d)
            callback: Función a llamar cuando llegue una vela
        """
        if not self.ws_client:
            raise RuntimeError("WebSocket no iniciado. Llama a start() primero.")
        
        def default_callback(msg):
            if msg.get("e") == "kline":
                k = msg["k"]
                symbol = msg["s"]
                is_closed = k["x"]  # True si la vela está cerrada
                
                kline_data = {
                    'symbol': symbol,
                    'timestamp': int(k['t']),
                    'open': float(k['o']),
                    'high': float(k['h']),
                    'low': float(k['l']),
                    'close': float(k['c']),
                    'volume': float(k['v']),
                    'is_closed': is_closed,
                    'close_time': int(k['T'])
                }
                
                logger.info(f"Vela {symbol}: {kline_data['close']} - Cerrada: {is_closed}")
                
                # Llamar callback personalizado si existe
                if callback:
                    callback(kline_data)
        
        self.ws_client.kline(
            symbol=symbol.lower(),
            id=1,
            interval=interval,
            callback=callback or default_callback
        )
        
        logger.info(f"Suscrito a velas de {symbol} con intervalo {interval}")
    
    def subscribe_ticker(self, symbol: str, callback=None):
        """
        Suscribe a cambios de precio en tiempo real
        """
        if not self.ws_client:
            raise RuntimeError("WebSocket no iniciado. Llama a start() primero.")
        
        def default_callback(msg):
            ticker_data = {
                'symbol': msg['s'],
                'price': float(msg['c']),
                'change': float(msg['P']),
                'change_percent': float(msg['P']),
                'high': float(msg['h']),
                'low': float(msg['l']),
                'volume': float(msg['v'])
            }
            
            logger.info(f"Ticker {symbol}: {ticker_data['price']} ({ticker_data['change_percent']:+.2f}%)")
            
            if callback:
                callback(ticker_data)
        
        self.ws_client.ticker(
            symbol=symbol.lower(),
            id=2,
            callback=callback or default_callback
        )
        
        logger.info(f"Suscrito a ticker de {symbol}")

def run_klines_stream(symbol="BTCUSDT", interval="1h", callback=None):
    """
    Función de conveniencia para ejecutar stream de velas
    """
    ws = BinanceWebSocket()
    
    try:
        ws.start()
        ws.subscribe_klines(symbol, interval, callback)
        
        # Mantener vivo
        import time
        logger.info("Stream iniciado. Presiona Ctrl+C para detener...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Deteniendo stream...")
    finally:
        ws.stop()

if __name__ == "__main__":
    # Ejemplo de uso
    def on_kline_received(kline_data):
        print(f"Vela recibida: {kline_data}")
    
    def on_ticker_received(ticker_data):
        print(f"Ticker recibido: {ticker_data}")
    
    # Probar stream de velas
    print("Iniciando stream de velas BTCUSDT...")
    run_klines_stream("BTCUSDT", "1h", on_kline_received)


