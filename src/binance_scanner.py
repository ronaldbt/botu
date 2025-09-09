# src/binance_scanner.py

import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar para DB
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

try:
    from app.db.database import SessionLocal  # type: ignore
    from app.db import models  # type: ignore
    from app.db import crud_tickers  # type: ignore
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    raise

# Importar módulos de Binance
from binance_client import fetch_klines, get_ticker_price
from binance_trader import place_market_buy, place_market_sell, get_account_balance

# Importar scanner existente
from scanner import scan_for_u
from binance_scanner_u import scan_for_u_binance
from binance_scanner_bnb import scan_for_u_bnb
from binance_scanner_eth import scan_for_u_eth
from binance_scanner_btc import scan_for_u_btc
from utils import log
from estado_u_utils import should_scan, update_estado_u

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceScanner:
    def __init__(self):
        self.session = SessionLocal()
        self.trading_enabled = os.getenv("BINANCE_TRADING_ENABLED", "false").lower() == "true"
        self.max_trade_amount = float(os.getenv("BINANCE_MAX_TRADE_AMOUNT", "50.0"))  # Máximo 50 USDT por trade
        self.stop_loss_percent = float(os.getenv("BINANCE_STOP_LOSS", "5.0"))  # 5% stop loss
        self.take_profit_percent = float(os.getenv("BINANCE_TAKE_PROFIT", "10.0"))  # 10% take profit
        
        # Parámetros específicos para BNB (basados en bnb_2023_backtest.py)
        self.bnb_stop_loss_percent = 3.0  # 3% stop loss para BNB (más conservador)
        self.bnb_take_profit_percent = 8.0  # 8% take profit para BNB (más realista)
        
        # Parámetros específicos para ETH (basados en eth_2023_backtest.py)
        self.eth_stop_loss_percent = 3.0  # 3% stop loss para ETH (más conservador)
        self.eth_take_profit_percent = 8.0  # 8% take profit para ETH (más realista)
        
        # Parámetros específicos para BTC (basados en bitcoin_2023_backtest.py actualizado)
        self.btc_stop_loss_percent = 3.0  # 3% stop loss para BTC (ahora conservador)
        self.btc_take_profit_percent = 8.0  # 8% take profit para BTC (ahora conservador)
        
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
    
    def get_crypto_tickers(self):
        """Obtiene solo los tickers de tipo crypto"""
        try:
            tickers_db = crud_tickers.get_all_tickers(self.session)
            crypto_tickers = [t for t in tickers_db if t.tipo == 'crypto' and t.activo]
            return [t.ticker for t in crypto_tickers]
        except Exception as e:
            logger.error(f"Error obteniendo tickers crypto: {e}")
            return []
    
    def convert_klines_to_ohlc(self, klines):
        """Convierte klines de Binance al formato esperado por el scanner"""
        ohlc_data = []
        for kline in klines:
            ohlc_data.append({
                'timestamp': kline['timestamp'],
                'open': kline['open'],
                'high': kline['high'],
                'low': kline['low'],
                'close': kline['close'],
                'volume': kline['volume']
            })
        return ohlc_data
    
    def scan_crypto_ticker(self, ticker):
        """Escanea un ticker crypto usando datos de Binance"""
        try:
            log(f"🔍 Escaneando {ticker} en Binance...")
            
            # Obtener velas de Binance (500 velas de 1 hora)
            klines = fetch_klines(ticker, "1h", 500)
            if not klines:
                log(f"❌ No se pudieron obtener velas para {ticker}")
                return None
            
            # Convertir al formato esperado por el scanner
            ohlc_data = self.convert_klines_to_ohlc(klines)
            
            # Usar el scanner específico según el ticker
            if ticker == "BNBUSDT":
                result = scan_for_u_bnb(ticker, klines, verbose=True)
                if verbose:
                    print(f"🪙 Usando estrategia BNB optimizada para {ticker}")
            elif ticker == "ETHUSDT":
                result = scan_for_u_eth(ticker, klines, verbose=True)
                if verbose:
                    print(f"💎 Usando estrategia ETH optimizada para {ticker}")
            elif ticker == "BTCUSDT":
                result = scan_for_u_btc(ticker, klines, verbose=True)
                if verbose:
                    print(f"₿ Usando estrategia BTC optimizada para {ticker}")
            else:
                result = scan_for_u_binance(ticker, klines, verbose=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error escaneando {ticker}: {e}")
            return None
    
    def create_alert(self, ticker, tipo_alerta, mensaje, nivel_ruptura=None, precio_actual=None):
        """Crea una alerta en la base de datos"""
        try:
            alerta = models.Alerta(
                ticker=ticker,
                tipo_alerta=tipo_alerta,
                mensaje=mensaje,
                nivel_ruptura=nivel_ruptura,
                precio_actual=precio_actual,
                fecha_creacion=datetime.now()
            )
            self.session.add(alerta)
            self.session.commit()
            log(f"📢 Alerta creada: {mensaje}")
        except Exception as e:
            logger.error(f"Error creando alerta: {e}")
            self.session.rollback()
    
    def create_order(self, ticker, tipo_orden, cantidad, precio=None, motivo=None, nivel_ruptura=None):
        """Crea una orden en la base de datos"""
        try:
            orden = models.Orden(
                ticker=ticker,
                tipo_orden=tipo_orden,
                cantidad=cantidad,
                precio=precio,
                estado='PENDING',
                motivo=motivo,
                nivel_ruptura=nivel_ruptura,
                fecha_creacion=datetime.now()
            )
            self.session.add(orden)
            self.session.commit()
            return orden
        except Exception as e:
            logger.error(f"Error creando orden: {e}")
            self.session.rollback()
            return None
    
    def execute_buy_order(self, ticker, nivel_ruptura, precio_actual):
        """Ejecuta una orden de compra cuando se detecta patrón U"""
        # Determinar estrategia específica para usar parámetros apropiados
        is_bnb = ticker == "BNBUSDT"
        is_eth = ticker == "ETHUSDT"
        is_btc = ticker == "BTCUSDT"
        strategy_info = (" (BNB Optimized)" if is_bnb else 
                        " (ETH Optimized)" if is_eth else 
                        " (BTC Optimized)" if is_btc else "")
        
        if not self.trading_enabled:
            log(f"🤖 Trading deshabilitado. Simulando compra de {ticker}{strategy_info}")
            self.create_alert(
                ticker, 
                'PATRON_U', 
                f"🚀 Patrón U detectado en {ticker}{strategy_info} - Compra simulada (Trading deshabilitado)",
                nivel_ruptura, 
                precio_actual
            )
            return None
        
        try:
            # Verificar balance disponible
            balance = get_account_balance('USDT')
            if not balance or balance['free'] < self.max_trade_amount:
                log(f"❌ Balance insuficiente para comprar {ticker}")
                self.create_alert(
                    ticker, 
                    'ERROR', 
                    f"Balance insuficiente para comprar {ticker}",
                    nivel_ruptura, 
                    precio_actual
                )
                return None
            
            # Crear orden en DB con motivo específico
            if is_bnb:
                motivo = 'PATRON_U_BNB_DETECTADO'
            elif is_eth:
                motivo = 'PATRON_U_ETH_DETECTADO'
            elif is_btc:
                motivo = 'PATRON_U_BTC_DETECTADO'
            else:
                motivo = 'PATRON_U_DETECTADO'
            orden = self.create_order(
                ticker=ticker,
                tipo_orden='BUY',
                cantidad=self.max_trade_amount,
                motivo=motivo,
                nivel_ruptura=nivel_ruptura
            )
            
            if not orden:
                return None
            
            # Ejecutar orden en Binance
            log(f"💰 Ejecutando compra de {self.max_trade_amount} USDT de {ticker}{strategy_info}")
            binance_order = place_market_buy(ticker, self.max_trade_amount)
            
            # Actualizar orden con resultado
            orden.binance_order_id = str(binance_order.get('orderId'))
            orden.estado = 'FILLED'
            orden.precio_ejecutado = float(binance_order.get('fills', [{}])[0].get('price', precio_actual))
            orden.fecha_ejecucion = datetime.now()
            self.session.commit()
            
            # Crear alerta de éxito
            if is_bnb:
                tipo_alerta = 'ORDEN_BNB_EJECUTADA'
            elif is_eth:
                tipo_alerta = 'ORDEN_ETH_EJECUTADA'
            elif is_btc:
                tipo_alerta = 'ORDEN_BTC_EJECUTADA'
            else:
                tipo_alerta = 'ORDEN_EJECUTADA'
            self.create_alert(
                ticker, 
                tipo_alerta, 
                f"✅ Compra ejecutada{strategy_info}: {self.max_trade_amount} USDT de {ticker} a {orden.precio_ejecutado}",
                nivel_ruptura, 
                orden.precio_ejecutado
            )
            
            log(f"✅ Compra exitosa: {ticker} - {self.max_trade_amount} USDT")
            return orden
            
        except Exception as e:
            logger.error(f"Error ejecutando compra: {e}")
            self.create_alert(
                ticker, 
                'ERROR', 
                f"Error ejecutando compra de {ticker}: {str(e)}",
                nivel_ruptura, 
                precio_actual
            )
            return None
    
    def process_ticker(self, ticker):
        """Procesa un ticker crypto completo"""
        try:
            # Verificar si se debe escanear
            if not should_scan(ticker):
                return
            
            log(f"🔍 Procesando {ticker}...")
            
            # Escanear con datos de Binance
            result = self.scan_crypto_ticker(ticker)
            if not result:
                return
            
            # Obtener precio actual
            precio_actual = get_ticker_price(ticker)
            
            # Determinar nuevo estado
            nuevo_estado = 'NO_U'
            is_bnb = ticker == "BNBUSDT"
            is_eth = ticker == "ETHUSDT"
            is_btc = ticker == "BTCUSDT"
            
            if result['alert']:
                nuevo_estado = 'RUPTURA'
                
                # Crear mensaje específico según la estrategia
                if is_bnb and result.get('strategy') == 'BNB_OPTIMIZED':
                    mensaje = (f"🚀 ¡Patrón U BNB detectado en {ticker}! "
                              f"Nivel: {result['precio_confirmacion']:.2f} "
                              f"(Estrategia BNB optimizada - Depth: {result.get('depth', 0)*100:.2f}%)")
                    tipo_alerta = 'PATRON_U_BNB'
                elif is_eth and result.get('strategy') == 'ETH_OPTIMIZED':
                    mensaje = (f"🚀 ¡Patrón U ETH detectado en {ticker}! "
                              f"Nivel: {result['precio_confirmacion']:.2f} "
                              f"(Estrategia ETH optimizada - Depth: {result.get('depth', 0)*100:.2f}%)")
                    tipo_alerta = 'PATRON_U_ETH'
                elif is_btc and result.get('strategy') == 'BTC_OPTIMIZED':
                    mensaje = (f"🚀 ¡Patrón U BTC detectado en {ticker}! "
                              f"Nivel: {result['precio_confirmacion']:.2f} "
                              f"(Estrategia BTC optimizada - Depth: {result.get('depth', 0)*100:.2f}%)")
                    tipo_alerta = 'PATRON_U_BTC'
                else:
                    mensaje = f"🚀 ¡Patrón U detectado en {ticker}! Nivel de ruptura: {result['precio_confirmacion']:.2f}"
                    tipo_alerta = 'PATRON_U'
                
                # Crear alerta de patrón U detectado
                self.create_alert(
                    ticker, 
                    tipo_alerta, 
                    mensaje,
                    result['nivel_ruptura'], 
                    precio_actual
                )
                
                # Ejecutar compra si está habilitado
                self.execute_buy_order(ticker, result['nivel_ruptura'], precio_actual)
                
            else:
                nuevo_estado = result.get('estado_sugerido', 'BASE')
                log(f"[{ticker}] No se detectó U. Estado: {nuevo_estado}")
            
            # Actualizar EstadoU en DB
            update_estado_u(
                ticker=ticker,
                nuevo_estado=nuevo_estado,
                nivel_ruptura=result['nivel_ruptura'] or 0.0,
                slope_left=result.get('slope_left', 0.0),
                precio_cierre=result.get('precio_confirmacion', precio_actual)
            )
            
        except Exception as e:
            logger.error(f"Error procesando {ticker}: {e}")
            self.create_alert(
                ticker, 
                'ERROR', 
                f"Error procesando {ticker}: {str(e)}",
                None, 
                None
            )
    
    def run_crypto_scan(self):
        """Ejecuta el escaneo de todos los tickers crypto"""
        log("🚀 Iniciando escaneo de criptomonedas en Binance...")
        
        # Obtener tickers crypto
        crypto_tickers = self.get_crypto_tickers()
        if not crypto_tickers:
            log("❌ No se encontraron tickers crypto activos")
            return
        
        log(f"📊 Escaneando {len(crypto_tickers)} criptomonedas...")
        
        for ticker in crypto_tickers:
            try:
                self.process_ticker(ticker)
                
                # Sleep entre tickers para evitar rate limits
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error en ticker {ticker}: {e}")
                continue
        
        log("✅ Escaneo de criptomonedas completado")

def main():
    """Función principal para ejecutar el scanner de crypto"""
    scanner = BinanceScanner()
    scanner.run_crypto_scan()

if __name__ == "__main__":
    main()

