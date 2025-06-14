# app/schemas/tickers_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import date

# Base (para uso común)
class TickerBase(BaseModel):
    ticker: str
    tipo: str                           # 'crypto', 'accion', 'otro'
    sub_tipo: Optional[str] = None      # Ej: 'dow_jones', 'nasdaq', 'brasil', etc.
    pais: Optional[str] = None          # Ej: 'USA', 'Brasil', 'Francia', etc.
    nombre: Optional[str] = None        # Nombre descriptivo
    activo: bool = True

# Para crear un ticker
class TickerCreate(TickerBase):
    pass

# Para devolver un ticker (con fecha_alta incluida)
class TickerOut(TickerBase):
    fecha_alta: date

    class Config:
        from_attributes = True  # Para compatibilidad con SQLAlchemy

# Para actualizar un ticker (campos opcionales)
class TickerUpdate(BaseModel):
    tipo: Optional[str] = None
    sub_tipo: Optional[str] = None
    pais: Optional[str] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = None

    class Config:
        from_attributes = True
