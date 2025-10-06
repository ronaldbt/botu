# src/main.py

import time
import random
import requests
import os
import sys

# Importar para DB
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

try:
    from app.db.database import SessionLocal  # type: ignore
    from app.db import crud_tickers  # type: ignore
except ImportError:
    # Fallback para el linter
    SessionLocal = None
    crud_tickers = None

# Importar scanners separados
from scanner_crypto import scan_crypto_for_u
from scanner_stocks import scan_stocks_for_u, set_custom_session
from utils import log
from estado_u_utils import should_scan, update_estado_u

# === CONFIGURACION PRO ANTI-BAN ===

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

TICKER_SLEEP = 5  # Sleep entre tickers para evitar 429

# === FUNCIONES ===

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

        # Devolver tickers con su tipo para routing
        tickers_data = [(t.ticker, t.tipo) for t in tickers_db]
        log(f"Se cargaron {len(tickers_data)} tickers desde la DB (activo={activo_only}).")
        return tickers_data
    finally:
        session.close()

def scan_ticker_by_type(ticker, tipo, verbose=False):
    """
    Enruta el ticker al scanner apropiado según su tipo
    """
    if tipo == 'crypto':
        return scan_crypto_for_u(ticker, verbose=verbose)
    else:
        # Crear sesión para acciones (anti-ban)
        user_agent = random.choice(USER_AGENTS)
        session = requests.Session()
        session.headers.update({'User-Agent': user_agent})
        set_custom_session(session)
        log(f"🌐 [STOCKS] Usando User-Agent: {user_agent}")
        
        return scan_stocks_for_u(ticker, verbose=verbose)

# === MAIN PROGRAM ===

start_time = time.time()
log("🚀 Iniciando BOT de detección de U...")

# Verificar si se debe ejecutar modo crypto
import os
from dotenv import load_dotenv
load_dotenv()

crypto_mode = os.getenv("BINANCE_CRYPTO_MODE", "false").lower() == "true"

if crypto_mode:
    log("🪙 Modo CRYPTO activado - Usando Binance Scanner")
    from binance_scanner import BinanceScanner
    scanner = BinanceScanner()
    scanner.run_crypto_scan()
    log("✅ Escaneo de crypto completado")
    exit(0)

# Modo mixto (todos los activos con scanners específicos)
log("🔄 Modo MIXTO activado - Escaneando todos los activos con scanners específicos")
tickers_data = load_tickers_from_db()

log(f"Comenzando escaneo de {len(tickers_data)} activos...")

alert_count = 0
total_tickers = len(tickers_data)
processed_tickers = 0

for ticker, tipo in tickers_data:
    try:
        # VERIFICAR SI SE DEBE ESCANEAR
        if not should_scan(ticker):
            continue

        processed_tickers += 1
        log(f"({processed_tickers}/{total_tickers}) Escaneando {ticker} [{tipo.upper()}]...")

        # Usar scanner específico según tipo
        result = scan_ticker_by_type(ticker, tipo, verbose=True)

        # === DETERMINAR nuevo_estado ===
        nuevo_estado = 'NO_U'
        if result['alert']:
            nuevo_estado = 'RUPTURA'
            message = (
                f"🚀 ¡Empieza la U en {ticker}!\n"
                f"🔹 Nivel de ruptura (precio de confirmación): {result['precio_confirmacion']:.2f}\n"
                f"🔹 ¡Revisar para posible compra!"
            )
            log(message)
            # send_telegram_message(message)  # Descomenta cuando lo configures
            alert_count += 1
        else:
            # Puedes refinar esta lógica según lo que detecte el scanner
            nuevo_estado = result.get('estado_sugerido', 'BASE')
            log(f"[{ticker}] No se detectó U en este activo. Estado sugerido: {nuevo_estado}")

        # ACTUALIZAR EstadoU en DB
        update_estado_u(
            ticker=ticker,
            nuevo_estado=nuevo_estado,
            nivel_ruptura=result['nivel_ruptura'] or 0.0,
            slope_left=result.get('slope_left', 0.0),
            precio_cierre=result.get('current_price', result.get('precio_confirmacion', 0.0))
        )

    except Exception as e:
        log(f"❌ Error escaneando {ticker} [{tipo.upper()}]: {e}")

    # Sleep entre tickers (con jitter aleatorio)
    sleep_time = TICKER_SLEEP + random.uniform(0, 2)
    log(f"⏳ Esperando {sleep_time:.2f} segundos antes del próximo ticker...")
    time.sleep(sleep_time)

# === FINAL ===

elapsed_time = time.time() - start_time
log(f"✅ Escaneo finalizado. Total alertas enviadas: {alert_count}.")
log(f"🕒 Tiempo total de ejecución: {elapsed_time:.2f} segundos.")
log("🚀 BOT de detección de U terminado.")
