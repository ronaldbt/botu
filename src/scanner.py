import yfinance as yf
import pandas as pd
import numpy as np
from utils import calc_slope, log

# Parámetros configurables
RUPTURE_FACTOR = 1.02
MIN_SLOPE_LEFT = -0.5

def scan_for_u(ticker, verbose=False):
    log(f"[{ticker}] Descargando datos mensuales de Yahoo Finance...")
    df = yf.download(ticker, interval="1mo", start="2018-01-01", progress=False)
    df.dropna(inplace=True)
    log(f"[{ticker}] Datos descargados. Total de velas recibidas: {len(df)}.")

    # Calcular mínimos locales
    df['min_local'] = (df['Low'].shift(2) > df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'])
    num_minimos = df['min_local'].sum()
    log(f"[{ticker}] Mínimos locales detectados: {num_minimos}.")

    # Si no hay mínimos locales, no hacemos nada
    if num_minimos == 0:
        log(f"[{ticker}] No se detectaron mínimos locales. Terminando escaneo.")
        return {"alert": False, "nivel_ruptura": None, "precio_confirmacion": None}

    # Tomamos el último mínimo local
    min_row = df[df['min_local']].iloc[-1]
    nivel_ruptura = (min_row['High'] * RUPTURE_FACTOR).item()  # limpio

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
        return {"alert": False, "nivel_ruptura": nivel_ruptura, "precio_confirmacion": nivel_ruptura}

    left_window = df.iloc[idx_min_pos - 5:idx_min_pos]['Close']
    slope_left = float(calc_slope(left_window))
    log(f"[{ticker}] Pendiente del palo izquierdo (últimas 5 velas antes del mínimo): {slope_left:.2f}.")

    # Detectar si se rompió el nivel de ruptura
    close_actual = df['Close'].iloc[-1].item()  # limpio
    log(f"[{ticker}] Precio de cierre actual: {close_actual:.2f}.")

    if verbose:
        print(f"[{ticker}] slope_left={slope_left:.2f}, nivel_ruptura={nivel_ruptura:.2f}, close_actual={close_actual:.2f}")

    if slope_left < MIN_SLOPE_LEFT and close_actual > nivel_ruptura:
        log(f"[{ticker}] 🚀 ¡Condiciones cumplidas! Se detecta una U.")
        return {"alert": True, "nivel_ruptura": nivel_ruptura, "precio_confirmacion": nivel_ruptura}
    else:
        log(f"[{ticker}] No se cumplen las condiciones para una U. Terminando escaneo.")
        return {"alert": False, "nivel_ruptura": nivel_ruptura, "precio_confirmacion": nivel_ruptura}
