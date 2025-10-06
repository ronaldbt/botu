# backend/app/schemas/orden_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class OrdenBase(BaseModel):
    ticker: str
    tipo_orden: str  # 'BUY', 'SELL'
    cantidad: float
    precio: Optional[float] = None
    motivo: Optional[str] = None
    nivel_ruptura: Optional[float] = None

class OrdenCreate(OrdenBase):
    pass

class OrdenResponse(OrdenBase):
    id: int
    precio_ejecutado: Optional[float] = None
    estado: str
    binance_order_id: Optional[str] = None
    fecha_creacion: datetime
    fecha_ejecucion: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

class OrdenUpdate(BaseModel):
    estado: Optional[str] = None
    precio_ejecutado: Optional[float] = None
    fecha_ejecucion: Optional[datetime] = None
    binance_order_id: Optional[str] = None

