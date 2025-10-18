# backend/app/api/v1/paxg_mainnet_routes.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import User
from app.core.auth import get_current_user
from app.services.paxg_scanner_service import paxg_scanner
from app.services.auto_trading_executor import auto_trading_executor
from app.db.models import TradingOrder
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(prefix="/trading/scanner/paxg-mainnet", tags=["paxg-mainnet-scanner"])

# --------------------------
# Control del Scanner PAXG Mainnet
# --------------------------

@router.post("/start")
async def start_paxg_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicia el scanner de PAXG para Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) iniciando scanner PAXG Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        if paxg_scanner.is_running:
            return {
                "success": False,
                "message": "El scanner PAXG Mainnet ya está ejecutándose",
                "status": paxg_scanner.get_status()
            }
        
        # Iniciar scanner
        import asyncio
        asyncio.create_task(paxg_scanner.start_scanning())
        
        logger.info("✅ Scanner PAXG Mainnet iniciado exitosamente")
        return {
            "success": True,
            "message": "Scanner PAXG Mainnet iniciado exitosamente",
            "status": paxg_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error iniciando scanner PAXG Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando scanner: {str(e)}")

@router.post("/stop")
async def stop_paxg_scanner(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detiene el scanner de PAXG para Mainnet"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) deteniendo scanner PAXG Mainnet")
        
        # Solo admins pueden controlar el scanner
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden controlar el scanner"
            )
        
        if not paxg_scanner.is_running:
            return {
                "success": False,
                "message": "El scanner PAXG Mainnet no está ejecutándose",
                "status": paxg_scanner.get_status()
            }
        
        # Detener scanner
        await paxg_scanner.stop_scanning()
        
        logger.info("✅ Scanner PAXG Mainnet detenido exitosamente")
        return {
            "success": True,
            "message": "Scanner PAXG Mainnet detenido exitosamente",
            "status": paxg_scanner.get_status()
        }
            
    except Exception as e:
        logger.error(f"❌ Error deteniendo scanner PAXG Mainnet: {e}")
        raise HTTPException(status_code=500, detail=f"Error deteniendo scanner: {str(e)}")

@router.get("/status")
async def get_paxg_scanner_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el estado actual del scanner PAXG Mainnet"""
    try:
        status_data = paxg_scanner.get_status()
        
        return {
            "success": True,
            "data": status_data
        }
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado del scanner PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@router.get("/logs")
async def get_paxg_scanner_logs(
    force: bool = False,
    ts: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los logs del scanner PAXG Mainnet"""
    try:
        logs = paxg_scanner.scanner_logs
        
        # Filtrar logs si se especifica timestamp
        if ts:
            # Convertir timestamp a datetime para comparación
            ts_datetime = datetime.fromtimestamp(ts / 1000)
            logs = [log for log in logs if log.get('timestamp', datetime.min) > ts_datetime]
        
        return {
            "success": True,
            "data": {
                "logs": logs[-1000:],  # Últimos 1000 logs
                "total_logs": len(paxg_scanner.scanner_logs),
                "latest_log": logs[-1] if logs else None
            }
        }
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo logs del scanner PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo logs: {str(e)}")

@router.get("/current-price")
async def get_current_paxg_price(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el precio actual de PAXG"""
    try:
        # Usar el precio del último escaneo si está disponible
        status_data = paxg_scanner.get_status()
        current_price = status_data.get('paxg_price')
        
        if current_price:
            return {
                "success": True,
                "price": current_price,
                "source": "scanner"
            }
        
        # Si no hay precio del scanner, obtener de Binance directamente
        import requests
        
        # Obtener precio desde Binance
        url = "https://api.binance.com/api/v3/ticker/price"
        params = {'symbol': 'PAXGUSDT'}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        price = float(data['price'])
        
        return {
            "success": True,
            "price": price,
            "environment": "mainnet",
            "timestamp": datetime.now().isoformat()
        }
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo precio de PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo precio: {str(e)}")

@router.post("/force-buy")
async def force_paxg_buy_signal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Fuerza una señal de compra PAXG para testing"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) forzando compra PAXG")
        
        # Solo admins pueden forzar compras
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden forzar compras"
            )
        
        # Obtener precio actual
        status_data = paxg_scanner.get_status()
        current_price = status_data.get('paxg_price', 2500)  # Precio por defecto si no hay datos
        
        # Crear señal artificial
        artificial_signal = {
            "symbol": "PAXGUSDT",
            "price": current_price,
            "rupture_level": current_price * 1.02,  # 2% arriba del precio actual
            "pattern_depth": 0.03,  # 3% de profundidad
            "confidence": 0.85,
            "timestamp": datetime.now(),
            "source": "manual_force"
        }
        
        # Ejecutar compra automática
        try:
            result = await auto_trading_executor.execute_buy_signal('paxg', artificial_signal, alerta_id=None)
            
            if result and result.get('success'):
                return {
                    "success": True,
                    "message": "Señal de compra PAXG ejecutada exitosamente",
                    "signal": artificial_signal,
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "message": "No se pudo ejecutar la compra PAXG",
                    "signal": artificial_signal,
                    "result": result
                }
        except Exception as exec_error:
            logger.error(f"❌ Error ejecutando compra forzada PAXG: {exec_error}")
            return {
                "success": False,
                "message": f"Error ejecutando compra: {str(exec_error)}",
                "signal": artificial_signal
            }
            
    except Exception as e:
        logger.error(f"❌ Error forzando compra PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error forzando compra: {str(e)}")

@router.get("/orders")
async def get_paxg_orders(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las órdenes de PAXG del usuario"""
    try:
        # Buscar órdenes de PAXG
        orders = db.query(TradingOrder).filter(
            TradingOrder.user_id == current_user.id,
            TradingOrder.symbol == "PAXGUSDT"
        ).order_by(TradingOrder.created_at.desc()).limit(limit).all()
        
        return {
            "success": True,
            "data": orders
        }
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo órdenes PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo órdenes: {str(e)}")

# --------------------------
# Configuración del Scanner
# --------------------------

@router.put("/config")
async def update_paxg_scanner_config(
    config_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza la configuración del scanner PAXG (solo admin)"""
    try:
        logger.info(f"👤 Usuario {current_user.id} ({current_user.username}) actualizando config PAXG")
        
        # Solo admins pueden actualizar configuración
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo administradores pueden actualizar configuración"
            )
        
        # Actualizar configuración
        paxg_scanner.update_config(config_data)
        
        logger.info("✅ Configuración PAXG actualizada exitosamente")
        return {
            "success": True,
            "message": "Configuración PAXG actualizada exitosamente",
            "config": paxg_scanner.config
        }
            
    except Exception as e:
        logger.error(f"❌ Error actualizando configuración PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error actualizando configuración: {str(e)}")

@router.get("/config")
async def get_paxg_scanner_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene la configuración actual del scanner PAXG"""
    try:
        return {
            "success": True,
            "data": paxg_scanner.config
        }
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo configuración PAXG: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")
