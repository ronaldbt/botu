# backend/app/schemas/alerta_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertaBase(BaseModel):
    ticker: str
    tipo_alerta: str  # 'PATRON_U', 'ORDEN_EJECUTADA', 'ERROR'
    mensaje: str
    nivel_ruptura: Optional[float] = None
    precio_actual: Optional[float] = None

class AlertaCreate(AlertaBase):
    pass

class AlertaResponse(AlertaBase):
    id: int
    fecha_creacion: datetime
    leida: bool
    usuario_id: Optional[int] = None

    class Config:
        from_attributes = True

class AlertaUpdate(BaseModel):
    leida: Optional[bool] = None

