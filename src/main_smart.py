# src/main_smart.py

import time
import random
import requests
from datetime import date
from scanner import scan_for_u, set_custom_session
from utils import log
from estado_u_utils import should_scan, update_estado_u, get_all_estados_u

# === CONFIGURACION PRO ANTI-BAN ===

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
]

TICKER_SLEEP = 5  # Sleep entre tickers para evitar 429

# === MAIN PROGRAM ===

start_time = time.time()
log("🚀 Iniciando BOT SMART de detección de U...")

# 1️⃣ Cargar todos los estados desde la DB
estados = get_all_estados_u()
log(f"Se cargaron {len(estados)} tickers desde la tabla estados_u.")

# 2️⃣ Filtrar solo los que toca escanear hoy
hoy = date.today()
tickers_a_scanear = [estado.ticker for estado in estados if estado.proxima_fecha_escaneo <= hoy]

log(f"Hoy toca escanear {len(tickers_a_scanear)} tickers ({len(estados)} en total en la DB).")

alert_count = 0
total_tickers = len(tickers_a_scanear)
processed_tickers = 0

for ticker in tickers_a_scanear:
    try:
        # Verificamos por seguridad si corresponde escanear (doble validación con should_scan)
        if not should_scan(ticker):
            log(f"[{ticker}] Saltado (should_scan=False).")
            continue

        processed_tickers += 1
        log(f"({processed_tickers}/{total_tickers}) Escaneando {ticker}...")

        # Crear User-Agent aleatorio y nueva sesión en cada ticker
        user_agent = random.choice(USER_AGENTS)
        session = requests.Session()
        session.headers.update({'User-Agent': user_agent})
        set_custom_session(session)

        log(f"🌐 Usando User-Agent: {user_agent}")

        # Escaneo con la session personalizada
        result = scan_for_u(ticker, verbose=True)

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
            nuevo_estado = result.get('estado_sugerido', 'BASE')
            log(f"[{ticker}] No se detectó U en este activo. Estado sugerido: {nuevo_estado}")

        # ACTUALIZAR EstadoU en DB
        update_estado_u(
            ticker=ticker,
            nuevo_estado=nuevo_estado,
            nivel_ruptura=result['nivel_ruptura'] or 0.0,
            slope_left=result.get('slope_left', 0.0),
            precio_cierre=result.get('precio_confirmacion', 0.0)
        )

    except Exception as e:
        log(f"❌ Error escaneando {ticker}: {e}")

    # Sleep entre tickers (con jitter aleatorio)
    sleep_time = TICKER_SLEEP + random.uniform(0, 2)
    log(f"⏳ Esperando {sleep_time:.2f} segundos antes del próximo ticker...")
    time.sleep(sleep_time)

# === FINAL ===

elapsed_time = time.time() - start_time
log(f"✅ SMART escaneo finalizado. Total alertas enviadas: {alert_count}.")
log(f"🕒 Tiempo total de ejecución: {elapsed_time:.2f} segundos.")
log("🚀 BOT SMART de detección de U terminado.")
