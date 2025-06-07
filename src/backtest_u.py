import yfinance as yf
import pandas as pd
import numpy as np
import time
from utils import calc_slope, log

# Parámetros configurables
RUPTURE_FACTOR = 1.02
MIN_SLOPE_LEFT = -0.5

# Carga tickers
def load_tickers(file_path):
    log(f"Cargando tickers desde archivo: {file_path}")
    with open(file_path, 'r') as f:
        tickers = [line.strip() for line in f if line.strip() != ""]
    log(f"Se cargaron {len(tickers)} tickers.")
    return tickers

# BACKTEST SCANNER
def backtest_scan_for_u(ticker):
    log(f"[{ticker}] Descargando datos mensuales de Yahoo Finance para backtest...")
    df = yf.download(ticker, interval="1mo", start="2018-01-01", progress=False)
    df.dropna(inplace=True)
    log(f"[{ticker}] Datos descargados. Total de velas recibidas: {len(df)}.")

    df['min_local'] = (df['Low'].shift(2) > df['Low'].shift(1)) & (df['Low'].shift(1) < df['Low'])

    u_signals = []

    # Recorremos cada mínimo local
    for idx_min in df[df['min_local']].index:
        idx_min_pos = df.index.get_loc(idx_min)

        if idx_min_pos < 5 or idx_min_pos >= len(df) - 1:
            continue  # no hay suficientes velas antes o después

        # Palo izquierdo
        left_window = df.iloc[idx_min_pos - 5:idx_min_pos]['Close']
        slope_left = float(calc_slope(left_window))

        # Nivel de ruptura
        min_row = df.loc[idx_min]
        nivel_ruptura = min_row['High'].item() * RUPTURE_FACTOR  # CORREGIDO: uso .item()

        # Ver si en las velas posteriores se rompe el nivel
        df_future = df.iloc[idx_min_pos + 1:]  # velas después del mínimo

        for idx_future, row_future in df_future.iterrows():
            close_actual = row_future['Close'].item()  # CORREGIDO: uso .item()
            if slope_left < MIN_SLOPE_LEFT and close_actual > nivel_ruptura:
                # Se detecta U
                signal = {
                    "fecha": idx_future.date(),
                    "nivel_ruptura": nivel_ruptura,
                    "slope_left": slope_left,
                    "precio_cierre": close_actual
                }
                u_signals.append(signal)
                log(f"[{ticker}] U detectada en {signal['fecha']} - Nivel ruptura: {nivel_ruptura:.2f}, Slope: {slope_left:.2f}, Close: {close_actual:.2f}")
                break  # solo consideramos la primera ruptura tras ese mínimo

    return u_signals

# MAIN BACKTEST
if __name__ == "__main__":
    start_time = time.time()
    log("🚀 Iniciando BACKTEST de detección de U en históricos...")

    tickers = load_tickers('tickers.txt')

    for ticker in tickers:
        log(f"🔍 Backtesteando {ticker}...")
        signals = backtest_scan_for_u(ticker)
        if signals:
            log(f"[{ticker}] Total señales de U detectadas: {len(signals)}")
            for signal in signals:
                print(f"    📅 {signal['fecha']} - Nivel ruptura: {signal['nivel_ruptura']:.2f}, Slope: {signal['slope_left']:.2f}, Close: {signal['precio_cierre']:.2f}")
        else:
            log(f"[{ticker}] No se detectaron señales de U en el histórico.")

    elapsed_time = time.time() - start_time
    log(f"✅ BACKTEST finalizado. Tiempo total: {elapsed_time:.2f} segundos.")
