# backend/app/api/v1/u_routes.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud_estados_u
from app.schemas.u_schema import SignalOut

router = APIRouter()

@router.get("/signals", response_model=list[SignalOut])
def get_u_signals(db: Session = Depends(get_db)):
    """Obtiene las señales U reales de la base de datos basadas en estados de tickers"""
    try:
        # Obtener estados de tickers que tengan patrón U detectado
        estados = crud_estados_u.get_all_estados_u(db)
        
        # Convertir estados a señales para el dashboard
        signals = []
        for estado in estados:
            if estado.estado_actual in ['RUPTURA', 'U_DETECTADO'] and estado.ultima_fecha_escaneo:
                signals.append(SignalOut(
                    id=hash(estado.ticker),  # Usar hash del ticker como ID único
                    ticker=estado.ticker,
                    date=estado.ultima_fecha_escaneo.strftime("%Y-%m-%d"),
                    nivel_ruptura=estado.nivel_ruptura or 0.0,
                    slope_left=estado.slope_left or 0.0,
                    precio_cierre=estado.precio_cierre or 0.0
                ))
        
        return signals
    except Exception as e:
        print(f"Error obteniendo señales: {e}")
        return []
