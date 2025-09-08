# src/backtest_u.py

import yfinance as yf
import pandas as pd
import numpy as np
import time
import os
import sys
import random
import requests  # <== NECESARIO PARA SESIONES

# Importar para DB
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

try:
    from app.db.database import SessionLocal  # type: ignore
    from app.db import crud_tickers  # type: ignore
except ImportError as e:
    print(f"Error importing backend modules: {e}")
    raise

from utils import calc_slope, log

# === CONFIGURACION PRO ANTI-BAN ===

# Lista de User-Agents realistas
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

# === PARAMETROS ===

RUPTURE_FACTOR = 1.02
MIN_SLOPE_LEFT = -0.5
TICKER_SLEEP = 5    # segundos base entre tickers
BATCH_SLEEP = 15    # segundos base entre batches
BATCH_SIZE = 10     # tamaño de los batches de descarga

# === FUNCIONES ===

# Carga tickers desde DB
def load_tickers_from_db(tipo_filter=None, sub_tipo_filter=None, activo_only=True):
    log("Cargando tickers desde base de datos...")

    session = SessionLocal()
    try:
        tickers_db = crud_tickers.get_all_tickers(session)

        # Filtrar por activo
        if activo_only:
            tickers_db = [t for t in tickers_db if t.activo]

        # Filtrar por tipo / sub_tipo si se pasa
        if tipo_filter:
            tickers_db = [t for t in tickers_db if t.tipo == tipo_filter]
        if sub_tipo_filter:
            tickers_db = [t for t in tickers_db if t.sub_tipo == sub_tipo_filter]

        tickers = [t.ticker for t in tickers_db]
        log(f"Se cargaron {len(tickers)} tickers desde la DB (activo={activo_only}).")
        return tickers
    finally:
        session.close()

# BACKTEST SCANNER
def backtest_scan_for_u(ticker, df):
    log(f"[{ticker}] Procesando datos para backtest...")
    try:
        df_ticker = df[df['Ticker'] == ticker].copy()
        df_ticker.dropna(inplace=True)
        log(f"[{ticker}] Datos recibidos. Total de velas: {len(df_ticker)}.")
    except Exception as e:
        log(f"[{ticker}] ❌ Error procesando datos: {e}")
        return []

    df_ticker['min_local'] = (df_ticker['Low'].shift(2) > df_ticker['Low'].shift(1)) & (df_ticker['Low'].shift(1) < df_ticker['Low'])

    u_signals = []

    # Recorremos cada mínimo local
    for idx_min in df_ticker[df_ticker['min_local']].index:
        idx_min_pos = df_ticker.index.get_loc(idx_min)

        if idx_min_pos < 5 or idx_min_pos >= len(df_ticker) - 1:
            continue  # no hay suficientes velas antes o después

        # Palo izquierdo
        left_window = df_ticker.iloc[idx_min_pos - 5:idx_min_pos]['Close']
        slope_left = float(calc_slope(left_window))

        # Nivel de ruptura
        min_row = df_ticker.loc[idx_min]
        nivel_ruptura = min_row['High'] * RUPTURE_FACTOR

        # Ver si en las velas posteriores se rompe el nivel
        df_future = df_ticker.iloc[idx_min_pos + 1:]

        for idx_future, row_future in df_future.iterrows():
            close_actual = row_future['Close']
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

    # Parámetros opcionales (ej: python backtest_u.py crypto nasdaq)
    tipo_filter = sys.argv[1] if len(sys.argv) > 1 else None
    sub_tipo_filter = sys.argv[2] if len(sys.argv) > 2 else None

    tickers = load_tickers_from_db(tipo_filter, sub_tipo_filter)

    # Procesamos en batches
    for batch_start in range(0, len(tickers), BATCH_SIZE):
        batch_tickers = tickers[batch_start:batch_start + BATCH_SIZE]
        log(f"📦 Descargando batch de {len(batch_tickers)} tickers: {batch_tickers}...")

        # Elegir User-Agent aleatorio para este batch
        user_agent = random.choice(USER_AGENTS)
        log(f"🌐 Usando User-Agent: {user_agent}")

        # Crear sesión con User-Agent y asignarla a yfinance
        session = requests.Session()
        session.headers.update({'User-Agent': user_agent})
        yf.utils.get_yf_session = lambda: session

        try:
            df_batch = yf.download(
                tickers=batch_tickers,
                interval="1mo",
                start="2018-01-01",
                progress=False,
                group_by='ticker'
            )
        except Exception as e:
            error_msg = str(e).lower()
            log(f"❌ Error descargando batch {batch_tickers}: {e}")

            # Detectamos 429
            if "429" in error_msg or "too many requests" in error_msg:
                log(f"🚨 Detectado posible 429 Too Many Requests! Aplicando sleep largo...")
                sleep_time = 60 + random.uniform(10, 30)
            else:
                sleep_time = BATCH_SLEEP + random.uniform(0, 5)

            log(f"⏳ Esperando {sleep_time:.2f} segundos por error en batch...")
            time.sleep(sleep_time)
            continue

        # Normalizamos el DataFrame en formato "multi-index" → un DataFrame plano con 'Ticker' como columna
        dfs = []
        for ticker in batch_tickers:
            try:
                df_ticker = df_batch[ticker].copy()
                df_ticker['Ticker'] = ticker
                df_ticker['Date'] = df_ticker.index
                dfs.append(df_ticker)
            except Exception as e:
                log(f"[{ticker}] ⚠️ Error procesando DataFrame del batch: {e}")

        if not dfs:
            log(f"❌ No se pudo procesar ningún ticker del batch {batch_tickers}.")
            continue

        df_all = pd.concat(dfs)

        # Procesamos cada ticker individual
        for ticker in batch_tickers:
            log(f"🔍 Backtesteando {ticker}...")
            signals = backtest_scan_for_u(ticker, df_all)
            if signals:
                log(f"[{ticker}] Total señales de U detectadas: {len(signals)}")
                for signal in signals:
                    print(f"    📅 {signal['fecha']} - Nivel ruptura: {signal['nivel_ruptura']:.2f}, Slope: {signal['slope_left']:.2f}, Close: {signal['precio_cierre']:.2f}")
            else:
                log(f"[{ticker}] No se detectaron señales de U en el histórico.")

            # Sleep entre tickers (con jitter aleatorio)
            sleep_time = TICKER_SLEEP + random.uniform(0, 2)
            log(f"⏳ Esperando {sleep_time:.2f} segundos antes del próximo ticker...")
            time.sleep(sleep_time)

        # Sleep extra entre batches (con jitter aleatorio)
        sleep_time = BATCH_SLEEP + random.uniform(0, 5)
        log(f"⏳ Batch completo. Esperando {sleep_time:.2f} segundos para no sobrecargar Yahoo Finance...")
        time.sleep(sleep_time)

    elapsed_time = time.time() - start_time
    log(f"✅ BACKTEST finalizado. Tiempo total: {elapsed_time:.2f} segundos.")
