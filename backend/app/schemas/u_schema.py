# app/schemas/u_schema.py

from pydantic import BaseModel
from datetime import date

class SignalBase(BaseModel):
    ticker: str
    date: date
    nivel_ruptura: float
    slope_left: float
    precio_cierre: float

class SignalCreate(SignalBase):
    pass

class SignalOut(SignalBase):
    id: int

    class Config:
        from_attributes = True  # ← así es en Pydantic v2
