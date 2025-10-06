# backend/app/schemas/trading_schema.py

from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

# --------------------------
# Schemas para Trading API Keys
# --------------------------

class TradingApiKeyBase(BaseModel):
    exchange: str = "binance"
    is_testnet: bool = True
    is_active: bool = True
    auto_trading_enabled: bool = False
    max_position_size_usdt: float = 50.0
    max_concurrent_positions: int = 3
    risk_percentage: float = 0.02
    btc_enabled: bool = False
    eth_enabled: bool = False
    bnb_enabled: bool = False
    
    # Bitcoin 30m - Separado por red
    btc_30m_testnet_enabled: bool = False
    btc_30m_mainnet_enabled: bool = False
    
    btc_allocated_usdt: float = 0.0
    eth_allocated_usdt: float = 0.0
    bnb_allocated_usdt: float = 0.0
    
    # Bitcoin 30m - Asignaciones separadas por red
    btc_30m_testnet_allocated_usdt: float = 0.0
    btc_30m_mainnet_allocated_usdt: float = 0.0
    profit_target: float = 0.08  # 8% TP (misma estrategia probada)
    stop_loss: float = 0.03      # 3% SL (misma estrategia probada)
    max_hold_hours: int = 320    # 13.3 días (misma estrategia probada)

class TradingApiKeyCreate(TradingApiKeyBase):
    api_key: str
    secret_key: str
    
    @validator('api_key')
    def api_key_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('API Key no puede estar vacía')
        return v.strip()
    
    @validator('secret_key')
    def secret_key_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Secret Key no puede estar vacía')
        return v.strip()
    
    @validator('max_position_size_usdt')
    def validate_position_size(cls, v):
        if v <= 0:
            raise ValueError('El tamaño de posición debe ser mayor a 0')
        if v > 10000:  # Límite de seguridad
            raise ValueError('El tamaño de posición no puede exceder $10,000')
        return v
    
    @validator('risk_percentage')
    def validate_risk(cls, v):
        if v <= 0 or v > 0.1:  # Máximo 10% de riesgo
            raise ValueError('El riesgo debe estar entre 0.1% y 10%')
        return v

class TradingApiKeyUpdate(BaseModel):
    is_testnet: Optional[bool] = None
    is_active: Optional[bool] = None
    auto_trading_enabled: Optional[bool] = None
    max_position_size_usdt: Optional[float] = None
    max_concurrent_positions: Optional[int] = None
    risk_percentage: Optional[float] = None
    btc_enabled: Optional[bool] = None
    eth_enabled: Optional[bool] = None
    bnb_enabled: Optional[bool] = None
    
    # Bitcoin 30m - Separado por red
    btc_30m_testnet_enabled: Optional[bool] = None
    btc_30m_mainnet_enabled: Optional[bool] = None
    
    # Asignaciones Bitcoin 30m - Separado por red
    btc_30m_testnet_allocated_usdt: Optional[float] = None
    btc_30m_mainnet_allocated_usdt: Optional[float] = None
    profit_target: Optional[float] = None
    stop_loss: Optional[float] = None
    max_hold_hours: Optional[int] = None

class TradingApiKeyResponse(TradingApiKeyBase):
    id: int
    user_id: int
    api_key_masked: Optional[str] = None  # Solo mostrar primeros 8 caracteres
    created_at: datetime
    last_used: Optional[datetime] = None
    connection_status: str
    connection_error: Optional[str] = None
    
    class Config:
        from_attributes = True

# --------------------------
# Schemas para Trading Orders
# --------------------------

class TradingOrderBase(BaseModel):
    symbol: str
    side: str
    order_type: str = "MARKET"
    quantity: float
    price: Optional[float] = None
    take_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    reason: Optional[str] = None

class TradingOrderCreate(TradingOrderBase):
    api_key_id: int
    alerta_id: Optional[int] = None

class TradingOrderResponse(TradingOrderBase):
    id: int
    user_id: int
    api_key_id: int
    alerta_id: Optional[int] = None
    status: str
    binance_order_id: Optional[str] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[float] = None
    created_at: datetime
    executed_at: Optional[datetime] = None
    pnl_usdt: Optional[float] = None
    pnl_percentage: Optional[float] = None
    commission: Optional[float] = None
    commission_asset: Optional[str] = None
    
    class Config:
        from_attributes = True

# --------------------------
# Schemas para respuestas de API
# --------------------------

class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    account_info: Optional[dict] = None
    balance_usdt: Optional[float] = None
    testnet: bool

class TradingStatusResponse(BaseModel):
    auto_trading_enabled: bool
    active_positions: int
    total_orders_today: int
    pnl_today_usdt: float
    available_balance_usdt: float
    last_trade: Optional[datetime] = None

class EnableCryptoRequest(BaseModel):
    crypto: str  # 'btc', 'btc_30m', 'eth', 'bnb'
    enabled: bool

class UpdateCryptoAllocationRequest(BaseModel):
    crypto: str  # 'btc', 'btc_30m', 'eth', 'bnb'
    enabled: bool
    allocated_usdt: float
    
    @validator('allocated_usdt')
    def validate_allocation(cls, v):
        if v < 0:
            raise ValueError('La asignación no puede ser negativa')
        if v > 50000:  # Límite de seguridad
            raise ValueError('La asignación no puede exceder $50,000')
        return v
    
    @validator('crypto')
    def validate_crypto(cls, v):
        valid_cryptos = ['btc', 'btc_30m', 'btc_30m_testnet', 'btc_30m_mainnet', 'eth', 'bnb']
        if v.lower() not in valid_cryptos:
            raise ValueError(f'Crypto debe ser uno de: {", ".join(valid_cryptos)}')
        return v.lower()