# app/db/models.py

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.db.database import Base

# --------------------------
# Tabla Signal
# --------------------------

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    date = Column(Date)
    nivel_ruptura = Column(Float)
    slope_left = Column(Float)
    precio_cierre = Column(Float)

# --------------------------
# Tabla User
# --------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    logins = relationship("UserLogin", back_populates="user")

# --------------------------
# Tabla UserLogin
# --------------------------

class UserLogin(Base):
    __tablename__ = "user_logins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    login_time = Column(DateTime, default=func.now())
    ip_address = Column(String)
    user_agent = Column(String)

    user = relationship("User", back_populates="logins")

# --------------------------
# Tabla EstadoU
# --------------------------

class EstadoU(Base):
    __tablename__ = "estados_u"

    ticker = Column(String, primary_key=True, index=True)
    estado_actual = Column(String, nullable=False)
    ultima_fecha_escaneo = Column(Date, nullable=True)
    proxima_fecha_escaneo = Column(Date, nullable=True)
    nivel_ruptura = Column(Float, nullable=True)
    slope_left = Column(Float, nullable=True)
    precio_cierre = Column(Float, nullable=True)

# --------------------------
# Tabla Ticker
# --------------------------

class Ticker(Base):
    __tablename__ = "tickers"

    ticker = Column(String, primary_key=True, index=True)
    tipo = Column(String, nullable=False)  # 'crypto', 'accion', 'otro'
    sub_tipo = Column(String, nullable=True)  # Ej: 'dow_jones', 'nasdaq', 'brasil', etc.
    pais = Column(String, nullable=True)  # Ej: 'USA', 'Brasil', 'Francia', etc.
    nombre = Column(String, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    fecha_alta = Column(Date, nullable=False, server_default=func.current_date())
