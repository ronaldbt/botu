# src/scanner_crypto.py
# Scanner dedicado exclusivamente para criptomonedas usando Binance API pública

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance_client import fetch_klines, get_ticker_price
from utils import calc_slope, log

# Parámetros específicos para CRYPTO
CRYPTO_CONFIG = {
    'TIMEFRAME': '4h',  # Timeframe principal para detección
    'CONFIRMATION_TIMEFRAME': '1d',  # Timeframe para confirmación
    'LOOKBACK_PERIODS': 200,  # Períodos a analizar
    'MIN_WINDOW': 10,  # Ventana mínima para detectar mínimos locales
    'RUPTURE_FACTOR_MIN': 1.03,  # 3% mínimo para crypto volátil
    'RUPTURE_FACTOR_MAX': 1.08,  # 8% máximo
    'MIN_SLOPE_LEFT': -0.3,  # Pendiente mínima del lado izquierdo
    'VOLUME_CONFIRMATION': True,  # Requerir confirmación de volumen
    'U_MIN_WIDTH': 5,  # Mínimo 5 períodos de ancho de la U
    'U_MAX_WIDTH': 50,  # Máximo 50 períodos de ancho
    'PROFIT_TARGET': 0.12,  # 12% profit target para crypto
    'STOP_LOSS': 0.05,  # 5% stop loss
}

def calculate_atr(df, period=14):
    """Calcula Average True Range para volatilidad dinámica"""
    df['prev_close'] = df['close'].shift(1)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['prev_close'])
    df['tr3'] = abs(df['low'] - df['prev_close'])
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    df['atr'] = df['tr'].rolling(period).mean()
    return df['atr'].iloc[-1]

def detect_significant_lows(df, window=10, min_depth_pct=0.03):
    """
    Detecta mínimos locales significativos
    - window: ventana para buscar mínimos
    - min_depth_pct: profundidad mínima del mínimo (3% default)
    """
    lows = []
    
    for i in range(window, len(df) - window):
        current_low = df.iloc[i]['low']
        
        # Verificar que es mínimo en la ventana
        window_slice = df.iloc[i-window:i+window+1]
        if current_low == window_slice['low'].min():
            
            # Verificar profundidad: debe ser X% más bajo que máximo local
            local_high = window_slice['high'].max()
            depth = (local_high - current_low) / local_high
            
            if depth >= min_depth_pct:
                lows.append({
                    'index': i,
                    'timestamp': df.iloc[i]['timestamp'],
                    'low': current_low,
                    'high': df.iloc[i]['high'],
                    'close': df.iloc[i]['close'],
                    'volume': df.iloc[i]['volume'],
                    'depth': depth
                })
    
    return lows

def calculate_dynamic_rupture_factor(atr, price, base_factor=1.03):
    """
    Calcula factor de ruptura dinámico basado en volatilidad
    """
    # ATR como porcentaje del precio
    atr_pct = atr / price
    
    # Ajustar factor según volatilidad
    if atr_pct < 0.02:  # Baja volatilidad
        factor = base_factor
    elif atr_pct < 0.05:  # Volatilidad media
        factor = base_factor + (atr_pct * 0.5)
    else:  # Alta volatilidad
        factor = min(base_factor + (atr_pct * 0.8), CRYPTO_CONFIG['RUPTURE_FACTOR_MAX'])
    
    return max(factor, CRYPTO_CONFIG['RUPTURE_FACTOR_MIN'])

def validate_u_pattern(df, min_idx, atr):
    """
    Valida que el patrón sea realmente una U válida
    """
    min_row = df.iloc[min_idx]
    current_price = df.iloc[-1]['close']
    
    # 1. Verificar ancho del patrón
    pattern_width = len(df) - min_idx - 1
    if pattern_width < CRYPTO_CONFIG['U_MIN_WIDTH'] or pattern_width > CRYPTO_CONFIG['U_MAX_WIDTH']:
        return False, "Patrón demasiado estrecho o ancho"
    
    # 2. Verificar que no hay otros mínimos significativos muy recientes
    recent_lows = detect_significant_lows(df.iloc[min_idx:], window=3, min_depth_pct=0.02)
    if len(recent_lows) > 1:
        return False, "Múltiples mínimos recientes"
    
    # 3. Verificar momentum (precio debe estar recuperándose)
    recent_slope = calc_slope(df.iloc[-5:]['close'])
    if recent_slope <= 0:
        return False, "Sin momentum alcista"
    
    return True, "Patrón válido"

def analyze_volume_pattern(df, min_idx):
    """
    Analiza patrón de volumen para confirmar U
    """
    if not CRYPTO_CONFIG['VOLUME_CONFIRMATION']:
        return True, "Confirmación de volumen deshabilitada"
    
    # Volumen promedio antes del mínimo
    pre_min_volume = df.iloc[:min_idx]['volume'].mean()
    
    # Volumen en el mínimo (debería ser bajo)
    min_volume = df.iloc[min_idx-2:min_idx+3]['volume'].mean()
    
    # Volumen reciente (debería incrementar)
    recent_volume = df.iloc[-5:]['volume'].mean()
    
    volume_increase = recent_volume / pre_min_volume if pre_min_volume > 0 else 1
    
    if volume_increase < 1.2:  # Al menos 20% más volumen
        return False, f"Volumen insuficiente: {volume_increase:.2f}x"
    
    return True, f"Volumen confirmado: {volume_increase:.2f}x"

def scan_crypto_for_u(symbol, verbose=False):
    """
    Scanner principal para criptomonedas usando datos exclusivos de Binance
    """
    log(f"🔍 [CRYPTO] Escaneando {symbol} con datos Binance...")
    
    try:
        # Obtener datos de Binance (4h timeframe)
        klines = fetch_klines(symbol, CRYPTO_CONFIG['TIMEFRAME'], CRYPTO_CONFIG['LOOKBACK_PERIODS'])
        if not klines:
            return create_error_result("No se pudieron obtener datos de Binance")
        
        # Convertir a DataFrame
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        log(f"[{symbol}] Datos obtenidos: {len(df)} velas de {CRYPTO_CONFIG['TIMEFRAME']}")
        
        # Calcular ATR para volatilidad
        atr = calculate_atr(df.copy())
        current_price = df.iloc[-1]['close']
        
        # Detectar mínimos locales significativos
        significant_lows = detect_significant_lows(df, window=CRYPTO_CONFIG['MIN_WINDOW'])
        
        if not significant_lows:
            return create_result(symbol, "NO_MIN_LOCAL", None, None, None, current_price, 
                               "No se detectaron mínimos locales significativos")
        
        # Tomar el mínimo más reciente
        last_low = significant_lows[-1]
        min_idx = last_low['index']
        
        log(f"[{symbol}] Último mínimo significativo: {last_low['low']:.4f} (profundidad: {last_low['depth']:.2%})")
        
        # Calcular factor de ruptura dinámico
        dynamic_factor = calculate_dynamic_rupture_factor(atr, current_price)
        nivel_ruptura = last_low['high'] * dynamic_factor
        
        log(f"[{symbol}] Factor de ruptura dinámico: {dynamic_factor:.3f} -> Nivel: {nivel_ruptura:.4f}")
        
        # Validar patrón U
        is_valid_u, u_message = validate_u_pattern(df, min_idx, atr)
        if not is_valid_u:
            return create_result(symbol, "INVALID_PATTERN", nivel_ruptura, None, None, current_price, u_message)
        
        # Analizar volumen
        volume_ok, volume_message = analyze_volume_pattern(df, min_idx)
        
        # Calcular pendiente izquierda
        left_window_size = min(10, min_idx)
        if left_window_size < 5:
            return create_result(symbol, "NO_DATA", nivel_ruptura, None, None, current_price, 
                               "Insuficientes datos antes del mínimo")
        
        left_window = df.iloc[min_idx - left_window_size:min_idx]['close']
        slope_left = calc_slope(left_window)
        
        log(f"[{symbol}] Pendiente izquierda: {slope_left:.3f}")
        log(f"[{symbol}] {volume_message}")
        
        # Determinar estado
        if slope_left < CRYPTO_CONFIG['MIN_SLOPE_LEFT'] and current_price > nivel_ruptura and volume_ok:
            # ¡RUPTURA CONFIRMADA!
            profit_target = nivel_ruptura * (1 + CRYPTO_CONFIG['PROFIT_TARGET'])
            stop_loss = nivel_ruptura * (1 - CRYPTO_CONFIG['STOP_LOSS'])
            
            return create_result(symbol, "RUPTURA", nivel_ruptura, slope_left, profit_target, 
                               current_price, f"🚀 RUPTURA CONFIRMADA! Target: {profit_target:.4f}, SL: {stop_loss:.4f}")
        
        elif slope_left < CRYPTO_CONFIG['MIN_SLOPE_LEFT']:
            return create_result(symbol, "U_DETECTADO", nivel_ruptura, slope_left, None, current_price, 
                               "⚠️ Patrón U detectado, esperando ruptura")
        
        elif current_price > nivel_ruptura * 1.05:  # 5% arriba
            return create_result(symbol, "POST_RUPTURA", nivel_ruptura, slope_left, None, current_price, 
                               "📈 Post-ruptura detectada")
        
        else:
            return create_result(symbol, "BASE", nivel_ruptura, slope_left, None, current_price, 
                               "📊 En formación de base")
            
    except Exception as e:
        log(f"❌ Error escaneando {symbol}: {e}")
        return create_error_result(f"Error: {str(e)}")

def create_result(symbol, estado, nivel_ruptura, slope_left, profit_target, current_price, message):
    """Crea resultado estructurado"""
    return {
        'symbol': symbol,
        'alert': estado == "RUPTURA",
        'nivel_ruptura': nivel_ruptura,
        'precio_confirmacion': nivel_ruptura,
        'slope_left': slope_left,
        'estado_sugerido': estado,
        'current_price': current_price,
        'profit_target': profit_target,
        'stop_loss': nivel_ruptura * (1 - CRYPTO_CONFIG['STOP_LOSS']) if nivel_ruptura else None,
        'message': message,
        'timeframe': CRYPTO_CONFIG['TIMEFRAME'],
        'scanner_type': 'CRYPTO_BINANCE'
    }

def create_error_result(error_msg):
    """Crea resultado de error"""
    return {
        'alert': False,
        'nivel_ruptura': None,
        'precio_confirmacion': None,
        'slope_left': None,
        'estado_sugerido': "ERROR",
        'message': error_msg,
        'scanner_type': 'CRYPTO_BINANCE'
    }

if __name__ == "__main__":
    # Test
    result = scan_crypto_for_u("BTCUSDT", verbose=True)
    print(f"Resultado: {result}")