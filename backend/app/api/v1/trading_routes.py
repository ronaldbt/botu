# backend/app/api/v1/trading_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.db.database import get_db
from app.db import crud_trading
from app.db.models import User, TradingApiKey
from app.schemas.trading_schema import (
    TradingApiKeyCreate, 
    TradingApiKeyUpdate, 
    TradingApiKeyResponse,
    TradingOrderResponse,
    ConnectionTestResponse,
    TradingStatusResponse,
    EnableCryptoRequest,
    UpdateCryptoAllocationRequest
)
from app.core.auth import get_current_user

# Importar binance_client desde src
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))
from binance_client import BinanceClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/trading", tags=["trading"])

# --------------------------
# Gestión de API Keys
# --------------------------

@router.post("/api-keys", response_model=TradingApiKeyResponse)
async def create_api_key(
    api_key_data: TradingApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una nueva API key de trading para el usuario"""
    try:
        logger.info(f"👤 Usuario {current_user.id} creando API key - Testnet: {api_key_data.is_testnet}")
        
        # Crear API key
        db_api_key = crud_trading.create_trading_api_key(db, api_key_data, current_user.id)
        
        # Preparar respuesta (enmascarar la API key)
        response_data = TradingApiKeyResponse.from_orm(db_api_key)
        response_data.api_key_masked = crud_trading.mask_api_key(api_key_data.api_key)
        
        logger.info(f"✅ API key creada exitosamente - ID: {db_api_key.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error creando API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error creando API key: {str(e)}")

@router.get("/api-keys", response_model=List[TradingApiKeyResponse])
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todas las API keys del usuario"""
    try:
        api_keys = crud_trading.get_user_trading_api_keys(db, current_user.id)
        
        # Preparar respuestas con API keys enmascaradas
        responses = []
        for api_key in api_keys:
            response = TradingApiKeyResponse.from_orm(api_key)
            # Obtener credenciales para enmascarar
            credentials = crud_trading.get_decrypted_api_credentials(db, api_key.id)
            if credentials:
                response.api_key_masked = crud_trading.mask_api_key(credentials[0])
            else:
                response.api_key_masked = "***ERROR***"
            responses.append(response)
        
        return responses
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo API keys: {str(e)}")

@router.put("/api-keys/{api_key_id}", response_model=TradingApiKeyResponse)
async def update_api_key(
    api_key_id: int,
    updates: TradingApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza configuración de una API key"""
    try:
        db_api_key = crud_trading.update_trading_api_key(db, api_key_id, current_user.id, updates)
        if not db_api_key:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        # Preparar respuesta
        response = TradingApiKeyResponse.from_orm(db_api_key)
        credentials = crud_trading.get_decrypted_api_credentials(db, api_key_id)
        if credentials:
            response.api_key_masked = crud_trading.mask_api_key(credentials[0])
        
        logger.info(f"✅ API key {api_key_id} actualizada por usuario {current_user.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando API key: {str(e)}")

@router.delete("/api-keys/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina una API key"""
    try:
        success = crud_trading.delete_trading_api_key(db, api_key_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        logger.info(f"✅ API key {api_key_id} eliminada por usuario {current_user.id}")
        return {"message": "API key eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando API key: {str(e)}")

# --------------------------
# Testing y Configuración
# --------------------------

@router.post("/test-connection/{api_key_id}", response_model=ConnectionTestResponse)
async def test_connection(
    api_key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Prueba la conexión con Binance usando una API key"""
    try:
        # Obtener API key
        api_key_config = crud_trading.get_trading_api_key(db, api_key_id, current_user.id)
        if not api_key_config:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        # Obtener credenciales
        credentials = crud_trading.get_decrypted_api_credentials(db, api_key_id)
        if not credentials:
            raise HTTPException(status_code=400, detail="No se pudieron obtener las credenciales")
        
        api_key, secret_key = credentials
        
        # Crear cliente y probar conexión
        client = BinanceClient(api_key, secret_key, testnet=api_key_config.is_testnet)
        success, result = client.test_connection()
        
        if success:
            # Actualizar estado en DB
            crud_trading.update_connection_status(db, api_key_id, 'active')
            
            # Obtener balance USDT si es posible
            balance_usdt = 0.0
            try:
                account_info = result
                for balance in account_info.get('balances', []):
                    if balance['asset'] == 'USDT':
                        balance_usdt = float(balance['free'])
                        break
            except:
                pass
            
            logger.info(f"✅ Conexión exitosa para usuario {current_user.id} - Balance: ${balance_usdt:.2f}")
            
            return ConnectionTestResponse(
                success=True,
                message="Conexión exitosa",
                account_info=result,
                balance_usdt=balance_usdt,
                testnet=api_key_config.is_testnet
            )
        else:
            # Actualizar estado de error
            crud_trading.update_connection_status(db, api_key_id, 'error', str(result))
            
            return ConnectionTestResponse(
                success=False,
                message=f"Error de conexión: {result}",
                testnet=api_key_config.is_testnet
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error probando conexión: {e}")
        raise HTTPException(status_code=500, detail=f"Error probando conexión: {str(e)}")

@router.put("/enable-crypto/{api_key_id}")
async def enable_disable_crypto(
    api_key_id: int,
    request: EnableCryptoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Habilita/deshabilita una crypto específica para trading automático"""
    try:
        # Mapear crypto a campo en la base de datos
        crypto_field = f"{request.crypto}_enabled"
        
        # Crear update dict
        update_dict = {crypto_field: request.enabled}
        updates = TradingApiKeyUpdate(**update_dict)
        
        # Actualizar
        db_api_key = crud_trading.update_trading_api_key(db, api_key_id, current_user.id, updates)
        if not db_api_key:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        action = "habilitada" if request.enabled else "deshabilitada"
        logger.info(f"✅ {request.crypto.upper()} {action} para usuario {current_user.id}")
        
        return {
            "message": f"{request.crypto.upper()} {action} para trading automático",
            "crypto": request.crypto,
            "enabled": request.enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configurando crypto: {e}")
        raise HTTPException(status_code=500, detail=f"Error configurando crypto: {str(e)}")

@router.put("/crypto-allocation/{api_key_id}")
async def update_crypto_allocation(
    api_key_id: int,
    request: UpdateCryptoAllocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la habilitación y asignación de balance para una crypto específica"""
    try:
        # Mapear crypto a campos en la base de datos
        enabled_field = f"{request.crypto}_enabled"
        allocated_field = f"{request.crypto}_allocated_usdt"
        
        # Crear update dict
        update_dict = {
            enabled_field: request.enabled,
            allocated_field: request.allocated_usdt
        }
        updates = TradingApiKeyUpdate(**update_dict)
        
        # Actualizar
        db_api_key = crud_trading.update_trading_api_key(db, api_key_id, current_user.id, updates)
        if not db_api_key:
            raise HTTPException(status_code=404, detail="API key no encontrada")
        
        action = "habilitada" if request.enabled else "deshabilitada"
        logger.info(f"✅ {request.crypto.upper()} {action} para usuario {current_user.id} con ${request.allocated_usdt} USDT")
        
        return {
            "message": f"{request.crypto.upper()} {action} con ${request.allocated_usdt} USDT asignados",
            "crypto": request.crypto,
            "enabled": request.enabled,
            "allocated_usdt": request.allocated_usdt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error configurando crypto allocation: {e}")
        raise HTTPException(status_code=500, detail=f"Error configurando crypto allocation: {str(e)}")

# --------------------------
# Monitoreo y Estadísticas
# --------------------------

@router.get("/status", response_model=TradingStatusResponse)
async def get_trading_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado actual del trading automático del usuario"""
    try:
        # Obtener API key activa
        active_api_key = crud_trading.get_active_trading_api_key(db, current_user.id)
        
        if not active_api_key:
            return TradingStatusResponse(
                auto_trading_enabled=False,
                active_positions=0,
                total_orders_today=0,
                pnl_today_usdt=0.0,
                available_balance_usdt=0.0
            )
        
        # Obtener estadísticas
        stats = crud_trading.get_trading_statistics(db, current_user.id, days=1)
        
        return TradingStatusResponse(
            auto_trading_enabled=active_api_key.auto_trading_enabled,
            active_positions=stats['active_positions'],
            total_orders_today=stats['total_orders'],
            pnl_today_usdt=stats['total_pnl_usdt'],
            available_balance_usdt=0.0,  # TODO: Obtener balance real
            last_trade=None  # TODO: Obtener último trade
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado de trading: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@router.get("/orders", response_model=List[TradingOrderResponse])
async def get_trading_orders(
    limit: int = 50,
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las órdenes de trading del usuario"""
    try:
        orders = crud_trading.get_user_trading_orders(db, current_user.id, limit, symbol, status)
        return [TradingOrderResponse.from_orm(order) for order in orders]
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo órdenes: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo órdenes: {str(e)}")

@router.get("/statistics")
async def get_trading_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene estadísticas de trading del usuario"""
    try:
        stats = crud_trading.get_trading_statistics(db, current_user.id, days)
        return {
            "period_days": days,
            "statistics": stats,
            "user_id": current_user.id
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.get("/health")
async def trading_health_check():
    """Health check para el módulo de trading"""
    return {
        "service": "trading",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "auto_trading": True,
            "supported_exchanges": ["binance"],
            "supported_cryptos": ["btc", "eth", "bnb"],
            "strategies": {
                "profit_target": "8%",
                "stop_loss": "3%",
                "max_hold": "13.3 days"
            }
        }
    }