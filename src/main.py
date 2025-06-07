import time
from scanner import scan_for_u
# from telegram_bot import send_telegram_message  # Descomenta cuando lo configures
from utils import log

# Leer tickers desde un archivo txt
def load_tickers(file_path):
    log(f"Cargando tickers desde archivo: {file_path}")
    with open(file_path, 'r') as f:
        tickers = [line.strip() for line in f if line.strip() != ""]
    log(f"Se cargaron {len(tickers)} tickers.")
    return tickers

# MAIN PROGRAM

start_time = time.time()
log("🚀 Iniciando BOT de detección de U...")

tickers = load_tickers('tickers.txt')

log(f"Comenzando escaneo de {len(tickers)} activos...")

alert_count = 0
total_tickers = len(tickers)
processed_tickers = 0

for ticker in tickers:
    try:
        processed_tickers += 1
        log(f"({processed_tickers}/{total_tickers}) Escaneando {ticker}...")
        
        # Activamos verbose=True para que scanner.py también sea muy explicativo
        result = scan_for_u(ticker, verbose=True)
        
        if result['alert']:
            message = (
                f"🚀 ¡Empieza la U en {ticker}!\n"
                f"🔹 Nivel de ruptura (precio de confirmación): {result['precio_confirmacion']:.2f}\n"
                f"🔹 ¡Revisar para posible compra!"
            )
            log(message)
            # send_telegram_message(message)  # Descomenta cuando lo configures
            alert_count += 1
        else:
            log(f"[{ticker}] No se detectó U en este activo.")

    except Exception as e:
        log(f"❌ Error escaneando {ticker}: {e}")

elapsed_time = time.time() - start_time
log(f"✅ Escaneo finalizado. Total alertas enviadas: {alert_count}.")
log(f"🕒 Tiempo total de ejecución: {elapsed_time:.2f} segundos.")
log("🚀 BOT de detección de U terminado.")
