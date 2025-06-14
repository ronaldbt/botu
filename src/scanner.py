# src/scanner.py

import yfinance as yf
yf.utils._use_pycurl = False
import pandas as pd
import numpy as np
import requests
from utils import calc_slope, log

# Parámetros configurables
RUPTURE_FACTOR = 1.02
MIN_SLOPE_LEFT = -0.5
POST_RUPTURA_THRESHOLD = 1.02  # 2% por encima del nivel de ruptura

# Sesión personalizada (se puede setear desde main.py o API)
_custom_session = None

def set_custom_session(session):
    """
    Permite setear una sesión de requests personalizada para yfinance.
    """
    global _custom_session
    _custom_session = session
    yf.utils.get_yf_session = lambda: _custom_session
    log("✅ Sesión personalizada configurada para yfinance.")

def scan_for_u(ticker, verbose=False):
    log(f"[{ticker}] Descargando datos mensuales de Yahoo Finance...")
    
    try:
        df = yf.download(ticker, interval="1mo", start="2018-01-01", progress=False)
    except Exception as e:
        log(f"[{ticker}] ❌ Error descargando datos: {e}")
        return {
            "alert": False,
            "nivel_ruptura": None,
            "precio_confirmacion": None,
            "slope_left": None,
            "estado_sugerido": "NO_DATA"
        }

    df.dropna(inplace=True)
    log(f"[{ticker}] Datos descargados. Total de velas recibidas: {len(df)}.")

    # Calcular mínimos locales
    df['min_local'] = (df['Low'].shift(2) > df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'])
    num_minimos = df['min_local'].sum()
    log(f"[{ticker}] Mínimos locales detectados: {num_minimos}.")

    # Si no hay mínimos locales, no hacemos nada
    if num_minimos == 0:
        log(f"[{ticker}] No se detectaron mínimos locales. Terminando escaneo.")
        return {
            "alert": False,
            "nivel_ruptura": None,
            "precio_confirmacion": None,
            "slope_left": None,
            "estado_sugerido": "NO_MIN_LOCAL"
        }

    # Tomamos el último mínimo local
    min_row = df[df['min_local']].iloc[-1]
    nivel_ruptura = float(min_row['High']) * RUPTURE_FACTOR

    # Proteger min_row.name
    try:
        min_date = min_row.name.date()
    except Exception:
        min_date = str(min_row.name)

    log(f"[{ticker}] Último mínimo local en fecha {min_date}. Nivel de ruptura calculado (precio de confirmación): {nivel_ruptura:.2f}.")

    # Detectar pendiente del palo izquierdo (5 velas antes del mínimo)
    idx_min = df[df['min_local']].index[-1]
    idx_min_pos = df.index.get_loc(idx_min)

    if idx_min_pos < 5:
        log(f"[{ticker}] No hay suficientes velas antes del mínimo ({idx_min_pos} velas). Terminando escaneo.")
        return {
            "alert": False,
            "nivel_ruptura": nivel_ruptura,
            "precio_confirmacion": nivel_ruptura,
            "slope_left": None,
            "estado_sugerido": "NO_DATA"
        }

    left_window = df.iloc[idx_min_pos - 5:idx_min_pos]['Close']
    slope_left = float(calc_slope(left_window))
    log(f"[{ticker}] Pendiente del palo izquierdo (últimas 5 velas antes del mínimo): {slope_left:.2f}.")

    # Detectar si se rompió el nivel de ruptura
    close_actual = float(df['Close'].iloc[-1])
    log(f"[{ticker}] Precio de cierre actual: {close_actual:.2f}.")

    # === Determinar estado_sugerido ===
    estado_sugerido = "BASE"  # valor por defecto

    if slope_left < MIN_SLOPE_LEFT:
        if close_actual > nivel_ruptura:
            estado_sugerido = "RUPTURA"
        else:
            estado_sugerido = "PALO_BAJANDO"
    else:
        # Si el precio actual ya está por encima de nivel_ruptura + 2%, considerar como POST_RUPTURA
        if close_actual > nivel_ruptura * POST_RUPTURA_THRESHOLD:
            estado_sugerido = "POST_RUPTURA"
        else:
            estado_sugerido = "BASE"

    if verbose:
        print(f"[{ticker}] slope_left={slope_left:.2f}, nivel_ruptura={nivel_ruptura:.2f}, close_actual={close_actual:.2f}, estado_sugerido={estado_sugerido}")

    # === Retorno completo ===
    if slope_left < MIN_SLOPE_LEFT and close_actual > nivel_ruptura:
        log(f"[{ticker}] 🚀 ¡Condiciones cumplidas! Se detecta una U.")
        return {
            "alert": True,
            "nivel_ruptura": nivel_ruptura,
            "precio_confirmacion": nivel_ruptura,
            "slope_left": slope_left,
            "estado_sugerido": "RUPTURA"
        }
    else:
        log(f"[{ticker}] No se cumplen las condiciones para una U. Estado sugerido: {estado_sugerido}.")
        return {
            "alert": False,
            "nivel_ruptura": nivel_ruptura,
            "precio_confirmacion": nivel_ruptura,
            "slope_left": slope_left,
            "estado_sugerido": estado_sugerido
        }
