# app/schemas/estados_u_schema.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

# Estado simple (para leer 1 estado simple)
class EstadoUSchema(BaseModel):
    ticker: str
    estado_actual: str
    ultima_fecha_escaneo: Optional[date] = None
    proxima_fecha_escaneo: Optional[date] = None
    nivel_ruptura: Optional[float] = None
    slope_left: Optional[float] = None
    precio_cierre: Optional[float] = None

    class Config:
        from_attributes = True

# Estado para crear o actualizar (POST / PUT)
class EstadoUCreate(BaseModel):
    ticker: str
    estado_actual: str
    ultima_fecha_escaneo: Optional[date] = None
    proxima_fecha_escaneo: Optional[date] = None
    nivel_ruptura: Optional[float] = None
    slope_left: Optional[float] = None
    precio_cierre: Optional[float] = None

# Estado con info del ticker (para mostrar en tabla del frontend)
class EstadoUWithTickerSchema(BaseModel):
    ticker: str
    estado_actual: str
    ultima_fecha_escaneo: Optional[date] = None
    proxima_fecha_escaneo: Optional[date] = None
    nivel_ruptura: Optional[float] = None
    slope_left: Optional[float] = None
    precio_cierre: Optional[float] = None
    tipo: Optional[str] = None
    sub_tipo: Optional[str] = None
    pais: Optional[str] = None

    class Config:
        from_attributes = True
