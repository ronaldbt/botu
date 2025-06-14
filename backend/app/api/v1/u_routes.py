# backend/app/api/v1/u_routes.py

from fastapi import APIRouter
from app.schemas.u_schema import SignalOut

router = APIRouter()

# ejemplo: endpoint para listar señales U (más adelante lo conectamos a DB)
@router.get("/signals", response_model=list[SignalOut])
def get_u_signals():
    # luego se reemplazará con query a Postgres
    return [
        SignalOut(id=1, ticker="AAPL", date="2024-06-01", nivel_ruptura=100.0, slope_left=-5.0, precio_cierre=110.0),
    ]
