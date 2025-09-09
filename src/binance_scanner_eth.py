# src/binance_scanner_eth.py

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def scan_for_u_eth(ticker, klines_data, verbose=False):
    """
    Scanner de patrones U optimizado específicamente para ETH
    Basado en la estrategia exitosa de eth_2023_backtest.py
    
    Args:
        ticker: Símbolo del ticker (ej: "ETHUSDT")
        klines_data: Lista de velas de Binance
        verbose: Si mostrar logs detallados
    
    Returns:
        dict: Resultado del análisis
    """
    if verbose:
        print(f"[{ticker}] 💎 Usando scanner ETH optimizado - {len(klines_data)} velas...")
    
    try:
        # Convertir datos de Binance a DataFrame
        df = pd.DataFrame(klines_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        # Convertir tipos de datos
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        
        # Ordenar por timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        if len(df) < 120:  # Necesitamos al menos 120 velas para el análisis ETH
            if verbose:
                print(f"[{ticker}] ❌ No hay suficientes datos para análisis ETH (necesario: 120, actual: {len(df)})")
            return {
                "alert": False,
                "nivel_ruptura": None,
                "precio_confirmacion": df['close'].iloc[-1] if len(df) > 0 else None,
                "slope_left": None,
                "estado_sugerido": "INSUFFICIENT_DATA",
                "strategy": "ETH_OPTIMIZED"
            }
        
        # Detectar señales usando algoritmo ETH optimizado
        signals = _detect_u_patterns_eth(df, verbose=verbose)
        
        if not signals:
            if verbose:
                print(f"[{ticker}] No se detectaron patrones U con criterios ETH")
            return {
                "alert": False,
                "nivel_ruptura": None,
                "precio_confirmacion": df['close'].iloc[-1],
                "slope_left": None,
                "estado_sugerido": "NO_U_ETH",
                "strategy": "ETH_OPTIMIZED"
            }
        
        # Tomar la mejor señal
        best_signal = signals[0]
        precio_actual = df['close'].iloc[-1]
        
        # Verificar si ya rompió el nivel
        if precio_actual > best_signal['entry_price']:
            if verbose:
                print(f"[{ticker}] ✅ PATRÓN U ETH DETECTADO Y ROTO!")
                print(f"[{ticker}] Nivel ETH: {best_signal['entry_price']:.4f}")
                print(f"[{ticker}] Precio actual: {precio_actual:.4f}")
                print(f"[{ticker}] Signal strength: {best_signal['signal_strength']:.4f}")
                print(f"[{ticker}] Profundidad: {best_signal['depth']*100:.2f}%")
                print(f"[{ticker}] ATR dinámico: {best_signal['atr']:.4f}")
            
            return {
                "alert": True,
                "nivel_ruptura": best_signal['entry_price'],
                "precio_confirmacion": precio_actual,
                "slope_left": best_signal['signal_strength'],
                "estado_sugerido": "U_ETH_ROTO",
                "strategy": "ETH_OPTIMIZED",
                "signal_strength": best_signal['signal_strength'],
                "depth": best_signal['depth'],
                "atr": best_signal['atr'],
                "dynamic_factor": best_signal['dynamic_factor']
            }
        else:
            if verbose:
                print(f"[{ticker}] ⚠️ Patrón U ETH detectado pero no roto")
                print(f"[{ticker}] Nivel ETH: {best_signal['entry_price']:.4f}")
                print(f"[{ticker}] Precio actual: {precio_actual:.4f}")
                print(f"[{ticker}] Falta: {((best_signal['entry_price']/precio_actual)-1)*100:.2f}%")
            
            return {
                "alert": False,
                "nivel_ruptura": best_signal['entry_price'],
                "precio_confirmacion": precio_actual,
                "slope_left": best_signal['signal_strength'],
                "estado_sugerido": "U_ETH_DETECTADO",
                "strategy": "ETH_OPTIMIZED",
                "signal_strength": best_signal['signal_strength'],
                "depth": best_signal['depth']
            }
        
    except Exception as e:
        logger.error(f"Error en scan_for_u_eth para {ticker}: {e}")
        return {
            "alert": False,
            "nivel_ruptura": None,
            "precio_confirmacion": None,
            "slope_left": None,
            "estado_sugerido": "ERROR",
            "strategy": "ETH_OPTIMIZED"
        }

def _detect_u_patterns_eth(df, verbose=False):
    """
    Detecta patrones U optimizado para ETH (similar a BNB, pero con parámetros específicos)
    Basado en la estrategia exitosa de eth_2023_backtest.py
    """
    signals = []
    
    # Detectar mínimos significativos optimizados para ETH
    significant_lows = _detect_lows_eth(df, window=6, min_depth_pct=0.025, verbose=verbose)  # 2.5% mínimo
    
    if not significant_lows:
        if verbose:
            print(f"   No se encontraron mínimos significativos para ETH")
        return signals
        
    # Analizar múltiples mínimos (no solo el último)
    for low in significant_lows[-3:]:  # Últimos 3 mínimos
        min_idx = low['index']
        
        # ATR y factor dinámico
        atr = _calculate_atr_simple(df)
        current_price = df.iloc[-1]['close']
        
        # Factor optimizado para ETH (bull market)
        dynamic_factor = _calculate_rupture_factor_eth(atr, current_price)
        nivel_ruptura = low['high'] * dynamic_factor
        
        # Condiciones optimizadas para ETH
        if len(df) - min_idx > 4 and len(df) - min_idx < 45:
            recent_slope = _calculate_slope(df.iloc[-6:]['close'].values)
            pre_slope = _calculate_slope(df.iloc[max(0, min_idx-6):min_idx]['close'].values)
            
            # Condiciones más estrictas para ETH (menos volátil que BTC)
            conditions = [
                pre_slope < -0.12,  # Más restrictivo para ETH
                current_price > nivel_ruptura * 0.97,  # Más conservador (97% vs 95%)
                recent_slope > -0.03,  # Momentum más positivo requerido
                low['depth'] >= 0.025,  # Al menos 2.5% de profundidad
                # Filtro adicional: evitar trades en tendencias bajistas prolongadas
                _check_momentum_filter_eth(df, min_idx)
            ]
            
            if all(conditions):
                signal_strength = abs(pre_slope)
                
                if verbose:
                    print(f"   ✨ Señal ETH válida encontrada:")
                    print(f"      Mínimo en índice: {min_idx}")
                    print(f"      Profundidad: {low['depth']*100:.2f}%")
                    print(f"      Nivel ruptura: {nivel_ruptura:.4f}")
                    print(f"      Factor dinámico: {dynamic_factor:.4f}")
                    print(f"      ATR: {atr:.4f}")
                    print(f"      Signal strength: {signal_strength:.4f}")
                
                signals.append({
                    'timestamp': df.index[-1],
                    'entry_price': nivel_ruptura,
                    'signal_strength': signal_strength,
                    'min_price': low['low'],
                    'pattern_width': len(df) - min_idx,
                    'atr': atr,
                    'dynamic_factor': dynamic_factor,
                    'depth': low['depth']
                })
                break  # Solo una señal por análisis
                
    return signals

def _detect_lows_eth(df, window=6, min_depth_pct=0.025, verbose=False):
    """Detecta mínimos optimizados para ETH"""
    lows = []
    
    for i in range(window, len(df) - window):
        current_low = df.iloc[i]['low']
        
        window_slice = df.iloc[i-window:i+window+1]
        if current_low == window_slice['low'].min():
            local_high = window_slice['high'].max()
            depth = (local_high - current_low) / local_high
            
            # Filtro adicional: verificar que no sea un mínimo muy reciente
            if depth >= min_depth_pct and i < len(df) - 5:
                # Verificar volumen para confirmar el mínimo
                volume_avg = df.iloc[i-window:i+window+1]['volume'].mean()
                current_volume = df.iloc[i]['volume']
                
                # Solo incluir si hay volumen suficiente o es un mínimo significativo
                if current_volume > volume_avg * 0.8 or depth >= 0.04:
                    lows.append({
                        'index': i,
                        'timestamp': df.index[i],
                        'low': current_low,
                        'high': df.iloc[i]['high'],
                        'close': df.iloc[i]['close'],
                        'volume': df.iloc[i]['volume'],
                        'depth': depth
                    })
    
    if verbose and lows:
        print(f"   Mínimos ETH detectados: {len(lows)} (profundidad min: {min_depth_pct*100:.1f}%)")
    
    return lows

def _calculate_rupture_factor_eth(atr, price, base_factor=1.015):
    """Factor de ruptura optimizado para ETH (similar a BNB, conservador)"""
    atr_pct = atr / price
    
    # Conservador para ETH (menos volátil que BTC)
    if atr_pct < 0.015:
        factor = base_factor
    elif atr_pct < 0.03:
        factor = base_factor + (atr_pct * 0.3)  # Menos agresivo
    else:
        factor = min(base_factor + (atr_pct * 0.5), 1.05)  # Máximo 5% para ETH
    
    return max(factor, 1.015)  # Mínimo 1.5%

def _check_momentum_filter_eth(df, min_idx):
    """Filtro de momentum para evitar trades en tendencias bajistas prolongadas"""
    if min_idx < 20:
        return True  # No hay suficientes datos para evaluar
    
    # Verificar tendencia de los últimos 20 períodos
    recent_20 = df.iloc[-20:]['close'].values
    trend_slope = _calculate_slope(recent_20)
    
    # Solo permitir trades si la tendencia general no es muy bajista
    return trend_slope > -0.1  # Permitir trades si pendiente > -0.1

def _calculate_atr_simple(df, period=14):
    """Calcula ATR simplificado"""
    tr_values = []
    for i in range(1, len(df)):
        high = df.iloc[i]['high']
        low = df.iloc[i]['low']
        prev_close = df.iloc[i-1]['close']
        
        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close)
        )
        tr_values.append(tr)
    
    return np.mean(tr_values[-period:]) if tr_values else df.iloc[-1]['high'] - df.iloc[-1]['low']

def _calculate_slope(values):
    """Calcula pendiente"""
    if len(values) < 2:
        return 0
    x = np.arange(len(values))
    return np.polyfit(x, values, 1)[0]