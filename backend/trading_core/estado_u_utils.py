# src/estado_u_utils.py

import os
import sys
import datetime
from datetime import timedelta
from utils import log

# Importar acceso a DB
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

try:
    from app.db.database import SessionLocal  # type: ignore
    from app.db import crud_estados_u  # type: ignore
    from app.schemas import estados_u_schema  # type: ignore
except ImportError as e:
    log(f"Error importing backend modules: {e}")
    raise

# Definir las frecuencias de escaneo por estado (en días)
ESTADO_SCAN_FREQUENCY = {
    'NO_U': 30,           # una vez al mes
    'PALO_BAJANDO': 30,
    'BASE': 7,            # una vez a la semana
    'RUPTURA': 1,         # diario
    'POST_RUPTURA': 7
}

# Por si algún estado no definido:
DEFAULT_SCAN_FREQUENCY_DAYS = 7

# --- FUNCIONES ---

# Decide si se debería escanear un ticker según su estado y ultima_fecha_escaneo
def should_scan(ticker: str) -> bool:
    session = SessionLocal()
    try:
        estado_db = crud_estados_u.get_estado_u(session, ticker)
        if not estado_db:
            # Si no existe aún, lo escaneamos
            log(f"[{ticker}] No hay estado en DB. Se escaneará.")
            return True

        estado_actual = estado_db.estado_actual or 'NO_U'
        ultima_fecha_escaneo = estado_db.ultima_fecha_escaneo

        # Frecuencia en días según estado
        frecuencia_dias = ESTADO_SCAN_FREQUENCY.get(estado_actual, DEFAULT_SCAN_FREQUENCY_DAYS)

        # Calcular si ya pasó suficiente tiempo
        if not ultima_fecha_escaneo:
            log(f"[{ticker}] Sin fecha previa de escaneo. Se escaneará.")
            return True

        dias_desde_ultimo = (datetime.date.today() - ultima_fecha_escaneo).days

        if dias_desde_ultimo >= frecuencia_dias:
            log(f"[{ticker}] Último escaneo hace {dias_desde_ultimo} días. Se escaneará. (Estado actual: {estado_actual}, frecuencia: {frecuencia_dias} días)")
            return True
        else:
            log(f"[{ticker}] Último escaneo hace {dias_desde_ultimo} días. NO se escaneará. (Estado actual: {estado_actual}, frecuencia: {frecuencia_dias} días)")
            return False
    finally:
        session.close()

# Actualiza el EstadoU tras un escaneo
def update_estado_u(
    ticker: str,
    nuevo_estado: str,
    nivel_ruptura: float,
    slope_left: float,
    precio_cierre: float
):
    session = SessionLocal()
    try:
        hoy = datetime.date.today()
        frecuencia_dias = ESTADO_SCAN_FREQUENCY.get(nuevo_estado, DEFAULT_SCAN_FREQUENCY_DAYS)
        proxima_fecha_escaneo = hoy + timedelta(days=frecuencia_dias)

        estado_update = estados_u_schema.EstadoUCreate(
            ticker=ticker,
            estado_actual=nuevo_estado,
            ultima_fecha_escaneo=hoy,
            proxima_fecha_escaneo=proxima_fecha_escaneo,
            nivel_ruptura=nivel_ruptura,
            slope_left=slope_left,
            precio_cierre=precio_cierre
        )

        crud_estados_u.upsert_estado_u(session, estado_update)
        log(f"[{ticker}] EstadoU actualizado: estado={nuevo_estado}, próxima escaneo={proxima_fecha_escaneo}")

    finally:
        session.close()
