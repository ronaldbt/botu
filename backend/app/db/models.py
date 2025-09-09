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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Campos de perfil personal
    full_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=True, index=True)
    phone = Column(String, nullable=True)
    country = Column(String, nullable=True)
    
    # Campos para Telegram por criptomoneda
    telegram_chat_id_btc = Column(String, nullable=True, index=True)
    telegram_chat_id_eth = Column(String, nullable=True, index=True)
    telegram_chat_id_bnb = Column(String, nullable=True, index=True)
    telegram_token_btc = Column(String, unique=True, nullable=True, index=True)
    telegram_token_eth = Column(String, unique=True, nullable=True, index=True)
    telegram_token_bnb = Column(String, unique=True, nullable=True, index=True)
    telegram_subscribed_btc = Column(Boolean, default=False)
    telegram_subscribed_eth = Column(Boolean, default=False)
    telegram_subscribed_bnb = Column(Boolean, default=False)
    
    # Campos de suscripción y pagos
    subscription_plan = Column(String, default='free')  # 'free', 'basic', 'premium'
    subscription_status = Column(String, default='inactive')  # 'active', 'inactive', 'suspended', 'expired'
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=True)  # 'paypal'
    paypal_subscription_id = Column(String, nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=func.now())

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
# Tabla EstadoU (ahora por criptomoneda)
# --------------------------

class EstadoU(Base):
    __tablename__ = "estados_u"

    ticker = Column(String, primary_key=True, index=True)
    crypto_symbol = Column(String, nullable=False, index=True)  # 'BTC', 'ETH', 'BNB'
    estado_actual = Column(String, nullable=False)
    ultima_fecha_escaneo = Column(DateTime, nullable=True)
    proxima_fecha_escaneo = Column(DateTime, nullable=True)
    nivel_ruptura = Column(Float, nullable=True)
    slope_left = Column(Float, nullable=True)
    precio_cierre = Column(Float, nullable=True)
    scanner_active = Column(Boolean, default=False)
    last_alert_sent = Column(DateTime, nullable=True)
    
    # Índice compuesto único
    __table_args__ = (
        {'extend_existing': True}
    )

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

# --------------------------
# Tabla Orden
# --------------------------

class Orden(Base):
    __tablename__ = "ordenes"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    tipo_orden = Column(String, nullable=False)  # 'BUY', 'SELL'
    cantidad = Column(Float, nullable=False)
    precio = Column(Float, nullable=True)  # Para órdenes limit
    precio_ejecutado = Column(Float, nullable=True)  # Precio real de ejecución
    estado = Column(String, nullable=False, default='PENDING')  # PENDING, FILLED, CANCELLED, FAILED
    binance_order_id = Column(String, nullable=True)  # ID de la orden en Binance
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_ejecucion = Column(DateTime, nullable=True)
    motivo = Column(String, nullable=True)  # Razón de la orden (ej: 'PATRON_U_DETECTADO')
    nivel_ruptura = Column(Float, nullable=True)  # Nivel de ruptura que disparó la orden
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relación con usuario
    usuario = relationship("User")

# --------------------------
# Tabla Alerta
# --------------------------

class Alerta(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, nullable=False, index=True)
    crypto_symbol = Column(String, nullable=False, index=True)  # 'BTC', 'ETH', 'BNB'
    tipo_alerta = Column(String, nullable=False)  # 'PATRON_U', 'ORDEN_EJECUTADA', 'ERROR'
    mensaje = Column(String, nullable=False)
    nivel_ruptura = Column(Float, nullable=True)
    precio_actual = Column(Float, nullable=True)
    fecha_creacion = Column(DateTime, default=func.now())
    leida = Column(Boolean, default=False)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    telegram_sent = Column(Boolean, default=False)
    
    # Relación con usuario
    usuario = relationship("User")

# --------------------------
# Tabla Subscription Plans
# --------------------------

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # 'free', 'basic', 'premium'
    display_name = Column(String, nullable=False)  # 'Plan Gratuito', 'Plan Básico', 'Plan Premium'
    description = Column(String, nullable=True)
    price_monthly = Column(Float, nullable=False, default=0.0)
    price_yearly = Column(Float, nullable=False, default=0.0)
    max_cryptos = Column(Integer, nullable=False, default=1)  # Número máximo de criptos
    features = Column(String, nullable=True)  # JSON string con características
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

# --------------------------
# Tabla Payment History
# --------------------------

class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    payment_method = Column(String, nullable=False)  # 'paypal'
    payment_provider_id = Column(String, nullable=False)  # PayPal transaction ID
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default='USD')
    billing_period = Column(String, nullable=False)  # 'monthly', 'yearly'
    status = Column(String, nullable=False)  # 'completed', 'pending', 'failed', 'refunded'
    payment_date = Column(DateTime, default=func.now())
    subscription_start = Column(DateTime, nullable=False)
    subscription_end = Column(DateTime, nullable=False)
    
    # Relaciones
    user = relationship("User")
    plan = relationship("SubscriptionPlan")
