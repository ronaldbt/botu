# backend/app/schemas/alerta_schema.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AlertaBase(BaseModel):
    ticker: str
    crypto_symbol: str  # 'BTC', 'ETH', 'BNB'
    tipo_alerta: str  # 'BUY', 'SELL', 'ERROR', 'INFO'
    mensaje: str
    nivel_ruptura: Optional[float] = None
    precio_entrada: Optional[float] = None
    precio_salida: Optional[float] = None
    cantidad: Optional[float] = None
    profit_usd: Optional[float] = None
    profit_percentage: Optional[float] = None
    alerta_buy_id: Optional[int] = None
    bot_mode: Optional[str] = None  # 'manual', 'automatic'

class AlertaCreate(AlertaBase):
    pass

class AlertaResponse(AlertaBase):
    id: int
    fecha_creacion: datetime
    fecha_cierre: Optional[datetime] = None
    leida: bool
    usuario_id: Optional[int] = None
    telegram_sent: bool = False

    class Config:
        from_attributes = True

class AlertaUpdate(BaseModel):
    leida: Optional[bool] = None

