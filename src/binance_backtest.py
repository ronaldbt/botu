# src/binance_backtest.py

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

# Importar para DB
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

try:
    from app.db.database import SessionLocal  # type: ignore
    from app.db import crud_tickers  # type: ignore
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    raise

from binance_client import get_spot_client, fetch_klines
from binance_scanner_u import scan_for_u_binance

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === PARAMETROS ===
RUPTURE_FACTOR = 1.02
MIN_SLOPE_LEFT = -0.5

def load_crypto_tickers_from_db():
    """Carga todos los tickers de crypto desde la base de datos"""
    logger.info("Cargando tickers de crypto desde base de datos...")
    
    session = SessionLocal()
    try:
        tickers_db = crud_tickers.get_all_tickers(session)
        crypto_tickers = [t.ticker for t in tickers_db if t.tipo == 'crypto' and t.activo]
        logger.info(f"Se cargaron {len(crypto_tickers)} tickers de crypto desde la DB.")
        return crypto_tickers
    finally:
        session.close()

def get_historical_klines(symbol, years_back=5):
    """
    Obtiene datos históricos de Binance para un símbolo específico
    
    Args:
        symbol: Símbolo del ticker (ej: "BTCUSDT")
        years_back: Años hacia atrás para obtener datos
    
    Returns:
        Lista de velas históricas
    """
    try:
        # Calcular fecha de inicio
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years_back * 365)
        
        logger.info(f"[{symbol}] Obteniendo datos históricos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
        
        # Obtener datos en chunks de 1000 velas (límite de Binance)
        all_klines = []
        current_start = start_date
        
        while current_start < end_date:
            try:
                # Obtener 1000 velas (aproximadamente 1000 horas = ~41 días)
                klines = fetch_klines(symbol, "1h", 1000)
                
                if not klines:
                    break
                
                # Filtrar por fecha
                filtered_klines = []
                for kline in klines:
                    kline_date = datetime.fromtimestamp(kline['timestamp'] / 1000)
                    if start_date <= kline_date <= end_date:
                        filtered_klines.append(kline)
                
                all_klines.extend(filtered_klines)
                
                # Actualizar fecha de inicio para el siguiente chunk
                if klines:
                    last_timestamp = klines[-1]['timestamp']
                    current_start = datetime.fromtimestamp(last_timestamp / 1000)
                else:
                    break
                
                # Pequeña pausa para no sobrecargar la API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"[{symbol}] Error obteniendo chunk de datos: {e}")
                break
        
        logger.info(f"[{symbol}] Obtenidas {len(all_klines)} velas históricas")
        return all_klines
        
    except Exception as e:
        logger.error(f"[{symbol}] Error obteniendo datos históricos: {e}")
        return []

def backtest_single_ticker(symbol, years_back=5):
    """
    Realiza backtest de un ticker específico
    
    Args:
        symbol: Símbolo del ticker
        years_back: Años hacia atrás para analizar
    
    Returns:
        dict: Resultados del backtest
    """
    logger.info(f"🔍 Iniciando backtest para {symbol} (últimos {years_back} años)")
    
    try:
        # Obtener datos históricos
        klines = get_historical_klines(symbol, years_back)
        
        if not klines:
            return {
                "symbol": symbol,
                "error": "No se pudieron obtener datos históricos",
                "signals": [],
                "total_signals": 0,
                "success_rate": 0,
                "years_analyzed": years_back
            }
        
        # Convertir a DataFrame para análisis
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"[{symbol}] Analizando {len(df)} velas históricas")
        
        # Detectar patrones U usando ventanas deslizantes
        signals = []
        window_size = 200  # Velas por ventana (aproximadamente 8-9 días)
        
        for i in range(window_size, len(df)):
            # Obtener ventana de datos
            window_data = df.iloc[i-window_size:i].copy()
            
            # Convertir a formato esperado por scan_for_u_binance
            klines_format = []
            for _, row in window_data.iterrows():
                klines_format.append([
                    int(row['timestamp'].timestamp() * 1000),  # timestamp
                    row['open'],  # open
                    row['high'],  # high
                    row['low'],   # low
                    row['close'], # close
                    row['volume'], # volume
                    int(row['timestamp'].timestamp() * 1000),  # close_time
                    0,  # quote_asset_volume
                    0,  # number_of_trades
                    0,  # taker_buy_base_asset_volume
                    0,  # taker_buy_quote_asset_volume
                    '0'  # ignore
                ])
            
            # Analizar patrón U en esta ventana
            result = scan_for_u_binance(symbol, klines_format, verbose=False)
            
            if result['alert'] and result['estado_sugerido'] == 'U_ROTO':
                # Verificar si la señal fue exitosa (precio subió después de la ruptura)
                current_price = result['precio_confirmacion']
                rupture_level = result['nivel_ruptura']
                
                # Buscar precio futuro para evaluar éxito
                future_window = df.iloc[i:i+50]  # Próximas 50 velas
                if len(future_window) > 0:
                    max_future_price = future_window['high'].max()
                    success = max_future_price > current_price * 1.02  # 2% de ganancia mínima
                    
                    signal = {
                        "timestamp": window_data.iloc[-1]['timestamp'],
                        "date": window_data.iloc[-1]['timestamp'].strftime('%Y-%m-%d %H:%M'),
                        "rupture_level": rupture_level,
                        "current_price": current_price,
                        "slope_left": result['slope_left'],
                        "max_future_price": max_future_price,
                        "success": success,
                        "profit_potential": ((max_future_price - current_price) / current_price) * 100
                    }
                    signals.append(signal)
                    
                    logger.info(f"[{symbol}] Señal detectada en {signal['date']} - "
                              f"Ruptura: {rupture_level:.4f}, "
                              f"Precio: {current_price:.4f}, "
                              f"Éxito: {success}, "
                              f"Ganancia: {signal['profit_potential']:.2f}%")
        
        # Calcular estadísticas
        total_signals = len(signals)
        successful_signals = len([s for s in signals if s['success']])
        success_rate = (successful_signals / total_signals * 100) if total_signals > 0 else 0
        
        logger.info(f"[{symbol}] Backtest completado - {total_signals} señales, "
                   f"{successful_signals} exitosas ({success_rate:.1f}%)")
        
        return {
            "symbol": symbol,
            "error": None,
            "signals": signals,
            "total_signals": total_signals,
            "successful_signals": successful_signals,
            "success_rate": success_rate,
            "years_analyzed": years_back,
            "total_candles": len(df)
        }
        
    except Exception as e:
        logger.error(f"[{symbol}] Error en backtest: {e}")
        return {
            "symbol": symbol,
            "error": str(e),
            "signals": [],
            "total_signals": 0,
            "success_rate": 0,
            "years_analyzed": years_back
        }

def get_available_tickers():
    """Obtiene lista de tickers disponibles para backtest"""
    return load_crypto_tickers_from_db()

if __name__ == "__main__":
    # Prueba con un ticker específico
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
        years = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        
        print(f"🚀 Iniciando backtest para {symbol} (últimos {years} años)")
        result = backtest_single_ticker(symbol, years)
        
        print(f"\n📊 Resultados del backtest:")
        print(f"Ticker: {result['symbol']}")
        print(f"Años analizados: {result['years_analyzed']}")
        print(f"Total de velas: {result.get('total_candles', 0)}")
        print(f"Señales detectadas: {result['total_signals']}")
        print(f"Señales exitosas: {result.get('successful_signals', 0)}")
        print(f"Tasa de éxito: {result['success_rate']:.1f}%")
        
        if result['signals']:
            print(f"\n📈 Primeras 5 señales:")
            for i, signal in enumerate(result['signals'][:5]):
                print(f"  {i+1}. {signal['date']} - "
                      f"Ruptura: {signal['rupture_level']:.4f}, "
                      f"Precio: {signal['current_price']:.4f}, "
                      f"Éxito: {signal['success']}, "
                      f"Ganancia: {signal['profit_potential']:.2f}%")
    else:
        print("Uso: python binance_backtest.py <SYMBOL> [YEARS]")
        print("Ejemplo: python binance_backtest.py BTCUSDT 5")