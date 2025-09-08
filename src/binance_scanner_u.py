# src/binance_scanner_u.py

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def scan_for_u_binance(ticker, klines_data, verbose=False):
    """
    Versión del scanner de patrones U adaptada para datos de Binance
    
    Args:
        ticker: Símbolo del ticker (ej: "BTCUSDT")
        klines_data: Lista de velas de Binance
        verbose: Si mostrar logs detallados
    
    Returns:
        dict: Resultado del análisis
    """
    if verbose:
        print(f"[{ticker}] Procesando {len(klines_data)} velas de Binance...")
    
    try:
        # Convertir datos de Binance a DataFrame
        df = pd.DataFrame(klines_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convertir tipos de datos
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        
        # Ordenar por timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        if verbose:
            print(f"[{ticker}] Datos procesados. Total de velas: {len(df)}")
        
        # Calcular mínimos locales
        df['min_local'] = (df['low'].shift(2) > df['low'].shift(1)) & (df['low'].shift(1) < df['low'])
        
        # Filtrar mínimos locales
        min_locales = df[df['min_local']].copy()
        
        if verbose:
            print(f"[{ticker}] Mínimos locales detectados: {len(min_locales)}")
        
        if len(min_locales) < 3:
            if verbose:
                print(f"[{ticker}] No se detectaron suficientes mínimos locales. Terminando escaneo.")
            return {
                "alert": False,
                "nivel_ruptura": None,
                "precio_confirmacion": None,
                "slope_left": None,
                "estado_sugerido": "NO_MIN_LOCAL"
            }
        
        # Buscar patrón U
        for i in range(len(min_locales) - 2):
            min1 = min_locales.iloc[i]
            min2 = min_locales.iloc[i + 1]
            min3 = min_locales.iloc[i + 2]
            
            # Verificar si forman un patrón U
            if (min1['low'] > min2['low'] and 
                min3['low'] > min2['low'] and
                min1['low'] - min2['low'] > 0.05 * min2['low'] and  # Al menos 5% de diferencia
                min3['low'] - min2['low'] > 0.05 * min2['low']):
                
                # Calcular nivel de ruptura (máximo entre min1 y min3)
                start_idx = min1.name
                end_idx = min3.name
                resistencia = df.loc[start_idx:end_idx, 'high'].max()
                
                # Calcular slope_left (pendiente del lado izquierdo)
                slope_left = (min1['low'] - min2['low']) / (min2['timestamp'] - min1['timestamp']).total_seconds() / 86400  # por día
                
                # Precio actual
                precio_actual = df['close'].iloc[-1]
                
                # Verificar si ya rompió la resistencia
                if precio_actual > resistencia:
                    if verbose:
                        print(f"[{ticker}] ✅ PATRÓN U DETECTADO Y ROTO!")
                        print(f"[{ticker}] Nivel de ruptura: {resistencia:.4f}")
                        print(f"[{ticker}] Precio actual: {precio_actual:.4f}")
                        print(f"[{ticker}] Slope left: {slope_left:.6f}")
                    
                    return {
                        "alert": True,
                        "nivel_ruptura": resistencia,
                        "precio_confirmacion": precio_actual,
                        "slope_left": slope_left,
                        "estado_sugerido": "U_ROTO"
                    }
                else:
                    if verbose:
                        print(f"[{ticker}] ⚠️ Patrón U detectado pero no roto")
                        print(f"[{ticker}] Nivel de ruptura: {resistencia:.4f}")
                        print(f"[{ticker}] Precio actual: {precio_actual:.4f}")
                    
                    return {
                        "alert": False,
                        "nivel_ruptura": resistencia,
                        "precio_confirmacion": precio_actual,
                        "slope_left": slope_left,
                        "estado_sugerido": "U_DETECTADO"
                    }
        
        if verbose:
            print(f"[{ticker}] No se detectó patrón U")
        
        return {
            "alert": False,
            "nivel_ruptura": None,
            "precio_confirmacion": df['close'].iloc[-1],
            "slope_left": None,
            "estado_sugerido": "NO_U"
        }
        
    except Exception as e:
        logger.error(f"Error en scan_for_u_binance para {ticker}: {e}")
        return {
            "alert": False,
            "nivel_ruptura": None,
            "precio_confirmacion": None,
            "slope_left": None,
            "estado_sugerido": "ERROR"
        }
